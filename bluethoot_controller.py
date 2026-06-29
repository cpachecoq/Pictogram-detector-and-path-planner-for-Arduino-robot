import serial
import time


class BluetoothController:
    def __init__(self, port="COM4", baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.bt = None
        self.last_message = None

    def connect(self):
        try:
            self.bt = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
            print(f"Bluetooth conectado en {self.port}")
            return True
        except Exception as e:
            print(f"Error conectando Bluetooth: {e}")
            self.bt = None
            return False

    def send_navigation_data(self, nav_data):
        if self.bt is None:
            return

        action = nav_data["action"]

        if action == "NAVIGATE":
            angle = nav_data["angle"]
            distance = nav_data["distance"]
            message = f"F-{angle:.1f},{distance:.1f}\n"

        elif action == "STOP":
            message = "S\n"

        else:
            return  # HOLD no envía nada

        if message == self.last_message:
            return

        self.bt.write(message.encode("utf-8"))
        self.last_message = message

        print(f"Enviado: {message.strip()}")

    def close(self):
        if self.bt is not None:
            self.bt.write(b"S\n")
            self.bt.close()
            self.bt = None
            print("Bluetooth cerrado")