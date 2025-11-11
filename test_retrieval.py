#!/usr/bin/env python3
"""
Test script for the retrieval system.

Usage:
    python test_retrieval.py
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.retrievers import ProductRetriever, BlogRetriever


def test_product_retrieval():
    """Test product retrieval with various queries and filters."""
    print("\n" + "=" * 60)
    print("TESTING PRODUCT RETRIEVAL")
    print("=" * 60 + "\n")

    retriever = ProductRetriever(top_k=3)

    # Test 1: Basic product search
    print("Test 1: Search for 'moisturizer for dry skin'")
    print("-" * 60)
    results = retriever.retrieve_products(query="moisturizer for dry skin", top_k=3)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['metadata'].get('name', 'Unknown')}")
        print(f"   Brand: {result['metadata'].get('brand', 'Unknown')}")
        print(f"   Price: ₹{result['metadata'].get('price', 0):.2f}")
        print(f"   Rating: {result['metadata'].get('rating', 0):.1f}/5")
        print(f"   Score: {result['score']:.3f}")

    # Test 2: Search with price filter
    print("\n\n" + "=" * 60)
    print("Test 2: Search for 'sunscreen' under ₹1000")
    print("-" * 60)
    results = retriever.retrieve_products(
        query="sunscreen SPF protection", top_k=3, max_price=1000
    )

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['metadata'].get('name', 'Unknown')}")
        print(f"   Price: ₹{result['metadata'].get('price', 0):.2f}")
        print(f"   Score: {result['score']:.3f}")

    # Test 3: Get recommendations by concern
    print("\n\n" + "=" * 60)
    print("Test 3: Get recommendations for 'acne' concern")
    print("-" * 60)
    recommendations = retriever.get_recommendations_by_concern(
        concern="acne", top_k=3, max_price=1500
    )

    print(f"\nFound {len(recommendations['results'])} products:")
    for i, result in enumerate(recommendations["results"], 1):
        print(f"\n{i}. {result['metadata'].get('name', 'Unknown')}")
        print(f"   Category: {result['metadata'].get('category', 'N/A')}")
        print(f"   Price: ₹{result['metadata'].get('price', 0):.2f}")


def test_blog_retrieval():
    """Test blog retrieval for educational content."""
    print("\n\n" + "=" * 60)
    print("TESTING BLOG RETRIEVAL")
    print("=" * 60 + "\n")

    retriever = BlogRetriever(top_k=3)

    # Test 1: Search for skincare information
    print("Test 1: Search for 'how to treat acne naturally'")
    print("-" * 60)
    results = retriever.retrieve_blogs(query="how to treat acne naturally", top_k=3)

    for i, result in enumerate(results, 1):
        metadata = result["metadata"]
        print(f"\n{i}. {metadata.get('title', 'Untitled')}")
        print(f"   Author: {metadata.get('author', 'Unknown')}")
        print(f"   Tags: {metadata.get('tags', 'None')}")
        print(f"   Score: {result['score']:.3f}")

    # Test 2: Search by topic
    print("\n\n" + "=" * 60)
    print("Test 2: Search articles about 'hair fall'")
    print("-" * 60)
    articles = retriever.search_by_topic(topic="hair fall prevention", top_k=3)

    print(f"\nFound {len(articles['results'])} articles:")
    for i, result in enumerate(articles["results"], 1):
        metadata = result["metadata"]
        print(f"\n{i}. {metadata.get('title', 'Untitled')}")
        print(f"   Date: {metadata.get('date', 'N/A')}")
        print(f"   Score: {result['score']:.3f}")

    # Test 3: Deduplicate articles (since blogs are chunked)
    print("\n\n" + "=" * 60)
    print("Test 3: Deduplicated results for 'vitamin C benefits'")
    print("-" * 60)
    results = retriever.retrieve_blogs(query="vitamin C serum benefits", top_k=10)
    deduplicated = retriever.get_deduplicated_articles(results)

    print(f"\nOriginal results: {len(results)}")
    print(f"After deduplication: {len(deduplicated)}")
    print("\nUnique articles:")
    for i, result in enumerate(deduplicated, 1):
        print(f"{i}. {result['metadata'].get('title', 'Untitled')}")


def test_combined_retrieval():
    """Test retrieving from both sources for a user query."""
    print("\n\n" + "=" * 60)
    print("TESTING COMBINED RETRIEVAL (Products + Blogs)")
    print("=" * 60 + "\n")

    product_retriever = ProductRetriever(top_k=2)
    blog_retriever = BlogRetriever(top_k=2)

    query = "anti-aging skincare routine"

    print(f"User Query: '{query}'")
    print("\n" + "-" * 60)
    print("PRODUCTS:")
    print("-" * 60)

    products = product_retriever.retrieve_products(query=query, top_k=2)
    for i, result in enumerate(products, 1):
        print(f"{i}. {result['metadata'].get('name', 'Unknown')}")
        print(f"   Price: ₹{result['metadata'].get('price', 0):.2f}")

    print("\n" + "-" * 60)
    print("EDUCATIONAL CONTENT:")
    print("-" * 60)

    blogs = blog_retriever.retrieve_blogs(query=query, top_k=2)
    for i, result in enumerate(blogs, 1):
        print(f"{i}. {result['metadata'].get('title', 'Untitled')}")

    print(
        "\n✅ This shows how you can combine both sources for a comprehensive response!"
    )


def main():
    """Run all tests."""
    print("\n🚀 Starting Retrieval System Tests...")
    print("=" * 60)

    try:
        # Test products
        test_product_retrieval()

        # Test blogs
        test_blog_retrieval()

        # Test combined
        test_combined_retrieval()

        print("\n\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n💡 Next steps:")
        print("   1. Build the agent orchestrator")
        print("   2. Create specialized agents using these retrievers")
        print("   3. Implement FastAPI endpoints")
        print()

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

