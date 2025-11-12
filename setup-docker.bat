@echo off
REM DermaGPT Docker Setup Script for Windows
REM This script helps set up the Docker environment

echo 🐳 DermaGPT Docker Setup
echo ========================

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Create .env file from template if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env.template .env
    echo ✅ .env file created. Please edit it with your API keys:
    echo    - OPENAI_API_KEY
    echo    - PINECONE_API_KEY
    echo    - SERPAPI_API_KEY
    echo.
    echo ⚠️  Edit .env file before continuing!
    pause
) else (
    echo ✅ .env file already exists
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist logs mkdir logs
if not exist data mkdir data

REM Check if data files exist
if exist "data\DermaGPT Product Database (1)_cleaned.csv" (
    echo ✅ Product data file found
) else (
    echo ⚠️  Product CSV file not found in data\ directory
    echo    Make sure you have the cleaned CSV file in the data\ directory
)

REM Build and start services
echo 🚀 Building and starting Docker services...
docker-compose build
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check service status
echo 📊 Service Status:
docker-compose ps

REM Run database migrations
echo 🗄️  Running database migrations...
docker-compose exec -T dermagpt-api alembic upgrade head

REM Test health endpoint
echo 🔍 Testing health endpoint...
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ API is healthy!
) else (
    echo ❌ API health check failed. Check logs:
    echo    docker-compose logs dermagpt-api
)

echo.
echo 🎉 Setup complete!
echo 📖 Access API documentation: http://localhost:8000/docs
echo 🔍 Health check: http://localhost:8000/health
echo 📋 View logs: docker-compose logs -f
echo.
echo 🛑 To stop: docker-compose down
echo 🔄 To restart: docker-compose restart
pause
