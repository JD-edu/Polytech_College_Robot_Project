import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import cv2
from google.generativeai import GenerativeModel, configure
from google.ai.generativelanguage_v1beta import Part
import base64
import numpy as np

class GeminiThread(QThread):
    response_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, client, image):
        super().__init__()
        self.client = client
        self.image = image

    def run(self):
        try:
            _, encoded_image = cv2.imencode('.png', self.image)
            base64_image = base64.b64encode(encoded_image).decode('utf-8')

            contents = [
                Part(
                    inline_data={
                        "data": base64_image,
                        "mime_type": "image/png"  # Assuming camera frames are PNG
                    }
                ),
                Part(text="Can you explain the image")
            ]

            response = self.client.generate_content(contents)
            if response.candidates and response.candidates[0].content.parts:
                text_response = response.candidates[0].content.parts[0].text
                self.response_signal.emit(text_response)
            else:
                self.error_signal.emit("No response from Gemini.")
        except Exception as e:
            self.error_signal.emit(f"Gemini API error: {e}")

class CameraDisplay(QWidget):
    def __init__(self):
        super().__init__()
        configure(api_key="AIzaSyCCNZaqXjtPY6yrB8XqzM96pF09k8_QsGY")  # Initialize API key
        self.client = GenerativeModel(model_name="gemini-2.0-flash")
        self.image = None
        self.setWindowTitle("Live Camera with Gemini")

        self.raw_image_label = QLabel()
        self.raw_image_label.setAlignment(Qt.AlignCenter)
        self.hsv_image_label = QLabel()
        self.hsv_image_label.setAlignment(Qt.AlignCenter)

        self.camera = cv2.VideoCapture(0)  # Use 0 for default camera

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)

        self.explain_button = QPushButton("Explain Image")
        self.clear_button = QPushButton("Clear Explanation")
        self.explain_button.setEnabled(True)

        camera_layout = QHBoxLayout()
        camera_layout.addWidget(self.raw_image_label)
        camera_layout.addWidget(self.hsv_image_label)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.explain_button)
        button_layout.addWidget(self.clear_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(camera_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.text_display)

        self.setLayout(main_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30 milliseconds

        self.gemini_thread = None

        self.explain_button.clicked.connect(self.start_gemini_query)
        self.clear_button.clicked.connect(self.clear_text_display)

         # HSV detection parameters (you can adjust these)
        self.lower_hsv = np.array([0, 30, 60])
        self.upper_hsv = np.array([30, 150, 255])

    def update_frame(self):
        ret, self.image = self.camera.read()
        if ret:
            frame = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.raw_image_label.setPixmap(pixmap)
            self.display_hsv_detection(frame)

    def display_hsv_detection(self, frame):
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_frame, self.lower_hsv, self.upper_hsv)
        detected_objects = cv2.bitwise_and(frame, frame, mask=mask)
        detected_objects_rgb = cv2.cvtColor(detected_objects, cv2.COLOR_BGR2RGB)
        h, w, ch = detected_objects_rgb.shape
        bytes_per_line = ch * w
        q_image = QImage(detected_objects_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.hsv_image_label.width(), self.hsv_image_label.height(), Qt.KeepAspectRatio)
        self.hsv_image_label.setPixmap(scaled_pixmap)

    def start_gemini_query(self):
        if self.image is not None and self.explain_button.isEnabled():
            self.explain_button.setEnabled(False)
            self.text_display.append("Analyzing image...")
            self.gemini_thread = GeminiThread(self.client, self.image.copy()) # Pass a copy to the thread
            self.gemini_thread.response_signal.connect(self.display_gemini_response)
            self.gemini_thread.error_signal.connect(self.display_gemini_error)
            self.gemini_thread.finished.connect(lambda: self.explain_button.setEnabled(True))
            self.gemini_thread.start()
        elif not self.explain_button.isEnabled():
            self.text_display.append("Previous analysis in progress...")
        else:
            self.text_display.append("No camera frame captured.")

    def display_gemini_response(self, response_text):
        self.text_display.append("Explanation:\n" + response_text)

    def display_gemini_error(self, error_message):
        self.text_display.append(f"Error: {error_message}")

    def clear_text_display(self):
        self.text_display.clear()

    def closeEvent(self, event):
        self.camera.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CameraDisplay()
    window.setGeometry(100, 100, 1400, 600)
    window.show()
    sys.exit(app.exec_())