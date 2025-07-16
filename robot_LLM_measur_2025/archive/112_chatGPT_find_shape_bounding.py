import os
import cv2
import base64
from openai import OpenAI

# OpenAI 클라이언트 초기화
client = OpenAI(api_key="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")  # ← API 키 보안 주의

# Base64 인코딩 함수
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 설명 요청 함수
def describe_image_with_json_prompt(image_path):
    base64_image = image_to_base64(image_path)

    # 복잡한 JSON 예시 포함 프롬프트
    json_string = """
{
    "shapes": [
        {
            "component shape": "round square",
            "description": [
                {
                    "side": "approximately 500 pixels"
                }
            ],
            "bounding_box": {
                "x": 10,
                "y": 10,
                "width": 510,
                "height": 510
            }
        },
        {
            "shape": "circle",
            "description": [
                {
                    "radius": "approximately 80 pixels"
                }
            ],
            "bounding_box": {
                "x": 200,
                "y": 20,
                "width": 160,
                "height": 160
            }
        },
        {
            "shape": "triangle",
            "description": [
                {
                    "side1": "approximately 170 pixels"
                },
                {
                    "side2": "approximately 170 pixels"
                },
                {
                    "side3": "approximately 170 pixels"
                },
                {
                    "vertex1": "60 degrees"
                },
                {
                    "vertex2": "60 degrees"
                },
                {
                    "vertex3": "60 degrees"
                }
            ],
            "bounding_box": {
                "x": 400,
                "y": 20,
                "width": 170,
                "height": 150
            }
        },
        {
            "shape": "pentagon",
            "description": [
                {
                    "side1": "approximately 80 pixels"
                },
                {
                    "side2": "approximately 80 pixels"
                },
                {
                    "side3": "approximately 80 pixels"
                },
                {
                    "side4": "approximately 80 pixels"
                },
                {
                    "side5": "approximately 80 pixels"
                }
            ],
            "bounding_box": {
                "x": 20,
                "y": 200,
                "width": 150,
                "height": 130
            }
        },
        {
            "shape": "ellipse",
            "description": [
                {
                    "major_axis_radius": "approximately 80 pixels"
                },
                {
                    "minor_axis_radius": "approximately 60 pixels"
                }
            ],
            "bounding_box": {
                "x": 200,
                "y": 180,
                "width": 160,
                "height": 140
            }
        },
        {
            "shape": "rectangle",
            "description": [
                {
                    "side1": "approximately 180 pixels"
                },
                {
                    "side2": "approximately 80 pixels"
                },
                {
                    "vertex_angle": "90 degrees"
                }
            ],
            "bounding_box": {
                "x": 400,
                "y": 200,
                "width": 180,
                "height": 80
            }
        }
    ]
}
"""

    prompt = (
        "I provide you an image of the top view of a mechanical component. "
        "Inside the component, there can be a couple of shapes. These can be circles, rectangles, squares, etc. "
        "Please analyze the image as follows:\n"
        "1. Describe the overall shape of the component. Put this at the beginning of the JSON.\n"
        "2. Find and describe each shape inside the component.\n"
        "3. Provide the result in JSON format, in left-to-right, top-to-bottom order.\n"
        "Use the following format as an example:\n"
        + json_string
    )

    # GPT-4o Vision 요청
    response = client.chat.completions.create(
        model="gpt-4o",
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
image_path = "many_shape.png"
image = cv2.imread(image_path)
if image is None:
    print("이미지를 찾을 수 없습니다.")
else:
    cv2.imshow("입력 이미지", image)
    cv2.waitKey(1000)
    cv2.destroyAllWindows()

    result = describe_image_with_json_prompt(image_path)
    print("GPT 설명 결과 (JSON):\n", result)
