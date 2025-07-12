# Quotex Trading Bot - VPS Deployment Guide

This guide provides step-by-step instructions for deploying the Quotex Trading Bot on a VPS server using Docker.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [VPS Setup](#vps-setup)
3. [Docker Installation](#docker-installation)
4. [Application Deployment](#application-deployment)
5. [Configuration](#configuration)
6. [Running the Bot](#running-the-bot)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Accounts
- **Quotex Account**: Active trading account with API access
- **Telegram Account**: For receiving trading signals
- **VPS Provider**: Any VPS provider (DigitalOcean, AWS, Vultr, etc.)

### VPS Requirements
- **OS**: Ubuntu 20.04 LTS or higher
- **RAM**: Minimum 2GB (4GB recommended)
- **Storage**: Minimum 20GB
- **CPU**: 1 vCPU minimum (2 vCPU recommended)
- **Network**: Stable internet connection

## VPS Setup

### Step 1: Connect to Your VPS
```bash
ssh root@your-vps-ip
```

### Step 2: Update System
```bash
# Update package list
apt update

# Upgrade existing packages
apt upgrade -y

# Install essential tools
apt install -y curl wget git nano htop ufw
```

### Step 3: Create Non-Root User (Security Best Practice)
```bash
# Create new user
adduser quotexbot

# Add user to sudo group
usermod -aG sudo quotexbot

# Switch to new user
su - quotexbot
```

### Step 4: Configure Firewall
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS (if needed)
sudo ufw allow 80
sudo ufw allow 443

# Check firewall status
sudo ufw status
```

## Docker Installation

### Step 1: Install Docker
```bash
# Update package index
sudo apt update

# Install prerequisites
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add user to docker group
sudo usermod -aG docker $USER

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version
```

### Step 2: Install Docker Compose
```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### Step 3: Logout and Login Again
```bash
# Logout to apply group changes
exit

# SSH back in
ssh quotexbot@your-vps-ip
```

## Application Deployment

### Step 1: Clone the Repository
```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/your-username/quotex-trading-bot.git

# Navigate to project directory
cd quotex-trading-bot
```

### Step 2: Create Required Directories
```bash
# Create directories for persistent data
mkdir -p config logs sessions

# Set proper permissions
chmod 755 config logs sessions
```

### Step 3: Build and Start the Application
```bash
# Build the Docker image
docker-compose build

# Start the application
docker-compose up -d

# Check if container is running
docker-compose ps
```

## Configuration

### Step 1: Access the Bot Configuration
```bash
# Attach to the running container
docker-compose exec quotex-bot bash

# Or run interactively for initial setup
docker-compose run --rm -it quotex-bot python main.py
```

### Step 2: Configure Quotex Credentials
The bot will prompt you to enter:
- **Quotex Email**: Your Quotex account email
- **Quotex Password**: Your Quotex account password
- **Trade Amount**: Initial trading amount
- **Gale Limit**: Maximum number of consecutive losses before stopping

### Step 3: Telegram Configuration
The bot uses these pre-configured Telegram settings:
- **API_ID**: 25712604
- **API_HASH**: 8c745804b912834996255dc41f92e1e4
- **BOT_TOKEN**: 8175643752:AAFclZVqlIZX0nE-9al-W5UZP4BlHkMlDn4
- **CHANNEL_ID**: -1002526280469

## Running the Bot

### Method 1: Docker Compose (Recommended)
```bash
# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

### Method 2: Direct Docker
```bash
# Run the container
docker run -d --name quotex-bot \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/sessions:/app/sessions \
  quotex-trading-bot

# View logs
docker logs -f quotex-bot

# Stop the container
docker stop quotex-bot
```

### Method 3: Interactive Mode (for configuration)
```bash
# Run interactively
docker-compose run --rm -it quotex-bot python main.py
```

## Monitoring and Maintenance

### Step 1: View Logs
```bash
# View real-time logs
docker-compose logs -f

# View specific number of lines
docker-compose logs --tail=100

# View logs from specific service
docker-compose logs quotex-bot
```

### Step 2: Check Container Status
```bash
# Check running containers
docker ps

# Check all containers (including stopped)
docker ps -a

# Check resource usage
docker stats
```

### Step 3: Backup Configuration
```bash
# Create backup directory
mkdir -p ~/backups/$(date +%Y%m%d)

# Backup configuration files
cp -r config/* ~/backups/$(date +%Y%m%d)/
cp -r sessions/* ~/backups/$(date +%Y%m%d)/
```

### Step 4: Update the Application
```bash
# Stop the current version
docker-compose down

# Pull latest changes
git pull origin main

# Rebuild and start
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: Container Won't Start
```bash
# Check container logs
docker-compose logs

# Check if ports are available
sudo netstat -tulpn | grep :5000

# Restart Docker service
sudo systemctl restart docker
```

#### Issue 2: Permission Denied
```bash
# Fix directory permissions
sudo chown -R $USER:$USER config logs sessions

# Fix Docker permissions
sudo chmod 666 /var/run/docker.sock
```

#### Issue 3: Memory Issues
```bash
# Check memory usage
free -h

# Increase swap space if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Issue 4: Network Connectivity
```bash
# Test internet connection
ping google.com

# Check DNS resolution
nslookup google.com

# Test Docker network
docker network ls
```

### Useful Commands

#### System Monitoring
```bash
# Check system resources
htop

# Check disk usage
df -h

# Check memory usage
free -h

# Check running processes
ps aux | grep python
```

#### Docker Management
```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Clean up everything
docker system prune -a
```

#### Log Management
```bash
# Rotate logs
sudo logrotate -f /etc/logrotate.conf

# Check log file sizes
du -sh logs/*

# Archive old logs
tar -czf logs_$(date +%Y%m%d).tar.gz logs/
```

## Security Considerations

### 1. Firewall Configuration
```bash
# Only allow necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
```

### 2. Regular Updates
```bash
# Update system weekly
sudo apt update && sudo apt upgrade -y

# Update Docker images monthly
docker-compose pull
docker-compose up -d
```

### 3. Backup Strategy
```bash
# Create automated backup script
cat > ~/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/quotexbot/backups/$DATE"
mkdir -p $BACKUP_DIR
cp -r config/* $BACKUP_DIR/
cp -r sessions/* $BACKUP_DIR/
tar -czf $BACKUP_DIR/logs.tar.gz logs/
echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x ~/backup.sh
```

## Performance Optimization

### 1. Resource Limits
```bash
# Add resource limits to docker-compose.yml
services:
  quotex-bot:
    # ... existing configuration ...
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

### 2. Log Rotation
```bash
# Configure log rotation
sudo nano /etc/logrotate.d/docker
```

Add:
```
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
```

## Support and Maintenance

### Regular Maintenance Tasks
1. **Daily**: Check bot logs and trading performance
2. **Weekly**: Update system packages and Docker images
3. **Monthly**: Review and optimize configuration
4. **Quarterly**: Full system backup and security audit

### Monitoring Tools
- **htop**: System resource monitoring
- **docker stats**: Container resource usage
- **logwatch**: Automated log analysis
- **fail2ban**: Intrusion prevention

### Emergency Procedures
1. **Bot Malfunction**: Stop container and check logs
2. **System Issues**: Restart Docker service
3. **Security Breach**: Isolate system and restore from backup
4. **Data Loss**: Restore from latest backup

---

## Quick Start Commands

For experienced users, here are the essential commands:

```bash
# Initial setup
git clone <repository-url>
cd quotex-trading-bot
mkdir -p config logs sessions
docker-compose up -d

# Daily operations
docker-compose logs -f          # View logs
docker-compose restart          # Restart bot
docker-compose down && docker-compose up -d  # Full restart

# Maintenance
docker system prune -a          # Clean up Docker
sudo apt update && sudo apt upgrade -y  # Update system
```

---

**Note**: This guide assumes you have basic Linux and Docker knowledge. If you encounter issues, refer to the troubleshooting section or seek professional assistance.

**Disclaimer**: Trading involves risk. This bot is for educational purposes. Always test thoroughly before using with real money.