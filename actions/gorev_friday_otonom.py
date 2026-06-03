import time
import json
import logging
from enum import Enum

# --- 1. Güvenlik - Loglara Hassas Veri Sızıntısı Potansiyeli ve Performans - Loglama Yoğunluğu ---
# Python'ın standart 'logging' modülü kullanılarak daha kontrollü ve esnek loglama sağlandı.
# Log seviyeleri (DEBUG, INFO, WARNING, ERROR) sayesinde üretimde gereksiz detaylardan kaçınılabilir.
# Hassas verilerin maskelenmesi için özel bir yardımcı fonksiyon eklendi.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 2. Kod Tasarımı/Performans - Otonom Gelişim Hedefi Belirleme Mekanizması ---
# Otonom gelişim hedeflerini daha yapılandırılmış ve hataya dayanıklı hale getirmek için Enum kullanıldı.
class AutonomousDevelopmentGoal(Enum):
    MONITOR_AND_LEARN = "monitor_and_learn"
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    ADAPT_TO_NEW_DATA_SCHEMA = "adapt_to_new_data_schema"
    # Gelecekte eklenecek hedefler buraya eklenebilir.

# --- 3. Güvenlik - Hassas Veri Maskeleme Yardımcı Fonksiyonu ---
def mask_sensitive_data(data, sensitive_keys=None):
    """
    Belirtilen anahtarlar altında bulunan hassas verileri maskeler.
    Args:
        data (dict/list): Maskelenecek veri yapısı.
        sensitive_keys (list, optional): Hassas olarak kabul edilen anahtar listesi.
                                        Varsayılan olarak belirlenen bazı anahtarları kullanır.
    Returns:
        dict/list: Hassas verileri maskelenmiş veri yapısı.
    """
    if sensitive_keys is None:
        # Örnek hassas anahtarlar. Gerçek uygulamada bu liste daha kapsamlı olmalı
        # ve yapılandırma dosyasından çekilmelidir.
        sensitive_keys = ["api_key", "password", "token", "auth_header", "personal_data", "secret"]

    if isinstance(data, dict):
        masked_data = data.copy()
        for key, value in masked_data.items():
            if key in sensitive_keys:
                masked_data[key] = "[MASKED]"
            elif isinstance(value, (dict, list)):
                masked_data[key] = mask_sensitive_data(value, sensitive_keys)
        return masked_data
    elif isinstance(data, list):
        return [mask_sensitive_data(item, sensitive_keys) for item in data]
    return data

