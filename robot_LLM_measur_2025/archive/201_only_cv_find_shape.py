import cv2
import numpy as np

def find_shapes_in_image(image_path):
    """
    이미지 내의 도형들을 찾고 각 도형의 위치(외접 사각형)를 출력하며,
    큰 도형과 작은 도형을 구분하여 시각화합니다.

    Args:
        image_path (str): 분석할 이미지 파일의 경로.
    """
    # 1. 이미지 로드
    img = cv2.imread(image_path)

    if img is None:
        print(f"오류: 이미지를 로드할 수 없습니다. 경로를 확인하세요: {image_path}")
        return

    # 원본 이미지를 복사하여 결과 그리기 용으로 사용
    output_img = img.copy()

    # 2. 이미지 전처리
    # 그레이스케일 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 이진화 (Thresholding)
    # 도형이 흰색이고 배경이 어두운 경우: cv2.THRESH_BINARY
    # 도형이 어두운색이고 배경이 밝은 경우: cv2.THRESH_BINARY_INV
    # 여기서는 많은 도형 이미지(many_shape.png)처럼 흰색 도형에 적합하도록 설정
    # 임계값은 이미지에 따라 조정해야 합니다.
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # 노이즈 제거 (Optional): 작은 노이즈를 제거하여 정확한 윤곽선 검출을 돕습니다.
    # kernel = np.ones((3,3),np.uint8)
    # thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations = 1)
    # thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations = 1)

    # 3. 윤곽선 찾기
    # cv2.RETR_EXTERNAL: 가장 바깥쪽 윤곽선만 찾습니다. (가장 큰 도형과 그 안에 있는 도형들을 찾기 위해)
    # cv2.RETR_CCOMP: 2단계 계층 구조를 가집니다. 외부 윤곽선과 내부 구멍의 윤곽선.
    # cv2.RETR_TREE: 모든 윤곽선을 트리 구조로 찾습니다. (가장 상세한 계층 정보 제공)
    # 이 예시에서는 바깥 도형과 안쪽 도형을 구분하기 위해 `cv2.RETR_TREE` 또는 `cv2.RETR_CCOMP`를 사용하는 것이 좋습니다.
    # 여기서는 일단 `cv2.RETR_TREE`를 사용하여 모든 계층 정보를 가져오겠습니다.
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    print(f"총 {len(contours)}개의 윤곽선이 발견되었습니다.")

    # 도형 정보 저장을 위한 리스트
    shapes_info = []

    # 4. 윤곽선 분석 및 시각화
    # hierarchy 배열은 [Next, Previous, First_Child, Parent] 형식입니다.
    # Parent가 -1인 경우, 최상위(외부) 윤곽선입니다.
    # Parent가 -1이 아닌 경우, 다른 윤곽선의 자식입니다 (보통 구멍을 의미).

    # 윤곽선 면적을 기준으로 정렬 (큰 도형부터 처리하기 위함)
    # contours = sorted(contours, key=cv2.contourArea, reverse=True) # 계층 정보와 함께 정렬 시 hierarchy 인덱스도 맞춰야 함.

    # 간단하게 hierarchy 정보 활용
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        
        # 너무 작은 윤곽선 (노이즈)는 무시
        if area < 50: # 최소 면적 임계값, 이미지에 따라 조정 필요
            continue

        x, y, w, h = cv2.boundingRect(contour) # 외접 사각형

        # 현재 윤곽선의 계층 정보
        # hierarchy[0][i][3]는 현재 윤곽선의 부모 윤곽선 인덱스입니다.
        parent_idx = hierarchy[0][i][3]

        shape_type = "Unknown"
        # 간단한 도형 유형 추정 (원의 경우 종횡비가 1에 가깝고, 사각형은 외접 사각형으로 판단)
        aspect_ratio = float(w)/h
        if 0.8 <= aspect_ratio <= 1.2 and abs(cv2.arcLength(contour, True)**2 / (4 * np.pi * area) - 1) < 0.2:
            # 원형에 가까운지 확인 (둘레와 면적 관계 이용)
            shape_type = "Circle"
        elif 0.7 <= aspect_ratio <= 1.3: # 사각형 또는 타원형
            # 굴곡도 등을 추가로 분석하여 더 정확히 구분할 수 있습니다.
            approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
            if len(approx) == 4:
                shape_type = "Square" # 또는 Rectangle
            else:
                shape_type = "Oval" # 또는 기타

        if parent_idx == -1:
            # 부모가 없는 윤곽선 (가장 바깥쪽 도형, 즉 큰 도형)
            cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 255, 0), 5) # 녹색 테두리
            cv2.putText(output_img, f"Large ({shape_type})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            shapes_info.append({
                "type": shape_type,
                "role": "large_container",
                "x": x, "y": y, "width": w, "height": h,
                "area": area,
                "parent_id": -1 # 최상위
            })
        else:
            # 부모가 있는 윤곽선 (작은 도형들)
            cv2.rectangle(output_img, (x, y), (x + w, y + h), (0, 0, 255), 3) # 빨간색 테두리
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.circle(output_img, (center_x, center_y), 5, (255, 0, 0), -1) # 중심점 파란색 원
            cv2.putText(output_img, f"Small ({shape_type})", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            shapes_info.append({
                "type": shape_type,
                "role": "small_inner_shape",
                "x": x, "y": y, "width": w, "height": h,
                "center_x": center_x,
                "center_y": center_y,
                "area": area,
                "parent_id": parent_idx # 부모 윤곽선 인덱스
            })

    # 결과 출력
    for shape in shapes_info:
        if shape["role"] == "large_container":
            print(f"큰 도형: {shape['type']}, 위치: (x={shape['x']}, y={shape['y']}, w={shape['width']}, h={shape['height']}), 면적: {shape['area']:.2f}")
        else:
            print(f"작은 도형: {shape['type']}, 위치: (x={shape['x']}, y={shape['y']}, w={shape['width']}, h={shape['height']}), "
                  f"중심점: (cx={shape['center_x']}, cy={shape['center_y']}), 면적: {shape['area']:.2f}, 부모 윤곽선 인덱스: {shape['parent_id']}")

    cv2.imshow('Detected Shapes', output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# --- 사용 예시 ---
# 'many_shape3.png'는 큰 둥근 사각형 안에 여러 작은 도형이 있는 이미지입니다.
# 이 파일을 현재 파이썬 스크립트와 같은 디렉토리에 두거나, 정확한 경로를 지정해야 합니다.
find_shapes_in_image('many_shape3.png')

# 만약 다른 이미지로 테스트하고 싶다면:
# find_shapes_in_image('your_image.jpg')