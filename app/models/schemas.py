"""
Pydantic schemas for API requests and responses.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


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

