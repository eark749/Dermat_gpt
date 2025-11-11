"""
Conversation service for managing chat sessions and messages.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.db.models import User, Conversation, Message
from dotenv import load_dotenv

load_dotenv()

# Configuration
SESSION_INACTIVE_HOURS = int(os.getenv("SESSION_INACTIVE_HOURS", "6"))


class ConversationService:
    """Service for managing conversations and messages."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_active_conversation(
        self, 
        user: User,
        conversation_id: Optional[int] = None
    ) -> Conversation:
        """
        Get an existing conversation or create a new one based on activity.
        
        If conversation_id is provided, use that.
        Otherwise, check if the user has an active conversation (active within SESSION_INACTIVE_HOURS).
        If not, create a new one.
        
        Args:
            user: User object
            conversation_id: Optional specific conversation ID
            
        Returns:
            Conversation object
        """
        if conversation_id:
            # Get specific conversation
            result = await self.db.execute(
                select(Conversation)
                .where(Conversation.id == conversation_id, Conversation.user_id == user.id)
            )
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found or access denied")
            
            return conversation
        
        # Check for active conversation
        inactive_threshold = datetime.utcnow() - timedelta(hours=SESSION_INACTIVE_HOURS)
        
        result = await self.db.execute(
            select(Conversation)
            .where(
                Conversation.user_id == user.id,
                Conversation.last_active_at > inactive_threshold
            )
            .order_by(desc(Conversation.last_active_at))
            .limit(1)
        )
        conversation = result.scalar_one_or_none()
        
        if conversation:
            return conversation
        
        # Create new conversation if none active
        return await self.create_conversation(user, title="New Conversation")
    
    async def create_conversation(
        self, 
        user: User, 
        title: str = "New Conversation"
    ) -> Conversation:
        """
        Create a new conversation for a user.
        
        Args:
            user: User object
            title: Conversation title
            
        Returns:
            Created conversation
        """
        conversation = Conversation(
            user_id=user.id,
            title=title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_active_at=datetime.utcnow(),
        )
        
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
    
    async def add_message(
        self,
        conversation: Conversation,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        agent_used: Optional[str] = None,
    ) -> Message:
        """
        Add a message to a conversation.
        
        Args:
            conversation: Conversation object
            role: Message role ('user' or 'assistant')
            content: Message content
            sources: Optional list of sources used
            agent_used: Optional agent that handled this message
            
        Returns:
            Created message
        """
        message = Message(
            conversation_id=conversation.id,
            role=role,
            content=content,
            sources=sources or [],
            agent_used=agent_used,
            timestamp=datetime.utcnow(),
        )
        
        # Update conversation's last_active_at
        conversation.last_active_at = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()
        
        # Auto-generate title from first user message
        if role == "user" and conversation.title == "New Conversation":
            # Check if this is the first message in the conversation
            result = await self.db.execute(
                select(func.count(Message.id))
                .where(Message.conversation_id == conversation.id)
            )
            message_count = result.scalar()
            
            # Only update title if this is the first message
            if message_count == 0:
                # Use first 50 characters of the message as title
                title = content[:50].strip()
                if len(content) > 50:
                    title += "..."
                conversation.title = title
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def get_conversation_with_messages(
        self, 
        conversation_id: int, 
        user: User
    ) -> Optional[Conversation]:
        """
        Get a conversation with all its messages.
        
        Args:
            conversation_id: Conversation ID
            user: User object (for authorization)
            
        Returns:
            Conversation with messages or None
        """
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id, Conversation.user_id == user.id)
        )
        
        return result.scalar_one_or_none()
    
    async def list_user_conversations(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Conversation], int]:
        """
        List all conversations for a user with pagination.
        
        Args:
            user: User object
            page: Page number (1-indexed)
            page_size: Number of conversations per page
            
        Returns:
            Tuple of (conversations list, total count)
        """
        # Get total count
        count_result = await self.db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.user_id == user.id)
        )
        total = count_result.scalar()
        
        # Get paginated conversations
        offset = (page - 1) * page_size
        
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.user_id == user.id)
            .order_by(desc(Conversation.last_active_at))
            .limit(page_size)
            .offset(offset)
        )
        
        conversations = result.scalars().all()
        
        return list(conversations), total
    
    async def delete_conversation(
        self, 
        conversation_id: int, 
        user: User
    ) -> bool:
        """
        Delete a conversation (and all its messages via cascade).
        
        Args:
            conversation_id: Conversation ID
            user: User object (for authorization)
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user.id)
        )
        
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            return False
        
        await self.db.delete(conversation)
        await self.db.commit()
        
        return True
    
    async def get_conversation_history_for_agent(
        self,
        conversation: Conversation,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for agent context.
        
        Args:
            conversation: Conversation object
            limit: Maximum number of recent messages to return
            
        Returns:
            List of message dicts with 'role' and 'content'
        """
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(desc(Message.timestamp))
            .limit(limit)
        )
        
        messages = result.scalars().all()
        
        # Reverse to get chronological order
        messages = list(reversed(messages))
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

