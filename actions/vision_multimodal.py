"""
J.A.R.V.I.S. 2.0 — Multimodal Görüş + Fonksiyon Çağırma
=========================================================
Webcam'den görüntü yakalar, Gemini Vision'a gönderir,
function calling ile aksiyonlar tetikler.
"""

from __future__ import annotations

import asyncio
import os
import webbrowser
from typing import Optional

try:
    import cv2
    import numpy as np
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False

try:
    from google import genai
    from google.genai import types
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


# Fonksiyon tanımları — Gemini'nin çağırabileceği aksiyonlar
VISION_FUNCTION_DECLARATIONS = [
    {
        "name": "open_datasheet",
        "description": "Tespit edilen nesnenin teknik dökümanını veya datasheet'ini web'de aç",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "object_name": {"type": "STRING", "description": "Nesnenin adı"},
                "search_query": {"type": "STRING", "description": "Aranacak sorgu"},
            },
            "required": ["object_name", "search_query"],
        },
    },
    {
        "name": "identify_and_describe",
        "description": "Nesneyi tanımla ve detaylı açıklama yap",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "object_name": {"type": "STRING", "description": "Nesnenin adı"},
                "category": {
                    "type": "STRING",
                    "description": "Kategori: elektronik, kitap, yiyecek, alet, diger",
                },
                "description": {"type": "STRING", "description": "Detaylı açıklama"},
            },
            "required": ["object_name"],
        },
    },
    {
        "name": "search_price",
        "description": "Nesnenin piyasa fiyatını ara",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "product_name": {"type": "STRING", "description": "Ürün adı"},
            },
            "required": ["product_name"],
        },
    },
]


class VisionMultimodal:
    """Webcam görüntüsünü Gemini'ye gönder, fonksiyon çağırma ile aksiyon al."""

    def __init__(self, api_key: str = ""):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self._cap: Optional[cv2.VideoCapture] = None

    def capture_frame(self) -> tuple[bool, bytes]:
        """Webcam'den tek kare yakala, JPEG olarak döndür."""
        if not _CV2_AVAILABLE:
            return False, b""
        
        if self._cap is None:
            self._cap = cv2.VideoCapture(0)
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        ret, frame = self._cap.read()
        if not ret:
            return False, b""

        # Aynalama — kullanıcı doğal görsün
        frame = cv2.flip(frame, 1)

        _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return True, jpeg.tobytes()

    async def analyze(self, user_question: str) -> dict:
        """Kameradan görüntü al, Gemini'ye sor, function call varsa döndür."""
        if not _GENAI_AVAILABLE:
            return {"type": "error", "error": "google.genai modülü yüklü değil"}

        success, image_bytes = self.capture_frame()
        if not success:
            return {"type": "error", "error": "Kamera açılamadı"}

        client = genai.Client(api_key=self._api_key)

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                types.Part.from_text(user_question),
            ],
            config=types.GenerateContentConfig(
                tools=[{"function_declarations": VISION_FUNCTION_DECLARATIONS}],
                temperature=0.3,
            ),
        )

        # Function call kontrolü
        candidate = response.candidates[0]
        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                return {
                    "type": "function_call",
                    "function": fc.name,
                    "args": dict(fc.args) if fc.args else {},
                }

        # Düz metin yanıt
        return {
            "type": "text",
            "response": response.text,
        }

    async def execute_function(self, func_name: str, args: dict) -> str:
        """Gemini'nin döndürdüğü function call'ı çalıştır."""
        if func_name == "open_datasheet":
            query = args.get("search_query", args.get("object_name", ""))
            url = f"https://www.google.com/search?q={query}+datasheet+PDF"
            await asyncio.to_thread(webbrowser.open, url)
            return f"'{args.get('object_name')}' için datasheet araması açıldı."

        elif func_name == "search_price":
            product = args.get("product_name", "")
            url = f"https://www.google.com/search?q={product}+fiyat"
            await asyncio.to_thread(webbrowser.open, url)
            return f"'{product}' fiyat araması açıldı."

        elif func_name == "identify_and_describe":
            desc = args.get("description", "Tanımlandı.")
            return f"Nesne: {args.get('object_name')} — {desc}"

        return f"Bilinmeyen fonksiyon: {func_name}"

    def release(self):
        """Kamerayı serbest bırak."""
        if self._cap:
            self._cap.release()
            self._cap = None
