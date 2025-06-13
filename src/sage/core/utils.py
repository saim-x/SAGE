import requests
from typing import List
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def call_ollama(prompt: str, model: str = "deepseek-r1:1.5b", base_url: str = "http://localhost:11434") -> str:
    """
    Call the Ollama API with the given prompt and model.
    Supported models include: 'gemma3:4b', 'deepseek-r1:1.5b', 'qwen3:1.7b'.
    Returns the response as a string.
    """
    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "").strip()

def extract_model_name_from_response(response: str, available_models: List[str]) -> str:
    """
    Extracts the model name from the LLM response by matching against available models.
    Returns the first match found, or raises ValueError if none found.
    """
    response_lower = response.lower()
    for model in available_models:
        if model.lower() in response_lower:
            return model
    raise ValueError(f"No valid model name found in response: {response}")

def call_gemini(prompt: str, model: str = "models/gemini-2.5-flash-preview-05-20", api_key: str = None, parameters: dict = None) -> str:
    """
    Call the Gemini API with the given prompt and model.
    Returns the response as a string.
    """
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment or .env file.")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return response.text.strip() if hasattr(response, 'text') else str(response) 