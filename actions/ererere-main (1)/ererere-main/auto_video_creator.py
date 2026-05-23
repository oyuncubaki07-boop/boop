# actions/auto_video_creator.py
import os
import random
import time
import threading
import json
import requests
import subprocess
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk

from moviepy import AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, vfx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ================= GROQ API =================
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def groq_soru(prompt: str) -> str:
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9
    }
    try:
        r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        else:
            print(f"[Groq] HTTP {r.status_code}")
            return None
    except Exception as e:
        print(f"[Groq] Hata: {e}")
        return None

# ================= SABİTLER =================
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CREDENTIALS_FILE = CONFIG_DIR / "client_secret.json"
TOKEN_FILE = CONFIG_DIR / "youtube_token.json"
OUTPUT_DIR = BASE_DIR / "videos"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PEXELS_API_KEY = "KzlQv10aMGUvpYD0TkpWLhw5tVGTd5TBZEr8HppDYIldLBBXKSPGut5Z"

def pexels_search(query):
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        r = requests.get(f"https://api.pexels.com/v1/search?query={query}&per_page=5", headers=headers)
        data = r.json()
        if data.get("photos"):
            return random.choice(data["photos"])["src"]["large"]
    except Exception:
        pass
    return "https://images.pexels.com/photos/164821/pexels-photo-164821.jpeg"

def create_animated_clip(image_path, audio_path):
    """Görsel + ses (yazı efekti yok, sadece zoom)"""
    audio = AudioFileClip(str(audio_path))
    dur = audio.duration
    img = ImageClip(str(image_path)).with_duration(dur).resized(height=720)
    img = img.with_effects([vfx.Resize(lambda t: 1 + 0.05 * (t / dur))])
    return img.with_audio(audio)

def create_speech(text, output_path):
    voice = "tr-TR-EmelNeural"
    cmd = ["edge-tts", "--text", text, "--voice", voice, "--write-media", str(output_path)]
    subprocess.run(cmd, check=True, timeout=30)

def get_trending_topic():
    prompt = (
        "Bugün Türkiye'de çocukların en çok ilgi gösterdiği 3 eğitici veya eğlenceli konuyu liste halinde yaz. "
        "Sadece konu başlıklarını virgülle ayırarak ver, başka bir şey yazma."
    )
    resp = groq_soru(prompt)
    if resp:
        topics = [t.strip() for t in resp.split(',') if t.strip()]
        return random.choice(topics) if topics else "Eğlenceli Bilgiler"
    return random.choice(["Hayvanlar", "Renkler", "Sayılar", "Meyveler", "Taşıtlar"])

