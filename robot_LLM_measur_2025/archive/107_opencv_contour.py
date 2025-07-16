import cv2
import numpy as np

# Load the image
image_path = './robot_LLM_measur_2025/many_shape.png'
img = cv2.imread(image_path)

if img is None:
    print(f"Error: Could not open or find the image at '{image_path}'")
    exit()

# Create a copy of the original image to draw on
img_copy = img.copy()

# Convert the image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Apply edge detection
edges = cv2.Canny(gray, 50, 150)
cv2.imshow('edge', edges)

# Find all contours in the edged image
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Assuming the outer rectangle is the border of the image or the largest rectangle
outer_rectangle_contour = None
max_area = 0
height, width = gray.shape

# Try to find a large rectangular contour, otherwise consider the image border
for contour in contours:
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
    if len(approx) == 4 and area > max_area and cv2.isContourConvex(approx):
        max_area = area
        outer_rectangle_contour = approx

if outer_rectangle_contour is None:
    outer_rectangle_contour = np.array([[[0, 0]], [[width - 1, 0]], [[width - 1, height - 1]], [[0, height - 1]]], dtype=np.int32)

# Create a mask for the outer rectangle to find shapes inside
mask = np.zeros_like(gray)
cv2.drawContours(mask, [outer_rectangle_contour], -1, 255, cv2.FILLED)

# Find contours within the mask
inner_shapes_edges = cv2.bitwise_and(edges, edges, mask=mask)
inner_contours, _ = cv2.findContours(inner_shapes_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Iterate through the inner contours
for contour in inner_contours:
    # Draw the contour
    cv2.drawContours(img_copy, [contour], -1, (0, 255, 0), 2)

    print("Contour Points:")
    print(contour.tolist())

    # Try to detect if the shape is a circle
    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
    if len(approx) > 5:  # A circle-like shape will have many approximation points
        (x, y), radius = cv2.minEnclosingCircle(contour)
        center = (int(x), int(y))
        radius = int(radius)
        if radius > 5:  # Avoid small noise
            circularity = 4 * np.pi * cv2.contourArea(contour) / (perimeter * perimeter) if perimeter > 0 else 0
            if circularity > 0.8:  # Adjust threshold for circle detection
                cv2.circle(img_copy, center, radius, (255, 0, 0), 2)
                print(f"Circle Center: {center}")

# Display the image with contours and circle centers
cv2.imshow("Shapes with Contours and Circle Centers", img_copy)
cv2.waitKey(0)
cv2.destroyAllWindows()