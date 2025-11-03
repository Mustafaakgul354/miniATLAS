#!/bin/bash
# Deployment script for DigitalOcean Droplet
# This script sets up mini-Atlas on a fresh Ubuntu droplet

set -e

echo "🚀 Starting mini-Atlas deployment on DigitalOcean Droplet..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get install -y \
    git \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nginx \
    certbot \
    python3-certbot-nginx \
    curl \
    wget

# Install Docker and Docker Compose
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Clone repository if not already cloned
if [ ! -d "/opt/mini-atlas" ]; then
    echo "📥 Cloning mini-Atlas repository..."
    sudo git clone https://github.com/Mustafaakgul354/miniATLAS.git /opt/mini-atlas
    sudo chown -R $USER:$USER /opt/mini-atlas
else
    echo "📂 Repository already exists, pulling latest changes..."
    cd /opt/mini-atlas
    git pull
fi

cd /opt/mini-atlas

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit /opt/mini-atlas/.env and configure:"
    echo "   - OPENAI_API_KEY (required if using OpenAI)"
    echo "   - Other environment variables as needed"
    echo ""
    read -p "Press enter to continue after editing .env file..."
fi

# Create necessary directories
mkdir -p logs storage

# Setup systemd service for non-Docker deployment (optional)
echo "⚙️  Setting up systemd service (optional - for non-Docker deployment)..."
sudo tee /etc/systemd/system/mini-atlas.service > /dev/null <<EOF
[Unit]
Description=mini-Atlas Browser Automation Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/mini-atlas
Environment="PATH=/opt/mini-atlas/.venv/bin"
ExecStart=/opt/mini-atlas/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setup Nginx reverse proxy
echo "🌐 Configuring Nginx reverse proxy..."
sudo tee /etc/nginx/sites-available/mini-atlas > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for long-running agent sessions
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/mini-atlas /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo ""
echo "✅ Deployment script completed!"
echo ""
echo "Next steps:"
echo "1. Edit /opt/mini-atlas/.env with your configuration"
echo ""
echo "2. Choose deployment method:"
echo ""
echo "   Option A - Docker (Recommended):"
echo "   cd /opt/mini-atlas"
echo "   docker-compose -f docker/docker-compose.yml up -d"
echo ""
echo "   Option B - Direct Python:"
echo "   cd /opt/mini-atlas"
echo "   python3.11 -m venv .venv"
echo "   source .venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   playwright install chromium"
echo "   playwright install-deps chromium"
echo "   sudo systemctl start mini-atlas"
echo "   sudo systemctl enable mini-atlas"
echo ""
echo "3. Access mini-Atlas at: http://YOUR_DROPLET_IP"
echo ""
echo "4. (Optional) Setup SSL with Let's Encrypt:"
echo "   sudo certbot --nginx -d your-domain.com"
echo ""
