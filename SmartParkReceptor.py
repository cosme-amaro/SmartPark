# Este script es para la Raspberry Pi que recibe el conteo de espacios ocupados desde otra Raspberry o Jetson
# y enciende LEDs dependiendo de si hay lugares disponibles o no.

import RPi.GPIO as GPIO  # Librería para controlar los pines GPIO de la Raspberry Pi
import time  # Librería para manejar pausas temporales
import requests  # Librería para hacer solicitudes HTTP al servidor Flask
import json  # Librería para leer archivos JSON (en este caso, las zonas de estacionamiento)

# Definición de los pines GPIO (usando numeración BCM)
LED_VERDE = 18  # LED verde conectado al GPIO 18 (pin físico 12)
LED_ROJO = 23   # LED rojo conectado al GPIO 23 (pin físico 16)

# Configuración de los pines como salidas
GPIO.setmode(GPIO.BCM)  # Usar la numeración de los pines BCM
GPIO.setup(LED_VERDE, GPIO.OUT)  # Configurar el pin del LED verde como salida
GPIO.setup(LED_ROJO, GPIO.OUT)   # Configurar el pin del LED rojo como salida

# Dirección IP del servidor Flask que devuelve el número de lugares ocupados
RASPBERRY_A_IP = 'http://192.168.1.100:5000/available_spots'  # Cambiar esta IP según la red

# Leer el archivo JSON que contiene las zonas para calcular el número total de lugares
try:
    with open('zonas/parking_zones.json', 'r') as f:
        raw_zones = json.load(f)  # Cargar el archivo JSON como una lista
        total_zones = len(raw_zones)  # El número total de zonas es igual al número de coordenadas guardadas
        print(f'Total de lugares disponibles: {total_zones}')
except Exception as e:
    print(f"Error al leer zonas: {e}")
    total_zones = 0  # En caso de error, se asigna 0 como número total de lugares

# Bucle principal del programa
try:
    while True:
        try:
            # Enviar solicitud al servidor para obtener el número de lugares ocupados
            response = requests.get(RASPBERRY_A_IP, timeout=3)  # Esperar hasta 3 segundos por respuesta
            data = response.json()  # Convertir la respuesta a formato JSON
            occupied = data.get('occupied', 0)  # Obtener el número de lugares ocupados

            print(f'Ocupados: {occupied}')  # Imprimir por consola

            # Lógica del semáforo:
            # Si todos los lugares están ocupados, encender el LED rojo
            if occupied >= total_zones:
                GPIO.output(LED_VERDE, GPIO.LOW)   # Apagar LED verde
                GPIO.output(LED_ROJO, GPIO.HIGH)   # Encender LED rojo
            else:
                # Si hay al menos un lugar libre, encender el LED verde
                GPIO.output(LED_VERDE, GPIO.HIGH)  # Encender LED verde
                GPIO.output(LED_ROJO, GPIO.LOW)    # Apagar LED rojo

        except Exception as e:
            # Si ocurre un error (por ejemplo, falla la conexión con el servidor), se apagan ambos LEDs
            print(f"Error al consultar: {e}")
            GPIO.output(LED_VERDE, GPIO.LOW)
            GPIO.output(LED_ROJO, GPIO.LOW)

        time.sleep(2)  # Esperar 2 segundos antes de hacer la siguiente consulta

except KeyboardInterrupt:
    # Si el usuario presiona Ctrl+C, se muestra un mensaje y se limpia la configuración de GPIO
    print("Programa detenido por el usuario.")

finally:
    GPIO.cleanup()  # Restablecer todos los pines GPIO usados