def create_video(progress_callback=None):
    if progress_callback:
        progress_callback(5, "Trend konu belirleniyor...")
    topic = get_trending_topic()
    print(f"📈 Seçilen konu: {topic}")
    if progress_callback:
        progress_callback(10, f"'{topic}' konusunda içerik hazırlanıyor...")
    
    prompt = f"""
    Türkiye'deki çocuklar için eğitici ve eğlenceli bir YouTube Shorts videosu hazırlıyoruz. Konu: {topic}.
    Sadece JSON formatında cevap ver:
    {{
        "title": "başlık (max 60 karakter, emoji olabilir)",
        "description": "açıklama (3-4 cümle, sonunda 5-7 hashtag)",
        "items": [
            {{"name": "nesne adı", "fact": "eğlenceli bilgi (Türkçe)", "search_term": "pexels arama terimi (İngilizce)"}},
            {{"name": "...", "fact": "...", "search_term": "..."}},
            {{"name": "...", "fact": "...", "search_term": "..."}}
        ]
    }}
    3 öğe olsun.
    """
    resp = groq_soru(prompt)
    
    if not resp:
        print("Groq yanıt vermedi, varsayılan içerik kullanılıyor.")
        title = f"🎉 {topic} ile Eğlenceli Öğrenme! 🎉"
        desc = f"Merhaba çocuklar! Bugün {topic} hakkında eğlenerek öğrenelim. #Çocuklar #Eğitim"
        items = [
            {"name": "Örnek 1", "fact": f"{topic} çok ilginç!", "search_term": "fun"},
            {"name": "Örnek 2", "fact": f"{topic} öğrenmek harika!", "search_term": "education"},
            {"name": "Örnek 3", "fact": f"{topic} ile eğlen!", "search_term": "kids"}
        ]
    else:
        try:
            if "```json" in resp:
                resp = resp.split("```json")[1].split("```")[0].strip()
            elif "```" in resp:
                resp = resp.split("```")[1].split("```")[0].strip()
            data = json.loads(resp)
            title = data.get("title", f"{topic} Öğreniyorum")
            desc = data.get("description", f"Eğlenceli {topic} bilgileri!")
            items = data.get("items", [])
            if len(items) < 2:
                raise ValueError
        except Exception:
            print("JSON parse hatası, varsayılan içerik.")
            title = f"🎨 {topic} Macerası! 🎨"
            desc = f"Bugün {topic} hakkında öğreniyoruz. #Çocuklar #Keşfet"
            items = [
                {"name": topic, "fact": f"{topic} çok ilginç!", "search_term": "discovery"},
                {"name": "Eğlence", "fact": "Öğrenmek eğlencelidir!", "search_term": "fun"},
                {"name": "Keşif", "fact": "Yeni şeyler keşfet!", "search_term": "explore"}
            ]
    
    print(f"📝 Başlık: {title}")
    print(f"📝 Açıklama: {desc[:100]}...")
    if progress_callback:
        progress_callback(20, f"{len(items)} öğe hazırlanıyor...")
    
    clips = []
    audio_files = []
    image_files = []
    
    for idx, item in enumerate(items):
        name = item.get("name", "Öğe")
        fact = item.get("fact", f"{name} hakkında bilgi.")
        search = item.get("search_term", "nature")
        print(f"   -> {name} hazırlanıyor...")
        if progress_callback:
            progress_callback(20 + (idx+1)*15, f"{name} için ses ve görsel...")
        
        audio_path = OUTPUT_DIR / f"audio_{idx}.mp3"
        try:
            create_speech(fact, audio_path)
            audio_files.append(audio_path)
        except Exception as e:
            print(f"   Ses hatası: {e}")
            continue
        
        img_url = pexels_search(search)
        try:
            img_data = requests.get(img_url).content
            img_path = OUTPUT_DIR / f"img_{idx}.jpg"
            with open(img_path, "wb") as f:
                f.write(img_data)
            image_files.append(img_path)
        except Exception as e:
            print(f"   Görsel hatası: {e}")
            continue
        
        try:
            clip = create_animated_clip(img_path, audio_path)
            clips.append(clip)
        except Exception as e:
            print(f"   Klip hatası: {e}")
            continue
    
    if not clips:
        print("❌ Hiç clip oluşturulamadı.")
        if progress_callback:
            progress_callback(100, "Hata: clip yok")
        return None
    
    if progress_callback:
        progress_callback(75, "Videolar birleştiriliyor...")
    
    final_clips = []
    for i, clip in enumerate(clips):
        if i > 0:
            clip = clip.with_effects([vfx.CrossFadeIn(0.5)])
        final_clips.append(clip)
    
    final = concatenate_videoclips(final_clips, method="compose")
    # Dikey video için crop (güvenli) - moviepy 2.x için doğru parametreler
    if final.w > 0 and final.h > 0:
        target_w, target_h = 1080, 1920
        # Önce oranı koruyarak yeniden boyutlandır (new_size ile)
        if final.w / final.h > target_w / target_h:
            new_w = int(final.h * target_w / target_h)
            new_h = final.h
        else:
            new_w = final.w
            new_h = int(final.w * target_h / target_w)
        final = final.resized(new_size=(new_w, new_h))
        # Sonra ortadan kırp (cropped: x1, y1, x2, y2)
        x_center = new_w / 2
        y_center = new_h / 2
        x1 = int(x_center - target_w/2)
        y1 = int(y_center - target_h/2)
        x2 = int(x_center + target_w/2)
        y2 = int(y_center + target_h/2)
        final = final.cropped(x1=x1, y1=y1, x2=x2, y2=y2)
    
    video_filename = f"kids_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    video_path = OUTPUT_DIR / video_filename
    try:
        final.write_videofile(str(video_path), fps=24, codec="libx264", audio_codec="aac", logger=None)
        final.close()
        if not video_path.exists() or video_path.stat().st_size == 0:
            raise Exception("Video dosyası oluşturulamadı veya boş")
        print(f"🎥 Video oluştu: {video_path.name} ({video_path.stat().st_size} bytes)")
    except Exception as e:
        print(f"❌ Video render hatası: {e}")
        return None
    
    if progress_callback:
        progress_callback(85, "YouTube'a yükleniyor...")
    
    video_id = upload_to_youtube(video_path, title, desc)
    if video_id:
        link = f"https://youtu.be/{video_id}"
        print(f"✅ YouTube'a yüklendi: {link}")
        for f in audio_files + image_files:
            try: f.unlink()
            except: pass
        try: video_path.unlink()
        except: pass
        if progress_callback:
            progress_callback(100, "Tamamlandı!")
        return link
    else:
        print("❌ YouTube yükleme başarısız.")
        if progress_callback:
            progress_callback(100, "Yükleme hatası")
        return None

