import sys
from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
import json
import io
from openai import OpenAI
import os
import time # 현재 시간 정보를 위해 추가

# --- 1. Flask 애플리케이션 초기화 ---
app = Flask(__name__)

# --- 2. Chat API 설정 ---
# OpenAI API 키를 환경 변수에서 가져오는 것을 권장합니다.
# 직접 키를 입력하려면 아래 주석 처리된 라인을 사용하세요.
try:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        # 환경 변수가 설정되지 않았다면, 여기에 직접 키를 입력하거나 에러를 발생시킵니다.
        # 주의: 실제 배포 시에는 키를 코드에 직접 넣는 것을 피하세요!
        OPENAI_API_KEY = "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" 
        app.logger.warning("OPENAI_API_KEY environment variable not set. Using hardcoded key (for testing only).")
        # raise ValueError("OPENAI_API_KEY environment variable not set. Please set it or provide it directly.")

    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    print("OpenAI client initialized.")
except Exception as e:
    app.logger.error(f"Error initializing OpenAI client: {e}")
    openai_client = None

CHATGPT_MODEL = "gpt-4o" # 'gpt-4o' 모델은 Vision 기능을 지원합니다.


# --- 3. OpenCV 이미지 분석 함수 ---
def analyze_image_with_opencv(image_np):
    """
    OpenCV를 사용하여 이미지 내의 도형들을 찾고 외접 사각형 정보를 반환합니다.
    """
    gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV) # 배경을 어둡게, 객체를 밝게
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    shapes_data = []
    img_height, img_width = image_np.shape[:2]
    largest_contour_area = 0
    largest_contour_idx = -1

    # 가장 큰 (메인 컨테이너) 윤곽선 찾기
    if contours and hierarchy is not None:
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            # hierarchy[0][i][3] == -1은 부모가 없는 (가장 바깥쪽) 컨투어를 의미
            if hierarchy[0][i][3] == -1 and area > largest_contour_area:
                largest_contour_area = area
                largest_contour_idx = i

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area < 100: # 너무 작은 노이즈는 무시
            continue

        x, y, w, h = cv2.boundingRect(contour)
        shape_type = "unknown"
        aspect_ratio = float(w) / h
        
        # 간단한 도형 분류 로직
        # 정사각형 또는 원
        if 0.85 <= aspect_ratio <= 1.15:
            if area > 0:
                # 원형도: 1에 가까울수록 원
                circularity = (4 * np.pi * area) / (cv2.arcLength(contour, True)**2)
                if circularity > 0.7: 
                    shape_type = "circle"
                else: 
                    shape_type = "square"
            else: # 면적이 0인 경우 방어 코드 (드물지만)
                shape_type = "square" if abs(w-h) < max(w,h)*0.1 else "rectangle"
        # 직사각형 또는 타원
        elif aspect_ratio < 0.85 or aspect_ratio > 1.15:
            # 볼록성 및 둘레 길이로 타원/직사각형 구분 시도 (간단한 휴리스틱)
            if cv2.isContourConvex(contour) and cv2.arcLength(contour, True) > (w+h)*1.5:
                shape_type = "oval"
            else:
                shape_type = "rectangle"

        center_x = x + w // 2
        center_y = y + h // 2
        
        # 이미지 전체 크기에 대한 상대적 중심 좌표
        relative_center_x = round(center_x / img_width, 4)
        relative_center_y = round(center_y / img_height, 4)

        # 도형의 역할 결정 (외부, 내부, 메인 컨테이너)
        role = "outer_shape" # 기본값
        if hierarchy is not None and hierarchy.size > 0:
            if i == largest_contour_idx:
                role = "main_container"
            elif hierarchy[0][i][3] != -1: # 부모 컨투어가 있는 경우 (내부 도형)
                role = "inner_shape"

        shapes_data.append({
            "id": len(shapes_data) + 1, # 고유 ID 부여
            "type": shape_type,
            "role": role,
            "bounding_box_pixel": {"x": x, "y": y, "width": w, "height": h},
            "center_coordinates_pixel": {"x": center_x, "y": center_y},
            "center_coordinates_relative": {"x": relative_center_x, "y": relative_center_y},
            "area_pixels": round(area, 2)
        })
    return shapes_data


