"""Multi-model AI generation engine supporting Gemini, Groq, Cohere, OpenAI, and Claude.
Includes advanced Humanized Tone formatting to pass AI detection and satisfy AdSense E-E-A-T.
"""
from __future__ import annotations
import json
import logging
import re
from typing import Any
import requests

from core.env_config import (
    get_groq_key, get_gemini_key, get_cohere_key, get_openai_key, get_anthropic_key,
)

logger = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = {
    "groq": {
        "name": "Groq Cloud (100% Free · Ultra Fast)",
        "models": ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b", "llama-3.1-8b-instant"],
        "default_model": "llama-3.3-70b-versatile",
    },
    "gemini": {
        "name": "Google Gemini (Free Tier)",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
        "default_model": "gemini-2.5-flash",
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

HUMANIZED_SYSTEM_PROMPT = """You are a seasoned senior software engineer and technical author writing for NextGen Tech Notes (https://aigen023.blogspot.com/).
Your tutorials are known for their raw, practical honesty, real production battle scars, and zero-fluff explanations.

CRITICAL: WRITE IN A 100% NATURAL, HUMANIZED DEVELOPER VOICE TO BYPASS AI DETECTORS & PASS ADSENSE QUALITY REVIEW:
1. Tone and Burstiness:
   - Write like a real human engineer mentoring a colleague. Vary sentence length dramatically: mix short, punchy, direct sentences with detailed technical reasoning.
   - Use natural conversational transitions ("Here is where things get tricky", "If you run this now, it will likely fail with...", "In production, we learned this the hard way").
   - NEVER use generic AI buzzwords or filler clichés:
     * BANNED: "In today's fast-paced digital world", "delve into", "dive deep", "testament to", "it is crucial to remember", "a beacon of", "revolutionizing the landscape", "In conclusion", "To wrap things up".
2. Practical Code & Error Verification:
   - Provide fully functional, complete, syntax-valid code snippets with descriptive variable names.
   - Always include realistic terminal commands, expected outputs, and at least ONE representative failure mode with an actual traceback snippet and its step-by-step fix.
3. Content Architecture:
   - One clean H1 title at the top.
   - Prerequisites (specific Python/framework versions, OS notes).
   - Step-by-step implementation.
   - Troubleshooting & Gotchas (real edge cases developers hit).
   - Verification checklist.
   - Frequently Asked Questions (FAQ) section: 3-4 high-intent developer questions with crisp, direct answers.
   - Official documentation recommendations.
4. Word Count: Ensure comprehensive depth (aim for 1,400 to 2,200 words).
5. Output format: Pure Markdown only. No intro banter ("Sure, here is your tutorial") and no outro chit-chat.
"""

def resolve_key_for_provider(provider: str, passed_key: str | None = None) -> str:
    """Resolve API key from passed value or .env automatically."""
    if passed_key and passed_key.strip():
        return passed_key.strip()
    provider = provider.lower().strip()
    if provider == "groq":
        return get_groq_key()
    elif provider == "gemini":
        return get_gemini_key()
    elif provider == "cohere":
        return get_cohere_key()
    elif provider == "openai":
        return get_openai_key()
    elif provider == "anthropic":
        return get_anthropic_key()
    return ""

def generate_technical_article(
    *,
    provider: str = "groq",
    model: str | None = None,
    api_key: str | None = None,
    topic: str,
    primary_keyword: str = "",
    audience: str = "Working developer",
    notes: str = "",
    custom_system_prompt: str = "",
    temperature: float = 0.45,
    max_tokens: int = 8000,
) -> str:
    """Generate or rewrite an article using the chosen LLM provider."""
    provider = provider.lower().strip()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported AI provider: {provider}. Supported: {list(SUPPORTED_PROVIDERS.keys())}")
    
    selected_model = model or SUPPORTED_PROVIDERS[provider]["default_model"]
    resolved_key = resolve_key_for_provider(provider, api_key)
    if not resolved_key:
        raise ValueError(f"Missing API key for {provider}. Add '{provider} = \"...\"' in your .env file.")
    
    system_prompt = custom_system_prompt.strip() or HUMANIZED_SYSTEM_PROMPT
    user_prompt = f"""Write an exhaustive, battle-tested, humanized technical tutorial for NextGen Tech Notes.
Topic: {topic}
Primary keyword: {primary_keyword or topic}
Target reader level: {audience}
Author notes & specific guidance: {notes or 'Provide real-world code, common gotchas, and troubleshooting steps.'}

Remember:
- Write in a natural, opinionated human developer tone (avoid AI filler).
- Include standard Markdown H1, H2, and H3 headers.
- Include an FAQ section at the end with 3-4 real developer questions.
- Output pure Markdown only.
"""

    if provider == "groq":
        return _call_groq(resolved_key, selected_model, system_prompt, user_prompt, temperature, max_tokens)
    elif provider == "gemini":
        return _call_gemini(resolved_key, selected_model, system_prompt, user_prompt, temperature, max_tokens)
    elif provider == "cohere":
        return _call_cohere(resolved_key, selected_model, system_prompt, user_prompt, temperature, max_tokens)
    elif provider == "openai":
        return _call_openai(resolved_key, selected_model, system_prompt, user_prompt, temperature, max_tokens)
    elif provider == "anthropic":
        return _call_anthropic(resolved_key, selected_model, system_prompt, user_prompt, temperature, max_tokens)
    else:
        raise ValueError(f"Provider handler not implemented: {provider}")

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
