# Este script permite al usuario desplegar un sistema de monitoreo de espacios de estacionamientoMore actions
# utilizando un modelo YOLO para la detección de vehículos.
# El sistema incluye una interfaz web para visualizar el estado de los espacios y ajustar manualmente el conteo.
# Diseñado para ejecutarse en Jetson Nano, aunque puede adaptarse a otros dispositivos.

import cv2
import json
import time
import threading
from flask import Flask, render_template, Response, jsonify, request
from ultralytics import YOLO

# --- Inicializar la aplicación Flask ---
app = Flask(__name__)

# --- Variables globales ---
manual_adjustment = 0             # Ajustes manuales hechos por el usuario (+ o - ocupación)
detected_occupied = 0             # Conteo de espacios ocupados detectados automáticamente
current_light_state = "day"       # Estado actual de luz (día/noche)

# --- Cargar modelo YOLOv8 preentrenado para seguimiento (tracking) ---
model = YOLO('yolov8s.pt', task='track')


# --- Cargar zonas de estacionamiento desde archivo JSON ---
with open('zonas/parking_zones.json', 'r') as f:
    raw_zones = json.load(f)
    # Convertir coordenadas de las zonas a formato de tuplas de enteros
    zones = [((int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1]))) for (p1, p2) in raw_zones]

# Reducción de tamaño para acelerar el procesamiento (opcional)
resize_factor = 0.5
zones = [
    ((int(p1[0] * resize_factor), int(p1[1] * resize_factor)),
     (int(p2[0] * resize_factor), int(p2[1] * resize_factor)))
    for (p1, p2) in zones
]

# Total de zonas definidas
total_zones = len(zones)

# Inicializar la cámara (0 = cámara predeterminada)
camera = cv2.VideoCapture(0)

# --- Función para detectar si es de noche, basado en el promedio de brillo ---
def is_night(frame, threshold=60):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    avg_brightness = gray.mean()
    return avg_brightness < threshold, avg_brightness

# --- Mejorar imagen en condiciones nocturnas ---
def enhance_night_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

# --- Hilo principal para procesamiento de cámara y detección con YOLO ---
def process_camera():
    global detected_occupied, current_light_state
    frame_count = 0
    inference_interval = 3     # Realizar inferencia cada 3 cuadros
    last_results = None        # Guardar último resultado del modelo

    while True:
        ret, frame = camera.read()
        if not ret:
            continue

        # Redimensionar el frame
        frame = cv2.resize(frame, (0, 0), fx=resize_factor, fy=resize_factor)

        # Verificar si es de noche
        is_dark, brightness = is_night(frame)
        if is_dark:
            frame = enhance_night_image(frame)

        # Cambio automático de estado día/noche
        if is_dark and current_light_state == "day":
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cambio a modo NOCHE. Brillo: {brightness:.2f}")
            current_light_state = "night"
        elif not is_dark and current_light_state == "night":
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cambio a modo DÃ­a. Brillo: {brightness:.2f}")
            current_light_state = "day"

        frame_count += 1
        if frame_count % inference_interval == 0:
            last_results = model.track(frame, persist=True)

        # Extraer objetos detectados
        current_objects = []
        if last_results:
            for r in last_results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])  # Clase detectada
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    track_id = int(box.id[0]) if box.id is not None else None
                    current_objects.append({
                        'cls_id': cls_id,
                        'bbox': (x1, y1, x2, y2),
                        'track_id': track_id
                    })

        # Verificar si cada zona está ocupada
        detected = 0
        for (p1, p2) in zones:
            x_min, y_min = min(p1[0], p2[0]), min(p1[1], p2[1])
            x_max, y_max = max(p1[0], p2[0]), max(p1[1], p2[1])
            zone_occupied = False

            for obj in current_objects:
                if obj['cls_id'] == 2:  # Clase 2 = auto
                    ox1, oy1, ox2, oy2 = obj['bbox']
                    if ox1 < x_max and ox2 > x_min and oy1 < y_max and oy2 > y_min:
                        zone_occupied = True
                        break
            if zone_occupied:
                detected += 1

        detected_occupied = detected
        time.sleep(0.1)

# --- Iniciar hilo para la cámara (detección constante en segundo plano) ---
t = threading.Thread(target=process_camera, daemon=True)
t.start()

# ======================= RUTAS FLASK =========================

# Página principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para obtener lugares ocupados y totales
@app.route('/available_spots')
def get_spots():
    global manual_adjustment, detected_occupied
    raw_occupied = detected_occupied + manual_adjustment
    occupied = max(0, min(raw_occupied, total_zones))  # Limita el valor entre 0 y total
    return jsonify({"occupied": occupied, "total": total_zones})

# Ruta para ajustar manualmente el contador
@app.route('/adjust_occupied', methods=['POST'])
def adjust_occupied():
    global manual_adjustment
    data = request.get_json()
    action = data.get('action')

    # Incrementar, decrementar o resetear el contador manual
    if action == 'increment':
        manual_adjustment += 1
    elif action == 'decrement':
        manual_adjustment -= 1
    elif action == 'reset':
        manual_adjustment = 0
    return jsonify({'manual_adjustment': manual_adjustment})

# Ruta para transmitir el video desde la cámara
@app.route('/video')
def video():
    def gen():
        while True:
            ret, frame = camera.read()
            if not ret:
                continue
            resized = cv2.resize(frame, (0, 0), fx=resize_factor, fy=resize_factor)
            is_dark, _ = is_night(resized)
            if is_dark:
                frame = enhance_night_image(resized)
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Ruta para obtener el estado actual de luz (día o noche)
@app.route('/light_status')
def light_status():
    return jsonify({"light_condition": current_light_state})

# --- Ejecutar el servidor web Flask ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Ejecuta el servidor accesible desde cualquier IP local