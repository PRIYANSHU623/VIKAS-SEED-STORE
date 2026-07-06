#!/bin/bash
# ============================================================
# KrishiSathi Production Deployment Quick Start
# ============================================================
# This script automates the basic production setup

set -e

echo "============================================================"
echo "KrishiSathi Production Deployment Setup"
echo "============================================================"

# Check prerequisites
check_requirements() {
    echo ""
    echo "Checking prerequisites..."
    
    command -v docker >/dev/null 2>&1 || {
        echo "❌ Docker not found. Please install Docker."
        exit 1
    }
    
    command -v docker-compose >/dev/null 2>&1 || {
        echo "❌ Docker Compose not found. Please install Docker Compose."
        exit 1
    }
    
    command -v git >/dev/null 2>&1 || {
        echo "❌ Git not found. Please install Git."
        exit 1
    }
    
    echo "✓ All prerequisites met"
}

# Generate SSL certificates
setup_ssl() {
    echo ""
    echo "Setting up SSL certificates..."
    
    if [ ! -f "nginx/ssl/cert.pem" ]; then
        chmod +x generate-ssl.sh
        ./generate-ssl.sh
        echo "✓ SSL certificates generated"
    else
        echo "✓ SSL certificates already exist"
    fi
}

# Setup environment
setup_environment() {
    echo ""
    echo "Setting up environment variables..."
    
    if [ ! -f ".env.production" ]; then
        cp .env.example .env.production
        echo "⚠ Created .env.production - PLEASE EDIT WITH YOUR VALUES"
        echo "  - DATABASE_URL"
        echo "  - SECRET_KEY (generate: python3 -c \"import secrets; print(secrets.token_hex(32))\")"
        echo "  - GEMINI_API_KEY"
        echo "  - CORS_ORIGINS"
        return 1
    else
        echo "✓ Environment file exists"
    fi
}

# Create necessary directories
setup_directories() {
    echo ""
    echo "Creating directories..."
    
    mkdir -p nginx/ssl
    mkdir -p backend/logs
    mkdir -p backend/app/uploads
    mkdir -p backups
    
    echo "✓ Directories created"
}

# Build Docker images
build_images() {
    echo ""
    echo "Building Docker images..."
    
    docker compose build --pull
    
    echo "✓ Docker images built"
}

# Start services
start_services() {
    echo ""
    echo "Starting services..."
    
    docker compose up -d
    
    echo "✓ Services started"
}

# Health check
health_check() {
    echo ""
    echo "Performing health check..."
    
    sleep 10
    
    # Check backend
    if curl -f http://localhost:8000/api/health >/dev/null 2>&1; then
        echo "✓ Backend is healthy"
    else
        echo "❌ Backend health check failed"
        docker compose logs backend
        return 1
    fi
    
    # Check database
    if docker compose exec -T postgres psql -U krishiuser -d krishisathi -c "SELECT 1" >/dev/null 2>&1; then
        echo "✓ Database is healthy"
    else
        echo "❌ Database health check failed"
        docker compose logs postgres
        return 1
    fi
}

# Display summary
summary() {
    echo ""
    echo "============================================================"
    echo "✓ KrishiSathi Production Setup Complete!"
    echo "============================================================"
    echo ""
    echo "Access Points:"
    echo "  - Frontend:    https://localhost (or your domain)"
    echo "  - Backend API: https://localhost/api (or your domain/api)"
    echo "  - API Docs:    https://localhost/api/docs (development only)"
    echo "  - Health:      https://localhost/api/health"
    echo ""
    echo "Useful Commands:"
    echo "  - View logs:   docker compose logs -f"
    echo "  - Stop:        docker compose down"
    echo "  - Status:      docker compose ps"
    echo "  - Backup DB:   ./backend/scripts/backup-db.sh"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure production domain in Nginx"
    echo "  2. Setup Let's Encrypt SSL certificates"
    echo "  3. Configure automated backups"
    echo "  4. Setup monitoring and alerts"
    echo ""
    echo "Full Guide: See DEPLOYMENT.md"
    echo "============================================================"
}

# Main execution
main() {
    check_requirements
    setup_directories
    setup_ssl
    
    if ! setup_environment; then
        echo ""
        echo "⚠ Please configure .env.production and run the script again"
        exit 1
    fi
    
    read -p "Ready to build and start services? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
    
    build_images
    start_services
    health_check
    summary
}

# Run main
main
