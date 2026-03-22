#!/bin/bash

# Barclays Credit Intelligence Platform - Startup Script
# This script starts all services in the correct order

set -e  # Exit on error

echo "========================================="
echo "Barclays Credit Intelligence Platform"
echo "Starting all services..."
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}Please edit .env with your configuration before continuing${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo ""
echo "Starting services with Docker Compose..."
echo ""

# Start services
docker-compose up --build -d

echo ""
echo -e "${GREEN}✓ Services started successfully!${NC}"
echo ""
echo "========================================="
echo "Service Status:"
echo "========================================="

# Wait a moment for services to initialize
sleep 5

# Check service health
echo ""
echo "Checking service health..."
echo ""

# Check PostgreSQL
if docker-compose ps | grep -q "barclays_postgres.*Up"; then
    echo -e "${GREEN}✓ PostgreSQL: Running${NC}"
else
    echo -e "${RED}✗ PostgreSQL: Not running${NC}"
fi

# Check Redis
if docker-compose ps | grep -q "barclays_redis.*Up"; then
    echo -e "${GREEN}✓ Redis: Running${NC}"
else
    echo -e "${RED}✗ Redis: Not running${NC}"
fi

# Check Backend
if docker-compose ps | grep -q "barclays_backend.*Up"; then
    echo -e "${GREEN}✓ Backend API: Running${NC}"
else
    echo -e "${RED}✗ Backend API: Not running${NC}"
fi

# Check Frontend
if docker-compose ps | grep -q "barclays_frontend.*Up"; then
    echo -e "${GREEN}✓ Frontend: Running${NC}"
else
    echo -e "${RED}✗ Frontend: Not running${NC}"
fi

echo ""
echo "========================================="
echo "Access Points:"
echo "========================================="
echo ""
echo "🌐 User Portal:     http://localhost:3000"
echo "🔧 Admin Portal:    http://localhost:3000/admin"
echo "📡 Backend API:     http://localhost:8000"
echo "📚 API Docs:        http://localhost:8000/docs"
echo "❤️  Health Check:   http://localhost:8000/api/v1/health"
echo ""
echo "========================================="
echo "Useful Commands:"
echo "========================================="
echo ""
echo "View logs:          docker-compose logs -f"
echo "Stop services:      docker-compose down"
echo "Restart services:   docker-compose restart"
echo "View status:        docker-compose ps"
echo ""
echo "========================================="
echo ""

# Test backend health
echo "Testing backend health..."
sleep 10  # Give backend time to start

if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is healthy and responding${NC}"
else
    echo -e "${YELLOW}⚠ Backend is starting up (this may take a minute)${NC}"
    echo "Run 'docker-compose logs backend' to check progress"
fi

echo ""
echo -e "${GREEN}Setup complete! Visit http://localhost:3000 to get started.${NC}"
echo ""