def run_action(parameters):
    action_id = parameters.get("action_id", "default_action")
    command = parameters.get("command", "execute")
    payload = parameters.get("payload", {})
    context = parameters.get("context", {})
    friday_protocol_input = parameters.get("friday_protocol_input", {})
    autonomous_development_goal_str = parameters.get("autonomous_development_goal", AutonomousDevelopmentGoal.MONITOR_AND_LEARN.value)

    # Gelen parametreleri hassas veri maskelemesi uygulayarak logla
    masked_params_for_log = mask_sensitive_data(parameters)
    logger.info(f"Eylem '{action_id}' başlatıldı. Komut: '{command}'. Parametreler (maskelenmiş): {json.dumps(masked_params_for_log)}")

    # --- FRIDAY Protokolü Entegrasyonu ---
    friday_response = {
        "status": "initiated",
        "message": "FRIDAY protokol etkileşimi başlatıldı."
    }
    try:
        # FRIDAY protokolüne gönderilen veriler detaylı olarak DEBUG seviyesinde loglandı.
        # Üretim ortamında DEBUG seviyesi genellikle kapalı olduğundan bu loglar görünmez.
        logger.debug(f"[FRIDAY] FRIDAY protokolüne veri gönderiliyor: {json.dumps(mask_sensitive_data(friday_protocol_input))}")

        # --- Performans - Simülasyon Gecikmelerinin Varlığı ---
        # time.sleep() çağrıları üretim kodundan kaldırıldı.
        # time.sleep(0.05) # Kaldırıldı

        message_type = friday_protocol_input.get("message_type")
        if message_type == "request_analysis":
            processed_data_summary = f"Analiz edildi: {payload.get('item_count', 0)} öğe."
            friday_response = {
                "status": "completed",
                "message": "FRIDAY protokolü isteği başarıyla işledi.",
                "protocol_result": {"analysis_summary": processed_data_summary, "engine_load": "low"}
            }
        elif message_type is None:
             friday_response = {
                "status": "missing_message_type",
                "message": "FRIDAY protokol girdisinde 'message_type' alanı eksik."
            }
        else:
            friday_response = {
                "status": "unsupported_type",
                "message": f"FRIDAY protokolü bu mesaj tipini desteklemiyor: {message_type}"
            }
        logger.debug(f"[FRIDAY] FRIDAY protokolünden yanıt alındı: {json.dumps(friday_response)}")

    # --- Güvenlik - Geniş Kapsamlı Hata Yakalama (Daha spesifik hale getirildi) ---
    # Harici bir servisle etkileşimde olunduğu varsayılarak, JSON parse hatası gibi
    # spesifik hatalar ayrı yakalandı. Diğer beklenmeyen hatalar için genel Exception
    # yakalaması tutuldu ancak 'exc_info=True' ile traceback loglanarak hata tespiti kolaylaştırıldı.
    except json.JSONDecodeError as e:
        friday_response = {
            "status": "error",
            "message": f"FRIDAY protokolü JSON parse hatası: {str(e)}"
        }
        logger.error(f"[FRIDAY HATA] {friday_response['message']}")
    except Exception as e:
        friday_response = {
            "status": "error",
            "message": f"FRIDAY protokol entegrasyonu genel hatası: {str(e)}. Lütfen daha spesifik hata yakalamaları ekleyin."
        }
        logger.error(f"[FRIDAY HATA] {friday_response['message']}", exc_info=True) # exc_info ile traceback loglanır

    # --- Otonom Gelişim ---
    development_status = {
        "progress": "no_change",
        "log": "Otonom gelişim için özel bir eylem tetiklenmedi.",
        "version_tag": "v1.0.0"
    }
    try:
        current_goal = None
        try:
            current_goal = AutonomousDevelopmentGoal(autonomous_development_goal_str)
        except ValueError:
            logger.warning(f"[OTONOM] Bilinmeyen otonom gelişim hedefi: '{autonomous_development_goal_str}'. "
                           f"Varsayılan olarak '{AutonomousDevelopmentGoal.MONITOR_AND_LEARN.value}' kullanılıyor.")
            current_goal = AutonomousDevelopmentGoal.MONITOR_AND_LEARN

        logger.debug(f"[OTONOM] Otonom gelişim hedefi için değerlendiriliyor: '{current_goal.value}'")

        # --- Performans - Simülasyon Gecikmelerinin Varlığı ---
        # time.sleep() çağrıları üretim kodundan kaldırıldı.
        # time.sleep(0.05) # Kaldırıldı

        if current_goal == AutonomousDevelopmentGoal.OPTIMIZE_PERFORMANCE:
            development_status["progress"] = "optimization_suggested"
            development_status["log"] = (
                f"'{command}' komutu için potansiyel performans darboğazı tespit edildi. "
                "İlgili modül için asenkron işlem önerildi. Dahili yapılandırma güncellendi."
            )
            development_status["version_tag"] = "v1.0.1_perf_optimized"
        elif current_goal == AutonomousDevelopmentGoal.ADAPT_TO_NEW_DATA_SCHEMA:
            development_status["progress"] = "schema_adapter_generated"
            development_status["log"] = "Yeni veri şemasına uyum sağlamak için otomatik bir adaptör modülü oluşturuldu ve entegre edildi."
            development_status["version_tag"] = "v1.1.0_schema_adapted"
        else: # AutonomousDevelopmentGoal.MONITOR_AND_LEARN veya bilinmeyen/varsayılan bir hedef
            development_status["progress"] = "evaluated_no_immediate_action"
            development_status["log"] = "Mevcut bağlam, belirli bir otonom gelişim döngüsünü tetiklemedi. İzlemeye devam ediliyor."

        logger.debug(f"[OTONOM] Gelişim Durumu: {development_status['progress']} - {development_status['log']}")

    except Exception as e:
        development_status = {
            "progress": "development_error",
            "log": f"Otonom gelişim süreci başarısız oldu: {str(e)}"
        }
        logger.error(f"[OTONOM HATA] {development_status['log']}", exc_info=True)

    # --- Eylem Sonucunu Oluşturma ---
    action_result_data = {}
    action_status = "success"
    action_message = f"Eylem '{action_id}' tamamlandı."

    if friday_response.get("status") == "completed":
        action_result_data["friday_processed_output"] = friday_response.get("protocol_result")
    else:
        action_status = "warning"
        action_message += " FRIDAY protokol etkileşiminde sorunlar yaşandı."
        logger.warning(f"FRIDAY protokol yanıtı beklenenden farklı veya hatalı: {friday_response.get('status')} - Mesaj: {friday_response.get('message')}")

    action_result_data["internal_processing_summary"] = {
        "command_executed": command,
        # --- Performans - Gereksiz JSON Serileştirme ve Hash İşlemi ---
        # Büyük payload'ların JSON'a dönüştürülüp sonra hash'lenmesi performansı etkileyebilir
        # ve objelerin hash'i Python çalıştırmaları arasında garanti edilmez.
        # Eğer bir unique identifier gerekiyorsa, bu payload'ın bir parçası olmalı
        # veya daha tutarlı bir yöntemle (örn. UUID, veri tabanı ID'si) üretilmelidir.
        # "input_payload_hash": hash(json.dumps(payload)) if payload else None # Kaldırıldı
    }

    logger.info(f"Eylem '{action_id}' durumu: {action_status}. Mesaj: {action_message}")

    return {
        "status": action_status,
        "message": action_message,
        "action_id": action_id,
        "timestamp": time.time(),
        "friday_protocol_response": friday_response,
        "autonomous_development_status": development_status,
        "output_data": action_result_data,
        "final_context": mask_sensitive_data(context) # Çıktıda da context'i maskeleyelim
    }

