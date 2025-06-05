# import libraries
import cv2
import json
import time
from ultralytics import YOLO

# load yolo model with tracking
model = YOLO('yolov8s.pt', task='track')

# load json with marked zones
with open('zonas/parking_zones.json', 'r') as f:
    raw_zones = json.load(f)
    zones = [((int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1]))) for (p1, p2) in raw_zones]

# Set camera
cap = cv2.VideoCapture(0)  # Change to your video source if needed

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Parameters for performance
target_fps = 10
frame_delay = 1.0 / target_fps
resize_factor = 1.5
last_frame_time = 0
inference_interval = 3  # Run inference every 3 frames
frame_count = 0

# Scale zones
zones = [(
    (int(p1[0] * resize_factor), int(p1[1] * resize_factor)),
    (int(p2[0] * resize_factor), int(p2[1] * resize_factor))
) for (p1, p2) in zones]

# Main loop
last_results = None

while cap.isOpened():
    current_time = time.time()
    if current_time - last_frame_time < frame_delay:
        continue
    last_frame_time = current_time

    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (0, 0), fx=resize_factor, fy=resize_factor)
    frame_count += 1

    # Run inference every few frames
    if frame_count % inference_interval == 0:
        last_results = model.track(frame, persist=True)

    current_objects = []
    if last_results:
        for r in last_results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                track_id = int(box.id[0]) if box.id is not None else None

                label = model.names[cls_id]
                color = (0, 255, 0) if cls_id == 0 else (255, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f'{label} {track_id}', (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                current_objects.append({
                    'cls_id': cls_id,
                    'bbox': (x1, y1, x2, y2),
                    'track_id': track_id
                })

    # Verificar zonas ocupadas
    occupied = 0
    for (p1, p2) in zones:
        x_min, y_min = min(p1[0], p2[0]), min(p1[1], p2[1])
        x_max, y_max = max(p1[0], p2[0]), max(p1[1], p2[1])
        zone_occupied = False

        for obj in current_objects:
            if obj['cls_id'] == 2:  # Car
                ox1, oy1, ox2, oy2 = obj['bbox']
                if ox1 < x_max and ox2 > x_min and oy1 < y_max and oy2 > y_min:
                    zone_occupied = True
                    break

        color = (0, 0, 255) if zone_occupied else (0, 255, 0)
        if zone_occupied:
            occupied += 1
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), color, 2)

    cv2.putText(frame, f' Available spaces: {occupied}/{len(zones)}', (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow('SmartPark', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
