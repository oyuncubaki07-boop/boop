# actions/kod_rehberi.py
# J.A.R.V.I.S. Komut Rehberi - Güncel ve Kapsamlı (Google Entegrasyonlu)

import tkinter as tk
from tkinter import ttk, scrolledtext

def kod_rehberi(parameters=None, player=None, root=None):
    """
    Kullanıcıya tüm komutları kategorilere ayrılmış, şık bir pencerede gösterir.
    Teknik dosya isimleri yerine kullanıcı dostu Türkçe başlıklar kullanır.
    """
    # Ana pencere
    win = tk.Toplevel(root) if root else tk.Tk()
    win.title("⚡ J.A.R.V.I.S. Komut Rehberi ⚡")
    win.geometry("950x720")
    win.configure(bg="#0a0a1a")
    win.attributes('-alpha', 0.98)

    # Başlık
    title_label = tk.Label(win, text="🔮  J.A.R.V.I.S.  🔮", font=("Orbitron", 22, "bold"),
                           fg="#00ffcc", bg="#0a0a1a")
    title_label.pack(pady=10)

    subtitle = tk.Label(win, text="Tüm Yetkileriniz Tek Ekranda | Güncel Modüller | Google Entegrasyonu", 
                        font=("Segoe UI", 11), fg="#88aaff", bg="#0a0a1a")
    subtitle.pack()

    # Bilgi notu
    note_frame = tk.Frame(win, bg="#1a1a2e", relief=tk.FLAT, bd=0)
    note_frame.pack(fill=tk.X, padx=20, pady=10)
    note = tk.Label(note_frame, text="💡 İpucu: Aşağıdaki komutları doğal dil ile JARVIS'e söyleyebilirsiniz.\n"
                                     "   Örnek: 'Jarvis, sinema modunu aç' veya 'Google Drive'da dosyaları listele'",
                   font=("Segoe UI", 9), fg="#bbccff", bg="#1a1a2e", wraplength=860, justify=tk.LEFT)
    note.pack(pady=8, padx=10)

    # Ana çerçeve (kategoriler sol, listeler sağ)
    main_frame = tk.Frame(win, bg="#0a0a1a")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

    # Sol kategori çerçevesi (kaydırılabilir)
    kategori_canvas = tk.Canvas(main_frame, bg="#12122a", highlightthickness=0, width=240)
    kategori_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=kategori_canvas.yview)
    kategori_scrollable_frame = tk.Frame(kategori_canvas, bg="#12122a")

    kategori_scrollable_frame.bind(
        "<Configure>",
        lambda e: kategori_canvas.configure(scrollregion=kategori_canvas.bbox("all"))
    )
    kategori_canvas.create_window((0, 0), window=kategori_scrollable_frame, anchor="nw", width=230)
    kategori_canvas.configure(yscrollcommand=kategori_scrollbar.set)

    kategori_canvas.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
    kategori_scrollbar.pack(side=tk.LEFT, fill=tk.Y)

    # Kategori başlığı
    tk.Label(kategori_scrollable_frame, text="📂  KATEGORİLER", font=("Orbitron", 11, "bold"),
             fg="#00ffcc", bg="#12122a").pack(pady=10, padx=10, anchor="w")

    # Kategoriler (ana başlık, teknik anahtar)
    kategoriler = [
        ("🛡️ Sistem & Güvenlik", "security"),
        ("🎬 Medya & Eğlence", "media"),
        ("📁 Dosya & Uygulama", "files"),
        ("⏰ Zamanlayıcılar", "timers"),
        ("💬 İletişim & Mesaj", "comm"),
        ("🌐 Tarayıcı & Web", "web"),
        ("🧠 Gelişmiş Yapay Zeka", "ai"),
        ("📸 Instagram", "instagram"),
        ("🔧 Sistem Araçları", "system_tools"),
        ("☁️ Google Entegrasyonu", "google"),
        ("🔐 Alfred Kamera", "alfred"),
        ("🛠️ Diğer Araçlar", "other"),
    ]

    def on_enter(e, btn, original_bg):
        btn.config(bg="#2a2a4a")
    def on_leave(e, btn, original_bg):
        btn.config(bg=original_bg)

    for text, key in kategoriler:
        btn = tk.Button(kategori_scrollable_frame, text=text, font=("Segoe UI", 10),
                        bg="#1e1e3a", fg="#e0e0ff", anchor="w", padx=10, pady=5,
                        relief=tk.FLAT, bd=0, cursor="hand2",
                        command=lambda k=key: show_category(k))
        btn.pack(fill=tk.X, pady=3, padx=10)
        btn.bind("<Enter>", lambda e, b=btn, bg="#1e1e3a": on_enter(e, b, bg))
        btn.bind("<Leave>", lambda e, b=btn, bg="#1e1e3a": on_leave(e, b, bg))

    # Sağ komut listesi
    komut_frame = tk.Frame(main_frame, bg="#12122a", relief=tk.FLAT, bd=2)
    komut_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    tk.Label(komut_frame, text="🔍  KOMUTLAR VE AÇIKLAMALARI", font=("Orbitron", 10, "bold"),
             fg="#00ffcc", bg="#12122a").pack(pady=5)

    komut_text = scrolledtext.ScrolledText(komut_frame, wrap=tk.WORD, font=("Consolas", 10),
                                           bg="#0f0f1f", fg="#e0e0ff", insertbackground="white",
                                           relief=tk.FLAT, borderwidth=0, padx=10, pady=10)
    komut_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Renk etiketleri
    komut_text.tag_config("cmd", foreground="#00ffcc", font=("Segoe UI", 11, "bold"))
    komut_text.tag_config("desc", foreground="#bbbbee", font=("Segoe UI", 10))

    # ----- TÜM KOMUTLAR (GÜNCEL VE KAPSAMLI) -----
    komutlar = {
        "security": [
            ("Biyometrik Kalkan", "➡️ Ne işe yarar: Parmak izi veya yüz tanıma ile güvenlik kalkanını aktif eder."),
            ("Kara Kutu", "➡️ Ne işe yarar: Sistem tanılama, çalışma süresi ve hata kayıtlarını gösterir."),
            ("İhlal Takibi", "➡️ Ne işe yarar: Veri sızıntısı olup olmadığını tarar ve raporlar."),
            ("Sistem Yedekleme", "➡️ Ne işe yarar: Tüm JARVIS yapılandırmalarının yedeğini alır."),
            ("Kilitlenme Protokolü", "➡️ Ne işe yarar: Acil durumda sistemi kilitler, ekranı karartır."),
            ("Koruyucu Kalkan", "➡️ Ne işe yarar: Gelişmiş koruma kalkanını devreye sokar."),
            ("Güvenlik Modu", "➡️ Ne işe yarar: Kamera, yüz tanıma ve uzaktan erişim ile tam güvenlik."),
            ("Siber Göz", "➡️ Ne işe yarar: Siber Göz servisini başlatır, güvenlik kameralarını izler."),
            ("Hayalet Modu", "➡️ Ne işe yarar: Hızlı gizlilik modu; tüm pencereleri gizler."),
            ("Gözlemci Modu", "➡️ Ne işe yarar: Arka planda kullanıcı aktivitelerini gözlemler."),
            ("Gölge Kayıt", "➡️ Ne işe yarar: Seri ekran görüntüleri alır, gizli delil toplar."),
            ("Ağ Durumu", "➡️ Ne işe yarar: İnternet bağlantı hızını ve durumunu kontrol eder."),
            ("Sistem Bakımı", "➡️ Ne işe yarar: Geçici dosyaları temizler, disk optimizasyonu yapar."),
            ("Siber Uyku", "➡️ Ne işe yarar: Bilgisayarı uyku moduna alır."),
            ("Performans Artırma", "➡️ Ne işe yarar: Gereksiz servisleri kapatarak performansı artırır."),
            ("TV Hakimiyeti", "➡️ Ne işe yarar: Televizyon ve 3. ekran kontrolünü ele geçirir."),
            ("Cihaz Tara", "➡️ Ne işe yarar: Ağa bağlı cihazları tarar."),
        ],
        "media": [
            ("Sinema Modu", "➡️ Ne işe yarar: Sinema modunu açar; ışıkları kıstır, ses sistemini ayarlar."),
            ("Eğlence Modu", "➡️ Ne işe yarar: Oyun, film ve müzik için ortamı hazırlar."),
            ("Medya Kontrol", "➡️ Ne işe yarar: Müzik/video oynatma kontrolleri (oynat/durdur/ileri/geri)."),
            ("YouTube Aç", "➡️ Ne işe yarar: YouTube'da arama yapıp videoyu açar."),
            ("Holografik HUD", "➡️ Ne işe yarar: 3D holografik kullanıcı arayüzünü gösterir."),
            ("Sabah Özeti", "➡️ Ne işe yarar: Sabah hava durumu, ajanda, haber özeti sunar."),
            ("Gece Modu", "➡️ Ne işe yarar: Ekranı kızar, ses seviyesini kısar, gece moduna geçer."),
            ("Çalışma Alanı", "➡️ Ne işe yarar: Çalışma ortamını hazırlar; gerekli uygulamaları açar."),
            ("Odak Modu", "➡️ Ne işe yarar: Dikkat dağıtıcı bildirimleri engeller."),
            ("Oyun Güncelleyici", "➡️ Ne işe yarar: Oyunları günceller (Steam, Epic Games)."),
            ("Haber Özeti", "➡️ Ne işe yarar: Kısa haber özeti oluşturur ve okur."),
        ],
        "files": [
            ("Uygulama Aç", "➡️ Ne işe yarar: İstediğiniz uygulamayı açar (Chrome, Spotify, VS Code)."),
            ("Sistem Durumu", "➡️ Ne işe yarar: CPU, RAM, disk kullanımı ve sıcaklık bilgisi verir."),
            ("Dosya Yöneticisi", "➡️ Ne işe yarar: Dosya listeleme, kopyalama, silme işlemleri yapar."),
            ("Bilgisayar Kontrol", "➡️ Ne işe yarar: Klavye ve fare makrolarını çalıştırır."),
            ("Masaüstü Düzenle", "➡️ Ne işe yarar: Masaüstü düzenini ayarlar, simgeleri sıralar."),
            ("Belge Oku", "➡️ Ne işe yarar: PDF, Word, TXT dosyalarını okur ve içeriğini seslendirir."),
            ("Klavye Kontrol", "➡️ Ne işe yarar: Tuş basımı veya metin yazma işlemleri yapar."),
            ("Bilgisayar Ayarları", "➡️ Ne işe yarar: Güç planı, ekran parlaklığı, ses ayarlarını değiştirir."),
            ("Ekran İşleme", "➡️ Ne işe yarar: Ekran görüntüsü alır, AI ile analiz eder."),
        ],
        "timers": [
            ("Kapanma Zamanlayıcı", "➡️ Ne işe yarar: Bilgisayarı belirtilen süre sonra kapatır."),
            ("Hatırlatıcı", "➡️ Ne işe yarar: Basit hatırlatıcı kurar."),
            ("Sabah Alarmı", "➡️ Ne işe yarar: Sabah alarmı kurar (saat belirterek)."),
            ("Akıllı Hatırlatıcı", "➡️ Ne işe yarar: Gelişmiş hatırlatıcı (tekrarlı, tarih saat)."),
        ],
        "comm": [
            ("Mesaj Gönder", "➡️ Ne işe yarar: WhatsApp/Telegram üzerinden mesaj gönderir."),
            ("Alternatif Mesaj", "➡️ Ne işe yarar: Alternatif mesaj gönderme modülü."),
            ("Konum Paylaş", "➡️ Ne işe yarar: Şu anki konumunuzu WhatsApp'tan paylaşır."),
            ("Sosyal Hayalet", "➡️ Ne işe yarar: Sosyal medya mesajlarını analiz eder, spam engeller."),
            ("Akıllı Çevirmen", "➡️ Ne işe yarar: Anlık çeviri yapar (metin veya sesli)."),
            ("Not Al", "➡️ Ne işe yarar: Sesli veya yazılı not alır, notları saklar."),
            ("Görüntü Tarama", "➡️ Ne işe yarar: Kameradan görüntü alır, yapay zeka ile analiz eder."),
            ("Hata Bildir", "➡️ Ne işe yarar: Hata raporu oluşturur ve gösterir."),
        ],
        "web": [
            ("Tarayıcı Kontrol", "➡️ Ne işe yarar: Tarayıcıda yeni sekme açar, URL gider, arama yapar."),
            ("Otomatik Pilot", "➡️ Ne işe yarar: Önceden ayarlanmış çalışma sekmelerini açar."),
            ("Web Arama", "➡️ Ne işe yarar: Google'da arama yapar, özetini getirir."),
            ("Uçuş Bulucu", "➡️ Ne işe yarar: Uçak bileti fiyatlarını Google Flights'ta aratır."),
            ("Hava Durumu", "➡️ Ne işe yarar: Hava durumu bilgisini getirir (şehir belirtilebilir)."),
        ],
        "ai": [
            ("Dış AI'ya Danış", "➡️ Ne işe yarar: ChatGPT/Claude gibi dış yapay zekalara soru sorar."),
            ("Kendini Onar", "➡️ Ne işe yarar: Hata oluştuğunda kodu analiz edip düzeltmeye çalışır."),
            ("Evrim Motoru", "➡️ Ne işe yarar: Yeni modüller veya özellikler üretir."),
            ("Geliştirici Ajan", "➡️ Ne işe yarar: Proje iskeleti oluşturur, kod yazar."),
            ("Kod Asistanı", "➡️ Ne işe yarar: Kod yazarken yardım eder, snippet önerir."),
            ("Komut Rehberi", "➡️ Ne işe yarar: Bu komut rehberini açar."),
            ("XP Yönetimi", "➡️ Ne işe yarar: Kullanıcının hedeflerine göre XP puanı verir."),
            ("Güvenlik ve Odak Paketi", "➡️ Ne işe yarar: Birden çok güvenlik ve odak modunu tek komutla çalıştırır."),
            ("Makro Otomasyon", "➡️ Ne işe yarar: Hazır makro otomasyonlarını çalıştırır."),
            ("Makro Ustası", "➡️ Ne işe yarar: Özel makro kaydeder ve oynatır."),
        ],
        "instagram": [
            ("Instagram Otomatik Yanıt", "➡️ Ne işe yarar: Instagram DM'lerine otomatik yanıt gönderir."),
        ],
        "system_tools": [
            ("Kontrol Paneli", "➡️ Ne işe yarar: JARVIS kontrol panelini açar (eDEX-UI)."),
            ("Hoş Geldin Ekranı", "➡️ Ne işe yarar: Hoş geldin hologramını gösterir."),
            ("Sistem Monitörü", "➡️ Ne işe yarar: Anlık sistem performansını gösterir."),
            ("Komut İstemcisi", "➡️ Ne işe yarar: Güvenli terminal komutları çalıştırır."),
        ],
        "google": [
            ("Google Drive", "➡️ Ne işe yarar: Drive'a dosya yükler, dosyaları listeler."),
            ("YouTube Yükleme", "➡️ Ne işe yarar: YouTube'a video yükler (gizli olarak)."),
            ("Google Kişiler", "➡️ Ne işe yarar: Google Kişiler listenizi gösterir."),
            ("Gmail Gönder", "➡️ Ne işe yarar: Gmail üzerinden e-posta gönderir."),
        ],
        "alfred": [
            ("Alfred Kamera", "➡️ Ne işe yarar: Alfred Home Security kamerasını tarayıcıda açar."),
        ],
        "other": [
            ("eDEX-UI Paneli", "➡️ Ne işe yarar: JARVIS kontrol panelini ASUS monitöründe açar."),
            ("Ekran İşleme (Gelişmiş)", "➡️ Ne işe yarar: Ekran görüntüsü alır, metin çıkarır (OCR)."),
            ("Akıllı Notlar", "➡️ Ne işe yarar: Not alır, listeler, okur, siler."),
            ("Raporlama", "➡️ Ne işe yarar: Görsel sistem uyarılarını gösterir."),
        ]
    }

    def show_category(cat):
        komut_text.delete(1.0, tk.END)
        if cat not in komutlar:
            komut_text.insert(tk.END, "❌ Bu kategoride henüz komut yok.\n", "desc")
            return
        for cmd, desc in komutlar[cat]:
            komut_text.insert(tk.END, f"▶ {cmd}\n", "cmd")
            komut_text.insert(tk.END, f"   {desc}\n\n", "desc")
        komut_text.see(1.0)

    # Varsayılan kategoriyi göster
    if kategoriler:
        show_category(kategoriler[0][1])

    # Alt bilgi ve kapatma butonu
    bottom_frame = tk.Frame(win, bg="#0a0a1a", height=50)
    bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
    bottom_frame.pack_propagate(False)

    close_btn = tk.Button(bottom_frame, text="✖  KAPAT  ✖", command=win.destroy,
                          bg="#ff3333", fg="white", font=("Orbitron", 10, "bold"),
                          padx=20, pady=5, relief=tk.FLAT, cursor="hand2")
    close_btn.pack()

    def on_close_enter(e):
        close_btn.config(bg="#ff5555")
    def on_close_leave(e):
        close_btn.config(bg="#ff3333")
    close_btn.bind("<Enter>", on_close_enter)
    close_btn.bind("<Leave>", on_close_leave)

    # Pencereyi ortala
    win.update_idletasks()
    x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
    y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
    win.geometry(f"+{x}+{y}")

    if root is None:
        win.mainloop()