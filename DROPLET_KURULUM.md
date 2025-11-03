# DigitalOcean Droplet Kurulum Rehberi

Bu rehber, mini-Atlas'ı DigitalOcean Droplet üzerinde nasıl kuracağınızı açıklamaktadır.

## Gereksinimler

- Bir DigitalOcean hesabı
- En az 2GB RAM'e sahip droplet (üretim için 4GB önerilir)
- Ubuntu 22.04 LTS veya daha yeni
- Droplet'inize SSH erişimi
- (İsteğe bağlı) Droplet IP'nize yönlendirilmiş bir domain

## Hızlı Kurulum

### 1. Droplet'inize Bağlanın

```bash
ssh root@DROPLET_IP_ADRESINIZ
```

### 2. Kurulum Scriptini İndirin ve Çalıştırın

```bash
curl -fsSL https://raw.githubusercontent.com/Mustafaakgul354/miniATLAS/main/deploy_droplet.sh -o deploy_droplet.sh
chmod +x deploy_droplet.sh
./deploy_droplet.sh
```

Script şunları yapacaktır:
- Sistem paketlerini güncelleyecek
- Docker, Docker Compose, Nginx ve diğer bağımlılıkları kuracak
- mini-Atlas deposunu `/opt/mini-atlas` dizinine klonlayacak
- Nginx'i reverse proxy olarak yapılandıracak
- Systemd servisi oluşturacak (Docker dışı kurulumlar için)

### 3. Ortam Değişkenlerini Yapılandırın

`.env` dosyasını düzenleyin:

```bash
cd /opt/mini-atlas
nano .env
```

**Zorunlu ayarlar:**
- `OPENAI_API_KEY` - OpenAI API anahtarınız (OpenAI kullanıyorsanız)
- `LLM_PROVIDER` - `openai`, `ollama` veya `vllm` olarak ayarlayın

**İsteğe bağlı ayarlar:**
- `BROWSER` - `headless` olarak ayarlayın (droplet için önerilir)
- `AGENT_MAX_STEPS` - Oturum başına maksimum adım sayısı
- `TIMEZONE` - Saat diliminiz (varsayılan: `Europe/Istanbul`)

### 4. Uygulamayı Başlatın

#### Seçenek A: Docker ile Kurulum (Önerilen)

```bash
cd /opt/mini-atlas
docker-compose -f docker/docker-compose.yml up -d
```

Durumu kontrol edin:
```bash
docker-compose -f docker/docker-compose.yml ps
docker-compose -f docker/docker-compose.yml logs -f
```

#### Seçenek B: Doğrudan Python ile Kurulum

```bash
cd /opt/mini-atlas
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium
sudo systemctl start mini-atlas
sudo systemctl enable mini-atlas
```

Durumu kontrol edin:
```bash
sudo systemctl status mini-atlas
sudo journalctl -u mini-atlas -f
```

### 5. Uygulamanıza Erişin

Tarayıcınızı açın ve şu adrese gidin:
```
http://DROPLET_IP_ADRESINIZ
```

ATLAS arayüzü için:
```
http://DROPLET_IP_ADRESINIZ/atlas
```

## SSL (HTTPS) Kurulumu

### Domain Adı ile

1. Domain'inizi droplet IP adresinize yönlendirin (A kaydı)

2. Let's Encrypt kullanarak SSL sertifikası kurun:

```bash
sudo certbot --nginx -d domain-adiniz.com -d www.domain-adiniz.com
```

3. SSL kurulumunu tamamlamak için talimatları izleyin

4. Certbot sertifikanızı otomatik olarak yenileyecektir. Yenilemeyi test edin:

```bash
sudo certbot renew --dry-run
```

Uygulamanız artık şu adreste erişilebilir olacak:
```
https://domain-adiniz.com
```

## Güvenlik Duvarı Yapılandırması

Güvenlik için UFW güvenlik duvarını yapılandırın:

```bash
# UFW'yi etkinleştir
sudo ufw enable

# SSH'a izin ver
sudo ufw allow ssh

# HTTP ve HTTPS'e izin ver
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Durumu kontrol et
sudo ufw status
```

## İzleme ve Bakım

### Uygulama Loglarını Görüntüleme

**Docker kurulumu:**
```bash
cd /opt/mini-atlas
docker-compose -f docker/docker-compose.yml logs -f mini-atlas
```

