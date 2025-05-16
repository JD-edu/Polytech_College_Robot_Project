from PIL import Image
from google import genai

client = genai.Client(api_key="AIzaSyCCNZaqXjtPY6yrB8XqzM96pF09k8_QsGY")

image = Image.open("./triangle.png")
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[image, "You can see a geometric shapes. Please explain it. And is it possible to find vertex pixel point values?"]
)
print(response.text)