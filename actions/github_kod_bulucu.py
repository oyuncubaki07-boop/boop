import json
import urllib.parse
import urllib.request
from pathlib import Path


def _load_config() -> dict:
    try:
        base = Path(__file__).resolve().parent.parent
        path = base / "config" / "api_keys.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _github_get(url: str, token: str = "") -> tuple[int, dict | list | str]:
    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "JARVIS-AI-Assistant",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body
    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8", errors="replace")
            return exc.code, json.loads(raw) if raw else {}
        except Exception:
            return exc.code, {}
    except Exception as exc:
        return 0, {"error": str(exc)}


def _fetch_raw(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS-AI"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def _search_code(query: str, token: str) -> str | None:
    if not token:
        return None
    try:
        q = urllib.parse.quote(f"{query} language:python")
        status, data = _github_get(f"https://api.github.com/search/code?q={q}&per_page=3", token)
        if status != 200 or not isinstance(data, dict):
            return None
        items = data.get("items") or []
        if not items:
            return None
        best = items[0]
        repo = best.get("repository", {}).get("full_name", "")
        path = best.get("path", "")
        if not repo or not path:
            return None
        status2, content_data = _github_get(
            f"https://api.github.com/repos/{repo}/contents/{urllib.parse.quote(path)}",
            token,
        )
        if status2 != 200 or not isinstance(content_data, dict):
            return None
        import base64

        raw = base64.b64decode(content_data.get("content", "")).decode("utf-8", errors="replace")
        if not raw:
            return None
        snippet = raw[:2500] + ("\n...[devam var]..." if len(raw) > 2500 else "")
        return (
            f"Efendim, kod aramasi (GitHub API):\n"
            f"Kaynak: {repo} -> {path}\n\n"
            f"```python\n{snippet}\n```\n\n"
            "Isterseniz konseyi_topla ile sisteme yetenek olarak ekleyebilirim."
        )
    except Exception:
        return None


def _search_repositories(query: str, token: str) -> str:
    try:
        q = urllib.parse.quote(f"{query} language:python")
        status, data = _github_get(
            f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page=5",
            token,
        )
        if status == 401:
            return (
                "Efendim, GitHub kimlik dogrulamasi gerekiyor. "
                "config/api_keys.json dosyasina 'github_token' ekleyin "
                "(GitHub -> Settings -> Developer settings -> Personal access tokens)."
            )
        if status == 403:
            return "Efendim, GitHub limitine takildik; bir dakika sonra tekrar deneyelim."
        if status != 200 or not isinstance(data, dict):
            return f"Efendim, GitHub aramasi tamamlanamadi. Kod: {status}"

        items = data.get("items") or []
        if not items:
            return f"Efendim, '{query}' icin depo bulamadim."

        repo = items[0]
        full_name = repo.get("full_name", "")
        description = repo.get("description") or "Aciklama yok"
        stars = repo.get("stargazers_count", 0)
        default_branch = repo.get("default_branch", "main")

        status2, tree = _github_get(
            f"https://api.github.com/repos/{full_name}/git/trees/{default_branch}?recursive=1",
            token,
        )
        py_files = []
        if status2 == 200 and isinstance(tree, dict):
            for node in tree.get("tree", []):
                if node.get("type") == "blob" and str(node.get("path", "")).endswith(".py"):
                    if not any(x in node["path"] for x in ("test", "__pycache__", "venv", ".git")):
                        py_files.append(node["path"])
                if len(py_files) >= 8:
                    break

        sample_path = py_files[0] if py_files else None
        code_block = ""
        if sample_path and token:
            status3, file_data = _github_get(
                f"https://api.github.com/repos/{full_name}/contents/{urllib.parse.quote(sample_path)}?ref={default_branch}",
                token,
            )
            if status3 == 200 and isinstance(file_data, dict) and file_data.get("content"):
                import base64

                code = base64.b64decode(file_data["content"]).decode("utf-8", errors="replace")
                code_block = (
                    f"\n\nOrnek dosya `{sample_path}`:\n```python\n{code[:2000]}\n```"
                    if code
                    else ""
                )

        file_list = "\n".join(f"- {p}" for p in py_files[:6]) if py_files else "- (liste alinamadi)"
        return (
            f"Efendim, en uygun depo: **{full_name}** ({stars} yildiz)\n"
            f"{description}\n\n"
            f"Python dosyalari:\n{file_list}"
            f"{code_block}\n\n"
            "konseyi_topla araciyla bunu kendi yetenegimize cevirmemi ister misiniz?"
        )
    except Exception as exc:
        return f"Efendim, GitHub aramasinda beklenmeyen bir durum: {exc}"


def run_action(parameters: dict) -> str:
    try:
        query = str((parameters or {}).get("query", "")).strip()
        if not query:
            return "Efendim, GitHub aramasi icin bir anahtar kelime soylemeniz yeterli."

        cfg = _load_config()
        token = str(cfg.get("github_token", "") or "").strip()

        code_result = _search_code(query, token)
        if code_result:
            return code_result

        return _search_repositories(query, token)
    except Exception as exc:
        return f"Efendim, GitHub modulu yanit veremedi: {exc}"
