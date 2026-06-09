# J.A.R.V.I.S. 2.0 Bulut Sunucu (Cloud VPS) Dağıtım Kılavuzu ☁️

Bu kılavuz, J.A.R.V.I.S. 2.0 (Mark XXXIX-OR) web ve API katmanını bilgisayarınızdan tamamen bağımsız, 7/24 açık kalacak şekilde bulut sunucularına (Render.com veya PythonAnywhere) nasıl kuracağınızı adım adım açıklamaktadır.

---

## 💾 1. Veri Kalıcılığı Mimarisi (Persistent Storage)

Bulut sunucularında (özellikle Render'da) kodunuzu her güncellediğinizde veya sunucu yeniden başladığında dosya sistemi sıfırlanır (ephemeral storage). SQLite veritabanı (`.db`) ve hafıza dosyalarının (`.json`) silinmemesi için **Kalıcı Disk (Persistent Volume)** kullanılması gerekir.

Projemizde bunu otomatikleştirmek için `JARVIS_PERSISTENT_DIR` ortam değişkeni eklenmiştir:
* **Ortam Değişkeni Tanımlıysa:** Tüm SQLite veritabanları, kullanıcı profilleri, NetworkX bilişsel grafikleri ve hafıza dosyaları bu dizinde kalıcı olarak saklanır.
* **Ortam Değişkeni Yoksa (Yerel Çalışma):** Dosyalar eskisi gibi proje klasörünün içindeki `memory/` klasörüne yazılır. Yerel Windows çalışmanız hiçbir şekilde etkilenmez.

---

## 🚀 SEÇENEK A: Render.com ile Dağıtım (Profesyonel & Tek Tıkla)

Render, GitHub deposu üzerinden otomatik olarak deploy yapabilen modern bir bulut platformudur.

### 📌 Adım 1: Projenizi GitHub'a Yükleyin
1. GitHub üzerinde yeni bir **Private (Gizli)** depo (repository) oluşturun.
2. J.A.R.V.I.S. projenizi bu depoya push edin.
   > [!WARNING]
   > `.env` veya API anahtarlarınızı içeren dosyaları kesinlikle GitHub'a yüklemeyin. Projede zaten `.gitignore` dosyası bunları hariç tutmaktadır.

### 📌 Adım 2: Render.com Blueprint Kullanarak Yayınlama
Proje kök dizininde bulunan [render.yaml](file:///c:/Users/Izoly/Downloads/Mark-XXXIX-OR-main/baki%20jarvis%202.0/render.yaml) dosyası sayesinde tek tıkla kurulum yapabilirsiniz:
1. Render.com hesabınıza giriş yapın.
2. Sol menüden **Blueprints** bölümüne gidin.
3. **New Blueprint Instance** butonuna tıklayın.
4. GitHub deponuzu bağlayın.
5. Render, `render.yaml` dosyasını otomatik okuyarak disk ve servis yapılandırmasını getirecektir.

### 📌 Adım 3: Çevre Değişkenlerini (Environment Variables) Tanımlayın
Render servisinizi oluştururken veya oluşturduktan sonra **Environment** sekmesinden aşağıdaki değişkenleri tanımlayın:
* `GEMINI_API_KEY`: Gemini API Anahtarınız.
* `GROQ_API_KEY`: Groq API Anahtarınız.
* `OPENROUTER_API_KEY` (Opsiyonel): OpenRouter anahtarınız.
* `JARVIS_PERSISTENT_DIR`: `/opt/render/project/src/memory_persistent` (Blueprint tarafından otomatik tanımlanır).

> [!IMPORTANT]
> **Render Kalıcı Disk Ücret Uyarısı:**
> Render üzerinde veri kalıcılığını sağlamak için `disk` (Persistent Disk) kullanımı gereklidir. Render free katmanında kalıcı disk desteği vermediği için disk eklemek servisin aylık ücretli (Starter - $7/ay + Disk $1/ay) katmana geçmesini gerektirir. Eğer tamamen ücretsiz bir çözüm arıyorsanız **Seçenek B (PythonAnywhere)** adımını uygulayın.

---

## 🐍 SEÇENEK B: PythonAnywhere ile Dağıtım (Tamamen Ücretsiz)

PythonAnywhere, Python web uygulamalarını (FastAPI/Flask/Django) ücretsiz katmanda barındırmanıza izin veren ve dosyalarınızı kalıcı olarak saklayan harika bir alternatiftir.

### 📌 Adım 1: Ücretsiz Hesap Açın
1. [PythonAnywhere.com](https://www.pythonanywhere.com/) adresine gidin ve **Beginner (Ücretsiz)** hesap açın.

### 📌 Adım 2: Dosyaları Yükleyin
Dosyaları tarayıcıdan tek tek yüklemek yerine terminal üzerinden GitHub ile çekmek en hızlı yöntemdir:
1. PythonAnywhere kontrol panelinden **Consoles** sekmesine gelin ve bir **Bash** konsolu açın.
2. Projenizi GitHub'dan klonlayın:
   ```bash
   git clone https://github.com/kullanici_adiniz/depo_adi.git jarvis
   ```
3. Proje klasörüne girin:
   ```bash
   cd jarvis
   ```

### 📌 Adım 3: Sanal Ortam (Virtualenv) Kurun
Konsolda şu komutları çalıştırarak bağımlılıkları yükleyin:
```bash
mkvirtualenv --python=/usr/bin/python3.10 jarvis-env
pip install -r requirements.txt
```
*Sanal ortamınız `/home/kullanici_adiniz/.virtualenvs/jarvis-env` dizinine kurulacaktır.*

### 📌 Adım 4: Kalıcı Klasörü Oluşturun
Bellek dosyalarının saklanacağı kalıcı klasörü oluşturun:
```bash
mkdir -p /home/kullanici_adiniz/jarvis_memory
```

### 📌 Adım 5: Web Uygulamasını Yapılandırın
1. PythonAnywhere panelinden **Web** sekmesine gidin.
2. **Add a new web app** butonuna tıklayın.
3. Kurulum sihirbazında sırasıyla:
   * Domain adresinizi seçin (ücretsiz hesapta `kullanici_adiniz.pythonanywhere.com` şeklindedir).
   * Web framework olarak **Manual Configuration** (Manuel Yapılandırma) seçin.
   * Python sürümü olarak **Python 3.10** seçin.
4. Kurulum bittikten sonra Web ayarları sayfasında:
   * **Code** bölümündeki **Source code** alanını projenin kök dizini yapın: `/home/kullanici_adiniz/jarvis`
   * **Working directory** alanını da `/home/kullanici_adiniz/jarvis` yapın.
   * **Virtualenv** bölümündeki yolu sanal ortam dizininiz yapın: `/home/kullanici_adiniz/.virtualenvs/jarvis-env`

### 📌 Adım 6: WSGI Ayarlarını Düzenleyin
PythonAnywhere FastAPI'yi çalıştırmak için WSGI arayüzünü kullanır. **Web** sekmesindeki **WSGI configuration file** linkine tıklayın ve içindekileri tamamen silip şunları yazın:

```python
import os
import sys

# Proje yollarını ekle
path = '/home/kullanici_adiniz/jarvis'
if path not in sys.path:
    sys.path.insert(0, path)

# Çevre Değişkenlerini Tanımla (API Anahtarları ve Kalıcı Klasör)
os.environ['JARVIS_PERSISTENT_DIR'] = '/home/kullanici_adiniz/jarvis_memory'
os.environ['GEMINI_API_KEY'] = 'YOUR_GEMINI_API_KEY'
os.environ['GROQ_API_KEY'] = 'YOUR_GROQ_API_KEY'
# Varsa diğer API anahtarlarınızı da buraya ekleyebilirsiniz:
# os.environ['OPENROUTER_API_KEY'] = '...'

# ASGI -> WSGI Dönüşümü için FastAPI uygulamasını yükle
from asgiref.wsgi import ASGIWrapper
from web.server import app

application = ASGIWrapper(app)
```
*(Gerekli düzenlemeleri yaptıktan sonra sağ üstteki **Save** butonuna tıklayın).*

### 📌 Adım 7: Uygulamayı Yeniden Başlatın
1. Tekrar **Web** sekmesine dönün.
2. Sayfanın üstündeki yeşil **Reload (Yeniden Yükle)** butonuna tıklayın.
3. Artık siteniz `http://kullanici_adiniz.pythonanywhere.com/` adresinde 7/24 aktif!

---

## 🛠️ Yönetici (Admin) Girişi ve Güvenlik

Bulutta çalışan J.A.R.V.I.S. 2.0 sitenizin admin paneline erişmek için:
1. Sitenizin sonuna `/admin` ekleyin (örn: `https://baki.render.com/admin` veya `http://baki.pythonanywhere.com/admin`).
2. İlk kurulumda varsayılan bilgiler:
   * **Kullanıcı Adı:** `baki`
   * **Şifre:** `3131626242`
3. Güvenliğiniz için sisteme giriş yaptıktan sonra **Hesaplar (Accounts)** sekmesinden şifrenizi hemen güncelleyin veya yeni admin hesapları tanımlayın.
