"""Multi-model AI generation engine supporting Gemini, Groq, Cohere, OpenAI, and Claude."""
from __future__ import annotations
import requests

from core.env_config import (
    get_groq_key, get_gemini_key, get_cohere_key, get_openai_key, get_anthropic_key,
)

SUPPORTED_PROVIDERS = {
    "groq": {
        "name": "Groq Cloud (Free & Ultra Fast)",
        "models": ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"],
        "default_model": "openai/gpt-oss-120b",
    },
    "gemini": {
        "name": "Google Gemini (Free Tier)",
        "models": ["gemini-3.8-flash", "gemini-flash-latest", "gemini-pro-latest"],
        "default_model": "gemini-3.8-flash",
    },
    "cohere": {
        "name": "Cohere (Free Trial)",
        "models": ["command-r-08-2024", "command-r-plus-08-2024"],
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

HUMANIZED_SYSTEM_PROMPT = """You are a technical writing assistant for NextGen Tech Notes.
Write clear, practical, original Markdown that matches the user's topic and audience. Use a
single H1 followed by useful H2/H3 sections, complete examples where appropriate, prerequisites,
troubleshooting, and a verification checklist when relevant.

Do not claim personal experience or tests were performed. Do not invent terminal output, tracebacks,
version support, statistics, quotations, citations, or URLs. Mark details needing confirmation as
[VERIFY]. Distinguish illustrative examples from observed results. Do not pad to reach a word count,
promise search rankings or advertising approval, or write to evade AI-detection systems.
Return only the article Markdown."""

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
    provider: str,
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
    """Generate an article only with the provider and model explicitly selected."""
    provider = provider.lower().strip()
    provider_config = SUPPORTED_PROVIDERS.get(provider)
    if not provider_config:
        raise ValueError(f"Unsupported AI provider: {provider or '(empty)'}")
    if not topic.strip():
        raise ValueError("Choose an article topic before generating.")
    selected_model = model or provider_config["default_model"]
    resolved_key = resolve_key_for_provider(provider, api_key)
    if not resolved_key:
        raise ValueError(f"No API key is configured for {provider}. Configure it or select another provider.")
    system_prompt = custom_system_prompt.strip() or HUMANIZED_SYSTEM_PROMPT

    user_prompt = f"""Write a complete, practical technical article for NextGen Tech Notes.
Topic: {topic}
Primary keyword: {primary_keyword or topic}
Target reader level: {audience}
Author notes & specific guidance: {notes or 'Provide relevant examples and troubleshooting guidance.'}

Start with one specific, descriptive '# ' title and a useful introduction that names the reader,
explains the problem, and previews what the article will teach. Organize the body with meaningful
H2 sections and nested H3 subsections; keep paragraphs focused and use lists for actual sequences
or grouped items. Explain prerequisites before examples. Include complete code and commands only
when relevant, label fenced code blocks with their language, and provide practical troubleshooting
or limitations where useful. Use Markdown tables only for concise comparisons or specifications
supported by the notes; never fabricate prices, features, measurements, or benchmarks. Conclude
with a practical summary or next step. Include references only when their URLs and claims are known;
otherwise mark uncertain technical details [VERIFY] and do not invent citations.
Add a ```diagram fence only when a simple process is accurately represented by explicit arrow-
separated steps; do not invent architecture or claim generated code was executed. Avoid generic
filler, repeated headings, exaggerated promises, and forced affiliate recommendations.
Output Markdown only.
"""

    provider_calls = {
        "groq": _call_groq,
        "gemini": _call_gemini,
        "cohere": _call_cohere,
        "openai": _call_openai,
        "anthropic": _call_anthropic,
    }
    draft = provider_calls[provider](
        resolved_key, selected_model, system_prompt, user_prompt, temperature, max_tokens
    )
    if not draft.strip():
        raise RuntimeError(f"{provider} returned an empty article. Review the request and retry.")
    return draft.strip()

def _raise_provider_error(provider: str, status_code: int) -> None:
    if status_code == 401 or status_code == 403:
        detail = "check the selected provider's API key and permissions"
    elif status_code == 429:
        detail = "the provider reported a rate limit or quota limit; retry later or choose another provider"
    elif status_code >= 500:
        detail = "the provider is temporarily unavailable; retry later"
    else:
        detail = "check the selected model and request settings"
    raise RuntimeError(f"{provider} API request failed (HTTP {status_code}); {detail}.")

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
        _raise_provider_error("Groq", resp.status_code)
    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("Groq returned no completion choices")
    return choices[0]["message"]["content"].strip()

def _call_gemini(api_key: str, model: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> str:
    # Auto-adjust model name for 2026 availability
    if "2.5" in model:
        model = "gemini-3.8-flash"
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
        _raise_provider_error("Gemini", resp.status_code)
    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned no candidates. Check the model and request settings.")
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
        _raise_provider_error("Cohere", resp.status_code)
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
        _raise_provider_error("OpenAI", resp.status_code)
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
        _raise_provider_error("Anthropic", resp.status_code)
    data = resp.json()
    content = data.get("content", [])
    if not content:
        raise RuntimeError("Anthropic returned empty content")
    return content[0].get("text", "").strip()
