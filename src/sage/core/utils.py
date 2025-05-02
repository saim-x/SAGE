import requests
from typing import List

def call_ollama(prompt: str, model: str = "deepseek-r1:1.5b", base_url: str = "http://localhost:11434") -> str:
    """
    Call the Ollama API with the given prompt and model.
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