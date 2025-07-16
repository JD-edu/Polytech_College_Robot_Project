from flask import Flask, request, jsonify
import cv2
import numpy as np
import base64
import json
import io
from openai import OpenAI # This will be used for Gemini API later

# --- 1. Flask 애플리케이션 초기화 ---
app = Flask(__name__)

# This will be used for Gemini API, but we'll initialize it properly in a later step.
# For now, we'll keep it as None or a placeholder.
client = None # Placeholder for OpenAI client

# --- Root Route (Optional for testing) ---
@app.route('/')
def home():
    return "Flask-based OpenCV Agent is running!"

# --- 애플리케이션 실행 ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    print("Flask app is running on http://0.0.0.0:5000")