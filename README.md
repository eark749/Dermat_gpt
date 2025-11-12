# DermaGPT - Multi-Agent RAG System for Skincare

A FastAPI-based multi-agent system for skincare recommendations and information retrieval.

---

## Quick Start

### 1. Install PostgreSQL

```bash
brew install postgresql@15
brew services start postgresql@15
psql postgres -c "CREATE DATABASE dermagpt;"
```

### 2. Activate Virtual Environment

```bash
cd /Users/vansh/Documents/GitHub/Dermat_gpt
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=your_pinecone_index_name
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dermagpt
JWT_SECRET_KEY=your-secret-key-here
```

### 5. Initialize Database

```bash
alembic upgrade head
```

### 6. Run the Server

```bash
python -m app.main
```

Server will be running at: **http://localhost:8000**

API Documentation: **http://localhost:8000/docs**

---

## Daily Run Commands

After initial setup, just run:

```bash
cd /Users/vansh/Documents/GitHub/Dermat_gpt
source venv/bin/activate
python -m app.main
```

---

## API Usage

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

### 3. Chat (with token)

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"message": "Recommend a moisturizer for dry skin"}'
```

---

## Stopping the Server

- Press `Ctrl+C` in terminal
- Stop PostgreSQL: `brew services stop postgresql@15`

---

## Troubleshooting

**PostgreSQL not running:**
```bash
brew services restart postgresql@15
```

**Port 8000 in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Reset database:**
```bash
psql postgres -c "DROP DATABASE dermagpt; CREATE DATABASE dermagpt;"
alembic upgrade head
```

---

## Project Structure

```
Dermat_gpt/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── agents/              # Multi-agent system
│   ├── api/                 # API routes
│   ├── auth/                # Authentication
│   ├── db/                  # Database models and connection
│   ├── retrievers/          # Vector search retrievers
│   ├── tools/               # Agent tools
│   └── services/            # Business logic
├── data/                    # Data files and embeddings
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
└── README.md               # This file
```

---

## Features

- 🤖 **Multi-Agent System**: Product, Blog, and Supervisor agents
- 🔍 **RAG (Retrieval Augmented Generation)**: Vector search with Pinecone
- 🔐 **JWT Authentication**: Secure user authentication
- 💬 **Chat History**: Persistent conversation management
- 🌐 **Web Search Integration**: Real-time information retrieval
- 📊 **PostgreSQL Database**: Async database operations

---

## Requirements

- Python 3.8+
- PostgreSQL 15
- OpenAI API Key
- Pinecone API Key
- macOS (or Linux/Windows with modifications)

---

For detailed setup instructions, see [SETUP.md](SETUP.md)

