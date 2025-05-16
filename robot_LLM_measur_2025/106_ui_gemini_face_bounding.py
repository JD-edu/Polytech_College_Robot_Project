import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import cv2
from google.generativeai import GenerativeModel, configure
from google.ai.generativelanguage_v1beta import Part
import base64
import json

class GeminiThread(QThread):
    response_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, client, image):
        super().__init__()
        self.client = client
        self.image = image
        self.bounding_box = [ 0, 0, 0, 0]

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
                Part(text="Can you find human face in this image? If you find a face, can you give me points of bounding box that surround a face")
            ]

            response = self.client.generate_content(contents)
            if response.candidates and response.candidates[0].content.parts:
                text_response = response.candidates[0].content.parts[0].text
                #print("test_response: ", text_response)
                start_index = text_response.find("[")
                end_index = text_response.rfind("]")+1
                json_string = text_response[start_index:end_index].strip()
                #print("json_string: ", json_string)
                data = json.loads(json_string)
                #print("data: ", data)
                if data and isinstance(data, list) and len(data) > 0 and "box_2d" in data[0]:
                    self.bounding_box = data[0]["box_2d"]
                    #print("bounding: ", self.bounding_box)

                self.response_signal.emit(text_response)
                
            else:
                self.error_signal.emit("No response from Gemini.")
        except Exception as e:
            self.error_signal.emit(f"Gemini API error: {e}")

    def set_bounding_box(self):
        return self.bounding_box

class CameraDisplay(QWidget):
    def __init__(self):
        super().__init__()
        configure(api_key="AIzaSyCCNZaqXjtPY6yrB8XqzM96pF09k8_QsGY")  # Initialize API key
        self.client = GenerativeModel(model_name="gemini-2.0-flash")
        self.image = None
        self.setWindowTitle("Live Camera with Gemini")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.camera = cv2.VideoCapture(0)  # Use 0 for default camera

        self.bounding_box = [0,0,0,0]

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)

        self.explain_button = QPushButton("Explain Image")
        self.clear_button = QPushButton("Clear Explanation")
        self.explain_button.setEnabled(True)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.explain_button)
        button_layout.addWidget(self.clear_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.image_label)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.text_display)

        self.setLayout(main_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Update every 30 milliseconds

        self.gemini_thread = None

        self.explain_button.clicked.connect(self.start_gemini_query)
        self.clear_button.clicked.connect(self.clear_text_display)

    def update_frame(self):
        ret, self.image = self.camera.read()
        if ret:
            ymin, xmin, ymax, xmax = self.bounding_box
            cv2.rectangle(self.image, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)
            frame = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)

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
        self.bounding_box = self.gemini_thread.set_bounding_box()
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
    window.setGeometry(100, 100, 800, 600)
    window.show()
    sys.exit(app.exec_())