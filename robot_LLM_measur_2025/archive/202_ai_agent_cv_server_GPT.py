import sys
from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
import json
import io
from openai import OpenAI

# --- 1. Flask 애플리케이션 초기화 ---
app = Flask(__name__)

# --- 2. Chat API 설정 ---
# IMPORTANT: Replace with your actual Chat API Key
client = OpenAI(api_key="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")  # ← API 키 보안 주의

# --- 3. OpenCV 이미지 분석 함수 ---
def analyze_image_with_opencv(image_np):
    """
    OpenCV를 사용하여 이미지 내의 도형들을 찾고 외접 사각형 정보를 반환합니다.

    Args:
        image_np (numpy.ndarray): OpenCV로 로드된 이미지 (BGR 포맷).

    Returns:
        list: 각 도형의 bounding box (x, y, w, h)와 예상 타입, 중심점, 면적 정보를 담은 딕셔너리 리스트.
    """
    gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    
    # 이진화: 배경과 도형을 분리. 이미지에 따라 임계값 조정이 필요할 수 있습니다.
    # many_shape.png와 같이 흰색 도형이 어두운 배경에 있는 경우 THRESH_BINARY_INV 사용
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    shapes_data = []
    
    # 이미지의 전체 너비와 높이
    img_height, img_width = image_np.shape[:2]

    # 부모 윤곽선 정보 (가장 큰 윤곽선이 바깥 도형이라고 가정)
    largest_contour_area = 0
    largest_contour_idx = -1
    if contours:
        for i, cnt in enumerate(contours):
            area = cv2.contourArea(cnt)
            # hierarchy[0][i][3] == -1 은 부모가 없음을 의미 (최상위 윤곽선)
            if hierarchy[0][i][3] == -1 and area > largest_contour_area:
                largest_contour_area = area
                largest_contour_idx = i

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)

        # 노이즈 필터링 또는 너무 작은 도형 제외
        if area < 100: # 최소 면적 임계값, 필요에 따라 조정
            continue

        x, y, w, h = cv2.boundingRect(contour)
        
        # 도형 타입 추정 (간단화)
        shape_type = "unknown"
        aspect_ratio = float(w) / h
        if 0.85 <= aspect_ratio <= 1.15: # 거의 정사각형/정원
            # 둘레와 면적을 이용한 원형 판별
            if area > 0: # 0으로 나누는 것 방지
                circularity = (4 * np.pi * area) / (cv2.arcLength(contour, True)**2)
                if circularity > 0.7: # 원에 가까운 도형
                    shape_type = "circle"
                else:
                    shape_type = "square"
            else: # 면적이 0인 경우 (예외 처리)
                shape_type = "square" if abs(w-h) < max(w,h)*0.1 else "rectangle" # 가로세로 길이로만 판단
        elif aspect_ratio < 0.85 or aspect_ratio > 1.15: # 직사각형 또는 타원
            shape_type = "oval" if cv2.isContourConvex(contour) and cv2.arcLength(contour, True) > (w+h)*1.5 else "rectangle" # 대략적인 판단
            # cv2.isContourConvex(contour)로 볼록성 판단 후, 둘레와 사각형 둘레 비교 등으로 더 정밀하게 할 수 있음.

        center_x = x + w // 2
        center_y = y + h // 2
        
        # 이미지 전체 크기 대비 상대적 중심 좌표
        relative_center_x = center_x / img_width
        relative_center_y = center_y / img_height

        # 부모-자식 관계를 통해 큰 도형과 작은 도형 구분
        if i == largest_contour_idx: # 가장 큰 최상위 윤곽선이 메인 컨테이너
            role = "main_container"
        elif hierarchy[0][i][3] != -1: # 부모가 있는 윤곽선 = 내부 도형
            role = "inner_shape"
        else: # 그 외의 최상위 윤곽선 (만약 큰 도형이 여러 개라면)
            role = "outer_shape" # 또는 다른 분류

        shapes_data.append({
            "id": len(shapes_data) + 1, # 단순 ID 부여
            "type": shape_type,
            "role": role,
            "bounding_box_pixel": {"x": x, "y": y, "width": w, "height": h},
            "center_coordinates_pixel": {"x": center_x, "y": center_y},
            "center_coordinates_relative": {"x": round(relative_center_x, 4), "y": round(relative_center_y, 4)},
            "area_pixels": round(area, 2)
        })
    return shapes_data

