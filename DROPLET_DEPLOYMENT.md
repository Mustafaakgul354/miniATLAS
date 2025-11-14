# DigitalOcean Droplet Deployment Guide

This guide explains how to deploy mini-Atlas on a DigitalOcean Droplet.

## Prerequisites

- A DigitalOcean account
- A droplet with at least 2GB RAM (4GB recommended for production)
- Ubuntu 22.04 LTS or newer
- SSH access to your droplet
- (Optional) A domain name pointed to your droplet's IP

## Quick Deployment

### 1. Connect to Your Droplet

```bash
ssh root@YOUR_DROPLET_IP
```

### 2. Download and Run the Deployment Script

```bash
curl -fsSL https://raw.githubusercontent.com/Mustafaakgul354/miniATLAS/main/deploy_droplet.sh -o deploy_droplet.sh
chmod +x deploy_droplet.sh
./deploy_droplet.sh
```

The script will:
- Update system packages
- Install Docker, Docker Compose, Nginx, and other dependencies
- Clone the mini-Atlas repository to `/opt/mini-atlas`
- Configure Nginx as a reverse proxy
- Set up a systemd service (for non-Docker deployment)

### 3. Configure Environment Variables

Edit the `.env` file:

```bash
cd /opt/mini-atlas
nano .env
```

**Required settings:**
- `OPENAI_API_KEY` - Your OpenAI API key (if using OpenAI)
- `LLM_PROVIDER` - Set to `openai`, `ollama`, or `vllm`

**Optional settings:**
- `BROWSER` - Set to `headless` (recommended for droplet)
- `AGENT_MAX_STEPS` - Maximum steps per session
- `TIMEZONE` - Your timezone (default: `Europe/Istanbul`)

### 4. Start the Application

#### Option A: Docker Deployment (Recommended)

```bash
cd /opt/mini-atlas
docker-compose -f docker/docker-compose.yml up -d
```

Check status:
```bash
docker-compose -f docker/docker-compose.yml ps
docker-compose -f docker/docker-compose.yml logs -f
```

#### Option B: Direct Python Deployment

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

Check status:
```bash
sudo systemctl status mini-atlas
sudo journalctl -u mini-atlas -f
```

### 5. Access Your Application

Open your browser and navigate to:
```
http://YOUR_DROPLET_IP
```

For the ATLAS interface:
```
http://YOUR_DROPLET_IP/atlas
```

## Setting Up SSL (HTTPS)

### With a Domain Name

1. Point your domain to your droplet's IP address (A record)

2. Install SSL certificate using Let's Encrypt:

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

3. Follow the prompts to complete the SSL setup

4. Certbot will automatically renew your certificate. Test the renewal:

```bash
sudo certbot renew --dry-run
```

Your application will now be available at:
```
https://your-domain.com
```

## Firewall Configuration

Configure UFW firewall for security:

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

## Monitoring and Maintenance

### View Application Logs

**Docker deployment:**
```bash
cd /opt/mini-atlas
docker-compose -f docker/docker-compose.yml logs -f mini-atlas
```

**Systemd deployment:**
```bash
sudo journalctl -u mini-atlas -f
```

### Update Application

```bash
cd /opt/mini-atlas
git pull
```

**For Docker:**
```bash
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d
```

**For systemd:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart mini-atlas
```

### Restart Application

**Docker:**
```bash
docker-compose -f docker/docker-compose.yml restart
```

**Systemd:**
```bash
sudo systemctl restart mini-atlas
```

### Stop Application

**Docker:**
```bash
cd /opt/mini-atlas
docker-compose -f docker/docker-compose.yml down
```

**Systemd:**
```bash
sudo systemctl stop mini-atlas
```

## Troubleshooting

### Application won't start

1. Check logs for errors:
   ```bash
   docker-compose -f docker/docker-compose.yml logs mini-atlas
   # or
   sudo journalctl -u mini-atlas -n 100
   ```

2. Verify environment variables are set correctly:
   ```bash
   cat /opt/mini-atlas/.env
   ```

3. Check if port 8000 is already in use:
   ```bash
   sudo lsof -i :8000
   ```

### Nginx errors

1. Check Nginx configuration:
   ```bash
   sudo nginx -t
   ```

2. View Nginx logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. Restart Nginx:
   ```bash
   sudo systemctl restart nginx
   ```

### Out of memory errors

1. Check memory usage:
   ```bash
   free -h
   htop
   ```

2. Consider upgrading to a larger droplet or adding swap space:
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

### Browser/Playwright issues

1. Reinstall browser dependencies:
   ```bash
   cd /opt/mini-atlas
   source .venv/bin/activate
   playwright install-deps chromium
   playwright install chromium
   ```

## Performance Tuning

### Recommended Droplet Sizes

- **Development/Testing:** 2GB RAM, 1 CPU ($12/month)
- **Small Production:** 4GB RAM, 2 CPU ($24/month)
- **Medium Production:** 8GB RAM, 4 CPU ($48/month)

### Docker Resource Limits

Edit `docker/docker-compose.yml` to adjust resource limits:

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

### Nginx Optimization

For high-traffic deployments, consider tuning Nginx:

```nginx
# Add to /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 1024;
```

## Security Best Practices

1. **Keep system updated:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. **Use strong passwords** and consider SSH key authentication only

3. **Enable firewall** (see Firewall Configuration section)

4. **Regularly backup** your data:
   ```bash
   # Backup storage and logs
   tar -czf backup-$(date +%Y%m%d).tar.gz /opt/mini-atlas/storage /opt/mini-atlas/logs
   ```

5. **Monitor logs** for suspicious activity

6. **Use HTTPS** with SSL certificates (see SSL setup section)

7. **Protect sensitive endpoints** by adding authentication if needed

## Additional Resources

- [DigitalOcean Documentation](https://docs.digitalocean.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [mini-Atlas Main README](README.md)

## Support

For issues specific to mini-Atlas deployment, please open an issue on the [GitHub repository](https://github.com/Mustafaakgul354/miniATLAS/issues).
