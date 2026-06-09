import json
import sys
import time
import base64
import logging
from pathlib import Path
from typing import Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openrouter_client")

def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "config").exists() or (parent / "main.py").exists():
            return parent
    return p.parent


BASE_DIR     = _get_base_dir()
API_KEY_PATH = BASE_DIR / "config" / "api_keys.json"

def _load_api_keys() -> list[str]:
    keys = []
    try:
        import sys
        root = str(API_KEY_PATH.parent.parent)
        if root not in sys.path:
            sys.path.insert(0, root)
        from core.config_loader import load_config
        cfg = load_config()
        for key_name in ["openrouter_api_key", "openrouter_api_key_2", "openrouter_api_key_3"]:
            val = cfg.get(key_name, "").strip()
            if val and val not in keys:
                keys.append(val)
    except Exception as e:
        logger.error(f"Failed to load OpenRouter API keys via config_loader: {e}")
        
    if not keys:
        try:
            with open(API_KEY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key_name in ["openrouter_api_key", "openrouter_api_key_2", "openrouter_api_key_3"]:
                val = data.get(key_name, "").strip()
                if val and val not in keys:
                    keys.append(val)
        except Exception as e:
            logger.error(f"Manual fallback for api_keys.json failed: {e}")
            
    if not keys:
        raise RuntimeError(f"No OpenRouter API keys found in config or at {API_KEY_PATH}")
    return keys

TEXT_MODELS: list[str] = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-3-12b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "anthropic/claude-3.5-sonnet",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
]

VISION_MODELS: list[str] = [
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "nvidia/llama-nemotron-embed-vl-1b-v2:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-3n-e4b-it:free",
    "google/gemma-3n-e2b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
]

API_URL               = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MAX_TOKENS    = 4096
DEFAULT_TEMPERATURE   = 0.7
REQUEST_TIMEOUT       = 60   # seconds per request
MAX_RETRIES_PER_MODEL = 2    # attempts before moving to next model
RETRY_DELAY           = 2    # seconds between retries
RATE_LIMIT_COOLDOWN   = 60   # seconds before retrying a rate-limited model

_rate_limited: dict[str, float] = {}

