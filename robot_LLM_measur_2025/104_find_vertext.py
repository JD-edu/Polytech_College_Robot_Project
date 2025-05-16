'''import cv2
import numpy as np

# Load the image
image = cv2.imread('./triangle.png')  # Replace 'triangle.png' with your image file

# Convert to grayscale (if needed)
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Edge detection
edges = cv2.Canny(gray, 50, 150)  # Adjust parameters (50, 150) as needed
#@cv2.imshow('edge', edges)
#cv2.imshow('gray', gray)
#cv2.waitKey(0)


# Hough Transform for line detection
lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=20)
#  Adjust parameters as needed to properly detect the lines

# Function to find intersection of two lines
def line_intersection(line1, line2):
    # (Implementation of line intersection calculation using equations of lines)
    # ...
    # Returns the (x, y) intersection point
    pass

# Extract the coordinates from Hough Lines
line_coordinates = []
for line in lines:
    x1, y1, x2, y2 = line[0]
    line_coordinates.append(((x1, y1), (x2, y2)))

#Calculate line equations for each line coordinate

# Calculate intersections between each line to find vertex

# Store vertex as coordinates
vertex_coordinates = []

# Print the coordinates
print("Vertex coordinates:", vertex_coordinates)

# Optionally draw the vertices on the image for visualization
for vertex in vertex_coordinates:
    x, y = vertex
    cv2.circle(image, (x, y), 5, (0, 0, 255), -1)  # Draw red circles at vertices

cv2.imshow('Triangle with Vertices', image)
cv2.waitKey(0)
cv2.destroyAllWindows()
'''
import cv2
import numpy as np

# 이미지 읽기 (삼각형 이미지 사용)
img = cv2.imread('triangle.png')  # 흑백 배경 위에 삼각형이 있는 이미지
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 이진화 처리
_, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

# 외곽선 찾기
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 첫 번째 윤곽선 기준으로 근사화
for cnt in contours:
    # 도형 근사화: 정확도는 전체 윤곽 길이의 2%
    epsilon = 0.02 * cv2.arcLength(cnt, True)
    approx = cv2.approxPolyDP(cnt, epsilon, True)

    if len(approx) == 3:
        print("삼각형 꼭짓점 좌표:")
        for point in approx:
            x, y = point[0]
            print(f"({x}, {y})")
            cv2.circle(img, (x, y), 5, (0, 0, 255), -1)

# 결과 시각화
cv2.imshow("Triangle", img)
cv2.waitKey(0)
cv2.destroyAllWindows()

