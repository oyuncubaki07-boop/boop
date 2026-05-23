"""
network_monitor.py - J.A.R.V.I.S. Ağ Bağlantı İzleme Modülü
Ping, gecikme, paket kaybı ve ağ arayüzü durumunu kontrol eder.
"""

import subprocess
import platform
import re
import sys
from typing import Dict, Any, Optional

def get_platform() -> str:
    """Çalışılan işletim sistemini döndürür."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    else:
        return "linux"

def ping_host(host: str = "8.8.8.8", count: int = 2) -> Dict[str, Any]:
    """
    Belirtilen host'a ping atar ve sonuçları döndürür.
    Dönüş: {
        "success": bool,
        "output": str,
        "avg_ms": float veya None,
        "loss_percent": float,
        "error": str (varsa)
    }
    """
    plat = get_platform()
    if plat == "windows":
        cmd = ["ping", "-n", str(count), host]
        # Windows çıktısı: "Ortalama = 24ms" veya "Average = 24ms"
        avg_pattern = r"(?:Ortalama|Average)[ =]+(\d+)ms"
        loss_pattern = r"Kayıp = (\d+)"
    else:  # Linux / macOS
        cmd = ["ping", "-c", str(count), host]
        # Örnek: "rtt min/avg/max/mdev = 20.123/25.456/30.789/4.321 ms"
        avg_pattern = r"rtt.* = [\d\.]+/([\d\.]+)/[\d\.]+/[\d\.]+ ms"
        loss_pattern = r"(\d+)% packet loss"
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout + result.stderr
        success = (result.returncode == 0)
        
        # Ortalama gecikmeyi bul
        avg_ms = None
        match = re.search(avg_pattern, output, re.IGNORECASE)
        if match:
            avg_ms = float(match.group(1))
        
        # Paket kaybı yüzdesini bul
        loss_percent = 0.0
        match_loss = re.search(loss_pattern, output, re.IGNORECASE)
        if match_loss:
            if plat == "windows":
                lost = int(match_loss.group(1))
                loss_percent = (lost / count) * 100
            else:
                loss_percent = float(match_loss.group(1))
        
        return {
            "success": success,
            "output": output,
            "avg_ms": avg_ms,
            "loss_percent": loss_percent,
            "error": None
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "avg_ms": None,
            "loss_percent": 100.0,
            "error": "Ping zaman aşımına uğradı."
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "avg_ms": None,
            "loss_percent": 100.0,
            "error": str(e)
        }

def get_active_interfaces() -> list:
    """Aktif ağ arayüzlerini (IP adresleriyle) döndürür."""
    interfaces = []
    plat = get_platform()
    try:
        if plat == "windows":
            result = subprocess.run(["ipconfig"], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            current_iface = None
            for line in lines:
                if "adapter" in line.lower():
                    current_iface = line.strip().rstrip(':')
                elif "IPv4" in line or "IP Address" in line:
                    ip = line.split(":")[-1].strip()
                    if ip and current_iface:
                        interfaces.append(f"{current_iface}: {ip}")
        else:
            # Linux / macOS
            result = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True)
            lines = result.stdout.splitlines()
            for line in lines:
                if "inet " in line and "127.0.0.1" not in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip = parts[1].split('/')[0]
                        # Arayüz adını bul (bir önceki satırda)
                        # Basitçe ip'yi döndür
                        interfaces.append(ip)
        return interfaces[:3]  # En fazla 3 arayüz
    except Exception:
        return []

def network_status(parameters: Optional[dict] = None, player=None) -> str:
    """
    Ağ bağlantı durumunu kontrol eder.
    parameters: {
        "host": "8.8.8.8",   # ping atılacak hedef (isteğe bağlı)
        "count": 2,          # ping sayısı
        "verbose": False     # detaylı çıktı
    }
    """
    params = parameters or {}
    host = params.get("host", "8.8.8.8")
    count = params.get("count", 2)
    verbose = params.get("verbose", False)
    
    if player:
        player.write_log(f"SYS: 🌐 Ağ bağlantısı kontrol ediliyor -> {host}")
    
    result = ping_host(host, count)
    
    # Kullanıcıya özet mesaj
    if result["success"]:
        if result["avg_ms"] is not None:
            latency_msg = f"Gecikme süresi ortalama {result['avg_ms']:.0f} ms."
        else:
            latency_msg = "Bağlantı hızı ölçülemedi ancak erişim var."
        
        if result["loss_percent"] > 0:
            loss_msg = f" Paket kaybı %{result['loss_percent']:.0f}."
        else:
            loss_msg = " Paket kaybı yok."
        
        status_msg = f"Ağ bağlantımız stabil patron. {latency_msg}{loss_msg}"
        
        if verbose and player:
            # Detaylı çıktıyı logla
            player.write_log(f"SYS: Ping detayı:\n{result['output'][:500]}")
        
        # Aktif arayüzleri de göster (opsiyonel)
        if verbose:
            interfaces = get_active_interfaces()
            if interfaces:
                status_msg += f" Aktif arayüzler: {', '.join(interfaces)}"
    else:
        if result["error"]:
            error_detail = result["error"]
        else:
            error_detail = "Dış ağa erişilemiyor."
        status_msg = f"Patron, internet bağlantısında sorun tespit ettim. {error_detail}"
    
    return status_msg