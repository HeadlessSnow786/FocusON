import serial
import time

# Replace with the correct port (e.g., "COM5" or "/dev/ttyACM1")
port = "/dev/cu.usbmodem1103"
ser = serial.Serial(port, 9600)

def score_to_color(score):
    if score >= 70:
        return "green"
    elif score >= 30:
        return "yellow"
    else:
        return "red"

def send_color(score):
    color = score_to_color(score)
    ser.write((color + "\n").encode())

# Example test
scores = [95, 50, 20, 75, 65, 10]
for s in scores:
    send_color(s)
    time.sleep(1)