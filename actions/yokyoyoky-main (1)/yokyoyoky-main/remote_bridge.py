# core/remote_bridge.py
import socket
from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head><title>JARVIS Remote Bridge</title></head>
<body>
<h1>JARVIS Remote Bridge</h1>
<p>Bu dosya sadece yer tutucudur. Ana işlevler main.py üzerinden yürütülür.</p>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

def start_bridge(port=5005, use_ngrok=False, ngrok_auth=None):
    print(f"Remote bridge çalışıyor (port {port}) - sadece yer tutucu")

def set_jarvis_instance(instance):
    pass

def broadcast_response(text, audio=None):
    pass

if __name__ == '__main__':
    app.run(port=5005)