# Este script permite al usuario desplegar un sistema de monitoreo de espacios de estacionamiento utilizando un modelo YOLO para la detección de vehículos. 
# El sistema incluye una interfaz web para visualizar el estado de los espacios y ajustar manualmente el conteo de ocupación.
# El sistema está diseñado para ser usado en una Jetson Nano, pero puede ser adaptado a otras plataformas.

import cv2
import json
import time
import threading
from flask import Flask, render_template, Response, jsonify, request
from ultralytics import YOLO

# --- Inicializar Flask ---
app = Flask(__name__)

# --- Variables globales ---
manual_adjustment = 0
detected_occupied = 0
current_light_state = "day"  # Puede ser "day" o "night"

# --- Cargar modelo YOLO ---
model = YOLO('yolov8s.pt', task='track')

# --- Cargar zonas desde archivo JSON ---
with open('zonas/parking_zones.json', 'r') as f:
    raw_zones = json.load(f)
    zones = [((int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1]))) for (p1, p2) in raw_zones]

resize_factor = 0.5
zones = [
    ((int(p1[0] * resize_factor), int(p1[1] * resize_factor)),
     (int(p2[0] * resize_factor), int(p2[1] * resize_factor)))
    for (p1, p2) in zones
]
total_zones = len(zones)
camera = cv2.VideoCapture(0)

# --- Funciones auxiliares ---
def is_night(frame, threshold=60):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    avg_brightness = gray.mean()
    return avg_brightness < threshold, avg_brightness

def enhance_night_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

# --- Hilo de procesamiento de cámara ---
def process_camera():
    global detected_occupied, current_light_state
    frame_count = 0
    inference_interval = 3
    last_results = None

    while True:
        ret, frame = camera.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (0, 0), fx=resize_factor, fy=resize_factor)

        is_dark, brightness = is_night(frame)
        if is_dark:
            frame = enhance_night_image(frame)

        if is_dark and current_light_state == "day":
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cambio a modo NOCHE. Brillo: {brightness:.2f}")
            current_light_state = "night"
        elif not is_dark and current_light_state == "night":
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cambio a modo DÍA. Brillo: {brightness:.2f}")
            current_light_state = "day"

        frame_count += 1
        if frame_count % inference_interval == 0:
            last_results = model.track(frame, persist=True)

        current_objects = []
        if last_results:
            for r in last_results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    track_id = int(box.id[0]) if box.id is not None else None
                    current_objects.append({
                        'cls_id': cls_id,
                        'bbox': (x1, y1, x2, y2),
                        'track_id': track_id
                    })

        detected = 0
        for (p1, p2) in zones:
            x_min, y_min = min(p1[0], p2[0]), min(p1[1], p2[1])
            x_max, y_max = max(p1[0], p2[0]), max(p1[1], p2[1])
            zone_occupied = False

            for obj in current_objects:
                if obj['cls_id'] == 2:
                    ox1, oy1, ox2, oy2 = obj['bbox']
                    if ox1 < x_max and ox2 > x_min and oy1 < y_max and oy2 > y_min:
                        zone_occupied = True
                        break
            if zone_occupied:
                detected += 1

        detected_occupied = detected
        time.sleep(0.1)

# --- Iniciar hilo de detección ---
t = threading.Thread(target=process_camera, daemon=True)
t.start()

# --- Rutas Flask ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/available_spots')
def get_spots():
    global manual_adjustment, detected_occupied
    raw_occupied = detected_occupied + manual_adjustment
    occupied = max(0, min(raw_occupied, total_zones))
    return jsonify({"occupied": occupied, "total": total_zones})

@app.route('/adjust_occupied', methods=['POST'])
def adjust_occupied():
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

@app.route('/light_status')
def light_status():
    return jsonify({"light_condition": current_light_state})

# --- Ejecutar servidor Flask ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
