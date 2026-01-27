#!/bin/bash

# Launch Docker + Cloudflare Tunnel in one command
# Ctrl+C stops both the tunnel and Docker services

echo "Starting OpenHeart with Cloudflare Tunnel..."

# Start cloudflared in the background
cloudflared tunnel --config tunnel-config.yml run &
TUNNEL_PID=$!

# Kill tunnel when script exits
trap "kill $TUNNEL_PID 2>/dev/null; exit" INT TERM EXIT

echo "Tunnel daemon started (PID $TUNNEL_PID)"
echo "Starting Docker services..."

docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up
