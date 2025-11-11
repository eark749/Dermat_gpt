"""
Script to create database tables for DermaGPT.
Run this script to set up the database schema.
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models to register them with Base
from app.db.models import Base, User, Conversation, Message

async def create_tables():
    """Create all database tables."""
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://dermagpt_user:dermagpt123@localhost:5432/dermagpt")
    
    print(f"Connecting to database...")
    print(f"Database URL: {database_url.replace('dermagpt123', '***')}")  # Hide password in logs
    
    try:
        # Create async engine
        engine = create_async_engine(database_url, echo=True)
        
        # Create all tables
        async with engine.begin() as conn:
            print("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
        
        print("Database tables created successfully!")
        print("\nTables created:")
        print("  - users (for authentication)")
        print("  - conversations (for chat sessions)")
        print("  - messages (for chat history)")
        
        # Close engine
        await engine.dispose()
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check your DATABASE_URL in .env file")
        print("3. Ensure the database 'dermagpt' exists")
        print("4. Verify user 'dermagpt_user' has proper permissions")
        return False
    
    return True

async def test_connection():
    """Test database connection and show existing tables."""
    
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://dermagpt_user:dermagpt123@localhost:5432/dermagpt")
    
    try:
        engine = create_async_engine(database_url)
        
        async with engine.begin() as conn:
            # Check if tables exist
            result = await conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = result.fetchall()
            
            if tables:
                print("\nExisting tables in database:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\nNo tables found in database")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("DermaGPT Database Setup")
    print("=" * 60)
    
    # Test connection first
    print("\n1. Testing database connection...")
    if not asyncio.run(test_connection()):
        print("\nCannot connect to database. Please check your setup.")
        exit(1)
    
    # Create tables
    print("\n2. Creating database tables...")
    if asyncio.run(create_tables()):
        print("\nDatabase setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: uvicorn app.main:app --reload")
        print("2. Visit: http://localhost:8000/docs")
        print("3. Register a user and start chatting!")
    else:
        print("\nDatabase setup failed. Please check the errors above.")
