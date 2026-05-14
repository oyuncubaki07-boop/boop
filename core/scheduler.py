import schedule
import time
import threading
from core.github_updater import update_system_from_github
from core.thinker import generate_and_save_tool

update_lock = threading.Lock()

def job_github_update():
    if not update_lock.locked():
        with update_lock:
            update_system_from_github()

def job_think_and_improve():
    if not update_lock.locked():
        with update_lock:
            print("[Scheduler] 5 Saatlik derin düşünme modu aktif. Yeni özellikler analiz ediliyor...")
            tool_name = f"auto_skill_{int(time.time())}"
            generate_and_save_tool("otonom gelişim", tool_name, is_autonomous=True)

def _run_scheduler_loop():
    schedule.every(1).hours.do(job_github_update)
    schedule.every(5).hours.do(job_think_and_improve)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def start_background_tasks():
    t = threading.Thread(target=_run_scheduler_loop, daemon=True, name="JarvisScheduler")
    t.start()
    print("[Scheduler] Otonom zamanlayıcı arka planda başlatıldı (1 saatlik güncelleme, 5 saatlik düşünme).")