# --- 4. API 엔드포인트 정의 ---
@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    if openai_client is None:
        return jsonify({"error": "OpenAI client is not initialized. Please check your API key and server logs."}), 500

    # 4.1. 이미지 파일 유효성 검사
    if 'image' not in request.files:
        return jsonify({"error": "Image file not found in 'image' field."}), 400

    image_file = request.files['image']
    text_prompt = request.form.get('prompt', "Determine the optimal measurement order for the identified shapes.")

    if image_file.filename == '':
        return jsonify({"error": "No selected image file."}), 400

    try:
        # 4.2. 이미지 읽기 및 OpenCV 디코딩
        image_bytes = image_file.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        img_decoded = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        if img_decoded is None:
            return jsonify({"error": "Could not decode image file. Please ensure it's a valid image format (e.g., PNG, JPEG)."}), 400

        # 4.3. OpenCV 이미지 분석 실행
        opencv_analysis_results = analyze_image_with_opencv(img_decoded)

        # 4.4. ChatGPT를 위한 이미지 준비 (Base64 인코딩)
        _, encoded_image = cv2.imencode('.png', img_decoded) # NumPy 배열을 PNG 형식으로 인코딩
        base64_image = base64.b64encode(encoded_image.tobytes()).decode('utf-8') # Base64 문자열로 변환

        # 4.5. ChatGPT 프롬프트 구성 (시스템 메시지 및 사용자 메시지)
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

        # 4.6. ChatGPT API 호출
        chatgpt_response = openai_client.chat.completions.create(
            model=CHATGPT_MODEL,
            messages=messages,
            response_format={ "type": "json_object" }, # JSON 응답을 강제
            max_tokens=1000
        )

        if chatgpt_response.choices and chatgpt_response.choices[0].message.content:
            chatgpt_raw_response = chatgpt_response.choices[0].message.content
            
            try:
                # 4.7. LLM의 응답 파싱
                parsed_measurement_data = json.loads(chatgpt_raw_response)
                
                # 4.8. LLM JSON을 간소화된 리스트로 변환
                simplified_measurement_list = []
                measurement_sequence = parsed_measurement_data.get('measurement_sequence', [])
                
                for step_data in measurement_sequence:
                    if all(k in step_data for k in ['center_x_pixel', 'center_y_pixel', 'shape_type']):
                        simplified_measurement_list.append({
                            "x": step_data['center_x_pixel'],
                            "y": step_data['center_y_pixel'],
                            "shape": step_data['shape_type']
                        })
                    else:
                        app.logger.warning(f"Skipping malformed measurement step from LLM: {step_data}")

                # --- 이미지에 정보 표시 및 저장 (OpenCV) ---
                annotated_image = img_decoded.copy() # 원본 이미지 복사
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 1
                font_color_type = (0, 255, 0) # Green for Type
                font_color_step = (255, 255, 255) # White for Step
                font_thickness = 2
                circle_radius = 10
                circle_color = (255, 0, 0) # Blue for Center Dot

                for i, item in enumerate(measurement_sequence):
                    center_x = item.get('center_x_pixel')
                    center_y = item.get('center_y_pixel')
                    shape_type = item.get('shape_type')
                    step = item.get('step')

                    # 유효한 좌표 및 타입이 있는 경우에만 그리기
                    if center_x is not None and center_y is not None and shape_type:
                        # 중심점 그리기
                        cv2.circle(annotated_image, (center_x, center_y), circle_radius, circle_color, -1)

                        # 도형 타입 텍스트 추가
                        text_shape = f"{shape_type}"
                        text_step = f"({step})"
                        text_offset_y = 20 # 텍스트 세로 오프셋

                        # 텍스트 배경 (가독성을 위해)
                        (text_width_shape, text_height_shape), _ = cv2.getTextSize(text_shape, font, font_scale * 0.7, font_thickness)
                        (text_width_step, text_height_step), _ = cv2.getTextSize(text_step, font, font_scale * 0.7, font_thickness)

                        # 텍스트 위치 계산 (원의 오른쪽 위 또는 아래)
                        text_pos_x = center_x + circle_radius + 5
                        text_pos_y_shape = center_y - 5 # 도형 타입은 위쪽에
                        text_pos_y_step = center_y + text_offset_y # 순서는 아래쪽에

                        # 배경 사각형 그리기 (타입)
                        cv2.rectangle(annotated_image, (text_pos_x - 2, text_pos_y_shape - text_height_shape - 2), 
                                      (text_pos_x + text_width_shape + 2, text_pos_y_shape + 2), (50, 50, 50), -1)
                        # 배경 사각형 그리기 (순서)
                        cv2.rectangle(annotated_image, (text_pos_x - 2, text_pos_y_step - text_height_step - 2), 
                                      (text_pos_x + text_width_step + 2, text_pos_y_step + 2), (50, 50, 50), -1)


                        cv2.putText(annotated_image, text_shape, (text_pos_x, text_pos_y_shape), font, font_scale * 0.7, font_color_type, font_thickness)
                        cv2.putText(annotated_image, text_step, (text_pos_x, text_pos_y_step), font, font_scale * 0.7, font_color_step, font_thickness)

                # 현재 타임스탬프를 사용하여 고유한 파일 이름 생성
                timestamp = int(time.time())
                output_image_filename = f"annotated_image_{timestamp}.png"
                cv2.imwrite(output_image_filename, annotated_image)
                
                # --- 응답 구성 ---
                final_response = {
                    "status": "success",
                    "opencv_analysis": opencv_analysis_results,
                    "measurement_order_full_json": parsed_measurement_data,
                    "simplified_measurement_list": simplified_measurement_list,
                    "annotated_image_url": f"/{output_image_filename}" # 클라이언트가 접근할 수 있는 URL (정적 파일 설정 필요)
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
    # 정적 파일 서비스를 위한 설정 추가 (웹에서 저장된 이미지에 접근하기 위함)
    # Flask 앱이 실행되는 디렉토리에서 정적 파일을 제공합니다.
    app.run(debug=True, host='0.0.0.0', port=5000)
    print("Flask app for OpenCV and ChatGPT is running on http://0.0.0.0:5000")