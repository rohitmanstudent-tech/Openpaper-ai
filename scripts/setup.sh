#!/bin/bash
set -e

echo "========================================"
echo "  OpenPaper AI - Project Setup"
echo "========================================"

echo ""
echo "1. Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "Error: Docker is not installed."; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo "Error: Docker Compose is not installed."; exit 1; }
echo "   Docker and Docker Compose found."

echo ""
echo "2. Setting up environment..."
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "   Created backend/.env from .env.example"
fi

echo ""
echo "3. Building and starting services..."
docker compose up -d --build

echo ""
echo "4. Waiting for services to be healthy..."
sleep 10

echo ""
echo "5. Pulling default Ollama model..."
docker compose exec -T ollama ollama pull llama3.1 2>/dev/null || echo "   Note: Ollama model pull will continue in background"

echo ""
echo "========================================"
echo "  Setup complete!"
echo "========================================"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "  Default services:"
echo "  - PostgreSQL on port 5432"
echo "  - Redis on port 6379"
echo "  - Qdrant on port 6333"
echo "  - Ollama on port 11434"
echo ""
echo "  Run 'docker compose logs -f' to follow logs"
echo "========================================"
