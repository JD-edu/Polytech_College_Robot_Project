from google import genai

client = genai.Client(api_key="AIzaSyCCNZaqXjtPY6yrB8XqzM96pF09k8_QsGY")

response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works in a few words"
)
print(response.text)