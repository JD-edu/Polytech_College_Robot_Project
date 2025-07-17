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
# API 키는 환경 변수나 보안된 방식으로 관리하는 것이 좋습니다.
# 여기서는 예시를 위해 직접 입력하지만, 실제 서비스에서는 os.environ.get 사용을 권장합니다.
CHATGPT_MODEL = "gpt-4o" # 'gpt-4o' 모델은 Vision 기능을 지원합니다.
openai_client = OpenAI(api_key="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") # 본인 키 입력


# --- 3. OpenCV 이미지 분석 함수 (동일하게 유지) ---
def analyze_image_with_opencv(image_np):
    """
    OpenCV를 사용하여 이미지 내의 도형들을 찾고 외접 사각형 정보를 반환합니다.
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
            if cv2.isContourConvex(contour) and cv2.arcLength(contour, True) > (w+h)*1.5:
                shape_type = "oval"
            else:
                shape_type = "rectangle"

        center_x = x + w // 2
        center_y = y + h // 2
        
        relative_center_x = round(center_x / img_width, 4)
        relative_center_y = round(center_y / img_height, 4)

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
            "center_coordinates_relative": {"x": relative_center_x, "y": relative_center_y},
            "area_pixels": round(area, 2)
        })
    return shapes_data


# --- 4. API 엔드포인트 정의 (JSON 응답을 위한 수정된 버전) ---
@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    if openai_client is None:
        return jsonify({"error": "OpenAI client is not initialized. Please check your API key."}), 500

    if 'image' not in request.files:
        return jsonify({"error": "Image file not found in 'image' field."}), 400

    image_file = request.files['image']
    # 사용자 프롬프트는 그대로 사용하되, LLM은 JSON 형식을 따르도록 지시
    text_prompt = request.form.get('prompt', "Determine the optimal measurement order for the identified shapes.")

    if image_file.filename == '':
        return jsonify({"error": "No selected image file."}), 400

    try:
        image_bytes = image_file.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        img_decoded = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        if img_decoded is None:
            return jsonify({"error": "Could not decode image file. Please ensure it's a valid image format."}), 400

        opencv_analysis_results = analyze_image_with_opencv(img_decoded)

        _, encoded_image = cv2.imencode('.png', img_decoded)
        base64_image = base64.b64encode(encoded_image.tobytes()).decode('utf-8')

        # --- 핵심 변경 부분: 시스템 메시지 및 사용자 프롬프트 수정 ---
        messages = [
            {
                "role": "system",
                "content": """
                You are an intelligent measurement planning assistant.
                Your task is to analyze geometric shapes and their precise spatial data (ID, type, role, pixel center coordinates) provided by an OpenCV agent.
                **Based on this data, you MUST generate a logical and optimal measurement sequence in a JSON array format.**

                Each item in the JSON array should represent a measurement step and must contain the following keys:
                - 'step': The sequential number of the measurement step (integer).
                - 'shape_id': The ID of the shape to be measured (integer, from OpenCV data).
                - 'shape_type': The type of the shape (string, e.g., "circle", "square", "rectangle", "oval").
                - 'center_x_pixel': The X-coordinate of the shape's center in pixels (integer).
                - 'center_y_pixel': The Y-coordinate of the shape's center in pixels (integer).
                - 'reason': A brief explanation for why this shape is measured at this step (string, e.g., "Top-left shape", "Inner shape of main container").

                Consider factors for ordering:
                1. Overall spatial arrangement (e.g., left-to-right, top-to-bottom preference).
                2. Container-inner shape relationships (measure container first, then its inner shapes).
                3. Role of each shape (main_container, inner_shape, outer_shape).
                
                **If no shapes are detected by OpenCV, return an empty JSON array `[]` for the 'measurement_sequence'.**
                **Your entire response must be a valid JSON object with a single key 'measurement_sequence'.**
                """
            }
        ]

        user_message_content = [
            {"type": "text", "text": f"User's request: {text_prompt}"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
        ]

        opencv_info_str = "\nDetailed OpenCV Analysis Results (for JSON generation):\n"
        if opencv_analysis_results:
            # LLM이 JSON을 만들기 쉽도록 핵심 정보만 깔끔하게 전달
            for shape in opencv_analysis_results:
                opencv_info_str += (
                    f"Shape ID: {shape['id']}, Type: {shape['type']}, Role: {shape['role']}, "
                    f"Center (pixel): (x={shape['center_coordinates_pixel']['x']}, y={shape['center_coordinates_pixel']['y']})\n"
                )
        else:
            opencv_info_str += "OpenCV found no discernible shapes.\n"
        
        user_message_content.append({"type": "text", "text": opencv_info_str})
        
        messages.append({
            "role": "user",
            "content": user_message_content
        })

        chatgpt_response = openai_client.chat.completions.create(
            model=CHATGPT_MODEL,
            messages=messages,
            response_format={ "type": "json_object" }, # 이 부분이 중요! JSON 응답을 강제
            max_tokens=1000
        )

        if chatgpt_response.choices and chatgpt_response.choices[0].message.content:
            chatgpt_raw_response = chatgpt_response.choices[0].message.content
            
            try:
                # LLM의 응답이 JSON 형식이라고 가정하고 파싱
                parsed_measurement_data = json.loads(chatgpt_raw_response)
                
                final_response = {
                    "status": "success",
                    "opencv_analysis": opencv_analysis_results,
                    "measurement_order": parsed_measurement_data.get('measurement_sequence', []) # 'measurement_sequence' 키의 값을 사용
                }
                return jsonify(final_response)
            except json.JSONDecodeError as e:
                app.logger.error(f"Failed to parse ChatGPT response as JSON: {e}. Raw response: {chatgpt_raw_response}", exc_info=True)
                return jsonify({"error": f"ChatGPT did not return a valid JSON: {str(e)}", "raw_chatgpt_response": chatgpt_raw_response}), 500
        else:
            return jsonify({"error": "Received an empty or invalid response from ChatGPT."}), 500

    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

# --- 애플리케이션 실행 ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    print("Flask app for OpenCV and ChatGPT is running on http://0.0.0.0:5000")