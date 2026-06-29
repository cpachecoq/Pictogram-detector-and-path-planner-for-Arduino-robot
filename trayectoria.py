import sys
import cv2
import numpy as np
import math
import time
from ultralytics import YOLO
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer

class IntegratedApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chakana + Orientación y Destino")
        self.setGeometry(100, 100, 800, 600)

        self.video_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        self.setLayout(layout)

        self.cap = cv2.VideoCapture(2)  # Ajusta según tu cámara
        self.model = YOLO("best.pt")   # Modelo YOLOv8 entrenado

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.STOP_PX = 60          # empieza con 60 px, luego ajustamos
        self.ANGLE_DEADBAND = 7.0  # mismo umbral que Arduino
        self.last_send = 0.0
        self.SEND_PERIOD = 0.12    #

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        centroid_chakana = None

        # Detección con YOLO
        results = self.model.predict(source=rgb, conf=0.2, verbose=False)
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            if cls_id == 0:  
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                roi = rgb[y1:y2, x1:x2]  # Recorte del pictograma

                # Procesar ROI para centroide
                centroid_chakana = self.get_centroid_from_roi(roi, offset=(x1, y1))
                if centroid_chakana:
                    cv2.circle(rgb, centroid_chakana, 5, (0, 0, 255), -1)
                    cv2.putText(rgb, f"Chakana ({centroid_chakana[0]}, {centroid_chakana[1]})",
                                (centroid_chakana[0]+10, centroid_chakana[1]), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                break  # Tomamos solo una pictograma

        # Convertir a HSV
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

        # Detectar puntos de orientación (rojo) y destino (azul)
        centroid_red = self.detect_color_centroid(hsv, [0, 100, 100], [10, 255, 255], rgb, "Orientación", (255, 0, 0))
        centroid_blue = self.detect_color_centroid(hsv, [100, 50, 50], [140, 255, 255], rgb, "Origen", (0, 255, 255))

        if centroid_blue and centroid_red and centroid_chakana:
            angle_deg, distance_px = self.compute_angle_distance(
                origin=centroid_blue,
                orient=centroid_red,
                dest=centroid_chakana
            )
            cv2.putText(rgb, f"angle={angle_deg:.1f} deg  dist={distance_px:.1f}px",
                        (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
            
        now = time.time()
        if (now - self.last_send) >= self.SEND_PERIOD:
            self.last_send = now

            if distance_px <= self.STOP_PX:
                cmd = "S\n"
            else:
                cmd = f"F-{angle_deg:.2f},{distance_px:.1f}\n"
                
            # Por ahora solo imprimimos para comprobar (en el siguiente paso lo enviamos por BT)
            print("CMD:", cmd.strip())
        
        else:
            # Si pierdes detecciones, manda Stop cada cierto tiempo (seguridad)
            now = time.time()
            if (now - self.last_send) >= self.SEND_PERIOD:
                self.last_send = now
                print("CMD: S (lost target)")

        # Dibujar relaciones
        if centroid_chakana and centroid_red:
            cv2.arrowedLine(rgb, centroid_blue, centroid_red, (255, 255, 0), 3, tipLength=0.2)

        if centroid_chakana and centroid_blue:
            cv2.line(rgb, centroid_blue, centroid_chakana, (0, 255, 0), 2)

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

    def detect_color_centroid(self, hsv_frame, lower_hsv, upper_hsv, draw_frame, label, color):
        lower = np.array(lower_hsv)
        upper = np.array(upper_hsv)
        mask = cv2.inRange(hsv_frame, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            area = cv2.contourArea(c)
            if area > 500:
                M = cv2.moments(c)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    cv2.circle(draw_frame, (cx, cy), 5, color, -1)
                    cv2.putText(draw_frame, f"{label} ({cx},{cy})", (cx + 10, cy),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    return (cx, cy)
        return None
    
    def compute_angle_distance(self, origin, orient, dest):
        # origin O, orient R, dest D  -> (x, y)
        Ox, Oy = origin
        Rx, Ry = orient
        Dx, Dy = dest

        v = np.array([Rx - Ox, Ry - Oy], dtype=np.float32)  # orientación
        u = np.array([Dx - Ox, Dy - Oy], dtype=np.float32)  # hacia destino

        # distancia (pixeles)
        distance = float(np.linalg.norm(u))

        # si algún vector es muy pequeño, no calculamos ángulo
        if np.linalg.norm(v) < 1e-5 or np.linalg.norm(u) < 1e-5:
            return 0.0, distance

        dot = float(v[0]*u[0] + v[1]*u[1])
        cross = float(v[0]*u[1] - v[1]*u[0])

        angle_rad = math.atan2(cross, dot)
        angle_deg = -math.degrees(angle_rad)  # <- clave por sistema de coordenadas de imagen

        return angle_deg, distance

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IntegratedApp()
    window.show()
    sys.exit(app.exec())
