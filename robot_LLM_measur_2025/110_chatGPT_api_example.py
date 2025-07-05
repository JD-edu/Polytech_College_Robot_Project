import os
from openai import OpenAI

# OpenAI 클라이언트 초기화
client = OpenAI(api_key="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")  # 또는 os.environ["OPENAI_API_KEY"] 사용 가능


# 대화 함수 정의
def chat_with_gpt(prompt, model="gpt-3.5-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# 예시 실행
user_input = "로봇공학이 뭐야?"
answer = chat_with_gpt(user_input)
print("ChatGPT:", answer)
