# Changelog - ATLAS Interface

## [Yeni] ATLAS Interface - ChatGPT-ATLAS Tarzı Arayüz

### 🎉 Yeni Özellikler

#### 1. Modern Split-Screen Interface (`/atlas`)
- **Sol Panel**: Tarayıcı görünümü (Screenshot preview)
- **Sağ Panel**: AI Agent logs ve hedefler
- Tek ekranda her şey, modern dark theme
- Real-time updates (2 saniye polling)

#### 2. Yeni UI Özellikleri
- ✅ Live agent reasoning ve actions
- ✅ Screenshot-based browser preview
- ✅ Status indicators (Running/Completed/Failed)
- ✅ Step-by-step tracking
- ✅ Modern dark theme
- ✅ Responsive design

#### 3. Yeni Dosyalar
```
mini-atlas/
├── app/
│   └── templates.py        # atlas_interface_html() fonksiyonu eklendi
├── ATLAS_INTERFACE.md      # Detaylı ATLAS dokümantasyonu
├── QUICKSTART_ATLAS.md     # Hızlı başlangıç kılavuzu
└── CHANGELOG_ATLAS.md      # Bu dosya
```

#### 4. Yeni Endpoints
```python
@app.get("/atlas")  # ATLAS Interface
```

#### 5. Dashboard Güncellemeleri
- Ana dashboarda ATLAS Interface'e bağlantı eklendi
- "🚀 ATLAS Interface (Yeni!)" butonu

### 📝 Değişiklikler

#### `app/templates.py`
- `atlas_interface_html()` fonksiyonu eklendi (~19KB HTML/CSS/JS)
- Modern split-screen layout
- Real-time polling ile session updates
- Screenshot rendering

#### `app/main.py`
- `GET /atlas` endpoint eklendi
- `atlas_interface_html` import edildi

#### `README.md`
- ATLAS Interface bölümü eklendi
- Web UI Endpoints bölümü güncellendi
- API Reference güncellendi

### 🎨 UI/UX İyileştirmeleri

#### ATLAS Interface Özellikleri:
1. **Top Bar**
   - URL input
   - Start/Stop butonları
   - Dashboard linki

2. **Browser Panel (Sol)**
   - Screenshot preview
   - Current URL display
   - Responsive image rendering

3. **Agent Panel (Sağ)**
   - Goals input (textarea)
   - Status indicator (animated dot)
   - Steps counter
   - Scrollable step list
   - Step details (reasoning, action, result)

4. **Step Cards**
   - Step number ve timestamp
   - Reasoning (italic)
   - Action details (monospace)
   - Success/Error indicators
   - Color-coded results

### 🔧 Teknik Detaylar

#### JavaScript Polling
```javascript
setInterval(loadSessionData, 2000)  // Her 2 saniyede güncelleme
```

#### Screenshot Rendering
```javascript
<img src="data:image/png;base64,${screenshot}" />
```

#### Status States
- `idle` - Başlangıç durumu
- `running` - Agent çalışıyor (yeşil, animasyonlu)
- `completed` - Tamamlandı (mavi)
- `failed` - Başarısız (kırmızı)
- `waiting_human` - CAPTCHA bekliyor (turuncu)

### 📊 Karşılaştırma

| Özellik | Dashboard (/) | ATLAS (/atlas) |
|---------|--------------|----------------|
| Layout | Liste görünümü | Split-screen |
| Browser | Detay sayfasında | Ana ekranda |
| Agent Logs | Detay sayfasında | Yan panelde |
| Tema | Açık | Koyu |
| Real-time | Manuel refresh | Otomatik (2s) |
| Use Case | Multi-session | Single-session focus |

### 🚀 Kullanım

```bash
# 1. Server başlat
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. ATLAS Interface'i aç
http://localhost:8000/atlas

# 3. URL ve goals gir, Start Agent
```

### 📚 Dokümantasyon

- **[ATLAS_INTERFACE.md](ATLAS_INTERFACE.md)** - Detaylı kullanım kılavuzu
- **[QUICKSTART_ATLAS.md](QUICKSTART_ATLAS.md)** - Hızlı başlangıç
- **[README.md](README.md)** - Ana dokümantasyon (güncellendi)

### 🐛 Bilinen Sınırlamalar

1. **Screenshot-based preview**: Gerçek browser iframe değil, screenshot gösterilir
2. **Polling**: WebSocket yerine HTTP polling kullanılıyor
3. **Single session**: Aynı anda tek session odaklı
4. **No video**: Video recording desteği yok (gelecek versiyonda)

### 🔮 Gelecek İyileştirmeler

- [ ] WebSocket ile real-time updates
- [ ] Gerçek browser iframe preview (VNC benzeri)
- [ ] Multi-session support
- [ ] Drag-to-resize panels
- [ ] Video recording ve export
- [ ] Dark/Light theme toggle
- [ ] Keyboard shortcuts
- [ ] Session resume/restore

### ⚠️ Breaking Changes

Yok - Bu tamamen yeni bir endpoint, mevcut API'lere dokunulmadı.

### 🙏 Teşekkürler

ChatGPT-ATLAS'tan ilham alınarak geliştirilmiştir.

---

**Tarih:** November 3, 2025  
**Versiyon:** 0.2.0-atlas  
**Durum:** ✅ Production Ready

