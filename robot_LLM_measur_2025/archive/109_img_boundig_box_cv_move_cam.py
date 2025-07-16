import json
import cv2
import numpy as np
from shape_info import ShapeInfo

# Your JSON string
json_string = """
{
    "shapes": [
        {
            "shape": "rounded square",
            "description": [
                {
                    "side": "approximately 450 pixels",
                    "corners": "rounded"
                }
            ],
            "bounding_box": {
                "x": 0,
                "y": 0,
                "width": 622,
                "height": 577
            }
        },
        {
            "shape": "circle",
            "description": [
                {
                    "radius": "approximately 48 pixels"
                }
            ],
            "bounding_box": {
                "x": 379,
                "y": 360,
                "width": 96,
                "height": 97
            }
        },
        {
            "shape": "square",
            "description": [
                {
                    "side": "approximately 97 pixels"
                }
            ],
            "bounding_box": {
                "x": 136,
                "y": 360,
                "width": 97,
                "height": 97
            }
        },
        {
            "shape": "square",
            "description": [
                {
                    "side": "approximately 96 pixels"
                }
            ],
            "bounding_box": {
                "x": 379,
                "y": 117,
                "width": 96,
                "height": 97
            }
        },
        {
            "shape": "circle",
            "description": [
                {
                    "radius": "approximately 48 pixels"
                }
            ],
            "bounding_box": {
                "x": 136,
                "y": 117,
                "width": 97,
                "height": 97
            }
        }
    ]
}
"""

# Load the JSON data
data = json.loads(json_string)

# Extract shapes excluding the outer shape (index 0)
shapes_list = data["shapes"]
shapes_class_list = []
# shape_list 변수는 JSON에서 추출한 모든 도형의 attribute 정보를 보유 
# 이것을 리스트 변수인 shape_class_list에 저장. 이 리스트는 다른 작업을 위한 저장소 역할  
for i in range(len(shapes_list)):
    s1 = ShapeInfo(shapes_list[i])
    shapes_class_list.append(s1)

image_path = "./robot_LLM_measur_2025/many_shape.png"
image = cv2.imread(image_path)
cv2.imshow('original', image)

for(i, shape) in enumerate(shapes_class_list):
    x = shape.bounding_box['x']
    y = shape.bounding_box['y']
    width = shape.bounding_box['width']
    height = shape.bounding_box['height']
    label = shape.shape
    label = label+" measure order: "+str(i)
    # Draw rectangle 
    cv2.rectangle(image, (x, y),  (x+width, y+height), (255,0,0), 5)
    # Draw shape label text
    cv2.putText(image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
    # Draw center point 
    center_x = x + width // 2
    center_y = y + height // 2
    cv2.circle(image, (center_x, center_y), 4, (0, 0, 255), -1)
    print(label)
    print(shape)
            
cv2.imshow('win', image)
cv2.waitKey(0)
cv2.destroyAllWindows()