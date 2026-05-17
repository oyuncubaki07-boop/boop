def run_action(parameters: dict) -> str:
    try:
        from infinity.core import get_infinity
        action = str((parameters or {}).get("action", "daily_report")).strip()
        query = str((parameters or {}).get("query", "")).strip()
        return get_infinity().run(action, query)
    except Exception as exc:
        return f"Efendim, INFINITY modulu: {exc}"
