import cv2
import json
import time
import threading
from flask import Flask, render_template, Response, jsonify, request
from ultralytics import YOLO

app = Flask(__name__)

# --- Variables globales ---
manual_occupied = 0  # Autos ocupando lugares (modificable con botones)
total_zones = 22     # Lugares totales (fijo)

# --- Cargar modelo YOLO ---
model = YOLO('yolov8s.pt', task='track')

# --- Cargar zonas desde archivo JSON ---
with open('zonas/parking_zones.json', 'r') as f:
    raw_zones = json.load(f)
    zones = [((int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1]))) for (p1, p2) in raw_zones]

# Escalar zonas según factor de reducción
resize_factor = 0.5
zones = [(
    (int(p1[0] * resize_factor), int(p1[1] * resize_factor)),
    (int(p2[0] * resize_factor), int(p2[1] * resize_factor))
) for (p1, p2) in zones]

camera = cv2.VideoCapture(0)

def process_camera():
    global manual_occupied
    frame_count = 0
    inference_interval = 3
    last_results = None

    while True:
        ret, frame = camera.read()
        if not ret:
            continue

        frame = cv2.resize(frame, (0, 0), fx=resize_factor, fy=resize_factor)
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

        # --- Conteo automático (aún no implementado) ---
        """
        occupied = 0
        for (p1, p2) in zones:
            x_min = min(p1[0], p2[0])
            y_min = min(p1[1], p2[1])
            x_max = max(p1[0], p2[0])
            y_max = max(p1[1], p2[1])
            zone_occupied = False

            for obj in current_objects:
                if obj['cls_id'] == 2:
                    ox1, oy1, ox2, oy2 = obj['bbox']
                    if ox1 < x_max and ox2 > x_min and oy1 < y_max and oy2 > y_min:
                        zone_occupied = True
                        break
            if zone_occupied:
                occupied += 1

        manual_occupied = occupied
        """

        time.sleep(0.1)

# --- Hilo del procesamiento ---
t = threading.Thread(target=process_camera, daemon=True)
t.start()

# --- Flask Endpoints ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/available_spots')
def get_spots():
    return jsonify({"occupied": manual_occupied, "total": total_zones})

@app.route('/update_occupied', methods=['POST'])
def update_occupied():
    global manual_occupied
    data = request.get_json()
    action = data.get('action')
    if action == 'increment' and manual_occupied < total_zones:
        manual_occupied += 1
    elif action == 'decrement' and manual_occupied > 0:
        manual_occupied -= 1
    return jsonify({'occupied': manual_occupied})

@app.route('/video')
def video():
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