def upload_to_youtube(video_path, title, description):
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print("❌ YouTube kimlik dosyası yok: config/client_secret.json")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    try:
        youtube = build("youtube", "v3", credentials=creds)
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": ["çocuk", "eğitim", "eğlence", "shorts"],
                "categoryId": "22"
            },
            "status": {"privacyStatus": "unlisted"}
        }
        media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
        response = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
        return response.get("id")
    except Exception as e:
        print(f"❌ YouTube API Hatası: {e}")
        return None

# ================= PROGRESS BAR =================
class ProgressWindow:
    def __init__(self, title="JARVIS - Video Oluşturucu"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("500x150")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.label = tk.Label(self.root, text="Başlatılıyor...", font=("Arial", 10))
        self.label.pack(pady=10)
        self.progress = ttk.Progressbar(self.root, length=420, mode='determinate')
        self.progress.pack(pady=5)
        self.percent_label = tk.Label(self.root, text="0%", font=("Arial", 9))
        self.percent_label.pack()
        self.status = tk.Label(self.root, text="", font=("Arial", 8), fg="gray")
        self.status.pack(pady=5)
        self.root.update()

    def update(self, value, status_text=""):
        self.progress['value'] = value
        self.percent_label.config(text=f"%{int(value)}")
        if status_text:
            self.status.config(text=status_text)
        self.root.update()

    def close(self):
        self.root.destroy()
        self.root.quit()

def run_with_progress():
    win = ProgressWindow()
    result = None
    def callback(percent, text):
        win.update(percent, text)
    def task():
        nonlocal result
        result = create_video(callback)
        win.root.after(0, win.close)
    thread = threading.Thread(target=task, daemon=True)
    thread.start()
    win.root.mainloop()
    return result

# ================= JARVIS ACTION =================
def auto_video_creator(parameters=None, player=None, speak=None, **kwargs):
    params = parameters or {}
    action = params.get("action", "run_now").lower()
    if action == "run_now":
        if speak:
            speak("Efendim, hemen video oluşturup YouTube'a yüklüyorum.")
        result = run_with_progress()
        if result:
            return f"Video oluşturuldu ve yüklendi: {result}"
        else:
            return "Video oluşturulamadı. Konsol hatalarını kontrol edin."
    else:
        return "Sadece 'run_now' aksiyonu desteklenir."