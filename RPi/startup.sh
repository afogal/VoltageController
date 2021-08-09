#!/bin/sh
mosquitto -c /home/jddmartin/VoltageController/mosquitto.conf -d
sleep 1
python3 /home/jddmartin/VoltageController/RPi/main.py
