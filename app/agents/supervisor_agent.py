"""
Supervisor Agent - Custom implementation (no LangChain).
Routes queries and provides web search.
"""

import os
from typing import Dict, Any, Optional

from app.agents.custom_agent import CustomAgent, CustomTool
from app.prompts.agent_prompts import SUPERVISOR_PROMPT

try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None


def create_supervisor_agent(
    model_name: str = "gpt-3.5-turbo",
    temperature: float = 0.3,
    openai_api_key: Optional[str] = None,
) -> CustomAgent:
    """
    Create a Supervisor Agent with web search capability.
    
    Args:
        model_name: OpenAI model to use
        temperature: Lower temperature for consistent routing
        openai_api_key: OpenAI API key
        
    Returns:
        CustomAgent instance
    """
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    
    # Define web search tool
    def web_search(query: str, num_results: int = 3) -> str:
        """Search the web for general skincare information."""
        if not serpapi_key:
            return "Web search is not available. Please set SERPAPI_API_KEY in environment variables."
        
        if GoogleSearch is None:
            return "Web search library not installed. Please run: pip install google-search-results"
        
        try:
            # Append skincare context
            search_query = f"{query} skincare dermatology"
            
            # Execute search
            search = GoogleSearch({
                "q": search_query,
                "api_key": serpapi_key,
                "num": num_results,
            })
            results = search.get_dict()
            
            # Extract results
            organic_results = results.get("organic_results", [])
            
            if not organic_results:
                return f"No web search results found for: {query}"
            
            # Format results
            output_parts = [f"Web search results for '{query}':\n"]
            
            for i, result in enumerate(organic_results[:num_results], 1):
                title = result.get("title", "No title")
                link = result.get("link", "")
                snippet = result.get("snippet", "No description available")
                
                output_parts.append(f"\n{i}. {title}")
                output_parts.append(f"   {snippet}")
                output_parts.append(f"   Source: {link}")
                output_parts.append("")
            
            output_parts.append("\nNote: This information is from web search. Always verify with reliable sources.")
            
            return "\n".join(output_parts)
        except Exception as e:
            return f"Error performing web search: {str(e)}"
    
    # Create tool
    tools = [
        CustomTool(
            name="web_search",
            description="Search the web for general skincare information, latest trends, or medical knowledge. Use when the query is about general dermatology, latest research, ingredients, or medical conditions requiring current information.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for general skincare information"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of search results (default 3)",
                        "default": 3
                    }
                },
                "required": ["query"]
            },
            function=web_search
        ),
    ]
    
    # Create and return agent
    return CustomAgent(
        name="SupervisorAgent",
        system_prompt=SUPERVISOR_PROMPT.replace("{chat_history}", "").replace("{input}", "").replace("{agent_scratchpad}", ""),
        tools=tools,
        model=model_name,
        temperature=temperature,
        openai_api_key=openai_api_key,
    )


def classify_intent(query: str) -> str:
    """
    Classify the intent of a query to determine which agent to route to.
    
    Args:
        query: User query
        
    Returns:
        One of: "product", "blog", "general"
    """
    query_lower = query.lower()
    
    # Product keywords
    product_keywords = [
        "recommend", "suggest", "buy", "purchase", "product", "best",
        "under", "below", "price", "budget", "cheap", "affordable",
        "₹", "rupees", "inr",
        "moisturizer", "cleanser", "sunscreen", "serum", "cream",
        "face wash", "toner", "mask", "oil", "gel",
        "where to buy", "show me", "need a", "looking for",
        "brand", "shop"
    ]
    
    # Blog/educational keywords
    blog_keywords = [
        "how to", "what is", "why does", "explain", "learn",
        "article", "blog", "read about", "guide", "tips",
        "benefits of", "causes of", "treatment for", "cure for",
        "routine for", "steps for", "regimen", "process",
        "information", "tell me about", "help me understand"
    ]
    
    # Count matches
    product_score = sum(1 for keyword in product_keywords if keyword in query_lower)
    blog_score = sum(1 for keyword in blog_keywords if keyword in query_lower)
    
    # Determine intent
    if product_score > blog_score:
        return "product"
    elif blog_score > product_score:
        return "blog"
    else:
        # If tied or no clear winner, check for specific patterns
        if any(word in query_lower for word in ["recommend", "buy", "purchase", "price", "under", "below"]):
            return "product"
        elif any(word in query_lower for word in ["how", "what", "why", "explain"]):
            return "blog"
        else:
            return "general"


def route_query(query: str) -> Dict[str, Any]:
    """
    Analyze query and return routing decision.
    
    Args:
        query: User query
        
    Returns:
        Dictionary with routing information
    """
    intent = classify_intent(query)
    
    return {
        "intent": intent,
        "query": query,
        "agent": intent if intent in ["product", "blog"] else "supervisor",
    }
