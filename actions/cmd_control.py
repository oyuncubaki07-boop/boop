"""Komut satiri / dosya acma — agent_task planlayicisi icin."""

from __future__ import annotations

import os
import subprocess
import sys


def cmd_control(parameters: dict | None = None, player=None, **kwargs) -> str:
    params = parameters or {}
    task = str(params.get("task") or "").strip()
    visible = bool(params.get("visible", True))

    if not task:
        return "Efendim, cmd_control icin bir gorev metni gerekli."

    task_lower = task.lower()

    try:
        if sys.platform == "win32":
            if "notepad" in task_lower or "open " in task_lower:
                if "desktop" in task_lower:
                    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                    for part in task.replace("open", "").replace("with notepad", "").split():
                        if "." in part:
                            path = os.path.join(desktop, part.strip("'\""))
                            if os.path.isfile(path):
                                subprocess.Popen(["notepad", path])
                                return f"Efendim, {path} Notepad ile acildi."
                subprocess.Popen(f'cmd /c start "" {task}', shell=True)
                return f"Efendim, komut calistirildi: {task[:80]}"
            subprocess.Popen(task, shell=True)
            return f"Efendim, sistem komutu gonderildi."
        subprocess.run(task, shell=True, check=False)
        return "Efendim, komut tamamlandi."
    except Exception as exc:
        return f"Efendim, cmd_control basarisiz: {exc}"
