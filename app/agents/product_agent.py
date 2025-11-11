"""
Product Recommendation Agent - Custom implementation (no LangChain).
"""

import sys
from pathlib import Path
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.agents.custom_agent import CustomAgent, CustomTool
from app.retrievers import ProductRetriever
from app.prompts.agent_prompts import PRODUCT_AGENT_PROMPT


def create_product_agent(
    model_name: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    openai_api_key: Optional[str] = None,
) -> CustomAgent:
    """
    Create a Product Recommendation Agent with three composable tools.

    Args:
        model_name: OpenAI model to use
        temperature: Temperature for response generation
        openai_api_key: OpenAI API key

    Returns:
        CustomAgent instance
    """
    # Initialize retriever
    retriever = ProductRetriever(top_k=5)

    # Define tool functions
    def semantic_product_search(query: str, top_k: int = 5) -> str:
        """Search for products using semantic vector search."""
        try:
            results = retriever.retrieve_products(query=query, top_k=top_k)

            if not results:
                return "No products found matching your query."

            # Format results
            output_parts = [f"Found {len(results)} products:\n"]

            for i, result in enumerate(results, 1):
                metadata = result["metadata"]
                output_parts.append(f"\n{i}. {metadata.get('name', 'Unknown Product')}")
                output_parts.append(f"   Brand: {metadata.get('brand', 'Unknown')}")
                output_parts.append(f"   Price: ₹{metadata.get('price', 0):.2f}")
                rating = metadata.get("rating", 0)
                if rating > 0:
                    output_parts.append(
                        f"   Rating: {rating:.1f}/5 ({metadata.get('rating_count', 0)} reviews)"
                    )
                output_parts.append(f"   Category: {metadata.get('category', 'N/A')}")
                if metadata.get("url"):
                    output_parts.append(f"   URL: {metadata.get('url')}")

            return "\n".join(output_parts)
        except Exception as e:
            return f"Error searching products: {str(e)}"

    def filter_by_metadata(
        query: str = "skincare products",
        category: Optional[str] = None,
        brand: Optional[str] = None,
        skin_type: Optional[str] = None,
        top_k: int = 5,
    ) -> str:
        """Filter products by category, brand, or skin type."""
        try:
            results = retriever.retrieve_products(
                query=query,
                top_k=top_k * 2,
                category=category,
                brand=brand,
            )

            # Additional filtering for skin_type
            if skin_type and results:
                filtered = [
                    r
                    for r in results
                    if skin_type.lower() in r["metadata"].get("tags", "").lower()
                ]
                results = filtered[:top_k] if filtered else results[:top_k]
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
                output_parts.append(f"   Price: ₹{metadata.get('price', 0):.2f}")
                rating = metadata.get("rating", 0)
                if rating > 0:
                    output_parts.append(f"   Rating: {rating:.1f}/5")
                output_parts.append(f"   Category: {metadata.get('category', 'N/A')}")

            return "\n".join(output_parts)
        except Exception as e:
            return f"Error filtering products: {str(e)}"

    def filter_by_price(
        query: str = "skincare products",
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        top_k: int = 5,
    ) -> str:
        """Filter products by price range."""
        try:
            results = retriever.retrieve_products(
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
                output_parts.append(f"   Price: ₹{metadata.get('price', 0):.2f}")
                rating = metadata.get("rating", 0)
                if rating > 0:
                    output_parts.append(f"   Rating: {rating:.1f}/5")

            return "\n".join(output_parts)
        except Exception as e:
            return f"Error filtering by price: {str(e)}"

    # Create tools
    tools = [
        CustomTool(
            name="semantic_product_search",
            description="Search for skincare products using natural language. Use this when user describes what they want (e.g., 'moisturizer for dry skin'). Returns relevant products.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language description of the product",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of products to retrieve (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
            function=semantic_product_search,
        ),
        CustomTool(
            name="filter_by_metadata",
            description="Filter products by specific attributes like category, brand, or skin type. Use when user mentions specific product types or brands.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product search query",
                        "default": "skincare products",
                    },
                    "category": {
                        "type": "string",
                        "description": "Product category (e.g., 'moisturizer', 'cleanser', 'serum')",
                    },
                    "brand": {
                        "type": "string",
                        "description": "Brand name to filter by",
                    },
                    "skin_type": {
                        "type": "string",
                        "description": "Skin type (e.g., 'oily', 'dry', 'sensitive')",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
            function=filter_by_metadata,
        ),
        CustomTool(
            name="filter_by_price",
            description="Filter products by price range in INR. Use when user mentions budget constraints like 'under 1000' or 'between 500 and 1500'.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product search query",
                        "default": "skincare products",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price in INR",
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Minimum price in INR",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
            function=filter_by_price,
        ),
    ]

    # Create and return agent
    return CustomAgent(
        name="ProductAgent",
        system_prompt=PRODUCT_AGENT_PROMPT.replace("{chat_history}", "")
        .replace("{input}", "")
        .replace("{agent_scratchpad}", ""),
        tools=tools,
        model=model_name,
        temperature=temperature,
        openai_api_key=openai_api_key,
    )
