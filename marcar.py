# Este script permite al usuario marcar zonas en un video en vivo desde la cámara.
# Se pueden dibujar rectángulos para definir áreas de interés, como espacios de estacionamiento.
# Al finalizar, las zonas se guardan en un archivo JSON para su posterior uso.

#Importar librerías necesarias
import cv2 # OpenCV para procesamiento de imágenes
import json # JSON para guardar las zonas
import os # OS para manejar rutas de archivos

# Ruta de guardado
output_folder = 'zonas'  # Carpeta donde se guardará el archivo JSON
os.makedirs(output_folder, exist_ok=True)  # Crea la carpeta si no existe
output_file = os.path.join(output_folder, 'parking_zones.json')  # Ruta completa del archivo de salida

# Variables globales
drawing = False  # Indica si el usuario está dibujando una zona
ix, iy = -1, -1  # Coordenadas iniciales del rectángulo
zones = []  # Lista de todas las zonas dibujadas
current_rect = []  # Zona que se está dibujando actualmente

# Callback del mouse para dibujar rectángulos
def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, current_rect

    # Cuando se presiona el botón izquierdo del mouse
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True  # Se empieza a dibujar
        ix, iy = x, y  # Se guardan las coordenadas iniciales

    # Mientras se mueve el mouse con el botón presionado
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            current_rect = [(ix, iy), (x, y)]  # Se actualiza el rectángulo actual

    # Cuando se suelta el botón izquierdo del mouse
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False  # Se deja de dibujar
        current_rect = [(ix, iy), (x, y)]  # Se define el rectángulo final
        zones.append(current_rect)  # Se agrega la zona a la lista
        print(f"Zona añadida: {current_rect}")
        current_rect = []  # Se limpia la zona actual

# Cargar video desde la cámara (índice 0)
cap = cv2.VideoCapture(0)
cv2.namedWindow('Marcar espacios')  # Crear ventana para mostrar la imagen
cv2.setMouseCallback('Marcar espacios', draw_rectangle)  # Asociar la función de callback del mouse

print("Presiona 's' para guardar y salir.")

# Bucle principal
while True:
    ret, frame = cap.read()  # Leer un frame del video
    if not ret:
        break  # Si no se puede leer el frame, salir del bucle

    clone = frame.copy()  # Crear una copia del frame para dibujar

    # Dibujar todas las zonas guardadas
    for rect in zones:
        cv2.rectangle(clone, rect[0], rect[1], (0, 255, 0), 2)  # Rectángulo verde

    # Dibujar la zona actual en rojo
    if current_rect:
        cv2.rectangle(clone, current_rect[0], current_rect[1], (0, 0, 255), 1)

    cv2.imshow('Marcar espacios', clone)  # Mostrar la imagen con las zonas

    key = cv2.waitKey(1)  # Esperar una tecla (con un pequeño retardo)

    if key == ord('s'):
        break  # Salir del bucle y guardar si se presiona 's'
    elif key == ord('z') and zones:
        print("Última zona eliminada")
        zones.pop()  # Eliminar la última zona agregada si se presiona 'z'

# Liberar la cámara y cerrar las ventanas
cap.release()
cv2.destroyAllWindows()

# Convertir las zonas a formato serializable (listas) y guardar en archivo JSON
json_zones = [ [list(p1), list(p2)] for (p1, p2) in zones ]
with open(output_file, 'w') as f:
    json.dump(json_zones, f, indent=4)

print(f"Zonas guardadas en {output_file}")
