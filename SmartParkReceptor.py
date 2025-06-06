# Este script es para la Raspberry Pi que recibe el conteo de espacios ocupados desde otra Raspberry o Jetson
# y enciende LEDs dependiendo de si hay lugares disponibles o no.

import RPi.GPIO as GPIO         # Librería para controlar los pines GPIO de la Raspberry Pi
import time                     # Librería para manejar pausas temporales
import requests                 # Librería para hacer solicitudes HTTP al servidor Flask

# Definición de los pines GPIO (usando numeración BCM)
LED_VERDE = 18  # LED verde conectado al GPIO 18 (pin físico 12)
LED_ROJO = 23   # LED rojo conectado al GPIO 23 (pin físico 16)

# Configuración de los pines como salidas
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_ROJO, GPIO.OUT)

# Dirección IP del servidor Flask que devuelve el número de lugares ocupados
RASPBERRY_A_IP = 'http://10.48.18.182:5000/available_spots'  # Cambiar esta IP según la red

# Umbral de ocupación (cuando hay 35 autos o más, se considera lleno)
UMBRAL_OCUPACION = 35

try:
    while True:
        try:
            # Consultar el número de lugares ocupados
            response = requests.get(RASPBERRY_A_IP, timeout=3)
            data = response.json()
            occupied = data.get('occupied', 0)

            print(f'Ocupados: {occupied}')

            # Lógica del semáforo:
            if occupied >= UMBRAL_OCUPACION:
                GPIO.output(LED_VERDE, GPIO.LOW)   # Apagar LED verde
                GPIO.output(LED_ROJO, GPIO.HIGH)   # Encender LED rojo
            else:
                GPIO.output(LED_VERDE, GPIO.HIGH)  # Encender LED verde
                GPIO.output(LED_ROJO, GPIO.LOW)    # Apagar LED rojo

        except Exception as e:
            print(f"Error al consultar: {e}")
            GPIO.output(LED_VERDE, GPIO.LOW)
            GPIO.output(LED_ROJO, GPIO.LOW)

        time.sleep(2)

except KeyboardInterrupt:
    print("Programa detenido por el usuario.")

finally:
    GPIO.cleanup()
