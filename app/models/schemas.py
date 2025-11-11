"""
Pydantic schemas for API requests and responses.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    query: str = Field(
        ...,
        description="User's skincare query",
        min_length=1,
        max_length=1000,
        examples=["Recommend a moisturizer under 1200 for oily skin"],
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID for conversation history",
        examples=["user123_session456"],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the benefits of vitamin C serum?",
                "session_id": "user123_session456",
            }
        }


class Source(BaseModel):
    """Source information for citations."""

    type: str = Field(
        ...,
        description="Type of source (product, blog, web)",
        examples=["product", "blog", "web"],
    )
    tool: Optional[str] = Field(
        default=None,
        description="Tool used to retrieve the source",
        examples=["semantic_product_search", "blog_search", "web_search"],
    )
    observation: Optional[str] = Field(
        default=None,
        description="Observation or content from the source",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "product",
                "tool": "semantic_product_search",
                "observation": "Found 5 products matching your criteria...",
            }
        }


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    response: str = Field(
        ...,
        description="Generated response from the agent",
    )
    agent_used: str = Field(
        ...,
        description="Which agent handled the query",
        examples=["product", "blog", "supervisor"],
    )
    sources: List[Source] = Field(
        default_factory=list,
        description="List of sources used to generate the response",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for this conversation",
    )
    conversation_id: Optional[int] = Field(
        default=None,
        description="Database conversation ID",
    )
    message_id: Optional[int] = Field(
        default=None,
        description="Database message ID",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if something went wrong",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on your requirements, I recommend these moisturizers...",
                "agent_used": "product",
                "sources": [
                    {
                        "type": "product",
                        "tool": "semantic_product_search",
                        "observation": "Found 3 products...",
                    }
                ],
                "session_id": "user123_session456",
                "conversation_id": 123,
                "message_id": 456,
                "error": None,
            }
        }


class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""

    status: str = Field(
        ...,
        description="Overall health status",
        examples=["healthy", "degraded", "unhealthy"],
    )
    orchestrator: str = Field(..., description="Orchestrator status")
    product_agent: str = Field(..., description="Product agent status")
    blog_agent: str = Field(..., description="Blog agent status")
    supervisor_agent: str = Field(..., description="Supervisor agent status")
    model: str = Field(..., description="LLM model being used")
    timestamp: Optional[str] = Field(
        default=None,
        description="Timestamp of health check",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "orchestrator": "healthy",
                "product_agent": "healthy",
                "blog_agent": "healthy",
                "supervisor_agent": "healthy",
                "model": "gpt-3.5-turbo",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserRegister(BaseModel):
    """Schema for user registration."""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username for the account",
        examples=["john_doe"],
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Password for the account",
    )
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (can include _ and -)')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "securePassword123",
            }
        }


class UserLogin(BaseModel):
    """Schema for user login."""
    
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "securePassword123",
            }
        }


class Token(BaseModel):
    """Schema for JWT token response."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": 1,
                "username": "john_doe",
            }
        }


class UserResponse(BaseModel):
    """Schema for user information response."""
    
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "john_doe",
                "created_at": "2024-01-15T10:30:00",
            }
        }


# ============================================================================
# Conversation & Message Schemas
# ============================================================================

class MessageResponse(BaseModel):
    """Schema for a single message."""
    
    id: int = Field(..., description="Message ID")
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    sources: List[Source] = Field(default_factory=list, description="Sources used")
    agent_used: Optional[str] = Field(None, description="Agent that handled this message")
    timestamp: datetime = Field(..., description="Message timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "role": "user",
                "content": "Recommend a moisturizer",
                "sources": [],
                "agent_used": None,
                "timestamp": "2024-01-15T10:30:00",
            }
        }


class ConversationSummary(BaseModel):
    """Schema for conversation summary in list view."""
    
    id: int = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    message_count: int = Field(..., description="Number of messages in conversation")
    last_message: Optional[str] = Field(None, description="Preview of last message")
    last_active_at: datetime = Field(..., description="Last activity timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Skincare routine advice",
                "message_count": 8,
                "last_message": "Thank you for the recommendations!",
                "last_active_at": "2024-01-15T14:30:00",
                "created_at": "2024-01-15T10:30:00",
            }
        }


class ConversationDetail(BaseModel):
    """Schema for full conversation details."""
    
    id: int = Field(..., description="Conversation ID")
    title: str = Field(..., description="Conversation title")
    messages: List[MessageResponse] = Field(..., description="All messages in conversation")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_active_at: datetime = Field(..., description="Last activity timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Skincare routine advice",
                "messages": [
                    {
                        "id": 1,
                        "role": "user",
                        "content": "Help me with skincare",
                        "sources": [],
                        "agent_used": None,
                        "timestamp": "2024-01-15T10:30:00",
                    }
                ],
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T14:30:00",
                "last_active_at": "2024-01-15T14:30:00",
            }
        }


class NewConversationRequest(BaseModel):
    """Schema for creating a new conversation."""
    
    title: Optional[str] = Field(
        default="New Conversation",
        max_length=255,
        description="Title for the conversation",
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Acne treatment advice",
            }
        }


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list."""
    
    conversations: List[ConversationSummary] = Field(..., description="List of conversations")
    total: int = Field(..., description="Total number of conversations")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversations": [],
                "total": 10,
                "page": 1,
                "page_size": 20,
            }
        }

