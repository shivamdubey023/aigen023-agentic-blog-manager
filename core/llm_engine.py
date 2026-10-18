"""Multi-model AI generation engine supporting Gemini, Groq, Cohere, OpenAI, and Claude."""
from __future__ import annotations
import json
import logging
import re
from typing import Any
import requests

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = {
    "gemini": {
        "name": "Google Gemini (Free Tier)",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
        "default_model": "gemini-2.5-flash",
    },
    "groq": {
        "name": "Groq Cloud (100% Free & Fast)",
        "models": ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b", "llama-3.1-8b-instant"],
        "default_model": "llama-3.3-70b-versatile",
    },
    "cohere": {
        "name": "Cohere (Trial / Free Key)",
        "models": ["command-r-plus-08-2024", "command-r-08-2024"],
        "default_model": "command-r-08-2024",
    },
    "openai": {
        "name": "OpenAI ChatGPT",
        "models": ["gpt-4o", "gpt-4o-mini"],
        "default_model": "gpt-4o-mini",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
        "default_model": "claude-3-5-sonnet-20241022",
    },
}

DEFAULT_SYSTEM_PROMPT = """You are an elite technical author and SEO content strategist writing for NextGen Tech Notes (https://aigen023.blogspot.com/).
Your goal is to produce deeply practical, authoritative, and Google AdSense compliant technical tutorials that rank organically and pass Google's Helpful Content and E-E-A-T guidelines.

Core guidelines:
1. Write at least 1,400 to 2,200 words of substantive, actionable technical content. Never write generic introductory fluff or filler.
2. Structure clearly:
   - One main H1 title.
   - Comprehensive prerequisites (OS, runtime versions, required packages).
   - Step-by-step implementation with fully functional, syntax-valid code snippets.
   - Realistic terminal commands with expected outputs.
   - Real-world failure modes and troubleshooting (include representative terminal tracebacks labeled as examples).
   - Practical verification checklist.
   - Frequently Asked Questions (FAQ) section with 3-4 clear, high-intent questions and answers.
   - Authoritative official documentation references.
3. Formatting: Output clean, standard Markdown only (no surrounding commentary or conversational wrapper).
"""

def generate_technical_article(
    *,
    provider: str = "gemini",
    model: str | None = None,
    api_key: str,
    topic: str,
    primary_keyword: str = "",
    audience: str = "Working developer",
    notes: str = "",
    custom_system_prompt: str = "",
    temperature: float = 0.35,
    max_tokens: int = 8000,
) -> str:
    """Generate or rewrite an article using the chosen LLM provider."""
    provider = provider.lower().strip()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported AI provider: {provider}. Supported: {list(SUPPORTED_PROVIDERS.keys())}")
    
    selected_model = model or SUPPORTED_PROVIDERS[provider]["default_model"]
    if not api_key or not api_key.strip():
        raise ValueError(f"API key for {provider} is required.")
    
    system_prompt = custom_system_prompt.strip() or DEFAULT_SYSTEM_PROMPT
    user_prompt = f"""Write an exhaustive technical tutorial for NextGen Tech Notes.
Topic: {topic}
Primary keyword: {primary_keyword or topic}
Target reader level: {audience}
Author notes & specific requirements: {notes or 'Provide exhaustive, hands-on production code, practical debugging tracebacks, and verification steps.'}

Remember to:
- Include a descriptive Markdown H1 header at the very top.
- Include deep H2 and H3 sections.
- Ensure all code blocks are fenced with appropriate language tags (e.g. ```python, ```bash).
- Include an FAQ section at the end with 3-4 common questions.
- Output pure Markdown only.
"""

    if provider == "gemini":
        return _call_gemini(api_key.strip(), selected_model, system_prompt, user_prompt, temperature, max_tokens)
    elif provider == "groq":
        return _call_groq(api_key.strip(), selected_model, system_prompt, user_prompt, temperature, max_tokens)
    elif provider == "cohere":
        return _call_cohere(api_key.strip(), selected_model, system_prompt, user_prompt, temperature, max_tokens)
    elif provider == "openai":
        return _call_openai(api_key.strip(), selected_model, system_prompt, user_prompt, temperature, max_tokens)
    elif provider == "anthropic":
        return _call_anthropic(api_key.strip(), selected_model, system_prompt, user_prompt, temperature, max_tokens)
    else:
        raise ValueError(f"Provider handler not implemented: {provider}")

def _call_gemini(api_key: str, model: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{system_prompt}\n\n---\n\n{user_prompt}"}]}
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
    }
    resp = requests.post(url, params={"key": api_key}, json=payload, timeout=120)
    if not resp.ok:
        raise RuntimeError(f"Gemini API error ({resp.status_code}): {resp.text[:400]}")
    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {data}")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise RuntimeError("Gemini returned empty parts")
    return parts[0].get("text", "").strip()

def _call_groq(api_key: str, model: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": min(max_tokens, 8192),
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=90)
    if not resp.ok:
        raise RuntimeError(f"Groq API error ({resp.status_code}): {resp.text[:400]}")
    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("Groq returned no completion choices")
    return choices[0]["message"]["content"].strip()

def _call_cohere(api_key: str, model: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str:
    url = "https://api.cohere.com/v2/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": min(max_tokens, 4096),
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=90)
    if not resp.ok:
        raise RuntimeError(f"Cohere API error ({resp.status_code}): {resp.text[:400]}")
    data = resp.json()
    message = data.get("message", {})
    content = message.get("content", [])
    if isinstance(content, list) and content:
        return content[0].get("text", "").strip()
    return str(message.get("content", "")).strip()

def _call_openai(api_key: str, model: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": min(max_tokens, 4096),
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=90)
    if not resp.ok:
        raise RuntimeError(f"OpenAI API error ({resp.status_code}): {resp.text[:400]}")
    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("OpenAI returned no completion choices")
    return choices[0]["message"]["content"].strip()

def _call_anthropic(api_key: str, model: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str:
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": min(max_tokens, 4096),
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=90)
    if not resp.ok:
        raise RuntimeError(f"Anthropic API error ({resp.status_code}): {resp.text[:400]}")
    data = resp.json()
    content = data.get("content", [])
    if not content:
        raise RuntimeError("Anthropic returned empty content")
    return content[0].get("text", "").strip()
