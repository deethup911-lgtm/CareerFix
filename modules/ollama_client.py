import os
import requests
import json

# Default to Ollama's standard local port
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Configurable model routing
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
REASONING_MODEL = os.getenv("OLLAMA_REASONING_MODEL", "qwen3:8b")

def generate_content(prompt, json_mode=False, model=DEFAULT_MODEL):
    """
    Sends a prompt to the local Ollama instance and returns the parsed JSON or text.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    if json_mode:
        payload["format"] = "json"

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        
        response_text = result.get("response", "")
        
        if json_mode:
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                print(f"Error parsing Ollama JSON response. Raw output: {response_text}")
                return None
        
        return response_text

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with local Ollama: {e}")
        return None
