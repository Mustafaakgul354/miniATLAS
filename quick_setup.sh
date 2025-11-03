#!/bin/bash
# Quick setup script for mini-Atlas on DigitalOcean Droplet
# Usage: curl -fsSL https://raw.githubusercontent.com/Mustafaakgul354/miniATLAS/main/quick_setup.sh | bash

set -e

REPO_URL="https://github.com/Mustafaakgul354/miniATLAS.git"
INSTALL_DIR="/opt/mini-atlas"

echo "🚀 Quick Setup for mini-Atlas"
echo "=============================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script requires root privileges. Please run with sudo:"
    echo "   curl -fsSL https://raw.githubusercontent.com/Mustafaakgul354/miniATLAS/main/quick_setup.sh | sudo bash"
    exit 1
fi

# Clone repository
if [ ! -d "$INSTALL_DIR" ]; then
    echo "📥 Cloning repository to $INSTALL_DIR..."
    if ! git clone "$REPO_URL" "$INSTALL_DIR"; then
        echo "❌ Failed to clone repository from $REPO_URL"
        exit 1
    fi
else
    echo "📂 Repository already exists at $INSTALL_DIR"
fi

# Run full deployment script
echo "🔧 Running deployment script..."
cd "$INSTALL_DIR"
chmod +x deploy_droplet.sh
./deploy_droplet.sh

echo ""
echo "✅ Quick setup completed!"
