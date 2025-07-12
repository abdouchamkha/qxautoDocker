#!/bin/bash

# Quotex Trading Bot - VPS Startup Script
# This script automates the deployment process

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to create directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p config logs sessions
    chmod 755 config logs sessions
    print_success "Directories created successfully"
}

# Function to build and start the application
deploy_application() {
    print_status "Building Docker image..."
    docker-compose build --no-cache
    
    print_status "Starting the application..."
    docker-compose up -d
    
    print_success "Application deployed successfully"
}

# Function to check application status
check_status() {
    print_status "Checking application status..."
    
    if docker-compose ps | grep -q "Up"; then
        print_success "Application is running"
        docker-compose ps
    else
        print_error "Application failed to start"
        docker-compose logs
        exit 1
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing application logs..."
    docker-compose logs -f
}

# Function to stop application
stop_application() {
    print_status "Stopping application..."
    docker-compose down
    print_success "Application stopped"
}

# Function to restart application
restart_application() {
    print_status "Restarting application..."
    docker-compose restart
    print_success "Application restarted"
}

# Function to update application
update_application() {
    print_status "Updating application..."
    
    # Stop current version
    docker-compose down
    
    # Pull latest changes
    if [ -d ".git" ]; then
        git pull origin main
    else
        print_warning "Not a git repository. Skipping git pull."
    fi
    
    # Rebuild and start
    docker-compose build --no-cache
    docker-compose up -d
    
    print_success "Application updated successfully"
}

# Function to backup data
backup_data() {
    print_status "Creating backup..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if [ -d "config" ]; then
        cp -r config/* "$BACKUP_DIR/" 2>/dev/null || true
    fi
    
    if [ -d "sessions" ]; then
        cp -r sessions/* "$BACKUP_DIR/" 2>/dev/null || true
    fi
    
    if [ -d "logs" ]; then
        tar -czf "$BACKUP_DIR/logs.tar.gz" logs/ 2>/dev/null || true
    fi
    
    print_success "Backup created: $BACKUP_DIR"
}

# Function to show help
show_help() {
    echo "Quotex Trading Bot - VPS Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy     - Deploy the application (build and start)"
    echo "  start      - Start the application"
    echo "  stop       - Stop the application"
    echo "  restart    - Restart the application"
    echo "  status     - Check application status"
    echo "  logs       - Show application logs"
    echo "  update     - Update and restart the application"
    echo "  backup     - Create backup of configuration and data"
    echo "  help       - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy    # First time deployment"
    echo "  $0 logs      # View real-time logs"
    echo "  $0 restart   # Restart the bot"
}

# Main script logic
main() {
    # Check if Docker is available
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found. Please run this script from the project directory."
        exit 1
    fi
    
    # Parse command line arguments
    case "${1:-deploy}" in
        "deploy")
            check_docker
            create_directories
            deploy_application
            check_status
            print_success "Deployment completed successfully!"
            print_status "Use '$0 logs' to view logs"
            ;;
        "start")
            check_docker
            deploy_application
            check_status
            ;;
        "stop")
            stop_application
            ;;
        "restart")
            check_docker
            restart_application
            check_status
            ;;
        "status")
            check_status
            ;;
        "logs")
            show_logs
            ;;
        "update")
            check_docker
            backup_data
            update_application
            check_status
            ;;
        "backup")
            backup_data
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"