# actions/kod_rehberi.py
# J.A.R.V.I.S. Komut Rehberi – PyQt6, güncel modüller

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QPalette

KOMUTLAR = {
    "🛡️ Güvenlik": [
        ("Biyometrik Kalkan", "Yüz tanıma ile güvenlik kalkanı açar."),
        ("Kara Kutu", "Sistem tanılama, çalışma süresi ve hata raporu."),
        ("İhlal Takibi", "Veri sızıntısı taraması yapar."),
        ("Sistem Yedekleme", "JARVIS ayarlarının yedeğini alır."),
        ("Kilitlenme Protokolü", "Acil durumda sistemi kilitler."),
        ("Koruyucu Kalkan", "Gelişmiş koruma kalkanı."),
        ("Güvenlik Modu", "Kamera, yüz tanıma, uzaktan erişim."),
        ("Siber Göz", "Güvenlik kameralarını izler."),
        ("Hayalet Modu", "Pencereleri hızlıca gizler."),
        ("Gözlemci Modu", "Sistem ve kullanıcı aktivitelerini izler."),
        ("Gölge Kayıt", "Seri ekran görüntüleri alır."),
        ("Ağ Durumu", "İnternet bağlantı hızını kontrol eder."),
        ("Sistem Bakımı", "Geçici dosya temizliği ve disk optimizasyonu."),
        ("Siber Uyku", "Bilgisayarı uyku moduna alır."),
        ("Performans Artırma", "Gereksiz servisleri kapatır."),
        ("TV Hakimiyeti", "Televizyon ve 3. ekran kontrolü."),
        ("Cihaz Tara", "Ağa bağlı cihazları listeler."),
        ("Hırsızlık Modu", "Hırsızlık/tehdit anında alarm ve kilit."),
    ],
    "🎬 Medya & Eğlence": [
        ("Sinema Modu", "Film izlemek için ortam hazırlar."),
        ("Eğlence Modu", "Oyun/film/müzik için eğlence ortamı."),
        ("Medya Kontrol", "Oynat, durdur, sonraki, önceki."),
        ("YouTube Aç", "YouTube'da arama yapar veya video açar."),
        ("Holografik HUD", "Holografik sistem arayüzü."),
        ("Sabah Özeti", "Sabah hava durumu, ajanda, haber."),
        ("Gece Modu", "Ekranı kızar, ses seviyesini kısar."),
        ("Çalışma Alanı", "Çalışma uygulamalarını açar."),
        ("Odak Modu", "Bildirimleri engeller, odak sağlar."),
        ("Oyun Güncelleyici", "Steam/Epic oyunlarını günceller."),
        ("Haber Özeti", "Güncel haber başlıklarını getirir."),
    ],
    "📁 Dosya & Uygulama": [
        ("Uygulama Aç", "Chrome, Spotify, VS Code vb. açar."),
        ("Sistem Durumu", "CPU, RAM, disk, sıcaklık bilgisi."),
        ("Dosya Yöneticisi", "Dosya listeleme, kopyalama, silme."),
        ("Bilgisayar Kontrol", "Klavye/fare makroları."),
        ("Masaüstü Düzenle", "Masaüstü simgelerini düzenler."),
        ("Belge Oku", "PDF, Word, TXT dosyalarını okur."),
        ("Klavye Kontrol", "Tuş gönderme ve metin yazma."),
        ("Bilgisayar Ayarları", "Güç, parlaklık, ses ayarları."),
        ("Ekran İşleme", "Ekran görüntüsü alır, AI analiz eder."),
    ],
    "⏰ Zamanlayıcılar": [
        ("Kapanma Zamanlayıcı", "Bilgisayarı süre sonunda kapatır."),
        ("Hatırlatıcı", "Basit hatırlatıcı kurar."),
        ("Sabah Alarmı", "Sabah alarmı (saatli)."),
        ("Akıllı Hatırlatıcı", "Gelişmiş, tekrarlı hatırlatıcı."),
    ],
    "💬 İletişim & Mesaj": [
        ("Mesaj Gönder", "WhatsApp/Telegram mesajı gönderir."),
        ("Arama Yap", "WhatsApp üzerinden sesli/görüntülü arama."),
        ("Konum Paylaş", "Konum linkini paylaşır."),
        ("Sosyal Hayalet", "Sosyal medya mesaj analizi."),
        ("Çevirmen", "Anlık metin çevirisi."),
        ("Not Al", "Sesli/yazılı not alır ve saklar."),
        ("Görüntü Tarama", "Kameradan görüntü alır, AI analiz eder."),
    ],
    "🌐 Tarayıcı & Web": [
        ("Tarayıcı Kontrol", "Yeni sekme, URL git, arama."),
        ("Otomatik Pilot", "Önceden ayarlanmış sekmeleri açar."),
        ("Web Arama", "Google araması yapıp özetler."),
        ("Uçuş Bulucu", "Google Flights'ta uçak bileti arar."),
        ("Hava Durumu", "Hava durumu bilgisi getirir."),
    ],
    "🧠 Yapay Zeka & Geliştirme": [
        ("Evrim Motoru", "Yeni modüller veya özellikler üretir."),
        ("Geliştirici Ajan", "Proje iskeleti oluşturur, kod yazar."),
        ("Kod Asistanı", "Kod yazarken yardım eder."),
        ("Komut Rehberi", "Bu rehberi açar."),
        ("XP Yönetimi", "Hedeflere göre XP puanı verir."),
        ("Güvenlik & Odak Paketi", "Birden çok modu tek komutla çalıştırır."),
        ("Makro Otomasyon", "Hazır makro otomasyonlarını çalıştırır."),
        ("Makro Ustası", "Özel makro kaydeder ve oynatır."),
    ],
    "☁️ Google Entegrasyonu": [
        ("Google Drive", "Dosya yükleme/listeleme."),
        ("YouTube Yükleme", "YouTube'a video yükleme."),
        ("Google Kişiler", "Kişi listenizi gösterir."),
        ("Gmail Gönder", "Gmail ile e-posta gönderir."),
    ],
    "🔧 Sistem Araçları": [
        ("Kontrol Paneli", "eDEX-UI kontrol panelini açar."),
        ("Hoş Geldin Ekranı", "Açılış hologramını gösterir."),
        ("Sistem Monitörü", "Anlık performans monitörü."),
        ("Komut İstemcisi", "Güvenli terminal komutları çalıştırır."),
    ],
}

