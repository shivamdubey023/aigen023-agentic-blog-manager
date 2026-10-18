"""Centralized environment loader that reads directly from .env file or system environment."""
from __future__ import annotations
import os
import re
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]

def load_local_env() -> dict[str, str]:
    """Parse .env file supporting python-dotenv, toml-like, and key=value formats."""
    env_vars: dict[str, str] = {}
    env_file = APP_ROOT / ".env"
    if not env_file.exists():
        return env_vars
    
    try:
        content = env_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Match key = "value" or key = value or KEY=value
            match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*[:=]\s*(?:[\"']?(.*?)[\"']?)$", line)
            if match:
                k = match.group(1).strip()
                v = match.group(2).strip()
                env_vars[k.lower()] = v
                env_vars[k.upper()] = v
                env_vars[k] = v
                # Also set in os.environ if not already set
                if k.upper() not in os.environ and v:
                    os.environ[k.upper()] = v
    except Exception as exc:
        print(f"Warning: could not read .env: {exc}")
    
    return env_vars

# Load on module import
_ENV = load_local_env()

def get_env(key: str, default: str = "") -> str:
    """Retrieve environment variable checking os.environ and parsed .env."""
    return os.environ.get(key, _ENV.get(key.lower(), _ENV.get(key.upper(), _ENV.get(key, default)))).strip()

def get_groq_key() -> str:
    return get_env("GROQ_API_KEY") or get_env("GROQ") or get_env("groq")

def get_gemini_key() -> str:
    return get_env("GEMINI_API_KEY") or get_env("GEMINI") or get_env("gemini")

def get_cohere_key() -> str:
    return get_env("COHERE_API_KEY") or get_env("COHERE") or get_env("Cohere") or get_env("cohere")

def get_openai_key() -> str:
    return get_env("OPENAI_API_KEY") or get_env("OPENAI") or get_env("openai")

def get_anthropic_key() -> str:
    return get_env("ANTHROPIC_API_KEY") or get_env("ANTHROPIC") or get_env("anthropic")

def get_pexels_key() -> str:
    return get_env("PEXELS_API_KEY")

def get_unsplash_key() -> str:
    return get_env("UNSPLASH_ACCESS_KEY")

def get_google_client_id() -> str:
    return get_env("GOOGLE_CLIENT_ID") or get_env("client_id")

def get_google_client_secret() -> str:
    return get_env("GOOGLE_CLIENT_SECRET") or get_env("client_secret")

def get_google_redirect_uri() -> str:
    return get_env("GOOGLE_OAUTH_REDIRECT_URI") or get_env("redirect_uri") or ""
