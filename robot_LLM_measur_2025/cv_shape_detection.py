import cv2
import numpy as np

# 이미지 로드
image = cv2.imread("many_shape.png")
cv2.imshow("1", image)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
cv2.imshow("2", gray)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
cv2.imshow("3", blurred)
_, thresh = cv2.threshold(blurred, 220, 255, cv2.THRESH_BINARY)
cv2.imshow("4", thresh)
# 윤곽선 찾기
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for contour in contours:

    # 윤곽선을 근사화하여 꼭짓점 찾기
    approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
    '''
    M = cv2.moments(contour)

    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])  # 중심점 x
        cy = int(M["m01"] / M["m00"])  # 중심점 y`
    else:`
        cx, cy = 0, 0

    # 도형 종류 판단
    num_vertices = len(approx)
    shape = "Unidentified"

    if num_vertices == 3:
        shape = "Triangle"
    elif num_vertices == 4:
        # 정사각형 vs 직사각형 구분
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = w / float(h)
        shape = "Square" if 0.95 <= aspect_ratio <= 1.05 else "Rectangle"
    elif num_vertices == 5:
        shape = "Pentagon"
    elif num_vertices > 5:
        shape = "Circle"  # 원이나 타원처럼 보이는 경우

    # 꼭짓점 좌표 출력
    print(f"{shape} - Center: ({cx}, {cy}), Vertices: {approx.reshape(-1, 2).tolist()}")

    # 시각화
    '''
    cv2.drawContours(image, [approx], -1, (0, 255, 0), 2)
    #cv2.circle(image, (cx, cy), 5, (255, 0, 0), -1)
    #cv2.putText(image, shape, (cx - 50, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
    

# 결과 출력
cv2.imshow("Detected Shapes", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
