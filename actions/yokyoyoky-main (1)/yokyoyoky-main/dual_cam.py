from flask import Flask, Response, render_template_string
import cv2
import numpy as np

app = Flask(__name__)

def pc_cam():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        # Kamera yoksa siyah bir frame gönder
        while True:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "KAMERA BULUNAMADI", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, jpeg = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        return

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    while True:
        ret, frame = cap.read()
        if not ret:
            # Hata durumunda siyah frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "KAMERA HATASI", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "YÜZ", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        ret, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
    cap.release()

@app.route('/pc')
def pc():
    return Response(pc_cam(), mimetype='multipart/x-mixed-replace; boundary=frame')

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>JARVIS - Çift Kamera</title>
    <style>
        body { background: #000; color: cyan; font-family: monospace; text-align: center; }
        .cams { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; }
        .cam { border: 3px solid cyan; border-radius: 10px; background: #111; }
        img { width: 640px; height: 480px; }
    </style>
</head>
<body>
    <h1>🛡️ J.A.R.V.I.S. Güvenlik</h1>
    <div class="cams">
        <div class="cam">
            <h3>📱 Tablet Kamera</h3>
            <img src="http://192.168.0.110:8080/video" onerror="this.src='data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22640%22%20height%3D%22480%22%20viewBox%3D%220%200%20640%20480%22%3E%3Crect%20width%3D%22100%25%22%20height%3D%22100%25%22%20fill%3D%22black%22%2F%3E%3Ctext%20x%3D%2250%25%22%20y%3D%2250%25%22%20dominant-baseline%3D%22middle%22%20text-anchor%3D%22middle%22%20fill%3D%22red%22%3ETablet%20kamera%20ba%C4%9Flanamad%C4%B1%3C%2Ftext%3E%3C%2Fsvg%3E'">
        </div>
        <div class="cam">
            <h3>💻 Bilgisayar Kamerası</h3>
            <img src="/pc">
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006)