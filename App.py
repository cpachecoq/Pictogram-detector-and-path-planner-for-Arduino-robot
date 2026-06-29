import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.setWindowTitle("Modulo de Control Cavia Porcellus")
        self.setGeometry(100, 100, 640, 480)

        # Ventana de seleccion de Opciones
        self.video_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        self.setLayout(layout)

        # Inicializar la cámara
        self.cap = cv2.VideoCapture(2)  # Ajusta el número según tu cámara

        # Temporizador para actualizar los frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Refresca cada 30 ms

    def update_frame(self):
        """ Captura, detecta los objetos y dibuja la flecha de orientación """
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convertir de BGR a RGB
            
            # Convertir a HSV para filtrar colores
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

            # Definir rangos de color en HSV
            lower_green = np.array([40, 40, 40])   # Umbral inferior para verde
            upper_green = np.array([80, 255, 255]) # Umbral superior para verde
            mask_green = cv2.inRange(hsv, lower_green, upper_green)

            lower_red = np.array([0, 100, 100])    # Umbral inferior para rojo
            upper_red = np.array([10, 255, 255])   # Umbral superior para rojo
            mask_red = cv2.inRange(hsv, lower_red, upper_red)

            lower_blue = np.array([100, 50, 50])   # Umbral inferior para azul
            upper_blue = np.array([140, 255, 255]) # Umbral superior para azul
            mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

            # Detectar el centroide del cuadrado verde (posición del objeto)
            centroid_green = self.detect_shape(frame, mask_green, color=(255, 0, 0), label="Objeto")
            # Detectar el centro del círculo rojo (orientación del objeto)
            centroid_red = self.detect_shape(frame, mask_red, color=(0, 0, 255), label="Orientacion")
            # Detectar contornos de cuadrados azules
            centroid_blue = self.detect_shape(frame, mask_blue, color=(255, 0, 255), label="Destino")  # Rojo para contornos azules

            # Si ambos centroides fueron encontrados, dibujar la flecha
            if centroid_green and centroid_red:
                cv2.arrowedLine(frame, centroid_green, centroid_red, (0, 255, 255), 3, tipLength=0.2)
            
            # Si ambos centroides fueron encontrados, dibujar línea
            if centroid_green and centroid_blue:
                cv2.line(frame, centroid_green, centroid_blue, (0, 0, 255), 2)  # Línea amarilla

            # Convertir a QImage y mostrar en la GUI
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def detect_shape(self, frame, mask, color, label):
        """ Detecta la figura en la imagen y devuelve su centroide """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        centroid = None

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Filtrar ruido y objetos pequeños
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    cv2.circle(frame, (cx, cy), 5, color, -1)  # Dibujar centroide
                    cv2.putText(frame, f"{label} ({cx}, {cy})", (cx + 10, cy - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    centroid = (cx, cy)  # Guardar el centroide

        return centroid  # Retornar el centroide encontrado

    def closeEvent(self, event):
        """ Se ejecuta al cerrar la ventana """
        self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraApp()
    window.show()
    sys.exit(app.exec())
