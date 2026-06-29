import serial
import time

PORT = "COM4"
BAUDRATE = 9600

def send_command(bt, command):
    message = command + "\n"
    bt.write(message.encode("utf-8"))
    print(f"Enviado: {command}")

try:
    print(f"Conectando a {PORT}...")
    bt = serial.Serial(PORT, BAUDRATE, timeout=1)

    time.sleep(2)  # tiempo para que el HC-05 establezca conexión

    print("Conectado. Enviando comandos...")

    send_command(bt, "V-120")
    time.sleep(3)

    send_command(bt, "F-0,100")
    time.sleep(3)

    send_command(bt, "S")
    time.sleep(0.5)

    bt.close()
    print("Puerto cerrado.")

except serial.SerialException as e:
    print("Error de conexión serial:")
    print(e)

except Exception as e:
    print("Error inesperado:")
    print(e)