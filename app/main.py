"""
Main FastAPI application for DermaGPT.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.routes import router, set_orchestrator
from app.api.auth_routes import router as auth_router
from app.api.chat_routes import router as chat_router
from app.agents.orchestrator import DermaGPTOrchestrator
from app.db.database import init_db, close_db


# Load environment variables
load_dotenv()


# Global orchestrator
orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    print("\n" + "=" * 60)
    print("🚀 Starting DermaGPT API Server")
    print("=" * 60 + "\n")

    global orchestrator

    try:
        # Initialize database
        print("Initializing database...")
        await init_db()
        
        # Initialize orchestrator
        orchestrator = DermaGPTOrchestrator(
            model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=0.7,
        )

        # Set orchestrator in routes
        set_orchestrator(orchestrator)

        print("\n" + "=" * 60)
        print("✅ DermaGPT API Server is ready!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Failed to initialize: {e}\n")
        print("The server will start but some features may not be available.")
        print("Please check your environment variables and API keys.\n")
        import traceback
        traceback.print_exc()

    yield

    # Shutdown
    print("\n" + "=" * 60)
    print("🛑 Shutting down DermaGPT API Server")
    print("=" * 60 + "\n")
    
    # Close database connections
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="DermaGPT API",
    description="""
    Multi-Agent RAG System for Skincare Recommendations and Information
    
    ## Features
    - **User Authentication**: JWT-based authentication for secure access
    - **Chat History**: Persistent conversation management with auto-session handling
    - **Product Recommendations**: Semantic search, metadata filtering, and price-based filtering
    - **Educational Content**: Access to 1500+ skincare blog articles
    - **General Knowledge**: Web search for latest skincare information
    
    ## Agents
    - **Product Agent**: Handles product recommendations using three composable tools
    - **Blog Agent**: Retrieves educational content from blog database
    - **Supervisor Agent**: Routes queries and provides web search for general questions
    
    ## Authentication
    1. Register: POST `/auth/register` with username and password
    2. Login: POST `/auth/login` to get JWT token
    3. Use token in Authorization header: `Bearer <token>`
    
    ## Usage
    Send authenticated POST request to `/chat` with your skincare query.
    The system will automatically route it to the appropriate specialist agent.
    Conversations are auto-managed - inactive conversations (>6 hours) trigger new sessions.
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(router, tags=["DermaGPT"])


# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

