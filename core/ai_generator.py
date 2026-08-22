import json
import urllib.request
from typing import Optional

def generate_commit_message_with_ai(diff_text: str, provider: str, api_key: str, model: str) -> Optional[str]:
    if not diff_text or not diff_text.strip():
        return None
        
    if not api_key:
        return None
        
    prompt = (
        "You are an expert programmer. Generate a concise, conventional git commit message based on the following git diff. "
        "Use the format: type(scope): description. "
        "Only return the raw commit message without any quotes, backticks, or extra explanation.\n\n"
        f"Git Diff:\n{diff_text[:3000]}"
    )
    
    try:
        if provider == "openai":
            return _call_openai(prompt, api_key, model)
        elif provider == "gemini":
            return _call_gemini(prompt, api_key, model)
    except Exception as e:
        from .logger import log_streamer
        log_streamer.log(f"Erreur API IA ({provider}) : {e}", level="error")
        
    return None

def _call_openai(prompt: str, api_key: str, model: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": model or "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 60
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        return res_data["choices"][0]["message"]["content"].strip()

def _call_gemini(prompt: str, api_key: str, model: str) -> str:
    model_name = model or "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 60
        }
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        return res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
