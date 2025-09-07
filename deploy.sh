#!/bin/bash

# DigitalOcean deployment script for Game Bot

echo "🚀 Starting deployment..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create project directory
PROJECT_DIR="/opt/game_bot"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# Clone repository (if not exists)
if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/rakhmatov1337/game_bot.git $PROJECT_DIR
fi

# Navigate to project directory
cd $PROJECT_DIR

# Pull latest changes
echo "🔄 Pulling latest changes..."
git pull origin main

# Create environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file..."
    cat > .env << EOF
DEBUG=False
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DB_NAME=game_bot_db
DB_USER=postgres
DB_PASSWORD=$(openssl rand -base64 32)
DB_HOST=db
DB_PORT=5432
EOF
fi

# Create log directory
sudo mkdir -p /var/log/django
sudo chown $USER:$USER /var/log/django

# Build and start services
echo "🏗️ Building and starting services..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 30

# Run migrations
echo "🗄️ Running migrations..."
docker-compose exec web python manage.py migrate --settings=game_bot_admin.production_settings

# Create superuser (optional)
echo "👤 Creating superuser..."
docker-compose exec web python manage.py createsuperuser --settings=game_bot_admin.production_settings --noinput || true

# Collect static files
echo "📁 Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput --settings=game_bot_admin.production_settings

# Setup nginx (optional)
if ! command -v nginx &> /dev/null; then
    echo "🌐 Installing Nginx..."
    sudo apt install nginx -y
    
    # Create nginx config
    sudo tee /etc/nginx/sites-available/game_bot << EOF
server {
    listen 80;
    server_name your-domain.com;  # O'z domain nomingizni qo'ying
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static/ {
        alias /opt/game_bot/staticfiles/;
    }
    
    location /media/ {
        alias /opt/game_bot/media/;
    }
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/game_bot /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t
    sudo systemctl restart nginx
    sudo systemctl enable nginx
fi

# Setup firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

# Create systemd service for auto-start
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/game-bot.service << EOF
[Unit]
Description=Game Bot Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable game-bot.service

echo "✅ Deployment completed!"
echo "🌐 Your application should be available at: http://46.101.107.199"
echo "📊 Check status with: docker-compose ps"
echo "📝 View logs with: docker-compose logs -f"
