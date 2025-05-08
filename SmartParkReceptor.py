import RPi.GPIO as GPIO
import time
import requests

# Pines GPIO (BCM)
LED_VERDE = 18  # Pin físico 12
LED_ROJO = 23   # Pin físico 16

# Configuración de pines
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_ROJO, GPIO.OUT)

# IP de la Raspberry que ejecuta el YOLO
RASPBERRY_A_IP = 'http://192.168.1.100:5000/available_spots'  # Cambia esta IP

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
                # Apaga ambos si el número está en 22 (por si acaso)
                GPIO.output(LED_VERDE, GPIO.LOW)
                GPIO.output(LED_ROJO, GPIO.LOW)

        except Exception as e:
            print(f"Error al consultar: {e}")
            # Si falla la consulta, apagar ambos LEDs por seguridad
            GPIO.output(LED_VERDE, GPIO.LOW)
            GPIO.output(LED_ROJO, GPIO.LOW)

        time.sleep(2)

except KeyboardInterrupt:
    print("Programa detenido por el usuario.")

finally:
    GPIO.cleanup()
