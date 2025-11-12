# DermaGPT Setup Guide

Complete setup instructions for running the DermaGPT backend on macOS.

---

## Prerequisites

- macOS
- Python 3.8+
- Homebrew (install from https://brew.sh)
- OpenAI API Key
- Pinecone API Key

---

## Step 1: Install PostgreSQL

```bash
# Install PostgreSQL using Homebrew
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Create the database
psql postgres -c "CREATE DATABASE dermagpt;"
```

**Verify PostgreSQL is running:**
```bash
brew services list
# Should show postgresql@15 as "started"
```

---

## Step 2: Clone and Navigate to Project

```bash
cd /Users/vansh/Documents/GitHub/Dermat_gpt
```

---

## Step 3: Set Up Python Virtual Environment

```bash
# Activate the existing virtual environment
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

---

## Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Pinecone Configuration (for vector search)
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=your_pinecone_index_name

# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dermagpt

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=168

# Optional: Web Search
SERPAPI_API_KEY=your_serpapi_key_here

# Session Configuration
SESSION_INACTIVE_HOURS=6
```

**Required API Keys:**
- **OpenAI API Key:** Get from https://platform.openai.com/api-keys
- **Pinecone API Key:** Get from https://www.pinecone.io/
- **SerpAPI Key (Optional):** Get from https://serpapi.com/

---

## Step 5: Initialize Database

Run database migrations:

```bash
# Apply database migrations
alembic upgrade head
```

**Alternative:** If migrations fail, create tables directly:
```bash
python create_tables.py
```

---

## Step 6: (Optional) Create Vector Embeddings

If you need to populate Pinecone with product/blog embeddings:

```bash
cd data
python create_embeddings.py
cd ..
```

---

## Step 7: Start the Backend Server

```bash
# Method 1: Using Python module
python -m app.main

# Method 2: Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on **http://localhost:8000**

---

## Step 8: Verify Installation

Open your browser and navigate to:

- **API Documentation:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

You should see the FastAPI interactive documentation.

---

## Troubleshooting

### PostgreSQL Connection Issues

**Check if PostgreSQL is running:**
```bash
brew services list
```

**Restart PostgreSQL:**
```bash
brew services restart postgresql@15
```

**Test database connection:**
```bash
psql -d dermagpt -c "SELECT 1;"
```

### Reset Database

If you need to start fresh:
```bash
psql postgres -c "DROP DATABASE dermagpt;"
psql postgres -c "CREATE DATABASE dermagpt;"
alembic upgrade head
```

### Python Package Installation Issues

```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Reinstall dependencies
pip install -r requirements.txt
```

### Port Already in Use

If port 8000 is already in use:
```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or run on a different port
uvicorn app.main:app --reload --port 8001
```

---

## Quick Start (After Initial Setup)

Once everything is configured, use these commands to start the server:

```bash
cd /Users/vansh/Documents/GitHub/Dermat_gpt
source venv/bin/activate
python -m app.main
```

---

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token

### Chat
- `POST /chat` - Send chat message (requires authentication)
- `GET /conversations` - Get conversation history

### Health Check
- `GET /` - API health check

---

## Development Mode

For development with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The `--reload` flag automatically restarts the server when code changes are detected.

---

## Stopping the Server

- Press `Ctrl+C` in the terminal where the server is running
- To stop PostgreSQL: `brew services stop postgresql@15`

---

## Notes

- The virtual environment (`venv`) is already created in the project
- Database tables are automatically created on first startup
- JWT tokens expire after 168 hours (7 days) by default
- CORS is enabled for all origins (configure for production use)

