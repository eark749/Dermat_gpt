"""
Web search tool using SerpAPI for general skincare knowledge.
"""

import os
from typing import Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv

try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None


load_dotenv()


class WebSearchInput(BaseModel):
    """Input schema for web search."""

    query: str = Field(
        description="Search query for general skincare information not in the database"
    )
    num_results: int = Field(
        default=3, description="Number of search results to return (default 3)"
    )


class WebSearchTool(BaseTool):
    """
    Tool for searching the web using SerpAPI.
    Use this for general skincare knowledge or information not in the product/blog database.
    """

    name: str = "web_search"
    description: str = """
    Search the web for general skincare information, latest trends, or medical knowledge.
    Use this when the query is:
    - About general dermatology or medical conditions
    - About latest skincare trends or news
    - About ingredients or treatments requiring current information
    - Too general or doesn't fit product/blog categories
    
    Examples:
    - "latest research on retinol"
    - "what is niacinamide"
    - "dermatologist recommended treatments for rosacea"
    
    Returns top search results with snippets and links.
    """
    args_schema: type[BaseModel] = WebSearchInput
    serpapi_api_key: Optional[str] = Field(default=None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.serpapi_api_key is None:
            self.serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        
        if not self.serpapi_api_key:
            print("Warning: SERPAPI_API_KEY not found. Web search will not work.")

    def _run(self, query: str, num_results: int = 3) -> str:
        """Execute web search."""
        if not self.serpapi_api_key:
            return (
                "Web search is not available. Please set SERPAPI_API_KEY in environment variables. "
                "For now, I can only help with product recommendations and blog content from our database."
            )

        if GoogleSearch is None:
            return (
                "Web search library not installed. Please run: pip install google-search-results"
            )

        try:
            # Append skincare context to improve results
            search_query = f"{query} skincare dermatology"

            # Execute search
            search = GoogleSearch({
                "q": search_query,
                "api_key": self.serpapi_api_key,
                "num": num_results,
            })
            results = search.get_dict()

            # Extract organic results
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

            output_parts.append(
                "\nNote: This information is from web search. Always verify with reliable sources."
            )

            return "\n".join(output_parts)

        except Exception as e:
            return f"Error performing web search: {str(e)}"

    async def _arun(self, query: str, num_results: int = 3) -> str:
        """Async version."""
        return self._run(query, num_results)

