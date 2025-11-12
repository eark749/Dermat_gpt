#!/bin/bash

# DermaGPT Docker Setup Script
# This script helps set up the Docker environment

echo "🐳 DermaGPT Docker Setup"
echo "========================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file from template if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.template .env
    echo "✅ .env file created. Please edit it with your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - PINECONE_API_KEY" 
    echo "   - SERPAPI_API_KEY"
    echo ""
    echo "⚠️  Edit .env file before continuing!"
    read -p "Press Enter after editing .env file..."
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data
chmod 755 logs

# Check if data files exist
if [ -f "data/DermaGPT Product Database (1)_cleaned.csv" ]; then
    echo "✅ Product data file found"
else
    echo "⚠️  Product CSV file not found in data/ directory"
    echo "   Make sure you have the cleaned CSV file in the data/ directory"
fi

# Build and start services
echo "🚀 Building and starting Docker services..."
docker-compose build
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker-compose ps

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T dermagpt-api alembic upgrade head

# Test health endpoint
echo "🔍 Testing health endpoint..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy!"
else
    echo "❌ API health check failed. Check logs:"
    echo "   docker-compose logs dermagpt-api"
fi

echo ""
echo "🎉 Setup complete!"
echo "📖 Access API documentation: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo "📋 View logs: docker-compose logs -f"
echo ""
echo "🛑 To stop: docker-compose down"
echo "🔄 To restart: docker-compose restart"
