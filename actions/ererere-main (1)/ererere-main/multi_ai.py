"""
multi_ai.py - J.A.R.V.I.S. Çoklu AI Motoru
DeepSeek, Gemini, OpenRouter, Mistral, Cohere arasında otomatik geçiş yapar.
"""

import json
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path

class MultiAI:
    """
    Birden fazla AI API'sini yöneten merkezi sınıf.
    - DeepSeek (birinci öncelik)
    - OpenRouter (ikinci)
    - Gemini (üçüncü)
    - Mistral (dördüncü)
    - Cohere (beşinci)
    """
    
    def __init__(self, player=None):
        self.player = player
        self.config = self._load_config()
        self.current_model = self.config.get("primary_model", "deepseek")
        self.fallback_models = self.config.get("fallback_models", ["openrouter", "gemini", "mistral", "cohere"])
        
    def _load_config(self) -> Dict[str, Any]:
        """API konfigürasyonunu yükler."""
        base_dir = Path(__file__).resolve().parent.parent
        config_paths = [
            base_dir / "config" / "api_keys.json",
            base_dir / "ui" / "config" / "api_keys.json"
        ]
        
        for path in config_paths:
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except:
                    pass
        return {}
    
    def log(self, msg: str):
        if self.player and hasattr(self.player, "write_log"):
            self.player.write_log(f"SYS: {msg}")
        else:
            print(f"[MULTI-AI] {msg}")
    
    def _call_deepseek(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """DeepSeek API çağrısı."""
        try:
            api_key = self.config.get("deepseek_api_key")
            if not api_key:
                self.log("DeepSeek API anahtarı bulunamadı")
                return None
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4096
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                self.log(f"DeepSeek API hatası: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"DeepSeek çağrı hatası: {e}")
            return None
    
    def _call_openrouter(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """OpenRouter API çağrısı."""
        try:
            api_key = self.config.get("openrouter_api_key")
            if not api_key:
                return None
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": "openai/gpt-3.5-turbo",
                "messages": messages,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return None
        except:
            return None
    
    def _call_gemini(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Gemini API çağrısı (metin modu)."""
        try:
            import google.generativeai as genai
            api_key = self.config.get("gemini_api_key")
            if not api_key:
                return None
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            full_prompt = system_prompt + "\n\n" + prompt if system_prompt else prompt
            response = model.generate_content(full_prompt)
            return response.text
        except:
            return None
    
    def _call_mistral(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Mistral API çağrısı."""
        try:
            api_key = self.config.get("mistral_api_key")
            if not api_key:
                return None
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": "mistral-small-latest",
                "messages": messages,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            return None
        except:
            return None
    
    def _call_cohere(self, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Cohere API çağrısı."""
        try:
            api_key = self.config.get("cohere_api_key")
            if not api_key:
                return None
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "command",
                "prompt": system_prompt + "\n\n" + prompt if system_prompt else prompt,
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(
                "https://api.cohere.ai/v1/generate",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["generations"][0]["text"]
            return None
        except:
            return None
    
    def chat(self, prompt: str, system_prompt: str = "") -> str:
        """
        Tüm modelleri dener, ilk başarılı olanın sonucunu döndürür.
        Öncelik: DeepSeek -> OpenRouter -> Gemini -> Mistral -> Cohere
        """
        models = [
            ("DeepSeek", self._call_deepseek),
            ("OpenRouter", self._call_openrouter),
            ("Gemini", self._call_gemini),
            ("Mistral", self._call_mistral),
            ("Cohere", self._call_cohere)
        ]
        
        for model_name, call_func in models:
            self.log(f"🔄 {model_name} deneniyor...")
            result = call_func(prompt, system_prompt)
            if result:
                self.log(f"✅ {model_name} başarılı yanıt verdi")
                return result
            self.log(f"❌ {model_name} başarısız oldu")
        
        return "Üzgünüm, hiçbir AI servisine bağlanamadım. Lütfen API key'lerinizi kontrol edin."
    
    def quick_chat(self, prompt: str) -> str:
        """Hızlı sohbet için basitleştirilmiş metod."""
        return self.chat(prompt, "Sen J.A.R.V.I.S.'sin, yardımsever bir yapay zeka asistanısın. Kısa ve net cevaplar ver.")