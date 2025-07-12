#!/bin/bash

# VPS Setup Script for Quotex Trading Bot
# This script installs Docker and Docker Compose on Ubuntu

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root. Please run as a regular user with sudo privileges."
        exit 1
    fi
}

# Function to check OS
check_os() {
    if [[ ! -f /etc/os-release ]]; then
        print_error "Cannot determine OS. This script supports Ubuntu 20.04+ only."
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        print_error "This script supports Ubuntu only. Detected: $ID"
        exit 1
    fi
    
    # Check Ubuntu version
    UBUNTU_VERSION=$(echo $VERSION_ID | cut -d. -f1)
    if [[ $UBUNTU_VERSION -lt 20 ]]; then
        print_error "This script requires Ubuntu 20.04 or higher. Detected: $VERSION_ID"
        exit 1
    fi
    
    print_success "OS check passed: Ubuntu $VERSION_ID"
}

# Function to update system
update_system() {
    print_status "Updating system packages..."
    sudo apt update
    sudo apt upgrade -y
    print_success "System updated successfully"
}

# Function to install essential packages
install_essentials() {
    print_status "Installing essential packages..."
    sudo apt install -y \
        curl \
        wget \
        git \
        nano \
        htop \
        ufw \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release
    print_success "Essential packages installed"
}

# Function to install Docker
install_docker() {
    print_status "Installing Docker..."
    
    # Remove old versions if they exist
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
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
    
    print_success "Docker installed successfully"
}

# Function to install Docker Compose
install_docker_compose() {
    print_status "Installing Docker Compose..."
    
    # Download Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Make it executable
    sudo chmod +x /usr/local/bin/docker-compose
    
    print_success "Docker Compose installed successfully"
}

# Function to configure firewall
configure_firewall() {
    print_status "Configuring firewall..."
    
    # Enable UFW
    sudo ufw --force enable
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow HTTP/HTTPS (optional)
    sudo ufw allow 80
    sudo ufw allow 443
    
    print_success "Firewall configured successfully"
}

# Function to create swap file (if needed)
create_swap() {
    print_status "Checking memory..."
    
    TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    
    if [[ $TOTAL_MEM -lt 2048 ]]; then
        print_warning "Low memory detected (${TOTAL_MEM}MB). Creating swap file..."
        
        # Check if swap already exists
        if ! swapon --show | grep -q "/swapfile"; then
            sudo fallocate -l 2G /swapfile
            sudo chmod 600 /swapfile
            sudo mkswap /swapfile
            sudo swapon /swapfile
            
            # Make swap permanent
            echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
            
            print_success "Swap file created (2GB)"
        else
            print_status "Swap file already exists"
        fi
    else
        print_success "Sufficient memory available (${TOTAL_MEM}MB)"
    fi
}

# Function to verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    # Check Docker
    if docker --version >/dev/null 2>&1; then
        print_success "Docker: $(docker --version)"
    else
        print_error "Docker verification failed"
        return 1
    fi
    
    # Check Docker Compose
    if docker-compose --version >/dev/null 2>&1; then
        print_success "Docker Compose: $(docker-compose --version)"
    else
        print_error "Docker Compose verification failed"
        return 1
    fi
    
    # Check if user is in docker group
    if groups $USER | grep -q docker; then
        print_success "User added to docker group"
    else
        print_warning "User not in docker group. You may need to log out and back in."
    fi
    
    return 0
}

# Function to show next steps
show_next_steps() {
    echo ""
    print_success "VPS setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Log out and log back in to apply group changes:"
    echo "   exit"
    echo "   ssh $USER@$(hostname -I | awk '{print $1}')"
    echo ""
    echo "2. Clone your repository:"
    echo "   git clone <your-repository-url>"
    echo "   cd <repository-directory>"
    echo ""
    echo "3. Deploy the application:"
    echo "   ./start.sh deploy"
    echo ""
    echo "4. View logs:"
    echo "   ./start.sh logs"
    echo ""
    echo "Useful commands:"
    echo "  ./start.sh status    # Check bot status"
    echo "  ./start.sh restart   # Restart bot"
    echo "  ./start.sh stop      # Stop bot"
    echo "  ./start.sh backup    # Create backup"
    echo ""
}

# Main function
main() {
    echo "=========================================="
    echo "  Quotex Trading Bot - VPS Setup Script"
    echo "=========================================="
    echo ""
    
    # Check if not running as root
    check_root
    
    # Check OS
    check_os
    
    # Update system
    update_system
    
    # Install essential packages
    install_essentials
    
    # Install Docker
    install_docker
    
    # Install Docker Compose
    install_docker_compose
    
    # Configure firewall
    configure_firewall
    
    # Create swap if needed
    create_swap
    
    # Verify installation
    if verify_installation; then
        show_next_steps
    else
        print_error "Installation verification failed. Please check the errors above."
        exit 1
    fi
}

# Run main function
main "$@"