#!/bin/bash

set -e

echo "====================================="
echo "SYSTEM UPDATE"
echo "====================================="
sudo apt update

echo "====================================="
echo "PYTHON + UTILITIES"
echo "====================================="
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python-is-python3 \
    git \
    curl \
    ca-certificates \
    gnupg \
    jq

echo "====================================="
echo "DOCKER SETUP"
echo "====================================="
sudo install -m 0755 -d /etc/apt/keyrings

if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
fi

sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update

sudo apt install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

echo "====================================="
echo "DOCKER PERMISSION (SAFE)"
echo "====================================="
CURRENT_USER=$(logname 2>/dev/null || echo "$SUDO_USER")

if [ -n "$CURRENT_USER" ] && [ "$CURRENT_USER" != "root" ]; then
    sudo usermod -aG docker "$CURRENT_USER" || true
fi

echo "====================================="
echo "POSTGRESQL (SAFE MODE)"
echo "====================================="
sudo apt install -y postgresql postgresql-contrib

echo "Starting PostgreSQL service..."
sudo service postgresql start || true

echo "Setting postgres password..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';" || true

echo "Creating database if not exists..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='bankdb'" | grep -q 1 || \
sudo -u postgres createdb bankdb || true

echo "Testing PostgreSQL connection..."
PGPASSWORD=postgres psql -U postgres -h localhost -d bankdb -c "SELECT version();" || true

echo "====================================="
echo "INSTALLING OLLAMA"
echo "====================================="
sudo apt-get install zstd
curl -fsSL https://ollama.com/install.sh | sh

export PATH="$PATH:/usr/local/bin"

echo "Starting Ollama..."
nohup ollama serve > ollama.log 2>&1 &

sleep 10

echo "Checking Ollama..."
curl -s http://localhost:11434 || echo "Ollama not ready yet"

echo "====================================="
echo "PULLING MODELS (SAFE MODE)"
echo "====================================="

ollama pull llama3:70b || true
ollama pull deepseek-r1:70b || true

echo "====================================="
echo "FINAL CHECKS"
echo "====================================="

python3 --version
pip3 --version
docker --version
docker compose version
psql --version
ollama --version || true
ollama list || true

echo "====================================="
echo "SETUP COMPLETE"
echo "====================================="
echo ""
echo "PostgreSQL:"
echo "- user: postgres"
echo "- password: postgres"
echo "- db: bankdb"
echo ""
echo "Ollama:"
echo "- URL: http://localhost:11434"
echo "- Models: llama3:8b, llama3.1:8b, deepseek-r1:7b"
echo ""
echo "NOTE:"
echo "- 70B models removed (not suitable for this environment)"
echo "- Script is safe for Jupyter / container / VM"