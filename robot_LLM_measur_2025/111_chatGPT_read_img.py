import os
import cv2
import base64
from openai import OpenAI

# OpenAI 클라이언트 초기화
client = OpenAI(api_key="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")  # ← 여기에 본인 키 입력

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def describe_image(image_path):
    base64_image = image_to_base64(image_path)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "이 이미지를 설명해 주세요."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        max_tokens=1000,
    )
    return response.choices[0].message.content

# OpenCV로 이미지 확인 및 처리
image_path = "many_shape.png"  # 분석할 이미지 파일 경로
image = cv2.imread(image_path)
if image is None:
    print("이미지를 찾을 수 없습니다.")
else:
    cv2.imshow("입력 이미지", image)
    cv2.waitKey(1000)
    cv2.destroyAllWindows()

    # 이미지 설명 요청
    result = describe_image(image_path)
    print("GPT 설명:", result)