# --- Örnek Kullanım ---
if __name__ == "__main__":
    logger.info("--- TEST BAŞLANGICI: Başarılı FRIDAY ve Otonom Gelişim ---")
    result1 = run_action({
        "action_id": "test_action_1",
        "command": "process_data",
        "payload": {"item_count": 100, "data_source": "external_api", "api_key": "secret_key_123"},
        "context": {"user_id": "user_abc", "session_id": "sess_xyz", "personal_data": {"email": "test@example.com"}},
        "friday_protocol_input": {"message_type": "request_analysis", "target_system": "data_warehouse"},
        "autonomous_development_goal": "optimize_performance"
    })
    #logger.info(f"Sonuç 1: {json.dumps(result1, indent=2)}\n") # Loglama seviyesi info, bu yüzden sadece sonuç özeti loglanmalı
    logger.info(f"Sonuç 1 (özet): Durum: {result1['status']}, FRIDAY: {result1['friday_protocol_response']['status']}, Otonom: {result1['autonomous_development_status']['progress']}\n")

    logger.info("--- TEST BAŞLANGICI: FRIDAY Hatası ve Schema Adaptasyonu ---")
    result2 = run_action({
        "action_id": "test_action_2",
        "command": "update_schema",
        "payload": {"new_schema_version": "2.0", "details": "customer_table_update", "password": "db_password"},
        "context": {"admin_user": "admin_xyz"},
        "friday_protocol_input": {"message_type": "unsupported_type_action", "data": "dummy_data"}, # Hatalı FRIDAY girdisi
        "autonomous_development_goal": "adapt_to_new_data_schema"
    })
    logger.info(f"Sonuç 2 (özet): Durum: {result2['status']}, FRIDAY: {result2['friday_protocol_response']['status']}, Otonom: {result2['autonomous_development_status']['progress']}\n")

    logger.info("--- TEST BAŞLANGICI: FRIDAY message_type eksik ve İzleme Hedefi ---")
    result3 = run_action({
        "action_id": "test_action_3",
        "command": "monitor_system",
        "payload": {"system_status": "stable"},
        "context": {"system_id": "sys_001"},
        "friday_protocol_input": {"data": "monitor_request"}, # Eksik message_type
        "autonomous_development_goal": "monitor_and_learn"
    })
    logger.info(f"Sonuç 3 (özet): Durum: {result3['status']}, FRIDAY: {result3['friday_protocol_response']['status']}, Otonom: {result3['autonomous_development_status']['progress']}\n")

    logger.info("--- TEST BAŞLANGICI: Otonom Gelişim Hedefi Bilinmeyen ---")
    result4 = run_action({
        "action_id": "test_action_4",
        "command": "deploy_module",
        "payload": {"module_name": "new_feature", "version": "1.0"},
        "context": {},
        "friday_protocol_input": {"message_type": "request_analysis", "target_system": "deployment_engine"},
        "autonomous_development_goal": "unknown_future_goal" # Bilinmeyen hedef
    })
    logger.info(f"Sonuç 4 (özet): Durum: {result4['status']}, FRIDAY: {result4['friday_protocol_response']['status']}, Otonom: {result4['autonomous_development_status']['progress']}\n")