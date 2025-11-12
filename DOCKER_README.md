# 🐳 DermaGPT Docker Setup Guide

This guide will help you run DermaGPT on any computer using Docker.

## 📋 Prerequisites

1. **Docker & Docker Compose** installed on your system
   - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Docker Compose is included with Docker Desktop

2. **API Keys** (Required):
   - OpenAI API Key
   - Pinecone API Key  
   - SerpAPI Key (for web search)

3. **Pinecone Index** created with 1024 dimensions

## 🚀 Quick Start

### 1. Clone and Setup Environment

```bash
# Navigate to the project directory
cd Dermat_gpt

# Copy environment template
cp env.template .env

# Edit .env file with your API keys
nano .env  # or use any text editor
```

### 2. Configure Environment Variables

Edit the `.env` file and fill in these **REQUIRED** values:

```bash
# API Keys (MUST be filled)
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
SERPAPI_API_KEY=your_serpapi_key_here

# Pinecone Configuration
PINECONE_INDEX_NAME=dermagpt-rag
PINECONE_ENVIRONMENT=us-east-1

# JWT Secret (generate a secure random string)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
```

### 3. Start the Application

```bash
# Start all services (development mode)
docker-compose up -d

# View logs
docker-compose logs -f dermagpt-api

# Check service status
docker-compose ps
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec dermagpt-api alembic upgrade head
```

### 5. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Chat Endpoint**: http://localhost:8000/chat (requires authentication)

## 📊 Service Architecture

The Docker setup includes:

- **dermagpt-api**: FastAPI application (port 8000)
- **postgres**: PostgreSQL database (port 5432)
- **redis**: Redis cache (port 6379)
- **nginx**: Reverse proxy (port 80) - production only

## 🔧 Development Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild application
docker-compose build dermagpt-api

# View logs
docker-compose logs -f [service-name]

# Execute commands in container
docker-compose exec dermagpt-api bash

# Reset database
docker-compose down -v
docker-compose up -d
```

## 🏭 Production Deployment

For production, use the nginx profile:

```bash
# Start with nginx reverse proxy
docker-compose --profile production up -d

# Access via nginx
curl http://localhost/health
```

## 📁 Data Volumes

The setup mounts these volumes:

- `./logs:/app/logs` - Application logs
- `./data:/app/data:ro` - Product data (read-only)
- `postgres_data` - Database persistence
- `redis_data` - Redis persistence

## 🔍 Troubleshooting

### Common Issues:

1. **Port conflicts**:
   ```bash
   # Change ports in .env file
   API_PORT=8001
   DATABASE_PORT=5433
   ```

2. **Permission issues**:
   ```bash
   # Fix log directory permissions
   mkdir -p logs
   chmod 755 logs
   ```

3. **Database connection issues**:
   ```bash
   # Check database status
   docker-compose logs postgres
   
   # Reset database
   docker-compose down -v
   docker-compose up -d postgres
   ```

4. **API key issues**:
   - Verify all API keys in `.env` file
   - Check Pinecone index exists with correct dimensions
   - Ensure OpenAI API key has sufficient credits

### Health Checks:

```bash
# Check all services
docker-compose ps

# Test API health
curl http://localhost:8000/health

# Check database connection
docker-compose exec postgres pg_isready -U dermagpt_user -d dermagpt
```

## 🔒 Security Notes

- Never commit `.env` file to version control
- Use strong passwords for production
- Generate secure JWT secret keys
- Consider using Docker secrets for production
- Enable SSL/TLS for production deployments

## 📈 Monitoring

View real-time logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f dermagpt-api

# Database logs
docker-compose logs -f postgres
```

## 🛑 Stopping Services

```bash
# Stop services (keep data)
docker-compose down

# Stop and remove volumes (lose data)
docker-compose down -v

# Stop and remove everything
docker-compose down -v --rmi all
```

## 💡 Tips

1. **First run**: Wait for database to initialize before starting API
2. **Development**: Use `docker-compose logs -f` to monitor startup
3. **Production**: Use nginx profile for better performance
4. **Backup**: Regularly backup postgres_data volume
5. **Updates**: Rebuild containers after code changes

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify environment variables in `.env`
3. Ensure all required API keys are valid
4. Check Docker and Docker Compose versions
5. Verify port availability on your system
