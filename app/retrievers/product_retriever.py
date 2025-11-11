"""
Product Retriever with filtering capabilities.
"""

from typing import List, Dict, Any, Optional
from .base_retriever import BaseRetriever


class ProductRetriever(BaseRetriever):
    """
    Specialized retriever for product recommendations with filtering.
    """

    def __init__(self, top_k: int = 5, **kwargs):
        """
        Initialize product retriever.

        Args:
            top_k: Number of products to retrieve
            **kwargs: Additional arguments for BaseRetriever
        """
        super().__init__(namespace="products", top_k=top_k, **kwargs)

    def retrieve_products(
        self,
        query: str,
        top_k: Optional[int] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        category: Optional[str] = None,
        min_rating: Optional[float] = None,
        brand: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve products with optional filters.

        Args:
            query: Search query
            top_k: Number of results
            max_price: Maximum price filter
            min_price: Minimum price filter
            category: Product category filter
            min_rating: Minimum rating filter
            brand: Brand name filter

        Returns:
            List of product results
        """
        # Build Pinecone metadata filters
        filters = {}

        if max_price is not None:
            filters["price"] = {"$lte": max_price}

        if min_price is not None:
            if "price" in filters:
                filters["price"]["$gte"] = min_price
            else:
                filters["price"] = {"$gte": min_price}

        if category:
            filters["category"] = {"$eq": category}

        if min_rating is not None:
            filters["rating"] = {"$gte": min_rating}

        if brand:
            filters["brand"] = {"$eq": brand}

        # Use base retriever with filters
        pinecone_filter = filters if filters else None
        return self.retrieve(query, top_k, pinecone_filter)

    def _format_result(self, metadata: Dict[str, Any]) -> str:
        """
        Format product metadata into readable text.

        Args:
            metadata: Product metadata

        Returns:
            Formatted product description
        """
        name = metadata.get("name", "Unknown Product")
        brand = metadata.get("brand", "Unknown Brand")
        price = metadata.get("price", 0)
        rating = metadata.get("rating", 0)
        rating_count = metadata.get("rating_count", 0)
        category = metadata.get("category", "")
        url = metadata.get("url", "")

        parts = [
            f"Product: {name}",
            f"Brand: {brand}",
            f"Price: ₹{price:.2f}",
        ]

        if rating > 0:
            parts.append(f"Rating: {rating:.1f}/5 ({rating_count} reviews)")

        if category:
            parts.append(f"Category: {category}")

        if url:
            parts.append(f"URL: {url}")

        return "\n".join(parts)

    def get_recommendations_by_concern(
        self,
        concern: str,
        top_k: int = 3,
        max_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Get product recommendations for a specific skin concern.

        Args:
            concern: Skin concern (e.g., "acne", "dry skin", "anti-aging")
            top_k: Number of products to recommend
            max_price: Optional price limit

        Returns:
            Dictionary with results and formatted context
        """
        query = f"products for {concern} treatment and care"
        results = self.retrieve_products(
            query=query,
            top_k=top_k,
            max_price=max_price,
        )

        return {
            "results": results,
            "context": self._format_recommendations(results),
            "concern": concern,
        }

    def _format_recommendations(self, results: List[Dict[str, Any]]) -> str:
        """Format product recommendations for LLM context."""
        if not results:
            return "No products found matching the criteria."

        parts = ["Here are the recommended products:\n"]

        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            parts.append(f"{i}. {self._format_result(metadata)}")
            parts.append(f"   Relevance Score: {result['score']:.3f}\n")

        return "\n".join(parts)

