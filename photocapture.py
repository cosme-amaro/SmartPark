import cv2
import os
from datetime import datetime, time as dtime
import time

# Intervalo de captura (segundos)
CAPTURE_INTERVAL = 30

# Horario de captura
START_TIME = dtime(5, 0)
END_TIME = dtime(23, 59)

# Carpeta base
PHOTO_BASE_DIR = 'photos'
os.makedirs(PHOTO_BASE_DIR, exist_ok=True)

# Inicializar cámara
cap = cv2.VideoCapture(0)

def capture_photo():
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    time_str = now.strftime('%H-%M-%S')

    date_folder = os.path.join(PHOTO_BASE_DIR, date_str)
    os.makedirs(date_folder, exist_ok=True)

    ret, frame = cap.read()
    if ret:
        filename = os.path.join(date_folder, f"{time_str}.jpg")
        cv2.imwrite(filename, frame)
        print(f"[📸] Foto guardada: {filename}")
        return frame
    else:
        print("[⚠️] Error al capturar la foto")
        return None

def is_within_schedule():
    now_time = datetime.now().time()
    return START_TIME <= now_time <= END_TIME

try:
    print("Captura de fotos activada. Presiona 's' para salir.")
    while True:
        if is_within_schedule():
            frame = capture_photo()
            if frame is not None:
                cv2.imshow("Vista previa - Presiona 's' para salir", frame)
        else:
            print(f"Fuera del horario permitido ({datetime.now().strftime('%H:%M:%S')}). Esperando...")
            black = 255 * np.ones((480, 640, 3), dtype=np.uint8)
            cv2.imshow("Vista previa - Fuera de horario", black)

        # Espera por tecla o timeout
        key = cv2.waitKey(CAPTURE_INTERVAL * 1000) & 0xFF
        if key == ord('s'):
            print("[🛑] Tecla 's' presionada. Finalizando captura.")
            break
except KeyboardInterrupt:
    print("\n Captura detenida manualmente con Ctrl+C.")
finally:
    cap.release()
    cv2.destroyAllWindows()
