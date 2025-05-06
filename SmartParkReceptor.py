import RPi.GPIO as GPIO
import time
import requests

# Configuración de pines
LED_VERDE = 17
LED_ROJO = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_ROJO, GPIO.OUT)

# IP de la Raspberry que ejecuta el YOLO
RASPBERRY_A_IP = 'http://192.168.1.100:5000/available_spots'  # Cambia a tu IP real

try:
    while True:
        try:
            response = requests.get(RASPBERRY_A_IP, timeout=3)
            data = response.json()
            occupied = data.get('occupied', 0)

            print(f'Ocupados: {occupied}')

            # Lógica de semáforo
            if occupied <= 21:
                GPIO.output(LED_VERDE, GPIO.HIGH)
                GPIO.output(LED_ROJO, GPIO.LOW)
            elif occupied >= 23:
                GPIO.output(LED_VERDE, GPIO.LOW)
                GPIO.output(LED_ROJO, GPIO.HIGH)
            else:
                # Ningún LED encendido si está entre 22
                GPIO.output(LED_VERDE, GPIO.LOW)
                GPIO.output(LED_ROJO, GPIO.LOW)

        except Exception as e:
            print(f"Error al consultar: {e}")
            GPIO.output(LED_VERDE, GPIO.LOW)
            GPIO.output(LED_ROJO, GPIO.LOW)

        time.sleep(2)  # Esperar 2 segundos

except KeyboardInterrupt:
    print("Programa detenido por usuario.")

finally:
    GPIO.cleanup()