class OpenRouterClient:

    def __init__(self) -> None:
        self.api_keys = _load_api_keys()
        self.current_key_index = 0

    @property
    def api_key(self) -> str:
        if 0 <= self.current_key_index < len(self.api_keys):
            return self.api_keys[self.current_key_index]
        return self.api_keys[0] if self.api_keys else ""

    def _is_rate_limited(self, model: str) -> bool:
        ts = _rate_limited.get(model)
        if ts is None:
            return False
        if time.time() - ts > RATE_LIMIT_COOLDOWN:
            del _rate_limited[model]
            return False
        return True

    def _mark_rate_limited(self, model: str) -> None:
        _rate_limited[model] = time.time()
        logger.warning(
            f"[OpenRouter] Rate limited: {model} — "
            f"cooling down for {RATE_LIMIT_COOLDOWN}s"
        )

    def _call(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        response_format: Optional[dict] = None,
    ) -> Optional[str]:
        payload: dict = {
            "model":       model,
            "messages":    messages,
            "max_tokens":  max_tokens,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        num_keys = len(self.api_keys)
        for i in range(num_keys):
            idx = (self.current_key_index + i) % num_keys
            api_key = self.api_keys[idx]
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
                "HTTP-Referer":  "https://github.com/mark-xxv",
                "X-Title":       "MARK XXV",
            }
            
            key_failed = False
            for attempt in range(1, MAX_RETRIES_PER_MODEL + 1):
                try:
                    resp = requests.post(
                        API_URL,
                        headers=headers,
                        json=payload,
                        timeout=REQUEST_TIMEOUT,
                    )

                    if resp.status_code in (401, 403):
                        logger.warning(
                            f"[OpenRouter fallback] API Key {idx+1} failed with status {resp.status_code}. "
                            f"Trying next key..."
                        )
                        key_failed = True
                        break

                    if resp.status_code == 400:
                        try:
                            err_msg = resp.json().get("error", {}).get("message", "").lower()
                            if "api key" in err_msg or "invalid" in err_msg or "unauthorized" in err_msg:
                                logger.warning(f"[OpenRouter fallback] API Key {idx+1} rejected: {err_msg}")
                                key_failed = True
                                break
                        except Exception:
                            pass

                    if resp.status_code == 429:
                        self._mark_rate_limited(model)
                        return None

                    if resp.status_code == 200:
                        self.current_key_index = idx
                        data    = resp.json()
                        content = (
                            data.get("choices", [{}])[0]
                                .get("message", {})
                                .get("content", "")
                        )
                        return content.strip() if content else None

                    logger.warning(
                        f"[OpenRouter] {model} → HTTP {resp.status_code} "
                        f"(attempt {attempt}/{MAX_RETRIES_PER_MODEL})"
                    )

                except requests.exceptions.Timeout:
                    logger.warning(
                        f"[OpenRouter] {model} → Timeout "
                        f"(attempt {attempt}/{MAX_RETRIES_PER_MODEL})"
                    )
                except Exception as e:
                    logger.error(f"[OpenRouter] {model} → Unexpected error: {e}")

                if attempt < MAX_RETRIES_PER_MODEL:
                    time.sleep(RETRY_DELAY)

            if key_failed:
                continue

        return None

    def _call_with_fallback(
        self,
        pool: list[str],
        messages: list[dict],
        model: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        response_format: Optional[dict] = None,
    ) -> str:
        if model and not self._is_rate_limited(model):
            result = self._call(model, messages, max_tokens, temperature, response_format)
            if result:
                return result
            logger.info(
                f"[OpenRouter] Requested model failed, "
                f"falling back to pool: {model}"
            )

        for m in pool:
            if self._is_rate_limited(m):
                continue
            logger.info(f"[OpenRouter] Trying: {m}")
            result = self._call(m, messages, max_tokens, temperature, response_format)
            if result:
                logger.info(f"[OpenRouter] ✓ Success: {m}")
                return result

        raise RuntimeError(
            "[OpenRouter] All models failed or are rate-limited. "
            "Check your API key and network connection."
        )

    def chat(
        self,
        prompt: str,
        system: str = (
            "You are a component of MARK XXV, an AI assistant inspired by JARVIS. "
            "Be concise, helpful, and precise."
        ),
        model: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ]
        return self._call_with_fallback(
            TEXT_MODELS, messages, model, max_tokens, temperature
        )

    def chat_json(
        self,
        prompt: str,
        system: str = (
            "Return ONLY valid JSON. "
            "No markdown fences, no extra text, no explanation."
        ),
        model: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> dict:
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ]
        raw = self._call_with_fallback(
            TEXT_MODELS, messages, model, max_tokens, temperature=0.2
        )

        clean = raw.strip()
        if clean.startswith("```"):
            parts = clean.split("```")
            clean = parts[1] if len(parts) > 1 else clean
            if clean.startswith("json"):
                clean = clean[4:]
        clean = clean.strip().rstrip("`").strip()

        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            logger.error(
                f"[OpenRouter] JSON parse failed: {e}\n"
                f"Raw response (first 300 chars): {raw[:300]}"
            )
            raise ValueError(
                f"Model returned unparseable JSON: {e}\n"
                f"Raw output: {raw[:200]}"
            )

    def vision(
        self,
        prompt: str,
        image_b64: str,
        mime: str = "image/png",
        system: str = "Analyze the image and describe what you see clearly and concisely.",
        model: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> str:
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{image_b64}"
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            },
        ]
        return self._call_with_fallback(
            VISION_MODELS, messages, model, max_tokens, temperature=0.2
        )

    def vision_from_file(
        self,
        prompt: str,
        image_path: str,
        system: str = "Analyze the image and describe what you see clearly and concisely.",
        model: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> str:
        path = Path(image_path)
        mime_map = {
            ".png":  "image/png",
            ".jpg":  "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif":  "image/gif",
        }
        mime = mime_map.get(path.suffix.lower(), "image/png")

        with open(path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        return self.vision(prompt, image_b64, mime, system, model, max_tokens)

    def multi_turn(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        return self._call_with_fallback(
            TEXT_MODELS, messages, model, max_tokens, temperature
        )

    def available_models(self) -> dict:
        return {
            "text_models":   TEXT_MODELS,
            "vision_models": VISION_MODELS,
            "rate_limited":  list(_rate_limited.keys()),
            "total_text":    len(TEXT_MODELS),
            "total_vision":  len(VISION_MODELS),
        }

_client_instance = None
_client_init_error = None


def get_client() -> OpenRouterClient:
    """Lazy singleton — created on first call, not at import time."""
    global _client_instance, _client_init_error
    if _client_instance is not None:
        return _client_instance
    if _client_init_error:
        raise _client_init_error
    try:
        _client_instance = OpenRouterClient()
        return _client_instance
    except Exception as e:
        _client_init_error = e
        raise


# Backward-compatible alias: access via or_client.client
class _LazyClient:
    """Proxy that defers OpenRouterClient creation until first attribute access."""
    def __getattr__(self, name):
        return getattr(get_client(), name)

client = _LazyClient()

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

    print("=" * 55)
    print("  MARK XXV — OpenRouter Client Self-Test")
    print("=" * 55)

    print("\n[TEST 1] Basic chat...")
    try:
        reply = get_client().chat("Introduce yourself in one sentence.")
        print(f"  Response : {reply}")
        print(f"  Status   : PASS ✓")
    except Exception as e:
        print(f"  Status   : FAIL ✗ — {e}")

    print("\n[TEST 2] JSON mode...")
    try:
        data = get_client().chat_json(
            'List 3 programming languages. Format: {"languages": ["a", "b", "c"]}',
            system="Return only valid JSON. No extra text."
        )
        print(f"  Response : {data}")
        print(f"  Status   : PASS ✓")
    except Exception as e:
        print(f"  Status   : FAIL ✗ — {e}")

    print("\n[TEST 3] Multi-turn conversation...")
    try:
        history = [
            {"role": "system",    "content": "You are a helpful assistant. Be brief."},
            {"role": "user",      "content": "My name is Tony."},
            {"role": "assistant", "content": "Hello Tony, how can I help you?"},
            {"role": "user",      "content": "What is my name?"},
        ]
        reply = get_client().multi_turn(history)
        print(f"  Response : {reply}")
        print(f"  Status   : PASS ✓")
    except Exception as e:
        print(f"  Status   : FAIL ✗ — {e}")

    print("\n[TEST 4] Model pool info...")
    info = get_client().available_models()
    print(f"  Text models   : {info['total_text']}")
    print(f"  Vision models : {info['total_vision']}")
    print(f"  Rate limited  : {info['rate_limited'] or 'none'}")
    print(f"  Status        : PASS ✓")

    print("\n" + "=" * 55)
    print("  All tests complete.")
    print("=" * 55)