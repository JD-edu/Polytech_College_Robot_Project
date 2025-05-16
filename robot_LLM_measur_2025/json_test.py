import json
gemini_response = """

Here are the bounding box detections:
```json
[
  {"box_2d": [237, 428, 731, 701], "label": "face"}
]

"""

start_index = gemini_response.find("[")
end_index = gemini_response.rfind("]") + 1
json_string = gemini_response[start_index:end_index].strip()

#print(json_string)

data = json.loads(json_string)

print(data[0])

if data and isinstance(data, list) and len(data) > 0 and "box_2d" in data[0]:
    bounding_box = data[0]["box_2d"]
    print(f"Extracted bounding box: {bounding_box}")
else:
    print("Could not find bounding box information in the response.")