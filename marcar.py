#Importar librerías necesarias
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

# Factor de escala para agrandar la ventana
resize_factor = 1.5  # Puedes ajustar a 1.0, 1.2, 2.0, etc.

# Callback del mouse
def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, current_rect

    # Convertir coordenadas escaladas a originales
    x_unscaled = int(x / resize_factor)
    y_unscaled = int(y / resize_factor)

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x_unscaled, y_unscaled

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        current_rect = [(ix, iy), (x_unscaled, y_unscaled)]

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        current_rect = [(ix, iy), (x_unscaled, y_unscaled)]
        zones.append(current_rect)
        print(f"Zona añadida: {current_rect}")
        current_rect = []

# Cargar cámara
cap = cv2.VideoCapture(0)
cv2.namedWindow('Marcar espacios')
cv2.setMouseCallback('Marcar espacios', draw_rectangle)

print("Presiona 's' para guardar y salir.")

# Bucle principal
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Mostrar frame escalado para visualizar mejor
    display_frame = cv2.resize(frame, (0, 0), fx=resize_factor, fy=resize_factor)
    clone = display_frame.copy()

    # Dibujar zonas ya guardadas
    for rect in zones:
        # Escalar coordenadas para visualización
        p1_scaled = (int(rect[0][0] * resize_factor), int(rect[0][1] * resize_factor))
        p2_scaled = (int(rect[1][0] * resize_factor), int(rect[1][1] * resize_factor))
        cv2.rectangle(clone, p1_scaled, p2_scaled, (0, 255, 0), 2)

    if current_rect:
        p1_scaled = (int(current_rect[0][0] * resize_factor), int(current_rect[0][1] * resize_factor))
        p2_scaled = (int(current_rect[1][0] * resize_factor), int(current_rect[1][1] * resize_factor))
        cv2.rectangle(clone, p1_scaled, p2_scaled, (0, 0, 255), 1)

    cv2.imshow('Marcar espacios', clone)

    key = cv2.waitKey(1)

    if key == ord('s'):
        break
    elif key == ord('z') and zones:
        print("Última zona eliminada")
        zones.pop()

cap.release()
cv2.destroyAllWindows()

# Guardar zonas en formato JSON
json_zones = [[list(p1), list(p2)] for (p1, p2) in zones]
with open(output_file, 'w') as f:
    json.dump(json_zones, f, indent=4)

print(f"Zonas guardadas en {output_file}")
