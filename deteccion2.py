import sys
import cv2
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer
from ultralytics import YOLO

class YoloCameraApp(QWidget):
    def __init__(self):
        super().__init__()

        # Configurar la ventana
        self.setWindowTitle("Detección de pictogramas con YOLOv8")
        self.setGeometry(100, 100, 640, 480)

        # Crear un QLabel para mostrar la imagen de la cámara
        self.video_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        self.setLayout(layout)

        # Inicializar la cámara
        self.cap = cv2.VideoCapture(1)

        # Cargar el modelo YOLOv8 entrenado
        self.model = YOLO("best20.pt")  # Asegúrate de que esté en el mismo directorio

        # Temporizador para refrescar los frames
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Cada 30 ms

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Ejecutar detección con YOLOv8
            results = self.model.predict(
                source=frame, 
                imgsz=768,
                iou=0.5,
                conf=0.7, 
                verbose=False)
            annotated = results[0].plot()  # Imagen con boxes y etiquetas

            # Convertir a RGB para mostrar en PyQt
            rgb_image = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

# Ejecutar esta clase sola (puedes cambiarla por CameraApp para probar la otra)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YoloCameraApp()
    window.show()
    sys.exit(app.exec())