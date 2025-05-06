import cv2
import json
import os

# Ruta de guardado
output_folder = 'zonas'
os.makedirs(output_folder, exist_ok=True)
output_file = os.path.join(output_folder, 'parking_zones.json')

# Variables globales
drawing = False
ix, iy = -1, -1
zones = []
current_rect = []

# Callback para el mouse
def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, current_rect

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            current_rect = [(ix, iy), (x, y)]

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        current_rect = [(ix, iy), (x, y)]
        zones.append(current_rect)
        print(f"Zona añadida: {current_rect}")
        current_rect = []

# Cargar imagen o video
cap = cv2.VideoCapture(1)
cv2.namedWindow('Marcar espacios')
cv2.setMouseCallback('Marcar espacios', draw_rectangle)

print("Presiona 's' para guardar y salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    clone = frame.copy()

    # Dibujar zonas ya guardadas
    for rect in zones:
        cv2.rectangle(clone, rect[0], rect[1], (0, 255, 0), 2)

    # Dibujar la zona actual
    if current_rect:
        cv2.rectangle(clone, current_rect[0], current_rect[1], (0, 0, 255), 1)

    cv2.imshow('Marcar espacios', clone)
    key = cv2.waitKey(1)

    if key == ord('s'):
        break
    elif key == ord('z') and zones:
        print("Última zona eliminada")
        zones.pop()

cap.release()
cv2.destroyAllWindows()

# Guardar zonas
json_zones = [ [list(p1), list(p2)] for (p1, p2) in zones ]
with open(output_file, 'w') as f:
    json.dump(json_zones, f, indent=4)

print(f"Zonas guardadas en {output_file}")
