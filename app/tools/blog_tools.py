"""
Blog search tool for the Blog Agent.
"""

import sys
from pathlib import Path
from typing import Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.retrievers import BlogRetriever


class BlogSearchInput(BaseModel):
    """Input schema for blog search."""

    query: str = Field(
        description="Natural language query about skincare topics, ingredients, routines, or concerns"
    )
    top_k: int = Field(
        default=3, description="Number of blog articles/chunks to retrieve (default 3)"
    )


class BlogSearchTool(BaseTool):
    """
    Tool for searching educational skincare blog content.
    Retrieves relevant articles and information from the blog database.
    """

    name: str = "blog_search"
    description: str = """
    Search through 1500+ skincare blog articles for educational information.
    Use this when users want to learn about skincare topics, ingredients, routines, or treatments.
    
    Examples:
    - "how to treat acne naturally"
    - "benefits of vitamin C serum"
    - "best skincare routine for oily skin"
    - "what causes dark circles"
    
    Returns relevant article excerpts with titles, authors, and URLs for citation.
    """
    args_schema: type[BaseModel] = BlogSearchInput
    retriever: BlogRetriever = Field(default=None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.retriever is None:
            self.retriever = BlogRetriever(top_k=3)

    def _run(self, query: str, top_k: int = 3) -> str:
        """Execute blog search."""
        try:
            results = self.retriever.retrieve_blogs(query=query, top_k=top_k)

            if not results:
                return "No relevant blog articles found for your query."

            # Deduplicate by article title (since blogs are chunked)
            deduplicated = self.retriever.get_deduplicated_articles(results)

            # Format results
            output_parts = [
                f"Found {len(deduplicated)} relevant article(s) about '{query}':\n"
            ]

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

                # If we have content in the chunk, show a snippet
                # (Note: content is not in metadata, it's in the vector DB as the embedded text)
                output_parts.append("")

            # Add note about citations
            output_parts.append(
                "\nNote: Always cite these articles when providing information to users."
            )

            return "\n".join(output_parts)

        except Exception as e:
            return f"Error searching blog articles: {str(e)}"

    async def _arun(self, query: str, top_k: int = 3) -> str:
        """Async version."""
        return self._run(query, top_k)

