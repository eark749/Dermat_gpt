"""
API routes for DermaGPT chat endpoint.
"""

from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import ChatRequest, ChatResponse, HealthResponse, Source
from app.db.database import get_db
from app.db.models import User
from app.auth.dependencies import get_current_user
from app.services.conversation_service import ConversationService


router = APIRouter()

# Global orchestrator instance (initialized in main.py)
orchestrator = None


def set_orchestrator(orch):
    """Set the global orchestrator instance."""
    global orchestrator
    orchestrator = orch


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with DermaGPT",
    description="Send a skincare query and get recommendations or information from specialized agents (requires authentication)",
)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Process a chat query through the multi-agent system.

    The query will be automatically routed to:
    - **Product Agent**: For product recommendations and shopping queries
    - **Blog Agent**: For educational content and skincare information
    - **Supervisor Agent**: For general queries requiring web search

    Args:
        request: ChatRequest with query and optional conversation_id
        current_user: Authenticated user
        db: Database session

    Returns:
        ChatResponse with agent's answer, sources, and metadata
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Orchestrator not initialized. Please check server logs.",
        )

    try:
        # Get conversation service
        conv_service = ConversationService(db)
        
        # Parse conversation_id from session_id if provided
        conversation_id: Optional[int] = None
        if request.session_id:
            try:
                conversation_id = int(request.session_id)
            except ValueError:
                pass  # If it's not a valid int, ignore it
        
        # Get or create active conversation
        conversation = await conv_service.get_or_create_active_conversation(
            user=current_user,
            conversation_id=conversation_id,
        )
        
        # Get conversation history for context
        chat_history = await conv_service.get_conversation_history_for_agent(
            conversation=conversation,
            limit=10,
        )
        
        # Save user message
        user_message = await conv_service.add_message(
            conversation=conversation,
            role="user",
            content=request.query,
        )
        
        # Process the query with orchestrator
        result = orchestrator.process_query(
            query=request.query,
            chat_history=chat_history if chat_history else None,
        )

        # Convert sources to Source objects
        sources = []
        for src in result.get("sources", []):
            if isinstance(src, dict):
                sources.append(Source(**src))
            else:
                sources.append(src)
        
        # Save assistant response
        assistant_message = await conv_service.add_message(
            conversation=conversation,
            role="assistant",
            content=result.get("response", "No response generated"),
            sources=[src.model_dump() if hasattr(src, 'model_dump') else src for src in sources],
            agent_used=result.get("agent_used", "unknown"),
        )

        # Create response
        response = ChatResponse(
            response=result.get("response", "No response generated"),
            agent_used=result.get("agent_used", "unknown"),
            sources=sources,
            session_id=str(conversation.id),
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            error=result.get("error"),
        )

        return response

    except ValueError as e:
        # Handle conversation not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        # Log the error
        print(f"❌ Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()

        # Return error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}",
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health status of all agents and the orchestrator",
)
async def health() -> HealthResponse:
    """
    Check the health of the DermaGPT system.

    Returns:
        HealthResponse with status of all components
    """
    if not orchestrator:
        return HealthResponse(
            status="unhealthy",
            orchestrator="not_initialized",
            product_agent="unknown",
            blog_agent="unknown",
            supervisor_agent="unknown",
            model="unknown",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    try:
        health_data = orchestrator.health_check()

        # Determine overall status
        agent_statuses = [
            health_data.get("product_agent"),
            health_data.get("blog_agent"),
            health_data.get("supervisor_agent"),
        ]

        if all(s == "healthy" for s in agent_statuses):
            overall_status = "healthy"
        elif any(s == "healthy" for s in agent_statuses):
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return HealthResponse(
            status=overall_status,
            orchestrator=health_data.get("orchestrator", "unknown"),
            product_agent=health_data.get("product_agent", "unknown"),
            blog_agent=health_data.get("blog_agent", "unknown"),
            supervisor_agent=health_data.get("supervisor_agent", "unknown"),
            model=health_data.get("model", "unknown"),
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    except Exception as e:
        print(f"❌ Error in health check: {e}")
        return HealthResponse(
            status="error",
            orchestrator="error",
            product_agent="error",
            blog_agent="error",
            supervisor_agent="error",
            model="error",
            timestamp=datetime.utcnow().isoformat() + "Z",
        )


@router.get(
    "/",
    summary="API Root",
    description="Welcome endpoint with API information",
)
async def root() -> Dict[str, Any]:
    """
    Root endpoint with API information.

    Returns:
        Welcome message and available endpoints
    """
    return {
        "message": "Welcome to DermaGPT API",
        "version": "1.0.0",
        "description": "Multi-agent RAG system for skincare recommendations and information",
        "endpoints": {
            "chat": "/chat - POST - Send skincare queries",
            "health": "/health - GET - Check system health",
            "docs": "/docs - GET - Interactive API documentation",
        },
        "agents": {
            "product": "Product recommendations with semantic search, metadata filtering, and price filtering",
            "blog": "Educational content from 1500+ skincare articles",
            "supervisor": "General queries with web search capability",
        },
    }

