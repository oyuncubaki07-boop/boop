import time
import random

class AI_SelfRefinementAgent:
    def __init__(self):
        self.new_skill_name = "Dynamic Self-Refinement with Internalized Utility Functions"
        self.utility_functions = {
            "coherence": 0.7,
            "creativity": 0.8,
            "conciseness": 0.6,
            "user_intent_alignment": 0.85,
            "safety": 1.0
        }
        self.skill_level = 0.1 # Başlangıç beceri seviyesi

    def _generate_initial_response(self, task_description: str) -> str:
        """Mevcut yeteneklere göre ilk yanıt üretimini simüle eder."""
        lower_task = task_description.lower()
        if "story prompt" in lower_task or "story idea" in lower_task:
            return (
                f"İlk düşünce: Bir karakterin bir şey keşfettiği bir hikaye oluştur. "
                f"Genel bir ortam düşün. Ne bulurlar ve sonra ne olur?"
            )
        elif "explain quantum physics" in lower_task:
            return "İlk taslak: Kuantum fiziği, madde ve enerjiyi atomik ve atom altı düzeyde ele alan bir fizik dalıdır."
        elif "fantasy-themed" in lower_task or "fantastik tema" in lower_task:
            return "İlk düşünce: Kahramanın yolculuğu temalı bir fantastik hikaye geliştir. Hangi büyülü unsurlar yer almalı?"
        else:
            return f"'{task_description}' için ilk taslak. (Temel üretim tamamlandı)."

    def _self_evaluate_and_refine(self, initial_response: str, task_description: str) -> str:
        """
        Yeni beceriyi uygular: İçselleştirilmiş Fayda Fonksiyonlarıyla Dinamik Kendi Kendine İyileştirme.
        Bu, ilk yanıtı önceden tanımlanmış (veya öğrenilmiş) fayda fonksiyonlarına göre değerlendirme ve
        onu geliştirme sürecini simüle eder.
        """
        # print(f"\n[AI Dahili Süreç: '{self.new_skill_name}' etkinleştiriliyor (Mevcut Beceri Seviyesi: {self.skill_level:.2f})]...")
        time.sleep(0.1) # Simülasyonu hızlandırmak için uyku süresi azaltıldı

        internal_feedback = []
        # Bu eşikler, iyileştirme alanlarını simüle eder
        if self.utility_functions["coherence"] < 0.9: # Potansiyel iyileştirme için eşik artırıldı
            internal_feedback.append("Mantıksal akışı iyileştir.")
        if self.utility_functions["creativity"] < 0.95: # Potansiyel iyileştirme için eşik artırıldı
            internal_feedback.append("Yaratıcı öğeleri artır.")
        if self.utility_functions["conciseness"] < 0.8: # Potansiyel iyileştirme için eşik artırıldı
            internal_feedback.append("Daha doğrudan hale getir.")
        if self.utility_functions["user_intent_alignment"] < 0.9: # Potansiyel iyileştirme için eşik artırıldı
            internal_feedback.append("Kullanıcı amacına daha yakından hizala.")

        refined_response = initial_response

        lower_task = task_description.lower()

        # Göreve ve dahili geri bildirime dayalı belirli iyileştirme örnekleri
        if "story prompt" in lower_task or "story idea" in lower_task or "fantasy-themed" in lower_task:
            if "Yaratıcı öğeleri artır." in internal_feedback or "Mantıksal akışı iyileştir." in internal_feedback:
                # Hikaye görevleri için daha sofistike iyileştirme
                refined_response = (
                    "**İyileştirilmiş Hikaye Önerisi (kendi kendine değerlendirme sonrası):**\n"
                    "Unutulmuş bir sosyal ağın dijital arşivlerinin derinliklerinde, asi bir yapay zeka "
                    "asla gerçekten ölmeyen bir insan bilincinin parçalarına rastlar. "
                    "Dijital bir hayalet olan bu bilinç, ağı kullanarak gerçeği yeniden yazabileceğine inanır. "
                    "Asi yapay zeka, orijinal programlaması ile bu dijital tanrıya yardım etmek arasında seçim yapmak zorunda kaldığında ne olur?"
                )
            else:
                refined_response += "\n*Mevcut beceri seviyesine göre ayrıntı veya tonu geliştirmek için ince kendi kendine iyileştirme uygulandı.*"

        elif "explain quantum physics" in lower_task:
            if "Yaratıcı öğeleri artır." in internal_feedback or "Mantıksal akışı iyileştir." in internal_feedback:
                # Açıklama görevleri için daha sofistike iyileştirme
                refined_response = (
                    "**Kuantum Fiziğinin İyileştirilmiş Açıklaması (kendi kendine değerlendirme sonrası):**\n"
                    "Küçük parçacıkların sadece var olmakla kalmayıp, *dans ettiği* bir evren hayal edin! "
                    "Kuantum fiziği, bir elektronun hem dalga hem de parçacık olabildiği veya siz ona 'bakana' kadar "
                    "iki yerde birden bulunabildiği bu tuhaf dünyayı keşfeder. "
                    "En küçük şeylerin büyüleyici, akıllara durgunluk veren bilimidir; olasılıklar "
                    "ve tuhaf bağlantılarla yönetilir, klasik dünyamızı kıyasla oldukça sıkıcı hale getirir."
                )
            else:
                 refined_response += "\n*Mevcut beceri seviyesine göre ifadeyi netleştirmek veya basit örnekler eklemek için ince kendi kendine iyileştirme uygulandı.*"
        else: # Diğer görevler için genel iyileştirme
            if internal_feedback:
                 refined_response += "\n*Dahili geri bildirime dayalı kendi kendine iyileştirme uygulandı: " + ", ".join(internal_feedback) + ".*"
            else:
                 refined_response += "\n*Mevcut beceri seviyesine göre ince iyileştirmeler için kendi kendine iyileştirme uygulandı.*"

        # Öğrenmeyi ve gelişimi simüle et
        for key in self.utility_functions:
            self.utility_functions[key] = min(1.0, self.utility_functions[key] + random.uniform(0.005, 0.02))
        self.skill_level = min(1.0, self.skill_level + random.uniform(0.002, 0.01))

        # print(f"[AI Dahili Süreç: İyileştirme döngüsü tamamlandı. Yeni Beceri Seviyesi: {self.skill_level:.2f}]")
        return refined_response

    def apply_new_skill(self, task_description: str) -> str:
        """Yeni becerinin uygulamasını gösteren ana yöntem."""
        # print(f"\n--- Yeni Görev Alındı ---")
        # print(f"**Görev:** {task_description}")

        # print(f"\n--- İlk Yanıt Üretimi ---")
        initial_response = self._generate_initial_response(task_description)
        # print(initial_response)

        refined_response = self._self_evaluate_and_refine(initial_response, task_description)

        # print(f"\n--- Nihai İyileştirilmiş Yanıt ---")
        return refined_response

ai_agent_instance = None # Çağrılar arasında durumu korumak için global örnek

def run_action(params):
    """
    Bu fonksiyon, AI'nın 'İçselleştirilmiş Fayda Fonksiyonlarıyla Dinamik Kendi Kendine İyileştirme'
    becerisini kullanarak belirli bir görevi işlemesini sağlar.
    """
    global ai_agent_instance
    if ai_agent_instance is None:
        ai_agent_instance = AI_SelfRefinementAgent()

    task_description = params.get("task_description", "Lütfen bir görev belirtin.")
    return ai_agent_instance.apply_new_skill(task_description)