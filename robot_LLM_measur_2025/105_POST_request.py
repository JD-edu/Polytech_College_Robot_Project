import requests
import json
import os

# --- Configuration ---
# The URL of your Flask application's analyze_image endpoint
# Note: Changed from 0.0.0.0 to 127.0.0.1 as per your curl command
API_URL = "http://127.0.0.1:5000/analyze_image"

# Path to the image file you want to send
# Make sure this file exists in the same directory as this script,
# or provide its full path.
IMAGE_PATH = "many_shape3.png" 

# The text prompt to send with the image
TEXT_PROMPT = "Tell me about the shapes you see in detail."

# --- Check if image file exists ---
if not os.path.exists(IMAGE_PATH):
    print(f"Error: Image file not found at '{IMAGE_PATH}'. Please ensure the path is correct.")
    exit()

# --- Prepare the request ---
try:
    # Open the image file in binary read mode
    with open(IMAGE_PATH, 'rb') as img_file:
        # 'files' dictionary for requests.post:
        # The key 'image' must match request.files['image'] in your Flask app.
        # The tuple format is: (filename, file_object, content_type)
        files = {
            'image': (os.path.basename(IMAGE_PATH), img_file, 'image/png')
        }

        # 'data' dictionary for requests.post:
        # The key 'prompt' must match request.form.get('prompt') in your Flask app.
        data = {
            'prompt': TEXT_PROMPT
        }

        print(f"Sending POST request to {API_URL} with image '{IMAGE_PATH}' and prompt '{TEXT_PROMPT}'...")

        # Send the POST request
        response = requests.post(API_URL, files=files, data=data)

        # --- Handle the response ---
        # Raise an HTTPError for bad responses (4xx or 5xx)
        response.raise_for_status() 

        # Parse the JSON response
        response_json = response.json()

        print("\n--- Response from Flask Agent ---")
        # Pretty print the JSON response
        print(json.dumps(response_json, indent=2, ensure_ascii=False))

except requests.exceptions.ConnectionError as e:
    print(f"\nError: Could not connect to the Flask app. Is it running at {API_URL}?")
    print(f"Details: {e}")
except requests.exceptions.HTTPError as e:
    print(f"\nError: HTTP status code {response.status_code} received.")
    print(f"Details: {response.text}")
except json.JSONDecodeError:
    print("\nError: Failed to decode JSON response.")
    print(f"Raw response content: {response.text}")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")