import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.config_loader import load_config as load_central_config
from core.gemini_client import generate_text as gemini_generate_text


def _base_dir() -> Path:
    try:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        return Path(__file__).resolve().parent.parent
    except Exception:
        return Path(".")


def load_config() -> dict:
    try:
        data = load_central_config()
        return data if isinstance(data, dict) else {}
    except Exception:
        try:
            path = _base_dir() / "config" / "api_keys.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}


@dataclass
class ProviderResult:
    name: str
    role: str
    text: str
    ok: bool
    error: str = ""


def _http_json(url: str, headers: dict, body: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_openai_style(data: dict) -> str:
    try:
        choices = data.get("choices") or []
        if not choices:
            return ""
        return (choices[0].get("message", {}).get("content") or "").strip()
    except Exception:
        return ""


class BaseProvider:
    def __init__(self, name: str, role: str, enabled: bool = True):
        self.name = name
        self.role = role
        self.enabled = enabled

    def chat(self, prompt: str, system: str = "") -> ProviderResult:
        if not self.enabled:
            return ProviderResult(self.name, self.role, "", False, "Devre disi")
        try:
            text = self._request(prompt, system)
            if text:
                return ProviderResult(self.name, self.role, text, True)
            return ProviderResult(self.name, self.role, "", False, "Bos yanit")
        except Exception as exc:
            return ProviderResult(self.name, self.role, "", False, str(exc))

    def _request(self, prompt: str, system: str) -> str:
        raise NotImplementedError


class GeminiProvider(BaseProvider):
    def __init__(self, api_key: str, model: str):
        super().__init__("Gemini", "Mimar", bool(api_key))
        self.model = model

    def _request(self, prompt: str, system: str) -> str:
        return gemini_generate_text(prompt, system=system, model=self.model)


class OpenRouterProvider(BaseProvider):
    def __init__(self, api_key: str | list[str], model: str):
        if isinstance(api_key, list):
            keys = [k for k in api_key if k]
        else:
            keys = [api_key] if api_key else []
        super().__init__("OpenRouter", "Analist", len(keys) > 0)
        self.api_keys = keys
        self.current_key_idx = 0
        self.model = model

    def _request(self, prompt: str, system: str) -> str:
        if not self.api_keys:
            raise ValueError("No API keys configured for OpenRouter")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        num_keys = len(self.api_keys)
        last_exc = None
        for i in range(num_keys):
            idx = (self.current_key_idx + i) % num_keys
            api_key = self.api_keys[idx]
            try:
                data = _http_json(
                    "https://openrouter.ai/api/v1/chat/completions",
                    {
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://jarvis.local",
                        "X-Title": "JARVIS Council",
                    },
                    {"model": self.model, "messages": messages, "temperature": 0.35},
                )
                
                # Check for API key error response
                if isinstance(data, dict):
                    err = data.get("error", {})
                    if err:
                        msg = err.get("message", "").lower()
                        code = err.get("code")
                        if code == 401 or "api key" in msg or "invalid" in msg or "unauthorized" in msg:
                            print(f"[OpenRouter fallback] Key {idx+1} rejected: {msg}")
                            continue

                res = _extract_openai_style(data)
                if res:
                    self.current_key_idx = idx
                    return res
            except Exception as exc:
                print(f"[OpenRouter fallback] Key {idx+1} failed: {exc}")
                last_exc = exc
                continue
        if last_exc:
            raise last_exc
        return ""


class MistralProvider(BaseProvider):
    def __init__(self, api_key: str, model: str):
        super().__init__("Mistral", "Kod Denetci", bool(api_key))
        self.api_key = api_key
        self.model = model

    def _request(self, prompt: str, system: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        data = _http_json(
            "https://api.mistral.ai/v1/chat/completions",
            {"Authorization": f"Bearer {self.api_key}"},
            {"model": self.model, "messages": messages, "temperature": 0.3},
        )
        return _extract_openai_style(data)


class CohereProvider(BaseProvider):
    def __init__(self, api_key: str, model: str):
        super().__init__("Cohere", "Risk Analisti", bool(api_key))
        self.api_key = api_key
        self.model = model

    def _request(self, prompt: str, system: str) -> str:
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
            "temperature": 0.35,
        }
        if system:
            body["preamble"] = system
        data = _http_json(
            "https://api.cohere.com/v2/chat",
            {"Authorization": f"Bearer {self.api_key}"},
            body,
        )
        parts = data.get("message", {}).get("content") or []
        return "\n".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()


class GroqProvider(BaseProvider):
    def __init__(self, api_key: str | list[str], model: str):
        if isinstance(api_key, list):
            keys = [k for k in api_key if k]
        else:
            keys = [api_key] if api_key else []
        super().__init__("Groq", "Hizli Denetci", len(keys) > 0)
        self.api_keys = keys
        self.current_key_idx = 0
        self.model = model

    def _request(self, prompt: str, system: str) -> str:
        if not self.api_keys:
            raise ValueError("No API keys configured for Groq")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        num_keys = len(self.api_keys)
        last_exc = None
        for i in range(num_keys):
            idx = (self.current_key_idx + i) % num_keys
            api_key = self.api_keys[idx]
            try:
                data = _http_json(
                    "https://api.groq.com/openai/v1/chat/completions",
                    {"Authorization": f"Bearer {api_key}"},
                    {"model": self.model, "messages": messages, "temperature": 0.2},
                )
                
                # Check for API key error response
                if isinstance(data, dict):
                    err = data.get("error", {})
                    if err:
                        msg = err.get("message", "").lower()
                        if "api key" in msg or "invalid" in msg or "unauthorized" in msg:
                            print(f"[Groq fallback] Key {idx+1} rejected: {msg}")
                            continue

                res = _extract_openai_style(data)
                if res:
                    self.current_key_idx = idx
                    return res
            except Exception as exc:
                print(f"[Groq fallback] Key {idx+1} failed: {exc}")
                last_exc = exc
                continue
        if last_exc:
            raise last_exc
        return ""


def build_providers(cfg: dict | None = None) -> list[BaseProvider]:
    try:
        cfg = cfg or load_config()
        models = cfg.get("ai_council", {}).get("models", {})
        
        # Load multiple openrouter keys
        or_keys = []
        for k in ["openrouter_api_key", "openrouter_api_key_2", "openrouter_api_key_3"]:
            val = cfg.get(k, "")
            if val and val not in or_keys:
                or_keys.append(val)
        if not or_keys:
            or_keys = [""]
            
        # Load multiple groq keys
        groq_keys = []
        for k in ["groq_api_key", "groq_api_key_2", "groq_api_key_3"]:
            val = cfg.get(k, "")
            if val and val not in groq_keys:
                groq_keys.append(val)
        if not groq_keys:
            groq_keys = [""]
            
        return [
            GeminiProvider(cfg.get("gemini_api_key", ""), models.get("gemini", "gemini-2.5-flash")),
            OpenRouterProvider(or_keys, models.get("openrouter", "google/gemini-2.0-flash-001")),
            MistralProvider(cfg.get("mistral_api_key", ""), models.get("mistral", "mistral-small-latest")),
            CohereProvider(cfg.get("cohere_api_key", ""), models.get("cohere", "command-r7b-12-2024")),
            GroqProvider(groq_keys, models.get("groq", "llama-3.3-70b-versatile")),
        ]
    except Exception:
        return []


def build_critic_providers(cfg: dict | None = None) -> list[BaseProvider]:
    try:
        return [p for p in build_providers(cfg) if p.name != "Gemini" and p.enabled]
    except Exception:
        return []


def parallel_chat(
    providers: list[BaseProvider],
    prompt: str,
    system: str = "",
    on_result: Callable[[ProviderResult], None] | None = None,
) -> list[ProviderResult]:
    results: list[ProviderResult] = []
    try:
        active = [p for p in providers if p.enabled]
        if not active:
            return results
        with ThreadPoolExecutor(max_workers=max(1, len(active))) as pool:
            futures = {pool.submit(p.chat, prompt, system): p for p in active}
            for fut in as_completed(futures):
                try:
                    res = fut.result()
                    results.append(res)
                    if on_result:
                        on_result(res)
                except Exception:
                    continue
    except Exception:
        pass
    try:
        return sorted(results, key=lambda r: r.name)
    except Exception:
        return results


def first_available(providers: list[BaseProvider]) -> BaseProvider | None:
    try:
        for p in providers:
            if p.enabled:
                return p
    except Exception:
        pass
    return None
