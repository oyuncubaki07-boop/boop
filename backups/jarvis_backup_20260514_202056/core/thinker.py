import json
import os
import time
from pathlib import Path
import google.generativeai as genai

from agent.planner import BASE_DIR, API_CONFIG_PATH

def _get_api_key() -> str:
    with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]

def generate_and_save_tool(task_description: str, tool_name: str, is_autonomous: bool = False):
    """
    is_autonomous=True ise kendi kendine düşünüp rastgele faydalı bir araç yazar.
    False ise kullanıcının istediği yapamadığı bir şeyi araştırıp yazar.
    """
    genai.configure(api_key=_get_api_key())
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    if is_autonomous:
        prompt = (
            "Sen gelişmiş bir kişisel asistanın Düşünme modülüsün. "
            "Sistemin yeteneklerini artırmak için basit ama faydalı bir otomasyon betiği yaz. "
            "Eğer tarayıcı kullanman gerekirse kesinlikle Opera GX kullan. "
            "Sadece Python kodunu ver. Kodu 'def run_action(params):' fonksiyonu içine yaz."
        )
    else:
        prompt = (
            f"Kullanıcı şu görevi istedi ama mevcut araçlarda yok: '{task_description}'. "
            "Bu görevi Stack Overflow veya belgelere dayanarak çözecek bir Python betiği yaz. "
            "Eğer tarayıcı açılması gerekiyorsa varsayılan olarak Opera GX kullan. "
            "Sadece 'def run_action(params):' fonksiyonunu içeren Python kodunu ver, açıklama yapma."
        )

    response = model.generate_content(prompt)
    code = response.text.strip().strip('`').replace('python\n', '')
    
    # Kalıcı dosya olarak actions klasörüne kaydet
    action_path = BASE_DIR / "actions" / f"{tool_name}.py"
    with open(action_path, "w", encoding="utf-8") as f:
        f.write(code)
        
    print(f"[Thinker] Yeni araç kalıcı olarak eklendi: actions/{tool_name}.py")
    return tool_name