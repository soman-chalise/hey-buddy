import os
import requests
import base64
import pyautogui
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# 💡 Concise vision response prompt
SYSTEM_PROMPT = (
     "You are a helpful assistant that analyzes screenshots. "
    "Return only a single, short sentence describing the main activity. "
    "Be direct and brief, like 'Watching a Tkinter tutorial on YouTube'. "
    "Avoid explanations or extra commentary. No markdown, no multiple sentences."
)

def take_screenshot(save_path="screen_temp.png"):
    pyautogui.screenshot(save_path)
    return save_path

def analyze_screen_with_groq_vision(prompt="What's on my screen?", image_path=None, short=False):
    if image_path:
        screenshot_path = image_path
    else:
        screenshot_path = take_screenshot()

    with open(screenshot_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 512,
        "temperature": 0.5
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        full_summary = response.json()["choices"][0]["message"]["content"].strip()

        if short:
            return full_summary.split(".")[0].strip()
        return full_summary

    except Exception as e:
        return f"❌ Groq Vision API failed: {e}"
