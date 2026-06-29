import sys
import cv2
import numpy as np
from ultralytics import YOLO
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer

CATEGORY_MAP = {
    "Chakana": "chakana",
    "Condor": "condor",
    "Cuy": "cuy",
    "Llama": "llama",
    "Maiz": "maiz",
    "Tinaja": "tinaja",
    "Zampoña": "zampona"
}

class IntegratedApp(QWidget):
    def __init__(self, category="Chakana"):
        super().__init__()

        self.category_label = category
        self.category = CATEGORY_MAP.get(category, category.lower())

        self.setWindowTitle(f"Detección: {self.category}")
        self.setGeometry(100, 100, 800, 600)

        self.video_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        self.setLayout(layout)

        self.cap = cv2.VideoCapture(1)
        self.model = YOLO("best20.pt")

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def setCategory(self, category):
        self.category_label = category
        self.category = CATEGORY_MAP.get(category, category.lower())
        self.setWindowTitle(f"Detección: {self.category_label}")

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        centroid_target = None

        # Detección con YOLO
        results = self.model.predict(
            source=frame,
            imgsz=768,
            iou=0.5,
            conf=0.7,
            verbose=False
        )

        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            class_name = self.model.names[cls_id]
 
            if class_name == self.category:
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                centroid_target = (cx, cy)

                cv2.circle(rgb, centroid_target, 6, (0, 0, 255), -1)
                cv2.putText(
                    rgb,
                    f"{self.category_label} ({cx},{cy})",
                    (cx + 10, cy),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )
                break

        # Convertir a HSV
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

        red_ranges = [
            ([0, 120, 70],   [10, 255, 255]),
            ([170, 120, 70], [179, 255, 255])
        ]

        blue_ranges = [
            ([90, 80, 50], [130, 255, 255])
        ]
    

        # Detectar puntos de orientación (rojo) y destino (azul)
        centroid_red = self.detect_color_centroid(hsv, red_ranges, rgb, "Orientación", (255, 0, 0), min_area=200)
        centroid_blue = self.detect_color_centroid(hsv, blue_ranges, rgb, "Origen", (0, 255, 255), min_area=200)

        # Dibujar relaciones
        if centroid_target and centroid_red and centroid_blue:
            cv2.arrowedLine(rgb, centroid_blue, centroid_red, (255, 255, 0), 3, tipLength=0.2)

        if centroid_target and centroid_blue:
            cv2.line(rgb, centroid_blue, centroid_target, (0, 255, 0), 2)

        # Mostrar en la interfaz
        h, w, ch = rgb.shape
        qt_image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    def get_centroid_from_roi(self, roi, offset=(0, 0)):
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
        _, thresh = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None
        
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        if area < 500:
            return None
        
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"]) + offset[0]
            cy = int(M["m01"] / M["m00"]) + offset[1]
            return (cx, cy)

        return None

    def detect_color_centroid(self, hsv_frame, ranges, draw_frame, label, color_rgb, min_area=250):
        """
        ranges: lista de tuplas (lowerHSV, upperHSV) para permitir múltiples rangos (ej rojo)
        color_rgb: color para dibujar sobre frame RGB (no BGR)
        """
        
        mask_total = None
        for (lower_hsv, upper_hsv) in ranges:
            lower = np.array(lower_hsv, dtype=np.uint8)
            upper = np.array(upper_hsv, dtype=np.uint8)
            mask = cv2.inRange(hsv_frame, lower, upper)
            mask_total = mask if mask_total is None else cv2.bitwise_or(mask_total, mask)

        # Limpieza de máscara (quita ruido + rellena)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_OPEN, kernel, iterations=1)
        mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        
        # Elegir mejor contorno por área (el más grande que pase min_area)
        best = None
        best_area = 0
        for c in contours:
            area = cv2.contourArea(c)
            if area >= min_area and area > best_area:
                best_area = area
                best = c

        if best is None:
            return None
        
        M = cv2.moments(best)
        if M["m00"] == 0:
            return None
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # Dibujo en frame RGB
        cv2.circle(draw_frame, (cx, cy), 6, color_rgb, -1)
        cv2.putText(draw_frame, f"{label} ({cx},{cy})", (cx + 10, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_rgb, 2)
        
        return (cx, cy)

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IntegratedApp()
    window.show()
    sys.exit(app.exec())
