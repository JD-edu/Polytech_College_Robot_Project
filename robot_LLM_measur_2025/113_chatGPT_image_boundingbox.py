import os
import cv2
import json
import base64
from openai import OpenAI
from shape_info_img import ShapeInfoImage

# OpenAI 클라이언트 초기화
client = OpenAI(api_key="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")  # ← API 키 보안 주의

# Base64 인코딩 함수
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def relative_to_pixel_coordinates(relative_x, relative_y, image_width, image_height):
    """
    상대적인 (0.0 ~ 1.0) 좌표를 이미지의 픽셀 좌표로 변환합니다.

    Args:
        relative_x (float): 이미지 너비에 대한 상대적인 x 좌표 (0.0 ~ 1.0).
        relative_y (float): 이미지 높이에 대한 상대적인 y 좌표 (0.0 ~ 1.0).
        image_width (int): 이미지의 전체 너비 (픽셀).
        image_height (int): 이미지의 전체 높이 (픽셀).

    Returns:
        tuple: (pixel_x, pixel_y) 형태의 픽셀 좌표 튜플.
    """
    if not (0.0 <= relative_x <= 1.0 and 0.0 <= relative_y <= 1.0):
        print("경고: 상대 좌표가 0.0에서 1.0 사이가 아닙니다. 결과가 예상과 다를 수 있습니다.")

    pixel_x = int(relative_x * image_width)
    pixel_y = int(relative_y * image_height)

    return pixel_x, pixel_y

# 설명 요청 함수
def describe_image_with_json_prompt(image_path):
    base64_image = image_to_base64(image_path)

    # 복잡한 JSON 예시 포함 프롬프트
    json_string = """
    {
        "shapes": [
            {
            "id": "1",
            "type": "circle",
            "location": "top-left",
            "center_coordinates_relative": {
                "x": 0.30,
                "y": 0.30
            }
            },
            {
            "id": "2",
            "type": "circle",
            "location": "bottom-left",
            "center_coordinates_relative": {
                "x": 0.30,
                "y": 0.70
            }
            },
            {
            "id": "3",
            "type": "square",
            "location": "top-right",
            "center_coordinates_relative": {
                "x": 0.75,
                "y": 0.25
            }
            },
            {
            "id": "4",
            "type": "square",
            "location": "bottom-right",
            "center_coordinates_relative": {
                "x": 0.75,
                "y": 0.75
            }
            },
            {
            "id": "5",
            "type": "circle",
            "location": "center-right",
            "center_coordinates_relative": {
                "x": 0.65,
                "y": 0.55
            }
            }
        ]
    }
    """
    prompt = (
         "이미지에 있는 각 서브도형들(원과 사각형)의 정확한 중심점 위치를 분석해주세요. 각 도형의 중심 좌표를 파악하여 중심점을 표시할 수 있도록 정보를 제공해주세요. \
         전체 이미지 크기 대비 상대적인 위치로 표현해주세요. 포멧은 다음과 같이 해주세요" + json_string
    )

    # GPT-4o Vision 요청
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        max_tokens=1500,
    )
    return response.choices[0].message.content

# 이미지 경로 설정
image_path = "many_shape3.png"
image = cv2.imread(image_path)
if image is None:
    print("이미지를 찾을 수 없습니다.")
else:
    cv2.imshow("입력 이미지", image)
    cv2.waitKey(1000)
    cv2.destroyAllWindows()

    result = describe_image_with_json_prompt(image_path)
    cleaned_result = result.replace('```json', '').replace('```', '').strip()
    try:
        data = json.loads(cleaned_result)
        #print("JSON 파싱 성공!")
        #print(data["shapes"][0])  # 첫 번째 shape 출력 예시
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패: {e}")
    print("GPT 설명 결과 (JSON):\n", result)
    
    # Extract shapes excluding the outer shape (index 0)
    shapes_list = data["shapes"]
    shapes_class_list = []
    # shape_list 변수는 JSON에서 추출한 모든 도형의 attribute 정보를 보유 
    # 이것을 리스트 변수인 shape_class_list에 저장. 이 리스트는 다른 작업을 위한 저장소 역할  
    for i in range(len(shapes_list)):
        s1 = ShapeInfoImage(shapes_list[i])
        shapes_class_list.append(s1)
    print(shapes_class_list)

    for(i, shape) in enumerate(shapes_class_list):
        x = shape.center['x']
        y = shape.center['y']
        #print(x, y)
        ax, ay = relative_to_pixel_coordinates(x, y, image.shape[0], image.shape[1])

        cv2.circle(image, (ax, ay), 4, (0, 0, 255), -1)
        
        #label = shape.shape
        #if label == None:
        #    continue
        #label = label+" order: "+str(i)
        # Draw rectangle 
        #cv2.rectangle(image, (x, y),  (x+width, y+height), (255,0,0), 5)
        # Draw shape label text
        #cv2.putText(image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        # Draw center point 
        #center_x = x + width // 2
        #center_y = y + height // 2
        #cv2.circle(image, (center_x, center_y), 4, (0, 0, 255), -1)
        #print(label)
        #print(shape)
        
        
                
cv2.imshow('win', image)
cv2.waitKey(0)
cv2.destroyAllWindows()