class KomutRehberiPenceresi(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚡ J.A.R.V.I.S. Komut Rehberi ⚡")
        self.setMinimumSize(950, 700)
        self.setStyleSheet("background-color: #0a0a1a;")
        self._build_ui()

    def _build_ui(self):
        ana_layout = QVBoxLayout(self)
        ana_layout.setContentsMargins(10, 10, 10, 10)

        başlık = QLabel("🔮  J.A.R.V.I.S.  🔮")
        başlık.setAlignment(Qt.AlignmentFlag.AlignCenter)
        başlık.setStyleSheet("color: #00ffcc; font-size: 22px; font-weight: bold;")
        ana_layout.addWidget(başlık)

        alt_başlık = QLabel("Tüm Yetkileriniz Tek Ekranda | Güncel Modüller | Google Entegrasyonu")
        alt_başlık.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alt_başlık.setStyleSheet("color: #88aaff; font-size: 11px;")
        ana_layout.addWidget(alt_başlık)

        ipucu = QLabel("💡 İpucu: Komutları doğal dil ile söyleyebilirsiniz.\n"
                       "   Örnek: 'Jarvis, sinema modunu aç' veya 'Google Drive'da dosyaları listele'")
        ipucu.setStyleSheet("color: #bbccff; background-color: #1a1a2e; padding: 8px; font-size: 9px;")
        ipucu.setWordWrap(True)
        ana_layout.addWidget(ipucu)

        içerik_layout = QHBoxLayout()

        sol_panel = QWidget()
        sol_panel.setFixedWidth(220)
        sol_panel.setStyleSheet("background-color: #12122a;")
        sol_layout = QVBoxLayout(sol_panel)
        sol_layout.setContentsMargins(5, 5, 5, 5)

        kategori_başlık = QLabel("📂  KATEGORİLER")
        kategori_başlık.setStyleSheet("color: #00ffcc; font-size: 11px; font-weight: bold;")
        sol_layout.addWidget(kategori_başlık)

        self.kategori_butonları = {}
        for kategori_adi, komut_listesi in KOMUTLAR.items():
            btn = QPushButton(kategori_adi)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left; padding: 8px; background-color: #1e1e3a; color: #e0e0ff;
                    border: none; font-size: 10px;
                }
                QPushButton:hover { background-color: #2a2a4a; }
            """)
            btn.clicked.connect(lambda _, k=kategori_adi: self._kategori_göster(k))
            sol_layout.addWidget(btn)
            self.kategori_butonları[kategori_adi] = btn

        sol_layout.addStretch()
        içerik_layout.addWidget(sol_panel)

        self.metin = QTextEdit()
        self.metin.setReadOnly(True)
        self.metin.setStyleSheet("""
            background-color: #0f0f1f; color: #e0e0ff; font-size: 10px;
            border: none; padding: 10px;
        """)
        içerik_layout.addWidget(self.metin)

        ana_layout.addLayout(içerik_layout)

        kapat_btn = QPushButton("✖  KAPAT  ✖")
        kapat_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3333; color: white; font-size: 10px; font-weight: bold;
                padding: 8px 20px; border: none;
            }
            QPushButton:hover { background-color: #ff5555; }
        """)
        kapat_btn.clicked.connect(self.close)
        ana_layout.addWidget(kapat_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        ilk_kategori = list(KOMUTLAR.keys())[0]
        self._kategori_göster(ilk_kategori)

    def _kategori_göster(self, kategori):
        self.metin.clear()
        if kategori not in KOMUTLAR:
            self.metin.setPlainText("❌ Bu kategoride henüz komut yok.")
            return
        for komut, açıklama in KOMUTLAR[kategori]:
            self.metin.append(f"▶ {komut}")
            self.metin.append(f"   ➡️ {açıklama}\n")
        self.metin.moveCursor(self.metin.textCursor().MoveOperation.Start)


# Pencerenin çöp toplayıcı (garbage collector) tarafından silinmemesi için global referans
_rehber_win = None 

def kod_rehberi(parameters=None, player=None, root=None):
    """
    Ana çağırma fonksiyonu. Komut rehberini ana iş parçacığında güvenle açar.
    """
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QMetaObject, Qt

    def arayuzu_ac():
        global _rehber_win
        _rehber_win = KomutRehberiPenceresi()
        _rehber_win.show()

    app = QApplication.instance()
    if app:
        # Arayüz açma işlemini ana thread'e kuyrukluyoruz, bu sayede sistem donmaz.
        QMetaObject.invokeMethod(app, arayuzu_ac, Qt.ConnectionType.QueuedConnection)
    
    return "Detaylı komut rehberi ana ekranda açılıyor efendim."