# SmartPark: Parking Monitoring System with YOLO, Jetson Nano and RaspberryPi3

**SmartPark** is a real-time vehicle detection system that uses computer vision to monitor parking occupancy and control a physical LED traffic light. Built using YOLOv8, Flask, Jetson, and Raspberry Pi, it allows users to view live parking availability through a web interface and reflect status using red and green LEDs.

## Features

- 🅿️ Vehicle detection using YOLOv8 (`yolov8s.pt`)
- 📸 Live video streaming via Flask
- 🧠 Occupancy logic based on manually defined zones
- 🔴🟢 Physical LED traffic light control with Raspberry Pi
- 🌐 Real-time parking status via HTTP API

## System Overview

- `zonas/parking_zones.json` – Coordinates for parking zones selected manually.
- `SmartPark.py` – Flask server that runs YOLO inference and exposes `/video` and `/available_spots` endpoints.
- `marcar.py` – Tool for manually marking parking zones over live camera feed.
- `SmarParkReceptor.py` – Raspberry Pi script that reads parking data and controls LEDs accordingly.

## Requirements

### Jetson or PC with Camera:
- Python 3.8+
- OpenCV
- Flask
- Ultralytics 

### Raspberry Pi (for LED control):
- Python 3
- RPi.GPIO
- requests
