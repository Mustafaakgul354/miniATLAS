# 🚀 Quick Start - ATLAS Interface

Hızlıca başlamak için bu kılavuzu takip edin.

## 1. Bağımlılıkları Yükleyin

```bash
cd mini-atlas

# Virtual environment oluştur
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# veya Windows: .venv\Scripts\activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# Playwright browser'ı yükle
playwright install chromium
playwright install-deps chromium  # Sistem bağımlılıkları
```

## 2. Environment Ayarları

```bash
# .env dosyası oluştur
cp .env.example .env

# .env dosyasını düzenle ve API key ekle:
# OPENAI_API_KEY=sk-your-key-here
```

Alternatif olarak environment variable olarak export edin:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

## 3. Sunucuyu Başlat

```bash
# Terminal 1: Server başlat
uvicorn app.main:app --host 0.0.0.0 --port 8000

# veya direkt Python ile:
python -m app.main
```

Çıktı:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 4. ATLAS Interface'i Aç

Tarayıcınızda açın:
```
http://localhost:8000/atlas
```

## 5. İlk Agent'ınızı Çalıştırın

### Arayüzde:

1. **URL** girin (örn: `https://example.com`)
2. **Goals** (Hedefler) girin:
   ```
   Navigate to about page
   Find contact information
   ```
3. **Start Agent** butonuna tıklayın
4. Agent'ın çalışmasını izleyin:
   - Sol panelde browser screenshot'ları
   - Sağ panelde agent reasoning ve actions

## Örnek Kullanım Senaryoları

### Senaryo 1: Basit Navigasyon

**URL:** `https://example.com`

**Goals:**
```
Navigate to the about page
Click on contact link
```

### Senaryo 2: Form Doldurma

**URL:** `https://httpbin.org/forms/post`

**Goals:**
```
Fill the customer name field with "Test User"
Fill the telephone field with "+90 555 123 4567"
Submit the form
```

### Senaryo 3: Bilgi Toplama

**URL:** `https://news.ycombinator.com`

**Goals:**
```
Read the top 5 article titles
Navigate to comments of the first article
```

## İpuçları

### 1. Screenshot'ları Etkinleştirin

`configs/config.yaml` dosyasında:
```yaml
agent:
  screenshot_every_step: true  # ✅ Zaten aktif
```

### 2. Debugging İçin Headed Mode

`.env` dosyasında:
```bash
BROWSER=headed  # Browser'ı göster
```

### 3. Adım Sayısını Artırın

Daha karmaşık görevler için:
```yaml
agent:
  max_steps: 50  # Varsayılan: 30
```

### 4. Timeout Ayarları

Yavaş sitelerde:
```bash
AGENT_STEP_TIMEOUT=60  # Her adım için 60 saniye
AGENT_TOTAL_TIMEOUT=600  # Toplam 10 dakika
```

## Sorun Giderme

### Playwright Kurulum Hatası

```bash
# Tam kurulum (bağımlılıklarla)
playwright install --with-deps chromium
```

### Port Zaten Kullanımda

```bash
# Farklı port kullan
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### LLM API Hatası

```bash
# API key'i kontrol et
echo $OPENAI_API_KEY

# Log level'ı artır
export LOG_LEVEL=DEBUG
```

### Screenshot Görünmüyor

Config kontrol et:
```yaml
agent:
  screenshot_every_step: true  # true olmalı
```

## Daha Fazla Bilgi

- **Full Documentation**: [README.md](README.md)
- **ATLAS Interface Details**: [ATLAS_INTERFACE.md](ATLAS_INTERFACE.md)
- **API Reference**: [README.md#api-reference](README.md#api-reference)
- **CLI Usage**: [README.md#cli-usage](README.md#cli-usage)

## Demo Video (Yakında)

Yakında ATLAS Interface kullanım videosu eklenecek.

## Yardıma mı İhtiyacınız Var?

- GitHub Issues: Report bugs or request features
- Discord: Join our community (coming soon)
- Email: support@mini-atlas.com (if available)

---

**Kolay gelsin! mini-Atlas ile keyifli browser automation deneyimler dileriz! 🤖✨**

