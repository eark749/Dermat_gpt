"""
Product search tools for the Product Agent.

These three tools can be used independently or combined:
- SemanticProductSearchTool: Vector search for meaning-based queries
- MetadataFilterTool: Filter by category, skin type, brand
- PriceRangeFilterTool: Filter by price constraints
"""

import sys
from pathlib import Path
from typing import Optional

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.retrievers import ProductRetriever


class SemanticProductSearchInput(BaseModel):
    """Input schema for semantic product search."""

    query: str = Field(
        description="Natural language description of the product (e.g., 'hydrating cream for dry patches')"
    )
    top_k: int = Field(
        default=5, description="Number of products to retrieve (default 5)"
    )


class SemanticProductSearchTool(BaseTool):
    """
    Tool for semantic vector search of products.
    Finds products based on meaning and context, not just keywords.
    """

    name: str = "semantic_product_search"
    description: str = """
    Search for skincare products using natural language descriptions.
    Use this when the user describes what they want (e.g., "moisturizer for dry skin", "anti-aging serum").
    This tool understands meaning and finds relevant products even without exact keyword matches.
    
    Input should be a natural language query describing the product type or benefits.
    """
    args_schema: type[BaseModel] = SemanticProductSearchInput
    retriever: ProductRetriever = Field(default=None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.retriever is None:
            self.retriever = ProductRetriever(top_k=5)

    def _run(self, query: str, top_k: int = 5) -> str:
        """Execute semantic search."""
        try:
            results = self.retriever.retrieve_products(query=query, top_k=top_k)

            if not results:
                return "No products found matching your query."

            # Format results
            output_parts = [f"Found {len(results)} products:\n"]

            for i, result in enumerate(results, 1):
                metadata = result["metadata"]
                output_parts.append(f"\n{i}. {metadata.get('name', 'Unknown Product')}")
                output_parts.append(f"   Brand: {metadata.get('brand', 'Unknown')}")
                output_parts.append(
                    f"   Price: ₹{metadata.get('price', 0):.2f}"
                )
                rating = metadata.get("rating", 0)
                if rating > 0:
                    output_parts.append(
                        f"   Rating: {rating:.1f}/5 ({metadata.get('rating_count', 0)} reviews)"
                    )
                output_parts.append(
                    f"   Category: {metadata.get('category', 'N/A')}"
                )
                if metadata.get("url"):
                    output_parts.append(f"   URL: {metadata.get('url')}")
                output_parts.append(f"   Relevance: {result['score']:.3f}")

            return "\n".join(output_parts)

        except Exception as e:
            return f"Error searching products: {str(e)}"

    async def _arun(self, query: str, top_k: int = 5) -> str:
        """Async version."""
        return self._run(query, top_k)


class MetadataFilterInput(BaseModel):
    """Input schema for metadata filtering."""

    query: str = Field(
        description="The product search query",
        default="skincare products"
    )
    category: Optional[str] = Field(
        default=None,
        description="Product category (e.g., 'moisturizer', 'cleanser', 'serum', 'sunscreen')",
    )
    brand: Optional[str] = Field(
        default=None, description="Brand name to filter by"
    )
    skin_type: Optional[str] = Field(
        default=None,
        description="Skin type (e.g., 'oily', 'dry', 'sensitive', 'combination')",
    )
    top_k: int = Field(default=5, description="Number of results (default 5)")


class MetadataFilterTool(BaseTool):
    """
    Tool for filtering products by metadata (category, brand, skin type).
    Use this to narrow down products by specific attributes.
    """

    name: str = "metadata_filter"
    description: str = """
    Filter products by specific attributes like category, brand, or skin type.
    Use this when the user mentions specific product types, brands, or skin types.
    
    Examples:
    - "serums for oily skin" -> category='serum', skin_type='oily'
    - "Minimalist brand products" -> brand='Minimalist'
    - "cleanser for sensitive skin" -> category='cleanser', skin_type='sensitive'
    
    Can be combined with semantic search for better results.
    """
    args_schema: type[BaseModel] = MetadataFilterInput
    retriever: ProductRetriever = Field(default=None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.retriever is None:
            self.retriever = ProductRetriever(top_k=5)

    def _run(
        self,
        query: str = "skincare products",
        category: Optional[str] = None,
        brand: Optional[str] = None,
        skin_type: Optional[str] = None,
        top_k: int = 5,
    ) -> str:
        """Execute metadata filtering."""
        try:
            # Note: The current ProductRetriever doesn't have direct skin_type field
            # We'll use tags as a workaround or category filtering
            results = self.retriever.retrieve_products(
                query=query,
                top_k=top_k * 2,  # Get more to filter
                category=category,
                brand=brand,
            )

            # Additional filtering for skin_type in tags if specified
            if skin_type and results:
                filtered_results = []
                for result in results:
                    tags = result["metadata"].get("tags", "").lower()
                    if skin_type.lower() in tags:
                        filtered_results.append(result)
                # If we filtered too much, fall back to original results
                if filtered_results:
                    results = filtered_results[:top_k]
                else:
                    results = results[:top_k]
            else:
                results = results[:top_k]

            if not results:
                filters_applied = []
                if category:
                    filters_applied.append(f"category={category}")
                if brand:
                    filters_applied.append(f"brand={brand}")
                if skin_type:
                    filters_applied.append(f"skin_type={skin_type}")
                return f"No products found with filters: {', '.join(filters_applied)}"

            # Format results
            filters = []
            if category:
                filters.append(f"category: {category}")
            if brand:
                filters.append(f"brand: {brand}")
            if skin_type:
                filters.append(f"skin type: {skin_type}")

            output_parts = [
                f"Found {len(results)} products"
                + (f" with {', '.join(filters)}" if filters else "")
                + ":\n"
            ]

            for i, result in enumerate(results, 1):
                metadata = result["metadata"]
                output_parts.append(f"\n{i}. {metadata.get('name', 'Unknown Product')}")
                output_parts.append(f"   Brand: {metadata.get('brand', 'Unknown')}")
                output_parts.append(
                    f"   Price: ₹{metadata.get('price', 0):.2f}"
                )
                rating = metadata.get("rating", 0)
                if rating > 0:
                    output_parts.append(
                        f"   Rating: {rating:.1f}/5 ({metadata.get('rating_count', 0)} reviews)"
                    )
                output_parts.append(
                    f"   Category: {metadata.get('category', 'N/A')}"
                )
                if metadata.get("url"):
                    output_parts.append(f"   URL: {metadata.get('url')}")

            return "\n".join(output_parts)

        except Exception as e:
            return f"Error filtering products: {str(e)}"

    async def _arun(
        self,
        query: str = "skincare products",
        category: Optional[str] = None,
        brand: Optional[str] = None,
        skin_type: Optional[str] = None,
        top_k: int = 5,
    ) -> str:
        """Async version."""
        return self._run(query, category, brand, skin_type, top_k)


class PriceRangeFilterInput(BaseModel):
    """Input schema for price range filtering."""

    query: str = Field(
        description="The product search query",
        default="skincare products"
    )
    max_price: Optional[float] = Field(
        default=None,
        description="Maximum price in INR (Indian Rupees)",
    )
    min_price: Optional[float] = Field(
        default=None,
        description="Minimum price in INR (Indian Rupees)",
    )
    top_k: int = Field(default=5, description="Number of results (default 5)")


class PriceRangeFilterTool(BaseTool):
    """
    Tool for filtering products by price range.
    Use this when the user mentions budget constraints.
    """

    name: str = "price_range_filter"
    description: str = """
    Filter products by price range (in Indian Rupees - INR).
    Use this when the user mentions price constraints or budget.
    
    Examples:
    - "under 1000" or "below 1000" -> max_price=1000
    - "between 500 and 1500" -> min_price=500, max_price=1500
    - "at least 800" or "above 800" -> min_price=800
    - "affordable" or "budget-friendly" -> max_price=1000
    
    Can be combined with other tools for precise filtering.
    """
    args_schema: type[BaseModel] = PriceRangeFilterInput
    retriever: ProductRetriever = Field(default=None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.retriever is None:
            self.retriever = ProductRetriever(top_k=5)

    def _run(
        self,
        query: str = "skincare products",
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        top_k: int = 5,
    ) -> str:
        """Execute price range filtering."""
        try:
            results = self.retriever.retrieve_products(
                query=query,
                top_k=top_k,
                max_price=max_price,
                min_price=min_price,
            )

            if not results:
                price_range = []
                if min_price:
                    price_range.append(f"minimum ₹{min_price:.2f}")
                if max_price:
                    price_range.append(f"maximum ₹{max_price:.2f}")
                return f"No products found in price range: {', '.join(price_range)}"

            # Format results
            price_desc = []
            if min_price:
                price_desc.append(f"₹{min_price:.2f}")
            price_desc.append("to")
            if max_price:
                price_desc.append(f"₹{max_price:.2f}")
            else:
                price_desc.append("any price")

            output_parts = [
                f"Found {len(results)} products in price range {' '.join(price_desc)}:\n"
            ]

            for i, result in enumerate(results, 1):
                metadata = result["metadata"]
                output_parts.append(f"\n{i}. {metadata.get('name', 'Unknown Product')}")
                output_parts.append(f"   Brand: {metadata.get('brand', 'Unknown')}")
                output_parts.append(
                    f"   Price: ₹{metadata.get('price', 0):.2f}"
                )
                rating = metadata.get("rating", 0)
                if rating > 0:
                    output_parts.append(
                        f"   Rating: {rating:.1f}/5 ({metadata.get('rating_count', 0)} reviews)"
                    )
                output_parts.append(
                    f"   Category: {metadata.get('category', 'N/A')}"
                )
                if metadata.get("url"):
                    output_parts.append(f"   URL: {metadata.get('url')}")

            return "\n".join(output_parts)

        except Exception as e:
            return f"Error filtering by price: {str(e)}"

    async def _arun(
        self,
        query: str = "skincare products",
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        top_k: int = 5,
    ) -> str:
        """Async version."""
        return self._run(query, max_price, min_price, top_k)

