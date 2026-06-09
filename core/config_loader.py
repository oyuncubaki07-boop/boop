"""Merkezi yapilandirma — JSON + ortam degiskeni (.env) + legacy düz metin anahtar dosyasi."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_CONFIG_CACHE = None
_CONFIG_CACHE_TIME = 0
_CONFIG_CACHE_TTL = 300  # seconds before cache auto-invalidates

_ENV_KEYS = {
    "GEMINI_API_KEY": "gemini_api_key",
    "OPENROUTER_API_KEY": "openrouter_api_key",
    "OPENROUTER_API_KEY_2": "openrouter_api_key_2",
    "OPENROUTER_API_KEY_3": "openrouter_api_key_3",
    "MISTRAL_API_KEY": "mistral_api_key",
    "COHERE_API_KEY": "cohere_api_key",
    "GROQ_API_KEY": "groq_api_key",
    "GROQ_API_KEY_2": "groq_api_key_2",
    "GROQ_API_KEY_3": "groq_api_key_3",
    "DEEPSEEK_API_KEY": "deepseek_api_key",
    "GITHUB_TOKEN": "github_token",
    "OPENWEATHER_API_KEY": "openweather_api_key",
    "NEWSAPI_API_KEY": "newsapi_api_key",
    "HUGGINGFACE_API_KEY": "huggingface_api_key",
    "HF_API_KEY": "huggingface_api_key",
    "OLLAMA_BASE_URL": "ollama_base_url",
    "OLLAMA_MODEL": "ollama_model",
}

_BOOL_KEYS = {
    "hourly_evolution",
    "evolution_require_approval",
    "offline_prefer_local",
}

_LEGACY_TEXT_KEY_ALIASES = {
    "groq": "groq_api_key",
    "hugging face": "huggingface_api_key",
    "huggingface": "huggingface_api_key",
    "open weather": "openweather_api_key",
    "openweather": "openweather_api_key",
    "newsapi": "newsapi_api_key",
}


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _config_path() -> Path:
    return get_base_dir() / "config" / "api_keys.json"


def _legacy_key_path() -> Path:
    return get_base_dir() / "config" / "apı keylerim.py"


def _load_dotenv() -> None:
    try:
        env_path = get_base_dir() / ".env"
        if not env_path.exists():
            return
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v
    except Exception:
        pass


def _normalize_label(label: str) -> str:
    return " ".join(label.lower().replace("_", " ").split())


def _parse_legacy_key_line(line: str) -> tuple[str, str] | None:
    cleaned = line.strip()
    if not cleaned or cleaned.startswith("#"):
        return None

    parts = cleaned.split()
    if len(parts) < 2:
        return None

    value = parts[-1].strip()
    label = _normalize_label(" ".join(parts[:-1]))

    key = _LEGACY_TEXT_KEY_ALIASES.get(label)
    if not key:
        key = _LEGACY_TEXT_KEY_ALIASES.get(label.replace(" ", ""))

    if not key:
        return None
    if not value:
        return None
    return key, value


def _load_legacy_text_keys() -> dict:
    data: dict = {}
    try:
        path = _legacy_key_path()
        if not path.exists():
            return data

        for line in path.read_text(encoding="utf-8").splitlines():
            parsed = _parse_legacy_key_line(line)
            if parsed:
                key, value = parsed
                data[key] = value
    except Exception:
        pass
    return data

def load_config() -> dict:
    global _CONFIG_CACHE, _CONFIG_CACHE_TIME
    import time as _time
    now = _time.time()
    if _CONFIG_CACHE is not None and (now - _CONFIG_CACHE_TIME) < _CONFIG_CACHE_TTL:
        return _CONFIG_CACHE

    _load_dotenv()
    data: dict = {}
    try:
        path = _config_path()
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                data = raw
    except Exception:
        pass

    for env_name, cfg_key in _ENV_KEYS.items():
        val = os.getenv(env_name, "").strip()
        if val:
            data[cfg_key] = val

    for bk in _BOOL_KEYS:
        ev = os.getenv(bk.upper(), "").strip().lower()
        if ev in ("1", "true", "yes", "on"):
            data[bk] = True
        elif ev in ("0", "false", "no", "off"):
            data[bk] = False

    data.setdefault("ollama_base_url", "http://127.0.0.1:11434")
    data.setdefault("ollama_model", "llama3.2")
    data.setdefault("evolution_require_approval", True)
    data.setdefault("hourly_evolution", True)
    data.setdefault("offline_prefer_local", False)
    data.setdefault("openweather_api_key", "")
    data.setdefault("newsapi_api_key", "")
    data.setdefault("huggingface_api_key", "")

    for key, value in _load_legacy_text_keys().items():
        if value and not str(data.get(key, "") or "").strip():
            data[key] = value

    _CONFIG_CACHE = data
    _CONFIG_CACHE_TIME = now
    return data


def reload_config() -> dict:
    """Force-reload configuration from disk, clearing the cache."""
    global _CONFIG_CACHE, _CONFIG_CACHE_TIME
    _CONFIG_CACHE = None
    _CONFIG_CACHE_TIME = 0
    return load_config()


def get_key(name: str, default: str = "") -> str:
    return str(load_config().get(name, default) or "")


def get_bool(name: str, default: bool = False) -> bool:
    val = load_config().get(name, default)
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("1", "true", "yes", "on")
    return bool(val)


def get_service_key(service: str, default: str = "") -> str:
    normalized = _normalize_label(service)
    aliases = {
        "gemini": "gemini_api_key",
        "openrouter": "openrouter_api_key",
        "mistral": "mistral_api_key",
        "cohere": "cohere_api_key",
        "groq": "groq_api_key",
        "deepseek": "deepseek_api_key",
        "deepseek api": "deepseek_api_key",
        "huggingface": "huggingface_api_key",
        "hugging face": "huggingface_api_key",
        "openweather": "openweather_api_key",
        "open weather": "openweather_api_key",
        "newsapi": "newsapi_api_key",
        "github": "github_token",
        "ollama": "ollama_base_url",
        "elevenlabs": "elevenlabs_api_key",
        "eleven labs": "elevenlabs_api_key",
    }
    cfg_key = aliases.get(normalized)
    if not cfg_key:
        cfg_key = aliases.get(normalized.replace(" ", ""))
    return get_key(cfg_key, default) if cfg_key else default
