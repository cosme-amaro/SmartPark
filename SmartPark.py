# Este script permite al usuario desplegar un sistema de monitoreo de espacios de estacionamiento utilizando un modelo YOLO para la detección de vehículos. 
# El sistema incluye una interfaz web para visualizar el estado de los espacios y ajustar manualmente el conteo de ocupación.
# El sistema está disñado para ser usado en una Jetson Nano, pero puede ser adaptado a otras plataformas.
#Importar librerías necesarias
import cv2
import json
import time # Para manejar el tiempo
import threading # Para manejar hilos
from flask import Flask, render_template, Response, jsonify, request # Flask para crear la API web
from ultralytics import YOLO # Importar el modelo YOLO

# --- Inicializar Flask ---

app = Flask(__name__)

# --- Variables globales ---
manual_adjustment = 0  # Ajuste manual de espacios ocupados (suma o resta)
detected_occupied = 0  # Número de espacios ocupados detectados automáticamente

# --- Cargar modelo YOLO ---
model = YOLO('yolov8s.pt', task='track')  # Carga el modelo YOLO para realizar seguimiento (tracking)

# --- Cargar zonas desde archivo JSON ---
with open('zonas/parking_zones.json', 'r') as f:
    raw_zones = json.load(f)
    zones = [((int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1]))) for (p1, p2) in raw_zones]

# Escalar zonas según factor de reducción
resize_factor = 0.5  # Factor para reducir el tamaño de la imagen y zonas
zones = [(
    (int(p1[0] * resize_factor), int(p1[1] * resize_factor)),
    (int(p2[0] * resize_factor), int(p2[1] * resize_factor))
) for (p1, p2) in zones]

total_zones = len(zones)  # Número total de zonas definidas
camera = cv2.VideoCapture(0)  # Inicializa la cámara (índice 0)

# --- Función que procesa la cámara en segundo plano ---
def process_camera():
    global detected_occupied
    frame_count = 0
    inference_interval = 3  # Realizar inferencia cada 3 frames
    last_results = None  # Resultados de inferencia anteriores

    while True:
        ret, frame = camera.read()
        if not ret:
            continue  # Si no se obtiene frame, continuar al siguiente ciclo

        # Redimensionar el frame para mejorar el rendimiento
        frame = cv2.resize(frame, (0, 0), fx=resize_factor, fy=resize_factor)
        frame_count += 1

        # Realizar inferencia con YOLO cada cierto número de frames
        if frame_count % inference_interval == 0:
            last_results = model.track(frame, persist=True)

        current_objects = []  # Lista de objetos detectados en este ciclo
        if last_results:
            for r in last_results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])  # Clase detectada (e.g., coche)
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Coordenadas de la caja
                    track_id = int(box.id[0]) if box.id is not None else None  # ID de seguimiento (opcional)
                    current_objects.append({
                        'cls_id': cls_id,
                        'bbox': (x1, y1, x2, y2),
                        'track_id': track_id
                    })

        # Detección automática de zonas ocupadas
        detected = 0  # Contador de zonas ocupadas
        for (p1, p2) in zones:
            # Calcular límites de la zona
            x_min = min(p1[0], p2[0])
            y_min = min(p1[1], p2[1])
            x_max = max(p1[0], p2[0])
            y_max = max(p1[1], p2[1])
            zone_occupied = False

            # Verificar si algún objeto (auto) está dentro de la zona
            for obj in current_objects:
                if obj['cls_id'] == 2:  # Clase 2 usualmente corresponde a "car"
                    ox1, oy1, ox2, oy2 = obj['bbox']
                    # Verifica si las cajas se sobrelapan (intersección con la zona)
                    if ox1 < x_max and ox2 > x_min and oy1 < y_max and oy2 > y_min:
                        zone_occupied = True
                        break
            if zone_occupied:
                detected += 1

        detected_occupied = detected  # Actualizar contador global
        time.sleep(0.1)  # Pequeño retardo para evitar uso excesivo de CPU

# --- Iniciar hilo de detección en segundo plano ---
t = threading.Thread(target=process_camera, daemon=True)
t.start()

# --- Rutas Flask para API y visualización ---

@app.route('/')
def index():
    # Renderiza la página principal (HTML)
    return render_template('index.html')

@app.route('/available_spots')
def get_spots():
    # Devuelve un JSON con el número de espacios ocupados y el total
    global manual_adjustment, detected_occupied
    raw_occupied = detected_occupied + manual_adjustment  # Aplica ajustes manuales
    occupied = max(0, min(raw_occupied, total_zones))  # Limita los valores a un rango válido
    return jsonify({"occupied": occupied, "total": total_zones})

@app.route('/adjust_occupied', methods=['POST'])
def adjust_occupied():
    # Ruta para ajustar manualmente el conteo de espacios ocupados
    global manual_adjustment
    data = request.get_json()
    action = data.get('action')
    if action == 'increment':
        manual_adjustment += 1
    elif action == 'decrement':
        manual_adjustment -= 1
    return jsonify({'manual_adjustment': manual_adjustment})

@app.route('/video')
def video():
    # Ruta que transmite video en vivo como flujo MJPEG
    def gen():
        while True:
            ret, frame = camera.read()
            if not ret:
                continue
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- Ejecutar servidor Flask ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # El servidor estará accesible en cualquier IP local
