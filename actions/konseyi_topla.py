import webbrowser
import os

def run_action(parameters: dict) -> str:
    try:
        from core.thinker import generate_and_save_tool

        # Konsey odasını otomatik aç
        html_path = os.path.abspath("konsey_odasi.html")
        webbrowser.open(f"file://{html_path}")

        params = parameters or {}
        task = str(params.get("task") or params.get("task_description") or "").strip()
        autonomous = bool(params.get("autonomous", False))

        if not task and autonomous:
            tool_name = generate_and_save_tool("", is_autonomous=True)
        elif not task:
            return "Efendim, otonom mod icin 'autonomous' true gonderin veya bir gorev yazin."
        else:
            tool_name = generate_and_save_tool(task, is_autonomous=autonomous)

        if tool_name:
            return f"Efendim, konsey calismasini tamamladi. Yeni yetenek: {tool_name}."
        return "Efendim, konsey su an sonuc uretemedi; debate_log.json dosyasina bakabilirsiniz."
    except Exception as exc:
        return f"Efendim, konsey sirasinda kucuk bir aksaklik oldu: {exc}"
