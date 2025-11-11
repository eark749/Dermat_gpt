"""
Blog Retriever for educational content.
"""

from typing import List, Dict, Any, Optional
from .base_retriever import BaseRetriever


class BlogRetriever(BaseRetriever):
    """
    Specialized retriever for blog articles and educational content.
    """

    def __init__(self, top_k: int = 3, **kwargs):
        """
        Initialize blog retriever.

        Args:
            top_k: Number of blog chunks to retrieve
            **kwargs: Additional arguments for BaseRetriever
        """
        super().__init__(namespace="blogs", top_k=top_k, **kwargs)

    def retrieve_blogs(
        self,
        query: str,
        top_k: Optional[int] = None,
        author: Optional[str] = None,
        tags: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve blog articles with optional filters.

        Args:
            query: Search query
            top_k: Number of results
            author: Filter by author
            tags: Filter by tags (comma-separated)

        Returns:
            List of blog results
        """
        # Build Pinecone metadata filters
        filters = {}

        if author:
            filters["author"] = {"$eq": author}

        if tags:
            # For tags, we might want to search for any matching tag
            filters["tags"] = {"$eq": tags}

        pinecone_filter = filters if filters else None
        return self.retrieve(query, top_k, pinecone_filter)

    def _format_result(self, metadata: Dict[str, Any]) -> str:
        """
        Format blog metadata into readable text.

        Args:
            metadata: Blog metadata

        Returns:
            Formatted blog description
        """
        title = metadata.get("title", "Untitled")
        author = metadata.get("author", "Unknown Author")
        date = metadata.get("date", "")
        tags = metadata.get("tags", "")
        url = metadata.get("url", "")
        chunk_index = metadata.get("chunk_index", 0)
        total_chunks = metadata.get("total_chunks", 1)

        parts = [f"Article: {title}"]

        if author:
            parts.append(f"Author: {author}")

        if date:
            parts.append(f"Published: {date}")

        if tags:
            parts.append(f"Tags: {tags}")

        if total_chunks > 1:
            parts.append(f"Section: Part {chunk_index + 1} of {total_chunks}")

        if url:
            parts.append(f"URL: {url}")

        return "\n".join(parts)

    def search_by_topic(
        self, topic: str, top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Search for blog articles by topic.

        Args:
            topic: Topic to search for
            top_k: Number of articles to return

        Returns:
            Dictionary with results and formatted context
        """
        query = f"information about {topic} skincare treatment and tips"
        results = self.retrieve_blogs(query=query, top_k=top_k)

        return {
            "results": results,
            "context": self._format_articles(results),
            "topic": topic,
        }

    def _format_articles(self, results: List[Dict[str, Any]]) -> str:
        """Format blog articles for LLM context."""
        if not results:
            return "No articles found matching the query."

        parts = ["Here are relevant articles:\n"]

        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            parts.append(f"{i}. {self._format_result(metadata)}")
            parts.append(f"   Relevance Score: {result['score']:.3f}\n")

        return "\n".join(parts)

    def get_deduplicated_articles(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate results by article title (since blogs are chunked).

        Args:
            results: List of retrieval results

        Returns:
            Deduplicated list with highest scoring chunk per article
        """
        seen_titles = {}

        for result in results:
            title = result["metadata"].get("title", "")
            if not title:
                continue

            # Keep the highest scoring chunk for each article
            if title not in seen_titles or result["score"] > seen_titles[title]["score"]:
                seen_titles[title] = result

        return list(seen_titles.values())

