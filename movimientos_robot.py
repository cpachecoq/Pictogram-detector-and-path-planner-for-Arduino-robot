from PyQt6 import QtWidgets, QtGui, QtCore
import os
import vlc
import ctypes
import sys
import cv2
import numpy as np
import serial
import threading

libvlc_path = r'C:/Program Files/VideoLAN/VLC/libvlc.dll'

# Carga la biblioteca manualmente
ctypes.CDLL(libvlc_path)

class RobotControlApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.camera_index = 1
        self.frame_width = 800
        self.frame_height = 600
        self.cm_per_pixel = 0.1122
        self.serial_connection = None
        self.processing = False
        self.lock = threading.Lock()
        self.mtx, self.dist = self.load_calibration_params('calibration_parameters6.npz')
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
        self.video_player = None  # Instancia de la ventana de reproducción de video
        self.video_path_meta1 = 'videos/cultura cañari.mp4'  #Cultura cañari video 1
        self.video_path_meta2 = 'videos/leyenda_origen_pueblo_cañari.mp4'  #Leyenda cañari video 2
        self.video_path_meta3 = 'videos/ejemplo_inca.mp4'  # Video Inca se peude modificar
        self.current_video_path = None

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret and self.processing:
            frame_display = self.process_frames(frame)
            frame_rgb = cv2.cvtColor(frame_display, cv2.COLOR_BGR2RGB)
            qImg = QtGui.QImage(frame_rgb.data, frame_rgb.shape[1], frame_rgb.shape[0], QtGui.QImage.Format_RGB888)
            self.image_label.setPixmap(QtGui.QPixmap.fromImage(qImg))
        elif not ret:
            print("Failed to capture frame from camera.")

    def init_ui(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('Robot Control Interface')
        self.image_label = QtWidgets.QLabel(self)
        self.image_label.resize(800, 600)
        self.connect_button = QtWidgets.QPushButton('Connect', self)
        self.connect_button.clicked.connect(self.connect_to_robot)
        self.disconnect_button = QtWidgets.QPushButton('Disconnect', self)
        self.disconnect_button.clicked.connect(self.disconnect_from_robot)
        self.start_button = QtWidgets.QPushButton('Start', self)
        self.start_button.clicked.connect(self.start_processing)
        self.stop_button = QtWidgets.QPushButton('Stop', self)
        self.stop_button.clicked.connect(self.stop_processing)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)

    def load_calibration_params(self, file_path):
        data = np.load(file_path)
        return data['mtx'], data['dist']

    def connect_to_robot(self):
        try:
            self.serial_connection = serial.Serial('COM6', 9600, timeout=1)
            print("Connected to robot.")
        except serial.SerialException as e:
            print(f"Error connecting to robot: {e}")

    def disconnect_from_robot(self):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Disconnected from robot.")

    def start_processing(self):
        if not self.processing:
            self.processing = True
            print("Processing started.")

    def stop_processing(self):
        self.processing = False
        self.send_command_to_robot(0, 0)  # Send stop command
        print("Processing stopped.")

    def process_frames(self, frame):
        frame_undistorted = cv2.undistort(frame, self.mtx, self.dist, None, self.mtx)
        lab_image = cv2.cvtColor(frame_undistorted, cv2.COLOR_BGR2Lab)

        # Máscaras para el robot, la meta 1, la meta 2 y la meta 3
        mask_robot = cv2.inRange(lab_image, np.array([0, 0, 0]), np.array([255, 255, 109]))
        mask_meta = cv2.inRange(lab_image, np.array([0, 0, 0]), np.array([158, 120, 175]))
        mask_meta2 = cv2.inRange(lab_image, np.array([0, 138, 0]), np.array([70, 255, 255]))  # Meta 2
        mask_meta3 = cv2.inRange(lab_image, np.array([0, 0, 0]), np.array([0, 0, 0]))  # Meta 3 - Ajusta los valores según sea necesario
        mask_frente = cv2.inRange(lab_image, np.array([78, 137, 122]), np.array([133, 201, 135]))
        mask_frente2 = cv2.inRange(lab_image, np.array([179, 134, 0]), np.array([255, 255, 158]))
        mask_frente3 = cv2.inRange(lab_image, np.array([116, 140, 0]), np.array([255, 255, 157]))
        mask_frente4 = cv2.inRange(lab_image, np.array([209, 125, 82]), np.array([255, 255, 138]))
        mask_frente5 = cv2.inRange(lab_image, np.array([0, 152, 0]), np.array([0, 0, 0]))

        # Encontrar centroides
        centroid_robot = self.find_centroid(mask_robot)
        centroid_meta = self.find_centroid(mask_meta)
        centroid_meta2 = self.find_centroid(mask_meta2)
        centroid_meta3 = self.find_centroid(mask_meta3)
        centroid_frente = self.find_centroid(mask_frente)
        centroid_frente2 = self.find_centroid(mask_frente2)
        centroid_frente3 = self.find_centroid(mask_frente3)
        centroid_frente4 = self.find_centroid(mask_frente4)
        centroid_frente5 = self.find_centroid(mask_frente5)

        # Utilizar el primero de los centroides de "FRENTE" que sea válido
        effective_centroid_frente = centroid_frente if centroid_frente is not None else (
            centroid_frente2 if centroid_frente2 is not None else centroid_frente3 if centroid_frente3 is not None else centroid_frente4 if centroid_frente4 is not None else
            centroid_frente5)

        if centroid_robot and (centroid_meta or centroid_meta2 or centroid_meta3) and effective_centroid_frente:
            target_centroid = centroid_meta if centroid_meta else centroid_meta2 if centroid_meta2 else centroid_meta3
            cv2.line(frame_undistorted, centroid_robot, target_centroid, (0, 255, 0), 2)
            pixel_distance = np.linalg.norm(np.array(centroid_robot) - np.array(target_centroid))
            distance_cm = pixel_distance * self.cm_per_pixel
            angle = self.calculate_orientation_angle(centroid_robot, target_centroid, effective_centroid_frente)
            if distance_cm > 30:
                self.send_command_to_robot(distance_cm, angle)
                if self.video_player:
                    self.video_player.stop_video()
                    self.video_player = None
            else:
                self.send_command_to_robot(0, 0)
                if centroid_meta:
                    new_video_path = self.video_path_meta1
                elif centroid_meta2:
                    new_video_path = self.video_path_meta2
                else:
                    new_video_path = self.video_path_meta3

                if not self.video_player or self.current_video_path != new_video_path:
                    if self.video_player:
                        self.video_player.stop_video()
                    self.current_video_path = new_video_path
                    self.video_player = VideoPlayerWindow(self.current_video_path)
                    self.video_player.play_video()
            cv2.putText(frame_undistorted, f"Distancia: {distance_cm:.2f} cm, Ángulo: {angle:.2f} grados", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return frame_undistorted

    def find_centroid(self, mask):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if cv2.contourArea(contour) > 500:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        return None

    def calculate_orientation_angle(self, centroid_robot, centroid_meta, centroid_frente):
        vector_meta = np.array([centroid_meta[0] - centroid_robot[0], centroid_meta[1] - centroid_robot[1]])
        vector_frente = np.array([centroid_frente[0] - centroid_robot[0], centroid_frente[1] - centroid_robot[1]])

        vector_meta_norm = vector_meta / np.linalg.norm(vector_meta)
        vector_frente_norm = vector_frente / np.linalg.norm(vector_frente)

        dot_product = np.dot(vector_meta_norm, vector_frente_norm)
        angle = np.arccos(np.clip(dot_product, -1.0, 1.0)) * np.sign(np.cross(vector_frente_norm, vector_meta_norm))

        return np.degrees(angle)

    def send_command_to_robot(self, distance, angle):
        if self.serial_connection and self.serial_connection.is_open:
            command = f'F-{angle:.2f},{distance:.2f}\n' if distance > 30 else 'S\n'
            self.serial_connection.write(command.encode())
            print(f"Command sent: {command.strip()}")

    def closeEvent(self, event):
        if self.processing:
            self.stop_processing()
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        if self.video_player:
            self.video_player.stop_video()
        self.cap.release()
        event.accept()


class VideoPlayerWindow(QtWidgets.QWidget):
    def __init__(self, video_path):
        super().__init__()
        self.setWindowTitle('Video Playback')
        self.setGeometry(100, 100, 800, 600)
        
        self.video_widget = QtWidgets.QFrame(self)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.video_widget)
        
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self.media_player.set_hwnd(self.video_widget.winId())
        self.media = self.instance.media_new(video_path)
        self.media_player.set_media(self.media)
        
    def play_video(self):
        self.show()
        self.media_player.play()
        
    def stop_video(self):
        self.media_player.stop()
        self.close()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ex = RobotControlApp()
    ex.show()
    sys.exit(app.exec_())
