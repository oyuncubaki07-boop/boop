def run_action(parameters: dict) -> str:
    try:
        from kod_rehberi_window import open_kod_rehberi, open_kod_rehberi_safe, QT_VERSION

        if QT_VERSION is None:
            return open_kod_rehberi_safe()

        # Dynamically import the correct QApplication / QTimer depending on QT_VERSION
        if QT_VERSION == "PyQt6":
            from PyQt6.QtCore import QTimer
            from PyQt6.QtWidgets import QApplication
        elif QT_VERSION == "PySide6":
            from PySide6.QtCore import QTimer
            from PySide6.QtWidgets import QApplication
        elif QT_VERSION == "PyQt5":
            from PyQt5.QtCore import QTimer
            from PyQt5.QtWidgets import QApplication
        else:
            return open_kod_rehberi_safe()

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
        try:
            from kod_rehberi_window import open_kod_rehberi_safe
            return open_kod_rehberi_safe()
        except Exception:
            return f"Efendim, kod rehberi modulu hazir degil: {exc}"
