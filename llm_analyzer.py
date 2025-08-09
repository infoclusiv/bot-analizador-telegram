# llm_analyzer.py
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def analyze_with_openrouter(prompt, video_data):
    if not OPENROUTER_API_KEY:
        return "Error: OPENROUTER_API_KEY no configurada en .env"

    video_data_json = json.dumps(video_data, indent=2, ensure_ascii=False)
    full_content = f"{prompt}\n\n### Video Data (JSON):\n\n{video_data_json}"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "tngtech/deepseek-r1t2-chimera:free", 
        "messages": [{"role": "user", "content": full_content}]
    }

    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        response_json = response.json()
        return response_json['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error en la solicitud a OpenRouter: {e}")
        return f"Error de comunicación con el LLM: {e}"