"""
Chat history and conversation management API routes.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User
from app.models.schemas import (
    ConversationSummary,
    ConversationDetail,
    ConversationListResponse,
    NewConversationRequest,
    MessageResponse,
)
from app.services.conversation_service import ConversationService
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/conversations", tags=["Chat History"])


@router.get(
    "",
    response_model=ConversationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List user conversations",
    description="Get paginated list of all conversations for the authenticated user",
)
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationListResponse:
    """
    List all conversations for the current user.
    
    Args:
        page: Page number
        page_size: Number of items per page
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Paginated list of conversations
    """
    service = ConversationService(db)
    conversations, total = await service.list_user_conversations(
        user=current_user,
        page=page,
        page_size=page_size,
    )
    
    # Build summaries
    summaries = []
    for conv in conversations:
        # Get message count and last message
        message_count = len(conv.messages)
        last_message = None
        
        if conv.messages:
            # Messages are ordered by timestamp
            last_msg = conv.messages[-1]
            last_message = last_msg.content[:100] + ("..." if len(last_msg.content) > 100 else "")
        
        summaries.append(
            ConversationSummary(
                id=conv.id,
                title=conv.title,
                message_count=message_count,
                last_message=last_message,
                last_active_at=conv.last_active_at,
                created_at=conv.created_at,
            )
        )
    
    return ConversationListResponse(
        conversations=summaries,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/new",
    response_model=ConversationDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create new conversation",
    description="Manually create a new conversation",
)
async def create_new_conversation(
    request: NewConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail:
    """
    Create a new conversation.
    
    Args:
        request: New conversation request with optional title
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Created conversation
    """
    service = ConversationService(db)
    conversation = await service.create_conversation(
        user=current_user,
        title=request.title or "New Conversation",
    )
    
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        messages=[],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        last_active_at=conversation.last_active_at,
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetail,
    status_code=status.HTTP_200_OK,
    summary="Get conversation",
    description="Get a specific conversation with all its messages",
)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationDetail:
    """
    Get a conversation with all messages.
    
    Args:
        conversation_id: Conversation ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Conversation with messages
        
    Raises:
        HTTPException: If conversation not found or access denied
    """
    service = ConversationService(db)
    conversation = await service.get_conversation_with_messages(
        conversation_id=conversation_id,
        user=current_user,
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied",
        )
    
    # Convert messages to response format
    messages = [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            sources=msg.sources,
            agent_used=msg.agent_used,
            timestamp=msg.timestamp,
        )
        for msg in conversation.messages
    ]
    
    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        messages=messages,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        last_active_at=conversation.last_active_at,
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete a conversation and all its messages",
)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a conversation.
    
    Args:
        conversation_id: Conversation ID
        current_user: Authenticated user
        db: Database session
        
    Raises:
        HTTPException: If conversation not found or access denied
    """
    service = ConversationService(db)
    deleted = await service.delete_conversation(
        conversation_id=conversation_id,
        user=current_user,
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied",
        )
    
    return None

