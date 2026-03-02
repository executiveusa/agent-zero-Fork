#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════╗
# ║         Agent Zero - Hostinger VPS Deployment Script                ║
# ║                  Almost Free AI Agent (~$4-8/month)                  ║
# ╚══════════════════════════════════════════════════════════════════════╝

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ $1${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_header "Agent Zero Hostinger Deployment - Step 1: System Check"

# Check system resources
TOTAL_RAM=$(free -m | awk 'NR==2{print $2}')
TOTAL_CPU=$(nproc)

echo ""
print_info "System Resources:"
echo "  RAM: ${TOTAL_RAM}MB"
echo "  CPU Cores: ${TOTAL_CPU}"
echo ""

if [ "$TOTAL_RAM" -lt 400 ]; then
    print_error "Insufficient RAM. Need at least 512MB. Current: ${TOTAL_RAM}MB"
    exit 1
fi

print_success "System resources sufficient"

# ═══════════════════════════════════════════════════════════════════════
print_header "Step 2: Install Docker and Docker Compose"

# Check if Docker is installed
if command -v docker &> /dev/null; then
    print_success "Docker already installed"
    docker --version
else
    print_info "Installing Docker..."

    # Update package list
    apt-get update

    # Install prerequisites
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Add Docker's official GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # Set up the repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Start Docker
    systemctl start docker
    systemctl enable docker

    print_success "Docker installed successfully"
fi

# Check if Docker Compose is installed
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    print_success "Docker Compose already installed"
else
    print_error "Docker Compose not found. Please install it manually."
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════
print_header "Step 3: Setup Application Directory"

# Set deployment directory
DEPLOY_DIR="/root/agent-zero"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

print_success "Created deployment directory: $DEPLOY_DIR"

# ═══════════════════════════════════════════════════════════════════════
print_header "Step 4: Clone Repository (if needed)"

if [ -d ".git" ]; then
    print_info "Repository already exists, pulling latest changes..."
    git pull
else
    print_info "Cloning Agent Zero repository..."

    # Check if current directory is empty
    if [ "$(ls -A)" ]; then
        print_warning "Directory not empty. Skipping clone."
    else
        read -p "Enter GitHub repository URL [https://github.com/executiveusa/agent-zero-Fork.git]: " REPO_URL
        REPO_URL=${REPO_URL:-https://github.com/executiveusa/agent-zero-Fork.git}

        git clone "$REPO_URL" .
        print_success "Repository cloned"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════
print_header "Step 5: Configure Environment"

ENV_FILE="$DEPLOY_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    print_warning ".env file already exists"
    read -p "Overwrite with Hostinger optimized config? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp deployment/.env.hostinger.template "$ENV_FILE"
        print_success "Copied Hostinger optimized .env"
    fi
else
    cp deployment/.env.hostinger.template "$ENV_FILE"
    print_success "Created .env from Hostinger template"
fi

echo ""
print_warning "IMPORTANT: You need to configure your .env file!"
print_info "Edit $ENV_FILE and add your API keys"
echo ""
print_info "For FREE deployment (no cost besides VPS):"
echo "  1. Set up Google Cloud OAuth for Gemini CLI (FREE)"
echo "  2. Optionally add Venice.ai API key (FREE tier)"
echo "  3. Optionally add Telegram bot token (FREE)"
echo ""
read -p "Press Enter to edit .env now, or Ctrl+C to exit and edit manually..."

# Open editor
if command -v nano &> /dev/null; then
    nano "$ENV_FILE"
elif command -v vi &> /dev/null; then
    vi "$ENV_FILE"
else
    print_warning "No text editor found. Please edit $ENV_FILE manually."
fi

# ═══════════════════════════════════════════════════════════════════════
print_header "Step 6: Setup Google Cloud OAuth (FREE Gemini Access)"

echo ""
print_info "To use FREE Gemini models via OAuth:"
echo "  1. Install Google Cloud SDK: curl https://sdk.cloud.google.com | bash"
echo "  2. Run: gcloud auth login"
echo "  3. Run: gcloud auth application-default login"
echo "  4. Set project: gcloud config set project YOUR_PROJECT_ID"
echo ""
read -p "Do you want to install gcloud SDK now? [y/N]: " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Installing Google Cloud SDK..."
    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL  # Reload shell
    print_success "Google Cloud SDK installed. Please run 'gcloud auth login' after this script."
fi

# ═══════════════════════════════════════════════════════════════════════
print_header "Step 7: Build Docker Images"

print_info "Building Hostinger-optimized Docker image..."
cd "$DEPLOY_DIR"

docker compose -f deployment/docker-compose.hostinger.yml build

print_success "Docker images built successfully"

# ═══════════════════════════════════════════════════════════════════════
print_header "Step 8: Start Services"

read -p "Enable Telegram bot? [y/N]: " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    PROFILE_FLAG="--profile telegram"
    print_info "Starting with Telegram bot..."
else
    PROFILE_FLAG=""
    print_info "Starting without Telegram bot..."
fi

docker compose -f deployment/docker-compose.hostinger.yml $PROFILE_FLAG up -d

print_success "Services started!"

# ═══════════════════════════════════════════════════════════════════════
print_header "Step 9: Configure Firewall (Optional)"

echo ""
print_info "Firewall Configuration:"
echo "  - Port 8000: Web UI (HTTP)"
echo "  - Port 8001: API (optional)"
echo ""
read -p "Configure firewall (ufw) now? [y/N]: " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp    # SSH
        ufw allow 8000/tcp  # Web UI
        ufw allow 8001/tcp  # API (optional)
        ufw --force enable
        print_success "Firewall configured"
    else
        print_warning "ufw not installed. Skipping firewall configuration."
    fi
fi

# ═══════════════════════════════════════════════════════════════════════
print_header "Step 10: Setup Reverse Proxy (Optional)"

echo ""
print_info "For production, you should set up a reverse proxy (nginx) with SSL"
echo "This allows you to:"
echo "  - Use domain name instead of IP:8000"
echo "  - Enable HTTPS/SSL encryption"
echo "  - Add authentication layer"
echo ""
read -p "Install nginx and setup reverse proxy? [y/N]: " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    apt-get install -y nginx certbot python3-certbot-nginx

    # Create nginx config
    cat > /etc/nginx/sites-available/agent-zero <<'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain

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
    }

    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

    # Enable site
    ln -sf /etc/nginx/sites-available/agent-zero /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # Test and reload nginx
    nginx -t && systemctl reload nginx

    print_success "Nginx configured"
    print_info "To enable SSL, run: certbot --nginx"
fi

# ═══════════════════════════════════════════════════════════════════════
print_header "Step 11: Setup Auto-Start (Systemd)"

# Create systemd service
cat > /etc/systemd/system/agent-zero.service <<EOF
[Unit]
Description=Agent Zero AI Assistant
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/bin/docker compose -f deployment/docker-compose.hostinger.yml up -d
ExecStop=/usr/bin/docker compose -f deployment/docker-compose.hostinger.yml down
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable agent-zero.service

print_success "Auto-start configured"

# ═══════════════════════════════════════════════════════════════════════
print_header "Deployment Complete! 🎉"

echo ""
print_success "Agent Zero is now running on your Hostinger VPS!"
echo ""
print_info "Access your agent at:"

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo "  Web UI: http://$SERVER_IP:8000"
echo "  API: http://$SERVER_IP:8001"
echo ""

if [ -n "$PROFILE_FLAG" ]; then
    print_info "Telegram bot is enabled and running"
fi

echo ""
print_info "Useful commands:"
echo "  View logs:    docker compose -f deployment/docker-compose.hostinger.yml logs -f"
echo "  Restart:      docker compose -f deployment/docker-compose.hostinger.yml restart"
echo "  Stop:         docker compose -f deployment/docker-compose.hostinger.yml down"
echo "  Update:       cd $DEPLOY_DIR && git pull && docker compose -f deployment/docker-compose.hostinger.yml up -d --build"
echo ""

print_info "Cost Summary:"
echo "  VPS (Hostinger): ~\$4-8/month"
echo "  Gemini CLI:      FREE (OAuth)"
echo "  Venice.ai:       FREE (tier)"
echo "  Telegram:        FREE"
echo "  ─────────────────────────────"
echo "  Total:          ~\$4-8/month"
echo ""

print_warning "Security Recommendations:"
echo "  1. Change default SSH port (edit /etc/ssh/sshd_config)"
echo "  2. Set up SSH key authentication"
echo "  3. Enable SSL with certbot --nginx"
echo "  4. Set strong passwords in .env"
echo "  5. Regularly update: apt-get update && apt-get upgrade"
echo ""

print_success "Setup complete! Enjoy your almost-free AI agent! 🚀"
