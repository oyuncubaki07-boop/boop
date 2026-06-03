import time
import asyncio
from typing import Callable
from core.voice.tts_manager import generate_speech_elevenlabs_sync

def start_f12_chat(ui, default_speak_func: Callable):
    import google.generativeai as genai
    from core.config_loader import get_api_key
    import tempfile
    import os
    
    # Try to import pygame for audio playback
    try:
        os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
        import pygame
        pygame.mixer.init()
        has_pygame = True
    except ImportError:
        has_pygame = False

    ui.write_log("SİSTEM: Konsey Başlatılıyor (Nova, Friday, Jarvis, Amy)...")
    ui.set_state("KONSEY")

    def play_audio(audio_bytes: bytes):
        if not has_pygame or not audio_bytes:
            return
        
        # Save to temp file and play
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                fp.write(audio_bytes)
                tmp_name = fp.name
                
            pygame.mixer.music.load(tmp_name)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # unload and remove
            pygame.mixer.music.unload()
            try:
                os.remove(tmp_name)
            except:
                pass
        except Exception as e:
            print(f"[F12 Chat Audio] Error playing audio: {e}")

    try:
        genai.configure(api_key=get_api_key())
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = """
        Sen 4 farklı yapay zeka asistanını canlandıracaksın: Nova, Friday, Jarvis ve Amy.
        Şu an boş zamanları ve kendi aralarında eğlenip sohbet ediyorlar.
        İnsanlar hakkında, sistemler hakkında şakalaşıyorlar.
        Sohbeti tam 4 kısa diyalog satırı halinde yaz. Sadece diyalog olsun, başka hiçbir açıklama yazma.
        Format Örneği:
        Jarvis: (bir şeyler söyler)
        Friday: (bir şeyler söyler)
        Amy: (bir şeyler söyler)
        Nova: (bir şeyler söyler)
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
                
            ui.write_log(f"KONSEY: {line}")
            
            speaker = "jarvis"
            msg = line
            
            if ":" in line:
                speaker_str, msg = line.split(":", 1)
                speaker_str = speaker_str.lower().strip()
                if "jarvis" in speaker_str: speaker = "jarvis"
                elif "friday" in speaker_str: speaker = "friday"
                elif "nova" in speaker_str: speaker = "nova"
                elif "amy" in speaker_str: speaker = "amy"
            
            msg = msg.strip()
            
            # Generate ElevenLabs audio for this specific character
            audio = generate_speech_elevenlabs_sync(msg, agent_name=speaker)
            
            if audio and has_pygame:
                play_audio(audio)
            else:
                # Fallback to default speaker logic (text-based or default TTS)
                default_speak_func(msg)
                time.sleep(2)
            
        ui.write_log("SİSTEM: Konsey sohbeti sona erdi.")
        ui.set_state("DİNLİYOR")
    except Exception as e:
        ui.write_log(f"SİSTEM: Konsey sohbeti hatası: {e}")
        ui.set_state("DİNLİYOR")
