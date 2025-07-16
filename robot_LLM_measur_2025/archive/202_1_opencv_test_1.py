import cv2
import numpy as np

image_np = cv2.imread("many_shape2.png")

gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    
# 이진화: 배경과 도형을 분리. 이미지에 따라 임계값 조정이 필요할 수 있습니다.
# many_shape.png와 같이 흰색 도형이 어두운 배경에 있는 경우 THRESH_BINARY_INV 사용
_, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
cv2.imshow('thresh', thresh)
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

for shape in shapes_data:
    data = shape["bounding_box_pixel"]
    x = data['x']
    y = data['y']
    w = data['width']
    h = data['height']
    print(x, y, w, h)
    cv2.rectangle(image_np, (x, y), (x+w, y+h), (0, 0, 255), 2)
cv2.imshow('win', image_np)
cv2.waitKey(0)
cv2.destroyAllWindows()
