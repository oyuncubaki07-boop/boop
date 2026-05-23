import datetime
from pathlib import Path

import psutil


class OmniDirective:
    """Safe and local version of the J.A.R.V.I.S. omni-intelligence layer."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)

    def build_context_snapshot(self) -> dict:
        open_processes = []
        try:
            for proc in psutil.process_iter(["name"]):
                name = proc.info.get("name")
                if name:
                    open_processes.append(name.lower())
        except Exception:
            pass

        context = {
            "timestamp": datetime.datetime.now().isoformat(),
            "workspace": str(self.base_dir),
            "cpu_percent": psutil.cpu_percent(interval=0.2),
            "memory_percent": psutil.virtual_memory().percent,
            "top_processes": open_processes[:30],
            "signals": {
                "opera_gx_active": any("opera" in name for name in open_processes),
                "browser_active": any(
                    browser in name
                    for name in open_processes
                    for browser in ("chrome", "opera", "firefox", "edge")
                ),
                "gaming_active": any(
                    game in name
                    for name in open_processes
                    for game in ("steam", "epicgameslauncher", "valorant")
                ),
                "creative_tools_active": any(
                    tool in name
                    for name in open_processes
                    for tool in ("photoshop", "illustrator", "figma", "blender", "capcut")
                ),
            },
        }
        return context

    def infer_intent_matrix(self, user_text: str, context: dict | None = None) -> list[dict]:
        context = context or self.build_context_snapshot()
        text = (user_text or "").lower().strip()

        candidates = [
            ("search", 0.15),
            ("open_app", 0.10),
            ("system_status", 0.10),
            ("focus_mode", 0.05),
            ("workspace_mode", 0.05),
        ]

        if any(word in text for word in ("ara", "bul", "search", "web", "haber")):
            candidates[0] = ("search", 0.92)
        if any(word in text for word in ("aç", "başlat", "open")):
            candidates[1] = ("open_app", 0.88)
        if any(word in text for word in ("durum", "sistem", "cpu", "ram")):
            candidates[2] = ("system_status", 0.85)
        if any(word in text for word in ("odak", "kilit", "dikkat")):
            candidates[3] = ("focus_mode", 0.82)
        if context.get("signals", {}).get("creative_tools_active"):
            candidates[4] = ("workspace_mode", 0.70)

        ranked = sorted(
            [{"intent": intent, "score": round(score, 2)} for intent, score in candidates],
            key=lambda item: item["score"],
            reverse=True,
        )
        return ranked[:5]

    def build_fallback_protocol(self, failing_system: str) -> list[str]:
        system_name = (failing_system or "unknown").lower()

        if "api" in system_name or "network" in system_name:
            return [
                "Yerel yapılandırmayı yeniden yükle",
                "Alternatif anahtar veya ikinci yapılandırma dosyasını dene",
                "Yerel fallback çıktısı üret ve kullanıcı akışını durdurma",
            ]
        if "audio" in system_name or "microphone" in system_name:
            return [
                "Ses giriş aygıtını yeniden bağlamayı dene",
                "Yalnızca yazılı transkripsiyon moduna düş",
                "Durumu logla ve ana oturumu yeniden başlat",
            ]
        return [
            "Durumu logla",
            "Alternatif yerel yol ara",
            "Oturumu güvenli şekilde yeniden dene",
        ]
