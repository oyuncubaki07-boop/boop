def run_action(parameters: dict) -> str:
    try:
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication
        from kod_rehberi_window import open_kod_rehberi, open_kod_rehberi_safe

        app = QApplication.instance()
        if app is None:
            return open_kod_rehberi_safe()

        result_holder = {"msg": "Efendim, kod rehberi aciliyor."}

        def _do_open():
            try:
                result_holder["msg"] = open_kod_rehberi_safe()
            except Exception as exc:
                result_holder["msg"] = f"Efendim, pencere acilamadi: {exc}"

        QTimer.singleShot(0, _do_open)
        return result_holder["msg"]
    except Exception as exc:
        return f"Efendim, kod rehberi modulu hazir degil: {exc}"
