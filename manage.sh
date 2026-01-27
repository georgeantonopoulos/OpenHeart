#!/bin/bash

# OpenHeart Environment Manager
# Usage: ./manage.sh [local|tunnel]

MODE=${1:-local} # Default to local

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[OpenHeart]${NC} $1"
}

error() {
    echo -e "${RED}[Error]${NC} $1"
}

cleanup() {
    echo ""
    log "Stopping services..."
    # Only stop containers, don't remove volumes to preserve data
    docker compose down
    
    if [ -n "$TUNNEL_PID" ]; then
        log "Stopping Cloudflare Tunnel..."
        kill $TUNNEL_PID 2>/dev/null
    fi
    log "Shutdown complete."
}

# Trap interrupts for clean shutdown
trap cleanup INT TERM EXIT

# Ensure we're in the project root
cd "$(dirname "$0")"

if [ "$MODE" == "tunnel" ]; then
    log "Switching to ${YELLOW}TUNNEL${NC} mode (Public Access)"
    
    # Check for cloudflared
    if ! command -v cloudflared &> /dev/null; then
        error "cloudflared tool is not installed or not in PATH."
        error "Please install it or use local mode."
        exit 1
    fi

    # Check for config
    if [ ! -f "tunnel-config.yml" ]; then
        error "tunnel-config.yml not found."
        exit 1
    fi

    log "Starting Cloudflare Tunnel..."
    cloudflared tunnel --config tunnel-config.yml run &
    TUNNEL_PID=$!
    
    # Wait for tunnel initialization
    sleep 3
    
    log "Starting Docker containers with tunnel configuration..."
    log "Frontend: https://openheart-demo.sequencyapp.com"
    log "Backend:  https://openheart-api.sequencyapp.com"
    
    # Force recreate to ensure env vars are picked up
    docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up --force-recreate --remove-orphans

else
    log "Switching to ${GREEN}LOCAL${NC} mode (localhost only)"
    
    log "Starting Docker containers with local configuration..."
    log "Frontend: http://localhost:3000"
    log "Backend:  http://localhost:8000"
    
    # Force recreate to ensure env vars are picked up
    docker compose -f docker-compose.yml up --force-recreate --remove-orphans
fi
