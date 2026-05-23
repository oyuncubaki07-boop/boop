"""
error_handler.py - J.A.R.V.I.S. Merkezi Hata Yönetim Sistemi
Tüm modüller için merkezi hata yakalama ve raporlama.
"""

import functools
import time
from typing import Callable, Any

class ErrorHandler:
    """Dekoratör ve yardımcı fonksiyonlarla hata yönetimi."""
    
    def __init__(self, healing_system=None):
        self.healing_system = healing_system
        
    def safe_execute(self, fallback_value: Any = None, error_message: str = None):
        """
        Dekoratör: Fonksiyonu try-except ile sarar.
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if self.healing_system:
                        self.healing_system.capture_error(e, context=func.__name__)
                    if error_message:
                        print(f"[ERROR] {error_message}: {e}")
                    return fallback_value
            return wrapper
        return decorator
    
    def retry(self, max_attempts: int = 3, delay: float = 1.0):
        """
        Dekoratör: Fonksiyonu belirtilen sayıda tekrar dener.
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_error = None
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_error = e
                        if attempt < max_attempts - 1:
                            time.sleep(delay)
                raise last_error
            return wrapper
        return decorator

# Global error handler instance
error_handler = ErrorHandler()
safe_execute = error_handler.safe_execute
retry = error_handler.retry