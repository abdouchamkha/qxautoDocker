# Quotex Trading Bot

A Python-based automated trading bot for Quotex platform that receives trading signals from Telegram channels and executes trades automatically.

## Features

- 🤖 **Automated Trading**: Executes trades based on Telegram signals
- 📊 **Real-time Monitoring**: Live trading statistics and performance tracking
- 🔄 **Martingale Strategy**: Configurable gale (martingale) system
- 💰 **Risk Management**: Stop-loss and take-profit limits
- 📱 **Telegram Integration**: Receives signals from Telegram channels
- 🐳 **Docker Support**: Easy deployment with Docker and Docker Compose
- 🔒 **Secure**: Credential management and session persistence
- 📈 **Performance Tracking**: Detailed profit/loss statistics

## Prerequisites

- **Quotex Account**: Active trading account with API access
- **Telegram Account**: For receiving trading signals
- **VPS Server**: Ubuntu 20.04+ with Docker support
- **Python 3.11+**: For local development

## Quick Start

### Option 1: VPS Deployment (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <your-repository-url>
   cd quotex-trading-bot
   ```

2. **Run VPS setup script** (first time only):
   ```bash
   ./vps-setup.sh
   ```

3. **Deploy the application**:
   ```bash
   ./start.sh deploy
   ```

4. **View logs**:
   ```bash
   ./start.sh logs
   ```

### Option 2: Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the bot**:
   ```bash
   python main.py
   ```

## Configuration

### Initial Setup

When you first run the bot, it will prompt you to configure:

1. **Quotex Credentials**:
   - Email address
   - Password

2. **Trading Parameters**:
   - Initial trade amount
   - Gale limit (maximum consecutive losses)
   - Stop-loss limit
   - Take-profit limit

3. **Account Selection**:
   - Choose from available Quotex accounts

### Telegram Configuration

The bot uses pre-configured Telegram settings:
- **API_ID**: 25712604
- **API_HASH**: 8c745804b912834996255dc41f92e1e4
- **BOT_TOKEN**: 8175643752:AAFclZVqlIZX0nE-9al-W5UZP4BlHkMlDn4
- **CHANNEL_ID**: -1002526280469

## Docker Deployment

### Using Docker Compose

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Restart
docker-compose restart
```

### Using Docker directly

```bash
# Build image
docker build -t quotex-trading-bot .

# Run container
docker run -d --name quotex-bot \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/sessions:/app/sessions \
  quotex-trading-bot

# View logs
docker logs -f quotex-bot
```

## Management Scripts

### Start Script (`start.sh`)

The `start.sh` script provides easy management commands:

```bash
./start.sh deploy     # Deploy application
./start.sh start      # Start application
./start.sh stop       # Stop application
./start.sh restart    # Restart application
./start.sh status     # Check status
./start.sh logs       # View logs
./start.sh update     # Update application
./start.sh backup     # Create backup
./start.sh help       # Show help
```

### VPS Setup Script (`vps-setup.sh`)

Automates VPS preparation:

```bash
./vps-setup.sh
```

This script:
- Updates system packages
- Installs Docker and Docker Compose
- Configures firewall
- Creates swap file (if needed)
- Sets up user permissions

## Project Structure

```
quotex-trading-bot/
├── main.py                 # Main application file
├── qxbroker.py            # Quotex broker integration
├── admin_ui_bot.py        # Admin interface
├── client_setup_gui.py    # Client setup GUI
├── quotexapi/             # Quotex API library
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── start.sh              # Management script
├── vps-setup.sh          # VPS setup script
├── VPS_DEPLOYMENT_GUIDE.md # Detailed deployment guide
├── config/               # Configuration directory
├── logs/                 # Log files directory
└── sessions/             # Telegram session files
```

## Configuration Files

### Persistent Data

The following directories are mounted as volumes for data persistence:

- **`config/`**: Application configuration and credentials
- **`logs/`**: Application logs and trading history
- **`sessions/`**: Telegram session files

### Environment Variables

You can customize the bot behavior using environment variables:

```bash
# Add to docker-compose.yml
environment:
  - TZ=UTC
  - PYTHONUNBUFFERED=1
```

## Monitoring and Maintenance

### Viewing Logs

```bash
# Real-time logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs quotex-bot
```

### Backup and Restore

```bash
# Create backup
./start.sh backup

# Manual backup
tar -czf backup_$(date +%Y%m%d).tar.gz config/ sessions/ logs/
```

### Updates

```bash
# Update application
./start.sh update

# Manual update
git pull origin main
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### Common Issues

1. **Container won't start**:
   ```bash
   docker-compose logs
   docker system prune -a
   ```

2. **Permission denied**:
   ```bash
   sudo chown -R $USER:$USER config logs sessions
   ```

3. **Memory issues**:
   ```bash
   free -h
   # Create swap if needed
   sudo fallocate -l 2G /swapfile
   ```

4. **Network connectivity**:
   ```bash
   ping google.com
   docker network ls
   ```

### Getting Help

1. Check the logs: `./start.sh logs`
2. Verify Docker installation: `docker --version`
3. Check system resources: `htop`
4. Review the [VPS Deployment Guide](VPS_DEPLOYMENT_GUIDE.md)

## Security Considerations

- **Firewall**: Only necessary ports are open (SSH, HTTP/HTTPS)
- **User Permissions**: Application runs as non-root user
- **Credential Storage**: Credentials are stored securely with proper permissions
- **Regular Updates**: System and Docker images are updated regularly

## Performance Optimization

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  quotex-bot:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

### Log Rotation

Configure log rotation to prevent disk space issues:

```bash
sudo nano /etc/logrotate.d/docker
```

## Support

For issues and questions:

1. Check the [VPS Deployment Guide](VPS_DEPLOYMENT_GUIDE.md)
2. Review the troubleshooting section
3. Check application logs
4. Verify system requirements

## Disclaimer

⚠️ **Trading involves risk**. This bot is for educational purposes. Always test thoroughly before using with real money. The authors are not responsible for any financial losses.

## License

This project is for educational purposes. Use at your own risk.

---

## Quick Reference

### Essential Commands

```bash
# First deployment
./vps-setup.sh
./start.sh deploy

# Daily operations
./start.sh logs      # View logs
./start.sh status    # Check status
./start.sh restart   # Restart bot

# Maintenance
./start.sh backup    # Create backup
./start.sh update    # Update application
```

### File Locations

- **Configuration**: `./config/`
- **Logs**: `./logs/`
- **Sessions**: `./sessions/`
- **Backups**: `./backups/`

### Important Notes

- Always backup before updates
- Monitor system resources regularly
- Keep credentials secure
- Test thoroughly before live trading