# mini-Atlas Kullanım Kılavuzu

## DigitalOcean Droplet'e Kurulum

mini-Atlas'ı DigitalOcean droplet'inize tek komutla kurabilirsiniz:

```bash
curl -fsSL https://raw.githubusercontent.com/Mustafaakgul354/miniATLAS/main/deploy_droplet.sh | sudo bash
```

Detaylı kurulum talimatları için [DROPLET_KURULUM.md](DROPLET_KURULUM.md) dosyasına bakın.

---

## Görsel Arayüz ve Çıktılar

mini-Atlas artık modern bir web arayüzü ile birlikte geliyor! Tüm oturumları ve çıktıları görsel olarak takip edebilirsiniz.

## Nasıl Kullanılır?

### 1. Sunucuyu Başlatın

```bash
cd mini-atlas
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Web Arayüzünü Açın

Tarayıcınızda şu adrese gidin:
```
http://localhost:8000
```

### 3. Yeni Oturum Başlatın

Ana sayfada (Dashboard) şunları yapabilirsiniz:

- **URL Girin**: Agent'in başlayacağı web sitesi adresi
- **Hedefler Girin**: Her satıra bir hedef yazın (örnek: "Login ol", "Dashboard'a git")
- **Maksimum Adım**: Kaç adım sonra dursun (opsiyonel)
- **Oturum Başlat** butonuna tıklayın

### 4. Oturumları İzleyin

Ana sayfada tüm oturumlarınızı görebilirsiniz:

- **Çalışıyor**: Yeşil badge - Agent aktif
- **Tamamlandı**: Yeşil badge - Başarıyla tamamlandı
- **Başarısız**: Kırmızı badge - Hata oluştu
- **İnsan Bekliyor**: Turuncu badge - CAPTCHA çözülmesi gerekiyor

Bir oturuma tıklayarak detay sayfasına gidebilirsiniz.

### 5. Oturum Detaylarını Görüntüleyin

Detay sayfasında şunları görebilirsiniz:

#### Durum Paneli
- Mevcut durum (çalışıyor/tamamlandı vb.)
- Toplam adım sayısı
- Mevcut URL
- Hedefler listesi

#### Adım Geçmişi
Her adım için:

- **Adım Numarası**: Kaçıncı adım olduğu
- **Zaman Damgası**: Ne zaman çalıştığı
- **URL ve Başlık**: Hangi sayfada olduğu
- **Element Sayısı**: Sayfada kaç tıklanabilir öğe var
- **Mantık (Reasoning)**: Agent'in neden bu adımı attığı
- **İşlem (Action)**: Hangi işlemi yaptığı (click, fill, vb.)
- **Sonuç**: İşlem başarılı mı başarısız mı
- **Screenshot**: O adımda çekilmiş ekran görüntüsü (tıklayarak büyütebilirsiniz)
- **Süre**: İşlemin ne kadar sürdüğü

### 6. CAPTCHA Yönetimi

Eğer bir CAPTCHA tespit edilirse:

1. Oturum durumu "İnsan Bekliyor" olarak değişir
2. Turuncu bir uyarı kutusu görünür
3. Tarayıcıda CAPTCHA'yı manuel olarak çözün
4. "Devam Et" butonuna tıklayın
5. Agent kaldığı yerden devam eder

### 7. Gerçek Zamanlı Güncellemeler

Aktif oturumlar için:
- Durum panosu otomatik olarak güncellenir (2 saniyede bir)
- Yeni adımlar otomatik olarak görünür
- Screenshot'lar gerçek zamanlı olarak eklenir

## API Kullanımı

Web arayüzü yerine API'yi doğrudan da kullanabilirsiniz:

### Yeni Oturum Başlat
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "goals": ["Login ol", "Dashboard aç"],
    "max_steps": 20
  }'
```

### Oturum Durumunu Kontrol Et
```bash
curl http://localhost:8000/status/{session_id}
```

### Tam Oturum Verilerini Al (Adımlar dahil)
```bash
curl http://localhost:8000/api/session/{session_id}/full
```

## Çıktı Türleri

### 1. Ekran Görüntüleri (Screenshots)
- Her adımda çekilen sayfa görüntüleri
- Base64 formatında saklanır
- Web arayüzünde otomatik gösterilir
- Tıklayarak büyütebilirsiniz

### 2. Adım Logları
- Her adımın detaylı bilgileri
- JSON formatında API'den alınabilir
- Web arayüzünde görsel olarak gösterilir

### 3. Ağ İzleme (Network Events)
- Backend API çağrıları
- Form gönderimleri
- Sayfa yüklemeleri
- Durum kodu ve yanıt süreleri

### 4. Hata Mesajları
- Selector bulunamadı hataları
- Zaman aşımı hataları
- CAPTCHA gereksinimleri
- Güvenlik politikası ihlalleri

## İpuçları

1. **Screenshot'ları Büyütmek**: Detay sayfasında screenshot'a tıklayın
2. **Otomatik Yenileme**: Aktif oturumlar otomatik güncellenir, sayfayı yenilemenize gerek yok
3. **Hızlı Navigasyon**: Ana sayfada oturum kartlarına tıklayarak hızlıca detaya geçebilirsiniz
4. **CAPTCHA Çözümü**: Headed mode kullanırsanız CAPTCHA'yı görebilirsiniz (`.env` dosyasında `BROWSER=headed`)

## Sorun Giderme

**Arayüz yüklenmiyor?**
- Sunucunun çalıştığından emin olun (`uvicorn app.main:app`)
- `http://localhost:8000` adresini kontrol edin

**Screenshot görünmüyor?**
- `configs/config.yaml` dosyasında `screenshot_every_step: true` olmalı
- Agent'ın çalıştığı adımları bekleyin

**Oturumlar güncellenmiyor?**
- Sayfayı yenileyin (F5)
- Tarayıcı konsolunu kontrol edin (F12)

**CAPTCHA çözüldü ama devam etmiyor?**
- "Devam Et" butonuna tıklayın
- Oturum durumunu kontrol edin (`/status/{session_id}`)

