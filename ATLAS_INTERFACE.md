# mini-Atlas - ATLAS Interface

## 🚀 ChatGPT-ATLAS Tarzı Arayüz

mini-Atlas artık ChatGPT-ATLAS gibi modern bir split-screen arayüze sahip!

### Özellikler

#### Split-Screen Layout
- **Sol Panel**: Tarayıcı görünümü (Screenshot'lar real-time gösterilir)
- **Sağ Panel**: AI Agent çalışma logları ve hedefler

#### Real-Time Updates
- Agent adımları anında görüntülenir
- Her 2 saniyede otomatik güncelleme
- Browser screenshot'ları otomatik yüklenir

#### Modern UI/UX
- Karanlık tema
- Smooth animasyonlar
- Responsive tasarım
- Status göstergeleri (Running, Completed, Failed, etc.)

### Kullanım

#### 1. Web Arayüzü ile

```bash
# Sunucuyu başlat
python -m app.main

# Tarayıcıda aç
http://localhost:8000/atlas
```

#### 2. Adımlar

1. URL girin (örn: `https://example.com`)
2. Hedefleri sağ panele yazın (her satıra bir hedef)
3. "Start Agent" butonuna tıklayın
4. Agent çalışmasını izleyin:
   - Sol panelde browser screenshot'ları
   - Sağ panelde agent reasoning ve action'lar

### Ekran Görünümü

```
┌────────────────────────────────────────────────────────────┐
│ 🤖 mini-Atlas    [URL Input]    [Start] [Stop] [Dashboard]│
├─────────────────────────────────────┬──────────────────────┤
│                                     │  AI Agent Goals      │
│                                     │  ┌──────────────────┐│
│         Browser View                │  │ - Navigate to... ││
│                                     │  │ - Fill form      ││
│    [Screenshot görüntülenir]        │  └──────────────────┘│
│                                     ├──────────────────────┤
│                                     │ ● Running  | 5 steps│
│                                     ├──────────────────────┤
│                                     │  Step #5             │
│                                     │  Reasoning: ...      │
│                                     │  Action: CLICK       │
│                                     │  ✓ Success           │
│                                     │                      │
│                                     │  Step #4             │
│                                     │  ...                 │
└─────────────────────────────────────┴──────────────────────┘
```

### Endpoints

#### ATLAS Interface
- **GET `/atlas`** - ATLAS style arayüz
- **GET `/`** - Klasik dashboard (oturum listesi)
- **GET `/session/{id}`** - Detaylı oturum görünümü

#### API Endpoints (Değişmedi)
- **POST `/run`** - Yeni oturum başlat
- **GET `/status/{id}`** - Oturum durumu
- **POST `/stop/{id}`** - Oturumu durdur
- **GET `/api/session/{id}/full`** - Tam oturum verisi (screenshot'lar dahil)

### Yapılandırma

Screenshot'ların otomatik alınması için `configs/config.yaml`:

```yaml
agent:
  screenshot_every_step: true  # ✅ Varsayılan: true
  vision_enabled: true         # Vision modeli için
```

### Özellikler

✅ Real-time browser preview (screenshot bazlı)  
✅ Agent reasoning'i canlı izleme  
✅ Modern karanlık tema  
✅ Otomatik güncelleme (2 saniye)  
✅ Status indicators (Running, Completed, Failed)  
✅ Step-by-step action tracking  
✅ Error handling ve display  
✅ Responsive design  

### Karşılaştırma

#### Eski Arayüz (Dashboard)
- Oturum listesi görünümü
- Detay sayfasına geçiş gerekli
- Statik, manuel yenileme

#### Yeni Arayüz (ATLAS)
- Tek ekranda her şey
- Browser + Agent yan yana
- Real-time updates
- Daha modern ve kullanıcı dostu

### İpuçları

1. **Screenshot Quality**: Config'de viewport boyutunu ayarlayabilirsiniz
2. **Update Speed**: JS'de `refreshInterval` değerini değiştirin (varsayılan: 2000ms)
3. **Panel Boyutu**: CSS'de `.agent-panel` width değerini ayarlayın (varsayılan: 450px)

### Geliştirme Notları

Gelecek iyileştirmeler:
- [ ] WebSocket ile real-time updates (polling yerine)
- [ ] Gerçek browser iframe görünümü (screenshot yerine)
- [ ] Video recording desteği
- [ ] Multi-session support (birden fazla agent aynı anda)
- [ ] Drag-to-resize panels
- [ ] Export session as video/gif

