"""Ollama local LLM calls. Async HTTP allows concurrent analysis requests."""
import os
import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


async def complete(system: str, prompt: str) -> str:
    if os.getenv("WEATHER_DEMO_MODE") == "1":
        return "SIMULATED ANALYSIS: Example explanatory narrative; no Ollama request was made."
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0},
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(OLLAMA_URL, json=payload)
        resp.raise_for_status()
        content = (resp.json().get("message") or {}).get("content", "").strip()
        if not content:
            raise RuntimeError("Ollama returned an empty answer")
        return content