# --- 4. API 엔드포인트 정의 ---
@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    if gemini_model is None:
        return jsonify({"error": "Gemini 모델이 초기화되지 않았습니다. API 키를 확인해주세요."}), 500

    if 'image' not in request.files:
        return jsonify({"error": "이미지 파일이 'image' 필드로 전송되지 않았습니다."}), 400

    image_file = request.files['image']
    text_prompt = request.form.get('prompt', "이미지에 있는 도형들을 분석해주세요.")

    if image_file.filename == '':
        return jsonify({"error": "선택된 이미지 파일이 없습니다."}), 400

    try:
        # 이미지 파일을 읽어 numpy 배열로 변환 (OpenCV용)
        image_bytes = image_file.read()
        image_np = np.frombuffer(image_bytes, np.uint8)
        img_decoded = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        if img_decoded is None:
            return jsonify({"error": "이미지 파일을 디코딩할 수 없습니다. 유효한 이미지 파일인지 확인하세요."}), 400

        # 1단계: OpenCV로 이미지 분석
        opencv_analysis_results = analyze_image_with_opencv(img_decoded)

        # 2단계: OpenCV 분석 결과와 사용자 프롬프트를 결합하여 Gemini에 전달
        # 이미지 바이트를 Base64로 인코딩
        _, encoded_image = cv2.imencode('.png', img_decoded) # PNG 형식으로 인코딩
        base64_image = base64.b64encode(encoded_image).decode('utf-8')

        # OpenCV 분석 결과를 문자열로 변환하여 프롬프트에 추가
        opencv_info_str = "OpenCV 분석 결과:\n"
        if opencv_analysis_results:
            for shape in opencv_analysis_results:
                opencv_info_str += (
                    f"- ID: {shape['id']}, 타입: {shape['type']}, 역할: {shape['role']}, "
                    f"픽셀 좌표: (x={shape['bounding_box_pixel']['x']}, y={shape['bounding_box_pixel']['y']}, w={shape['bounding_box_pixel']['width']}, h={shape['bounding_box_pixel']['height']}), "
                    f"상대 중심: (x={shape['center_coordinates_relative']['x']}, y={shape['center_coordinates_relative']['y']})\n"
                )
        else:
            opencv_info_str += "OpenCV가 도형을 찾지 못했습니다.\n"

        # Gemini에게 보낼 전체 프롬프트
        full_prompt = f"""
        사용자 요청: {text_prompt}

        이 이미지는 2차원 그림이며, 하나의 큰 도형 안에 여러 개의 작은 도형들이 있습니다.
        OpenCV 기반의 정밀 분석 결과가 아래에 제공됩니다. 이 정보를 바탕으로 이미지 내의 도형들에 대해 상세하게 설명해주세요.
        각 도형의 종류(예: 원, 사각형, 타원 등), 역할(예: 큰 컨테이너, 내부 도형), 정확한 픽셀 단위의 외접 사각형 좌표, 그리고 이미지 전체 크기 대비 상대적인 중심점 좌표를 설명해주세요.

        {opencv_info_str}

        각 도형의 특성과 위치를 명확하게 제시하고, 특히 큰 컨테이너 도형과 그 안에 포함된 작은 도형들을 구분하여 설명해주세요.
        """

        contents = [
            Part(
                inline_data={
                    "data": base64_image,
                    "mime_type": "image/png"
                }
            ),
            Part(text=full_prompt)
        ]

        # 3단계: Gemini API 호출
        gemini_response = gemini_model.generate_content(contents)

        if gemini_response.candidates and gemini_response.candidates[0].content.parts:
            gemini_text_response = gemini_response.candidates[0].content.parts[0].text
            
            # 최종 응답 JSON 구성
            final_response = {
                "status": "success",
                "opencv_analysis": opencv_analysis_results,
                "gemini_explanation": gemini_text_response
            }
            return jsonify(final_response)
        else:
            return jsonify({"error": "Gemini로부터 유효한 응답을 받지 못했습니다."}), 500

    except Exception as e:
        app.logger.error(f"이미지 분석 중 서버 오류 발생: {e}", exc_info=True)
        return jsonify({"error": f"이미지 분석 중 오류 발생: {str(e)}"}), 500

# --- 애플리케이션 실행 ---
if __name__ == '__main__':
    # 디버그 모드는 개발 중에만 사용하고, 실제 서비스에서는 비활성화해야 합니다.
    app.run(debug=True, host='0.0.0.0', port=5000)
    print("CV 에이전트가 http://0.0.0.0:5000 에서 실행 중입니다.")