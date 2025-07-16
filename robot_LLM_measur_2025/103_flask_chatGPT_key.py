#POST request in powershell
#& "C:\Windows\System32\curl.exe" -X POST -F "image=@many_shape3.png" -F "prompt=Tell me about the shapes you see in detail." http://127.0.0.1:5000/analyze_image
import sys
from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
import json
import io
from openai import OpenAI
import os # Import the os module to access environment variables

# --- 1. Flask 애플리케이션 초기화 ---
app = Flask(__name__)

# --- 2. Chat API 설정 ---
# IMPORTANT: Load your OpenAI API key securely!
# Method A: Load from environment variable (RECOMMENDED for production)
#try:
    #OPENAI_API_KEY = os.environ.get("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")
    #if not OPENAI_API_KEY:
    #    raise ValueError("OPENAI_API_KEY environment variable not set.")
    #openai_client = OpenAI(api_key=OPENAI_API_KEY)
    #print("OpenAI client initialized using environment variable.")
#except Exception as e:
    #app.logger.error(f"Error initializing OpenAI client from env var: {e}")
    #openai_client = None # Set to None if initialization fails

# Method B: Hardcode your key directly (FOR DEVELOPMENT ONLY, NOT RECOMMENDED FOR PRODUCTION)
# If you are struggling with environment variables for quick testing, you can uncomment and use this:
# openai_client = OpenAI(api_key="sk-your-actual-openai-key-here") # <<< Replace with your actual key
# CHATGPT_MODEL = "gpt-4o" # Or "gpt-3.5-turbo", "gpt-4", etc.

CHATGPT_MODEL = "gpt-4o" # Specify the model you want to use

openai_client = OpenAI(api_key="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")  # ← 여기에 본인 키 입력

# --- 3. OpenCV 이미지 분석 함수 (This section remains unchanged from Part 2) ---
def analyze_image_with_opencv(image_np):
    """
    OpenCV를 사용하여 이미지 내의 도형들을 찾고 외접 사각형 정보를 반환합니다.
    (This function remains the same as in Part 2)
    """
    gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    shapes_data = []
    img_height, img_width = image_np.shape[:2]
    largest_contour_area = 0
    largest_contour_idx = -1
    if contours:
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            if hierarchy[0][i][3] == -1 and area > largest_contour_area:
                largest_contour_area = area
                largest_contour_idx = i

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < 100:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        shape_type = "unknown"
        aspect_ratio = float(w) / h
        if 0.85 <= aspect_ratio <= 1.15:
            if area > 0:
                circularity = (4 * np.pi * area) / (cv2.arcLength(contour, True)**2)
                if circularity > 0.7:
                    shape_type = "circle"
                else:
                    shape_type = "square"
            else:
                shape_type = "square" if abs(w-h) < max(w,h)*0.1 else "rectangle"
        elif aspect_ratio < 0.85 or aspect_ratio > 1.15:
            shape_type = "oval" if cv2.isContourConvex(contour) and cv2.arcLength(contour, True) > (w+h)*1.5 else "rectangle"

        center_x = x + w // 2
        center_y = y + h // 2
        
        relative_center_x = center_x / img_width
        relative_center_y = center_y / img_height

        if hierarchy.size > 0 and i == largest_contour_idx:
            role = "main_container"
        elif hierarchy.size > 0 and hierarchy[0][i][3] != -1:
            role = "inner_shape"
        else:
            role = "outer_shape"

        shapes_data.append({
            "id": len(shapes_data) + 1,
            "type": shape_type,
            "role": role,
            "bounding_box_pixel": {"x": x, "y": y, "width": w, "height": h},
            "center_coordinates_pixel": {"x": center_x, "y": center_y},
            "center_coordinates_relative": {"x": round(relative_center_x, 4), "y": round(relative_center_y, 4)},
            "area_pixels": round(area, 2)
        })
    return shapes_data

# --- 4. API 엔드포인트 정의 (Placeholder, will be completed in Part 4) ---
@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    if openai_client is None:
        return jsonify({"error": "OpenAI client is not initialized. Please check your API key."}), 500
    
    # This part will be fully implemented in Part 4 and Part 5
    return jsonify({"message": "API endpoint is now checking OpenAI client initialization. Further logic is coming in Part 4 & 5!"})

# --- 애플리케이션 실행 ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    print("Flask app for OpenCV and ChatGPT is running on http://0.0.0.0:5000")