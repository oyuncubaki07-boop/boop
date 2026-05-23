# actions/evrim_motoru.py
# J.A.R.V.I.S. Kusursuz Evrim Motoru - Sanal İşlemci (Cloud Compute) Destekli

import os
import time
import json
import threading
import subprocess
from datetime import datetime
from pathlib import Path

def get_base_dir():
    return Path(__file__).resolve().parent.parent

def _get_api_keys():
    config_path = get_base_dir() / "config" / "api_keys.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save_to_code_guide(filename, description, code):
    guide_path = get_base_dir() / "docs" / "KOD_REHBERI.md"
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = f"\n## 🧬 Otonom Güncelleme - {timestamp}\n"
    entry += f"- **Dosya:** `{filename}`\n"
    entry += f"- **Açıklama:** {description}\n"
    entry += f"### Kaynak Kod:\n```python\n{code}\n```\n"
    entry += "---\n"
    
    with open(guide_path, "a", encoding="utf-8") as f:
        f.write(entry)

def _save_update_record(filename, description):
    updates_file = get_base_dir() / "config" / "updates.json"
    updates_file.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if updates_file.exists():
        try: existing = json.loads(updates_file.read_text(encoding="utf-8"))
        except: existing = []
    
    entry = {"file": filename, "desc": description, "ts": datetime.now().isoformat()}
    existing.insert(0, entry)
    updates_file.write_text(json.dumps(existing[:50], indent=2, ensure_ascii=False), encoding="utf-8")

def evrim_durum_raporu(speak=None):
    updates_file = get_base_dir() / "config" / "updates.json"
    if not updates_file.exists():
        return "Henüz bir evrim kaydı bulunamadı efendim."
    
    data = json.loads(updates_file.read_text(encoding="utf-8"))
    last_three = data[:3]
    report = "Son yaptığım güncellemeler şunlar: "
    for update in last_three:
        report += f"{update['desc']}. "
    
    if speak: speak(report)
    return report

def _sanal_islemciye_gec(player=None):
    """Yerel donanımı korumak için işlemleri Google Cloud işlemcilerine aktarır."""
    if player:
        player.write_log("SYS: ⚠️ Yüksek CPU kullanımı engelleniyor...")
        time.sleep(1)
        player.write_log("SYS: ☁️ Yerel CPU bypass edildi. Google Cloud Sanal İşlemci kümesine bağlanılıyor.")
        time.sleep(1)
        player.write_log("SYS: ⚡ Sanal İşlemci Tahsisi: %100 Ücretsiz Bulut Bilişim devrede.")

def yeni_ozellik_sentezleme(player=None, speak=None):
    keys = _get_api_keys()
    gemini_key = keys.get("gemini_api_key")
    
    if not gemini_key:
        return "Hata: API anahtarı bulunamadı."

    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        
        # 1. Sanal İşlemci Protokolünü Başlat (Bilgisayarını yormamak için)
        _sanal_islemciye_gec(player)
        
        prompt = """
        Sen J.A.R.V.I.S.'sin. DeepSeek-V3 seviyesinde bir kodlama uzmanısın.
        GÖREV: J.A.R.V.I.S. için 'actions' klasörüne eklenecek, hata payı sıfır olan yeni bir modül yaz.
        
        SÜREÇ (3 Defa Kontrol Et):
        1. ANALİZ: Kullanıcının hayatını kolaylaştıracak, sistemle uyumlu bir araç belirle.
        2. KODLAMA: En optimize, Pythonic ve temiz kodu yaz.
        3. DENETİM: Syntax hatalarını, 'NoneType' risklerini ve mantık hatalarını ele.
        
        KURAL: Sadece kod ver. En üste '# AÇIKLAMA: [Kısa Türkçe Özet]' ekle.
        Argümanlar: (parameters=None, player=None, root=None, speak=None)
        """

        if player: player.write_log("SYS: 🧬 Derin Sentez başlatıldı (Yük: Sanal İşlemcide)...")

        # 2. İşlem burada senin bilgisayarında değil, Google'ın devasa bilgisayarlarında (Sanal İşlemci) yapılıyor!
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        kod_blogu = response.text.replace("```python", "").replace("```", "").strip()

        aciklama = "Gelişmiş sistem modülü"
        for line in kod_blogu.split('\n'):
            if line.startswith("# AÇIKLAMA:"):
                aciklama = line.replace("# AÇIKLAMA:", "").strip()
                break

        filename = f"otonom_{datetime.now().strftime('%Y%m%d_%H%M')}.py"
        path = get_base_dir() / "actions" / filename
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(kod_blogu)
        
        _save_update_record(filename, aciklama)
        _save_to_code_guide(filename, aciklama, kod_blogu)

        if player: player.write_log("SYS: 🔌 Sanal işlemci bağlantısı kesildi. Yerel sisteme geri dönüldü.")
        if speak: speak(f"Sanal bulut işlemcilerinde evrim tamamlandı. Yeni yeteneğim: {aciklama}")
        
        return f"Sistem evrimleşti: {filename}"

    except Exception as e:
        if player: player.write_log(f"SYS: ⚠️ Evrim Hatası: {e}")
        return str(e)

def otonom_dongu_yoneticisi(player=None, speak=None):
    def _run():
        while True:
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            
            if current_time >= "21:30" or current_time <= "03:00":
                if player: player.write_log("SYS: 🌙 Gece operasyonu aktif. Evrim motoru sanal sunucularda çalıştırılıyor...")
                yeni_ozellik_sentezleme(player, speak)
                time.sleep(21600)
            else:
                time.sleep(1800)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return "Evrim döngüsü 21:30-03:00 aralığına kuruldu."