**Systemd kurulumu:**
```bash
sudo journalctl -u mini-atlas -f
```

### Uygulamayı Güncelleme

```bash
cd /opt/mini-atlas
git pull
```

**Docker için:**
```bash
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d
```

**Systemd için:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart mini-atlas
```

### Uygulamayı Yeniden Başlatma

**Docker:**
```bash
docker-compose -f docker/docker-compose.yml restart
```

**Systemd:**
```bash
sudo systemctl restart mini-atlas
```

### Uygulamayı Durdurma

**Docker:**
```bash
cd /opt/mini-atlas
docker-compose -f docker/docker-compose.yml down
```

**Systemd:**
```bash
sudo systemctl stop mini-atlas
```

## Sorun Giderme

### Uygulama başlamıyor

1. Hata loglarını kontrol edin:
   ```bash
   docker-compose -f docker/docker-compose.yml logs mini-atlas
   # veya
   sudo journalctl -u mini-atlas -n 100
   ```

2. Ortam değişkenlerinin doğru ayarlandığını doğrulayın:
   ```bash
   cat /opt/mini-atlas/.env
   ```

3. 8000 portunun zaten kullanımda olup olmadığını kontrol edin:
   ```bash
   sudo lsof -i :8000
   ```

### Nginx hataları

1. Nginx yapılandırmasını kontrol edin:
   ```bash
   sudo nginx -t
   ```

2. Nginx loglarını görüntüleyin:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. Nginx'i yeniden başlatın:
   ```bash
   sudo systemctl restart nginx
   ```

### Bellek yetersizliği hataları

1. Bellek kullanımını kontrol edin:
   ```bash
   free -h
   htop
   ```

2. Daha büyük bir droplet'e yükseltmeyi veya swap alanı eklemeyi düşünün:
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

### Tarayıcı/Playwright sorunları

1. Tarayıcı bağımlılıklarını yeniden kurun:
   ```bash
   cd /opt/mini-atlas
   source .venv/bin/activate
   playwright install-deps chromium
   playwright install chromium
   ```

## Performans Ayarları

### Önerilen Droplet Boyutları

- **Geliştirme/Test:** 2GB RAM, 1 CPU ($12/ay)
- **Küçük Üretim:** 4GB RAM, 2 CPU ($24/ay)
- **Orta Üretim:** 8GB RAM, 4 CPU ($48/ay)

### Docker Kaynak Limitleri

Kaynak limitlerini ayarlamak için `docker/docker-compose.yml` dosyasını düzenleyin:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

### Nginx Optimizasyonu

Yüksek trafikli dağıtımlar için Nginx'i ayarlamayı düşünün:

```nginx
# /etc/nginx/nginx.conf dosyasına ekleyin
worker_processes auto;
worker_connections 1024;
```

## Güvenlik En İyi Uygulamaları

1. **Sistemi güncel tutun:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. **Güçlü parolalar kullanın** ve yalnızca SSH anahtarı kimlik doğrulamasını düşünün

3. **Güvenlik duvarını etkinleştirin** (Güvenlik Duvarı Yapılandırması bölümüne bakın)

4. **Verilerinizi düzenli olarak yedekleyin:**
   ```bash
   # Storage ve logları yedekle
   tar -czf backup-$(date +%Y%m%d).tar.gz /opt/mini-atlas/storage /opt/mini-atlas/logs
   ```

5. **Şüpheli aktivite için logları izleyin**

6. **SSL sertifikaları ile HTTPS kullanın** (SSL kurulum bölümüne bakın)

7. **Hassas endpoint'leri** gerekirse kimlik doğrulama ekleyerek koruyun

## Ek Kaynaklar

- [DigitalOcean Dokümantasyonu](https://docs.digitalocean.com/)
- [Docker Dokümantasyonu](https://docs.docker.com/)
- [Nginx Dokümantasyonu](https://nginx.org/en/docs/)
- [Let's Encrypt Dokümantasyonu](https://letsencrypt.org/docs/)
- [mini-Atlas Ana README](README.md)

## Destek

mini-Atlas dağıtımına özgü sorunlar için lütfen [GitHub deposunda](https://github.com/Mustafaakgul354/miniATLAS/issues) bir issue açın.
