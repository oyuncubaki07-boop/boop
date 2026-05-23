"""
J.A.R.V.I.S. 2.0 — MediaPipe El Hareketi Kontrolü
====================================================
Arka plan thread'inde çalışır, UI'ı dondurmaz.
MediaPipe Hands ile el landmark'larını yakalar ve gesture tanır.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

try:
    import cv2
    import numpy as np
    import mediapipe as mp
    _MEDIAPIPE_AVAILABLE = True
except ImportError:
    _MEDIAPIPE_AVAILABLE = False


class Gesture(Enum):
    """Tanınabilir el hareketleri."""
    NONE        = "none"
    POINT       = "point"         # İşaret parmağı uzatılmış
    FIST        = "fist"          # Yumruk — durdur/kapat
    OPEN_PALM   = "open_palm"     # Açık avuç — dur/bekle
    PEACE       = "peace"         # Barış işareti — ekran görüntüsü
    THUMBS_UP   = "thumbs_up"     # Başparmak yukarı — onay
    PINCH       = "pinch"         # Başparmak + işaret — seç/zoom


@dataclass
class GestureEvent:
    """Algılanan gesture bilgisi."""
    gesture: Gesture
    cursor_x: float     # Normalize 0-1 (ekran genişliği oranı)
    cursor_y: float     # Normalize 0-1 (ekran yüksekliği oranı)
    confidence: float   # MediaPipe güven skoru
    timestamp: float = field(default_factory=time.time)


class GestureController(threading.Thread):
    """
    MediaPipe Hands ile el izleme — daemon thread.
    
    Kullanım:
        def on_gesture(event: GestureEvent):
            print(f"Gesture: {event.gesture.value}")
        
        gc = GestureController(on_gesture=on_gesture)
        gc.start()
        ...
        gc.stop()
    """

    def __init__(
        self,
        on_gesture: Optional[Callable[[GestureEvent], None]] = None,
        camera_index: int = 0,
        screen_w: int = 1920,
        screen_h: int = 1080,
    ):
        super().__init__(daemon=True, name="GestureControlThread")
        self.on_gesture = on_gesture
        self.camera_index = camera_index
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._running = False
        self._prev_x = 0.5
        self._prev_y = 0.5
        self._smooth_factor = 5
        self._last_gesture = Gesture.NONE
        self._last_gesture_time = 0.0
        self._gesture_cooldown = 0.5  # Aynı gesture'ı 500ms'de bir raporla

    @property
    def is_available(self) -> bool:
        """MediaPipe + OpenCV yüklü mü?"""
        return _MEDIAPIPE_AVAILABLE

    def run(self):
        """Ana izleme döngüsü — thread'de çalışır."""
        if not _MEDIAPIPE_AVAILABLE:
            print("[GestureControl] ❌ mediapipe veya opencv yüklü değil. Devre dışı.")
            return

        self._running = True
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        mp_hands = mp.solutions.hands

        print("[GestureControl] 🖐️ El hareket izleme başlatıldı.")

        with mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.6,
        ) as hands:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.01)
                    continue

                # Aynalama — doğal kontrol
                frame = cv2.flip(frame, 1)
                h, w, _ = frame.shape

                # BGR → RGB
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb)

                if results.multi_hand_landmarks:
                    hand = results.multi_hand_landmarks[0]
                    lm = hand.landmark

                    # İşaret parmağı ucu (8) → ekran koordinatına ölçekle
                    idx_tip = lm[8]
                    cursor_x = np.interp(idx_tip.x, [0.1, 0.9], [0.0, 1.0])
                    cursor_y = np.interp(idx_tip.y, [0.1, 0.9], [0.0, 1.0])

                    # Smoothing — titreme engelleme
                    self._prev_x += (cursor_x - self._prev_x) / self._smooth_factor
                    self._prev_y += (cursor_y - self._prev_y) / self._smooth_factor

                    # Gesture tanıma
                    gesture = self._classify_gesture(lm)

                    # Cooldown kontrolü — aynı gesture'ı spam etme
                    now = time.time()
                    if gesture != Gesture.NONE:
                        if gesture != self._last_gesture or (now - self._last_gesture_time) > self._gesture_cooldown:
                            self._last_gesture = gesture
                            self._last_gesture_time = now

                            if self.on_gesture:
                                confidence = results.multi_handedness[0].classification[0].score
                                event = GestureEvent(
                                    gesture=gesture,
                                    cursor_x=float(np.clip(self._prev_x, 0, 1)),
                                    cursor_y=float(np.clip(self._prev_y, 0, 1)),
                                    confidence=confidence,
                                )
                                try:
                                    self.on_gesture(event)
                                except Exception as e:
                                    print(f"[GestureControl] ⚠️ Callback hatası: {e}")

                # ~30 FPS
                time.sleep(0.033)

        cap.release()
        print("[GestureControl] 🛑 El hareket izleme durduruldu.")

    def _classify_gesture(self, landmarks) -> Gesture:
        """Landmark noktalarından gesture tanı."""
        tips = [4, 8, 12, 16, 20]      # Parmak uçları
        pips = [3, 6, 10, 14, 18]      # Parmak orta eklemleri

        fingers_up = []
        # Başparmak — x ekseninde kontrol (sağ el için)
        fingers_up.append(landmarks[4].x < landmarks[3].x)
        # Diğer 4 parmak — y ekseninde kontrol
        for tip, pip_ in zip(tips[1:], pips[1:]):
            fingers_up.append(landmarks[tip].y < landmarks[pip_].y)

        up_count = sum(fingers_up)

        # Başparmak + işaret parmağı yakınlığı → PINCH
        thumb_idx_dist = np.hypot(
            landmarks[4].x - landmarks[8].x,
            landmarks[4].y - landmarks[8].y,
        )
        if thumb_idx_dist < 0.05:
            return Gesture.PINCH

        if up_count == 0:
            return Gesture.FIST
        if up_count == 5:
            return Gesture.OPEN_PALM
        if fingers_up == [False, True, False, False, False]:
            return Gesture.POINT
        if fingers_up == [False, True, True, False, False]:
            return Gesture.PEACE
        if fingers_up == [True, False, False, False, False]:
            return Gesture.THUMBS_UP

        return Gesture.NONE

    def stop(self):
        """Thread'i güvenli şekilde durdur."""
        self._running = False
