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
import os

# --- 1. Flask 애플리케이션 초기화 ---
app = Flask(__name__)

# --- 2. Chat API 설정 ---
'''
try:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("OpenAI client initialized using environment variable.")
except Exception as e:
    app.logger.error(f"Error initializing OpenAI client from env var: {e}")
    openai_client = None
'''
CHATGPT_MODEL = "gpt-4o" # Specify the model you want to use. 'gpt-4o' supports vision.
openai_client = OpenAI(api_key="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")  # ← 여기에 본인 키 입력


# --- 3. OpenCV 이미지 분석 함수 (Remains unchanged) ---
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


# --- 4. API 엔드포인트 정의 (Final Version) ---
@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    # 4.1. Check if OpenAI client is initialized
    if openai_client is None:
        return jsonify({"error": "OpenAI client is not initialized. Please check your API key."}), 500

    # 4.2. Validate incoming request data
    if 'image' not in request.files:
        return jsonify({"error": "Image file not found in 'image' field."}), 400

    image_file = request.files['image']
    text_prompt = request.form.get('prompt', "Describe the shapes found in the image.")

    if image_file.filename == '':
        return jsonify({"error": "No selected image file."}), 400

    try:
        # Step 1: Read and decode the image for OpenCV
        image_bytes = image_file.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        img_decoded = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        if img_decoded is None:
            return jsonify({"error": "Could not decode image file. Please ensure it's a valid image format."}), 400

        # Step 2: Perform OpenCV image analysis
        opencv_analysis_results = analyze_image_with_opencv(img_decoded)

        # Step 3: Prepare image for ChatGPT (Base64 encoding)
        # It's good practice to ensure the image type is consistent for Base64 (e.g., PNG or JPEG)
        # We'll encode it as PNG for consistent behavior.
        _, encoded_image = cv2.imencode('.png', img_decoded) # Encode NumPy array to PNG format
        base64_image = base64.b64encode(encoded_image.tobytes()).decode('utf-8') # Convert to base64 string

        # Step 4: Construct the prompt for ChatGPT
        # Include a system message to guide the AI's behavior
        messages = [
            {
                "role": "system",
                "content": """
                You are an advanced image analysis AI. Your task is to provide detailed descriptions of geometric shapes in images.
                You will be given an image and precise geometric analysis results from an OpenCV agent.
                Combine the visual information from the image with the provided OpenCV data to answer the user's request comprehensively.
                Clearly state the type, role (e.g., main container, inner shape), exact pixel coordinates (bounding box: x, y, width, height),
                and relative center coordinates (x, y) for each identified shape.
                Always prioritize the detailed numerical data from OpenCV for shape properties and locations, and use the image for visual confirmation and overall context.
                Focus on explaining the relationships between shapes, especially the container and inner shapes.
                """
            }
        ]

        # Add the user's message with both text and image parts
        user_message_content = [
            {"type": "text", "text": f"User's request: {text_prompt}"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
        ]

        # Add the OpenCV analysis results as part of the text for the AI to process
        opencv_info_str = "\nOpenCV Analysis Results:\n"
        if opencv_analysis_results:
            for shape in opencv_analysis_results:
                opencv_info_str += (
                    f"- ID: {shape['id']}, Type: {shape['type']}, Role: {shape['role']}, "
                    f"Bounding Box (pixel): (x={shape['bounding_box_pixel']['x']}, y={shape['bounding_box_pixel']['y']}, w={shape['bounding_box_pixel']['width']}, h={shape['bounding_box_pixel']['height']}), "
                    f"Center (relative): (x={shape['center_coordinates_relative']['x']}, y={shape['center_coordinates_relative']['y']}), "
                    f"Area: {shape['area_pixels']} pixels²\n"
                )
        else:
            opencv_info_str += "OpenCV found no discernible shapes in the image.\n"
        
        user_message_content.append({"type": "text", "text": opencv_info_str})
        
        messages.append({
            "role": "user",
            "content": user_message_content
        })

        # Step 5: Call the ChatGPT API
        chatgpt_response = openai_client.chat.completions.create(
            model=CHATGPT_MODEL,
            messages=messages,
            max_tokens=1000 # Limit the response length to avoid excessive costs/wait times
        )

        # Step 6: Extract ChatGPT's explanation
        if chatgpt_response.choices and chatgpt_response.choices[0].message.content:
            chatgpt_text_response = chatgpt_response.choices[0].message.content
            
            # Final response combining OpenCV data and ChatGPT explanation
            final_response = {
                "status": "success",
                "opencv_analysis": opencv_analysis_results,
                "chatgpt_explanation": chatgpt_text_response
            }
            return jsonify(final_response)
        else:
            return jsonify({"error": "Received an empty or invalid response from ChatGPT."}), 500

    except Exception as e:
        app.logger.error(f"Error during image analysis and ChatGPT call: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

# --- 애플리케이션 실행 ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    print("Flask app for OpenCV and ChatGPT is running on http://0.0.0.0:5000")