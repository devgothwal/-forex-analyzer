#!/bin/bash

# Forex Analyzer Deployment Script
# Automated deployment for development and production environments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="forex-analyzer"
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is required but not installed"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is required but not installed"
        exit 1
    fi
    
    log_success "All requirements satisfied"
}

setup_backend() {
    log_info "Setting up backend..."
    
    cd backend
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Create necessary directories
    mkdir -p uploads cache models
    
    log_success "Backend setup completed"
    cd ..
}

setup_frontend() {
    log_info "Setting up frontend..."
    
    cd frontend
    
    # Install Node.js dependencies
    log_info "Installing Node.js dependencies..."
    npm install
    
    log_success "Frontend setup completed"
    cd ..
}

start_backend() {
    log_info "Starting backend server..."
    
    cd backend
    
    # Start FastAPI server
    uvicorn app.main:app --reload --host 0.0.0.0 --port $BACKEND_PORT &
    BACKEND_PID=$!
    
    # Wait for backend to start
    sleep 5
    
    # Check if backend is running
    if curl -f http://localhost:$BACKEND_PORT/health &> /dev/null; then
        log_success "Backend started successfully on port $BACKEND_PORT"
        echo $BACKEND_PID > backend.pid
    else
        log_error "Failed to start backend"
        exit 1
    fi
    
    cd ..
}

start_frontend() {
    log_info "Starting frontend server..."
    
    cd frontend
    
    # Set environment variables
    export REACT_APP_API_URL=http://localhost:$BACKEND_PORT/api/v1
    
    # Start React development server
    npm start &
    FRONTEND_PID=$!
    
    # Wait for frontend to start
    sleep 10
    
    # Check if frontend is running
    if curl -f http://localhost:$FRONTEND_PORT &> /dev/null; then
        log_success "Frontend started successfully on port $FRONTEND_PORT"
        echo $FRONTEND_PID > frontend.pid
    else
        log_warning "Frontend may still be starting..."
    fi
    
    cd ..
}

deploy_docker() {
    log_info "Deploying with Docker..."
    
    cd deployment/docker
    
    # Build and start containers
    docker-compose up -d --build
    
    # Wait for services to start
    sleep 30
    
    # Check health
    if docker-compose ps | grep -q "Up"; then
        log_success "Docker deployment completed successfully"
        log_info "Frontend: http://localhost"
        log_info "Backend: http://localhost:8000"
    else
        log_error "Docker deployment failed"
        docker-compose logs
        exit 1
    fi
    
    cd ../..
}

stop_services() {
    log_info "Stopping services..."
    
    # Stop backend
    if [ -f backend/backend.pid ]; then
        kill $(cat backend/backend.pid) 2>/dev/null || true
        rm backend/backend.pid
    fi
    
    # Stop frontend
    if [ -f frontend/frontend.pid ]; then
        kill $(cat frontend/frontend.pid) 2>/dev/null || true
        rm frontend/frontend.pid
    fi
    
    # Stop Docker containers
    if [ -f deployment/docker/docker-compose.yml ]; then
        cd deployment/docker
        docker-compose down 2>/dev/null || true
        cd ../..
    fi
    
    log_success "Services stopped"
}

show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  dev       Start development environment"
    echo "  prod      Deploy production environment with Docker"
    echo "  stop      Stop all services"
    echo "  setup     Setup dependencies only"
    echo "  check     Check system requirements"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 dev        # Start development servers"
    echo "  $0 prod       # Deploy with Docker"
    echo "  $0 stop       # Stop all services"
}

# Main script logic
case "${1:-}" in
    "dev")
        log_info "Starting development environment..."
        check_requirements
        setup_backend
        setup_frontend
        start_backend
        start_frontend
        
        log_success "Development environment started!"
        log_info "Frontend: http://localhost:$FRONTEND_PORT"
        log_info "Backend: http://localhost:$BACKEND_PORT"
        log_info "API Docs: http://localhost:$BACKEND_PORT/api/docs"
        log_info ""
        log_info "Press Ctrl+C to stop services"
        
        # Wait for interrupt
        trap stop_services INT
        wait
        ;;
        
    "prod")
        log_info "Deploying production environment..."
        check_requirements
        
        # Check if Docker is available
        if ! command -v docker &> /dev/null; then
            log_error "Docker is required for production deployment"
            exit 1
        fi
        
        deploy_docker
        
        log_success "Production deployment completed!"
        log_info "Access the application at http://localhost"
        ;;
        
    "setup")
        log_info "Setting up dependencies..."
        check_requirements
        setup_backend
        setup_frontend
        log_success "Setup completed!"
        ;;
        
    "check")
        check_requirements
        log_success "System check passed!"
        ;;
        
    "stop")
        stop_services
        ;;
        
    "help"|"")
        show_usage
        ;;
        
    *)
        log_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac