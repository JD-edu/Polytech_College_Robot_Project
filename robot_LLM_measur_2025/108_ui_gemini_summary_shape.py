import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QTextEdit
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import cv2
from google.generativeai import GenerativeModel, configure
from google.ai.generativelanguage_v1beta import Part
import base64
import numpy as np
from shape_info import ShapeInfo
import json

# JSON response example 
json_string = """
{
    "shapes": [
        {
            "shape": "rounded square",
            "description": [
                {
                    "side": "approximately 450 pixels",
                    "corners": "rounded"
                }
            ],
            "bounding_box": {
                "x": 00,
                "y": 00,
                "width": 000,
                "height": 000
            }
        },
        {
            "shape": "circle",
            "description": [
                {
                    "radius": "approximately 00 pixels"
                }
            ],
            "bounding_box": {
                "x": 00,
                "y": 00,
                "width": 000,
                "height": 000
            }
        },
        {
            "shape": "square",
            "description": [
                {
                    "side": "approximately 00 pixels"
                }
            ],
            "bounding_box": {
                "x": 000,
                "y": 000,
                "width": 00,
                "height": 00
            }
        },
        {
            "shape": "square",
            "description": [
                {
                    "side": "approximately 00 pixels"
                }
            ],
            "bounding_box": {
                "x": 00,
                "y": 000,
                "width": 00,
                "height": 00
            }
        },
        {
            "shape": "circle",
            "description": [
                {
                    "radius": "approximately 00 pixels"
                }
            ],
            "bounding_box": {
                "x": 000,
                "y": 000,
                "width": 000,
                "height": 000
            }
        }
    ]
}

"""

class GeminiThread(QThread):
    response_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, client, image):
        super().__init__()
        self.client = client
        #self.image = image
        self.image = cv2.imread('many_shape.png')

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
              
                  Part(text="  \
                     I provide you a image of top view of mechanical component. \
                     Inside component, there can be a couple of shape. These can be circles, rectangles, squares. \
                     Please explain this iamge as followings.  Put component analysis at fron of JSON\
                     1. Explain shape of compoennt \
                     2. Find shapes inside component.  \
                     3. Explain each shapes.  \
                     Regarding bounding box, please find rectangle box to enclose shapes\
                     Please give JSON format describing each shape inside rectangle. JSON sequxnce is from left to right from up to down direction  \
                     Below JSON format is just from. When you analysis the image, please do not change JSON form - keyword etc\
                     JSON foramt example:  "  + json_string

                )
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
        self.contour_image_label = QLabel()
        self.contour_image_label.setAlignment(Qt.AlignCenter)

        self.camera = cv2.VideoCapture(0)  # Use 0 for default camera

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)

        self.explain_button = QPushButton("Explain Image")
        self.clear_button = QPushButton("Clear Explanation")
        self.explain_button.setEnabled(True)

        camera_layout = QHBoxLayout()
        camera_layout.addWidget(self.raw_image_label)
        camera_layout.addWidget(self.contour_image_label)

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

        # Shape class list that hold shape info
        self.shapes_class_list = []

    def update_frame(self):
        #ret, self.image = self.camera.read()
        ret = True
        self.image = cv2.imread('many_shape.png')
        # fix image display width 
        target_width = 320
        if ret:
            # reszize original image with fixed aspect ratio    
            frame_ = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            h_, w_ = frame_.shape[:2]
            aspect_ratio = h_ / w_
            new_height = int(target_width * aspect_ratio)
            frame = cv2.resize(frame_, (target_width, new_height))
            # Putting scaled image into PyQt5 (Pixmap)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.raw_image_label.setPixmap(pixmap)
            # Using camera image, generating HSV image
            #self.display_hsv_detection(frame)
    '''
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
    '''

    def draw_shape_contour(self, frame):
        for shape in self.shapes_class_list:
            x = shape.bounding_box['x']
            y = shape.bounding_box['y']
            width = shape.bounding_box['width']
            height = shape.bounding_box['height']
            cv2.rectangle(frame, (x, y),  (x+width, y+height), (255,0,0), 5)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.contour_image_label.width(), self.contour_image_label.height(), Qt.KeepAspectRatio)
        self.contour_image_label.setPixmap(scaled_pixmap)
        


    def start_gemini_query(self):
        if self.image is not None and self.explain_button.isEnabled():
            self.explain_button.setEnabled(False)
            self.text_display.append("Analyzing image...")
            self.gemini_thread = GeminiThread(self.client, self.image.copy()) # Pass a copy to the thread
            # Gemini_thread가 보내는 response_signal의 callback을 셋팅 
            self.gemini_thread.response_signal.connect(self.display_gemini_response)
            # Gemini_thread가 보내는 error_signal을 셋팅  
            self.gemini_thread.error_signal.connect(self.display_gemini_error)
            self.gemini_thread.finished.connect(lambda: self.explain_button.setEnabled(True))
            # One shot thread - asking to 
            self.gemini_thread.start()
        elif not self.explain_button.isEnabled():
            self.text_display.append("Previous analysis in progress...")
        else:
            self.text_display.append("No camera frame captured.")
    '''
    이 클래스 함수는 response_signal을 받으면 실행되는 callback 함수임 
    response_signal은 Gemini_Thread가 보내줌. Gemini에 질문을 하고 답이 왔을 때 실행된다. 
    입력: response_text -> Gemini가 보낸 답변 문자열
    '''
    def display_gemini_response(self, response_text):
        # JSPN에서 "```json" "```" 두개가 포함되어 Gemini가 보내오므로 이것을 제거 해야 함 
        print(response_text)
        cleaned_text = response_text.replace('```json', '').replace('```', '').strip()
       
        try:
            data = json.loads(cleaned_text)
            shapes_list = data['shapes']

            # shape_list 변수는 JSON에서 추출한 모든 도형의 attribute 정보를 보유 
            # 이것을 리스트 변수인 shape_class_list에 저장. 이 리스트는 다른 작업을 위한 저장소 역할  
            for i in range(len(shapes_list)):
                s1 = ShapeInfo(shapes_list[i])
                self.shapes_class_list.append(s1)
            
            # 텍스트 위젯에 모든 도형의 attribute를 프린트하기 위해서 문자열로 만들기 
            shape_info_string = ""
            for s1 in self.shapes_class_list:
                shape_info_string += s1.make_string_shape_info()
            self.text_display.append(shape_info_string)
            self.draw_shape_contour(self.image)
        
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")

    '''
    이 클래스 함수는 error_signal을 받으면 실행되는 callback 함수임 
    error_signal은 Gemini_Thread가 보내줌. Gemini에 질문을 하고 에러가 발생하면면 실행된다. 
    입력: error_text -> Gemini가 보낸 error 문자열
    '''
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