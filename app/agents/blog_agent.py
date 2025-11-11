"""
Blog/Educational Content Agent - Custom implementation (no LangChain).
"""

import sys
from pathlib import Path
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.custom_agent import CustomAgent, CustomTool
from app.retrievers import BlogRetriever
from app.prompts.agent_prompts import BLOG_AGENT_PROMPT


def create_blog_agent(
    model_name: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    openai_api_key: Optional[str] = None,
) -> CustomAgent:
    """
    Create a Blog/Educational Content Agent.
    
    Args:
        model_name: OpenAI model to use
        temperature: Temperature for response generation
        openai_api_key: OpenAI API key
        
    Returns:
        CustomAgent instance
    """
    # Initialize retriever
    retriever = BlogRetriever(top_k=3)
    
    # Define tool function
    def blog_search(query: str, top_k: int = 3) -> str:
        """Search through blog articles for educational content."""
        try:
            results = retriever.retrieve_blogs(query=query, top_k=top_k)
            
            if not results:
                return "No relevant blog articles found for your query."
            
            # Deduplicate by article title
            deduplicated = retriever.get_deduplicated_articles(results)
            
            # Format results
            output_parts = [f"Found {len(deduplicated)} relevant article(s) about '{query}':\n"]
            
            for i, result in enumerate(deduplicated, 1):
                metadata = result["metadata"]
                output_parts.append(f"\n{i}. {metadata.get('title', 'Untitled Article')}")
                
                if metadata.get("author"):
                    output_parts.append(f"   Author: {metadata.get('author')}")
                
                if metadata.get("date"):
                    output_parts.append(f"   Published: {metadata.get('date')}")
                
                if metadata.get("tags"):
                    output_parts.append(f"   Tags: {metadata.get('tags')}")
                
                if metadata.get("url"):
                    output_parts.append(f"   Read more: {metadata.get('url')}")
                
                output_parts.append(f"   Relevance: {result['score']:.3f}")
                output_parts.append("")
            
            output_parts.append("\nNote: Always cite these articles when providing information to users.")
            
            return "\n".join(output_parts)
        except Exception as e:
            return f"Error searching blog articles: {str(e)}"
    
    # Create tool
    tools = [
        CustomTool(
            name="blog_search",
            description="Search through 1500+ skincare blog articles for educational information. Use when users want to learn about skincare topics, ingredients, routines, or treatments. Returns relevant article excerpts with titles and URLs.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query about skincare topics (e.g., 'benefits of vitamin C serum')"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of articles to retrieve (default 3)",
                        "default": 3
                    }
                },
                "required": ["query"]
            },
            function=blog_search
        ),
    ]
    
    # Create and return agent
    return CustomAgent(
        name="BlogAgent",
        system_prompt=BLOG_AGENT_PROMPT.replace("{chat_history}", "").replace("{input}", "").replace("{agent_scratchpad}", ""),
        tools=tools,
        model=model_name,
        temperature=temperature,
        openai_api_key=openai_api_key,
    )
