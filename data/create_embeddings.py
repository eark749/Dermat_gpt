#!/usr/bin/env python3
"""
create_embeddings.py
--------------------
Single script to create embeddings for both products and blogs,
then upload to Pinecone with separate namespaces.

Usage:
    1. Set up .env file with OPENAI_API_KEY, PINECONE_API_KEY, etc.
    2. Run: python create_embeddings.py

Features:
- Loads products from cleaned CSV
- Recursively processes 1500+ blog folders
- Chunks long blogs (600 tokens with 100 token overlap)
- Generates OpenAI embeddings (text-embedding-3-small, 1536 dims)
- Uploads to Pinecone namespaces: "products" and "blogs"
- Progress tracking, cost estimation, error handling
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime

import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

# OpenAI and Pinecone imports
try:
    from openai import OpenAI
    import tiktoken
    from pinecone import Pinecone
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("💡 Please run: pip install -r requirements.txt")
    sys.exit(1)


# ========================================
# CONFIGURATION
# ========================================

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "dermagpt-rag")

# Processing Configuration
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))
CHUNK_SIZE = 600  # tokens
CHUNK_OVERLAP = 100  # tokens
MAX_CHUNK_THRESHOLD = 800  # chunk if text > this many tokens

# File paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
PRODUCTS_CSV = Path(
    r"C:\Users\sonid\OneDrive\Desktop\Dermat_gpt\data\DermaGPT Product Database (1)_cleaned.csv"
)
BLOGS_DIR = Path(r"C:\Users\sonid\OneDrive\Desktop\Dermat_gpt\Skin _ Hair Care Guide")

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(SCRIPT_DIR / "embedding_creation.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# ========================================
# INITIALIZATION
# ========================================


def validate_config():
    """Validate that all required configuration is present."""
    errors = []

    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY not set in .env file")
    if not PINECONE_API_KEY:
        errors.append("PINECONE_API_KEY not set in .env file")
    if not PRODUCTS_CSV.exists():
        errors.append(f"Products CSV not found at: {PRODUCTS_CSV}")
    if not BLOGS_DIR.exists():
        errors.append(f"Blogs directory not found at: {BLOGS_DIR}")

    if errors:
        logger.error("❌ Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.info("\n💡 Please create a .env file with:")
        logger.info("  OPENAI_API_KEY=your_key_here")
        logger.info("  PINECONE_API_KEY=your_key_here")
        logger.info("  PINECONE_ENVIRONMENT=your_env_here")
        logger.info("  PINECONE_INDEX_NAME=dermagpt-rag")
        sys.exit(1)

    logger.info("✅ Configuration validated")


def initialize_clients():
    """Initialize OpenAI and Pinecone clients."""
    try:
        # Initialize OpenAI client
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("✅ OpenAI client initialized")

        # Initialize Pinecone client
        pc = Pinecone(api_key=PINECONE_API_KEY)

        # Get or create index (assumes index already exists per requirements)
        try:
            index = pc.Index(PINECONE_INDEX_NAME)
            logger.info(f"✅ Connected to Pinecone index: {PINECONE_INDEX_NAME}")
        except Exception as e:
            logger.error(
                f"❌ Failed to connect to Pinecone index '{PINECONE_INDEX_NAME}': {e}"
            )
            logger.info(
                "💡 Please create the index in Pinecone dashboard first with dimension=1024"
            )
            sys.exit(1)

        return openai_client, index

    except Exception as e:
        logger.error(f"❌ Failed to initialize clients: {e}")
        sys.exit(1)


# ========================================
# TEXT CHUNKING
# ========================================


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.get_encoding(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Token counting failed: {e}, using character approximation")
        return len(text) // 4  # Rough approximation


def chunk_text(
    text: str,
    title: str = "",
    max_tokens: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[str]:
    """
    Split text into chunks with overlap.

    Args:
        text: The text to chunk
        title: Optional title to prepend to each chunk for context
        max_tokens: Maximum tokens per chunk
        overlap: Number of tokens to overlap between chunks

    Returns:
        List of text chunks
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)

    # If text is short enough, return as single chunk
    if len(tokens) <= MAX_CHUNK_THRESHOLD:
        if title:
            return [f"{title}\n\n{text}"]
        return [text]

    chunks = []
    start = 0

    # Prepend title tokens if provided
    title_tokens = encoding.encode(f"{title}\n\n") if title else []
    title_token_count = len(title_tokens)

    while start < len(tokens):
        # Calculate end position
        end = start + max_tokens - title_token_count

        # Get chunk tokens
        chunk_tokens = tokens[start:end]

        # Decode to text
        chunk_text = encoding.decode(chunk_tokens)

        # Add title context if provided
        if title:
            chunk_text = f"{title}\n\n{chunk_text}"

        chunks.append(chunk_text)

        # Move start forward with overlap
        start = end - overlap

        # Break if we've processed all tokens
        if end >= len(tokens):
            break

    return chunks


# ========================================
# PRODUCT PROCESSING
# ========================================


def parse_rating(rating_value):
    """Parse rating value which might be a JSON string or a float."""
    if pd.isna(rating_value):
        return 0.0

    rating_str = str(rating_value)

    # Check if it's a JSON string
    if rating_str.startswith("{"):
        try:
            rating_json = json.loads(rating_str)
            return float(rating_json.get("value", 0))
        except (json.JSONDecodeError, ValueError, KeyError):
            return 0.0

    # Try to convert directly to float
    try:
        return float(rating_str)
    except ValueError:
        return 0.0


def load_products() -> List[Dict[str, Any]]:
    """
    Load products from cleaned CSV and prepare for embedding.

    Returns:
        List of product records with content and metadata
    """
    logger.info(f"📂 Loading products from: {PRODUCTS_CSV}")

    try:
        df = pd.read_csv(PRODUCTS_CSV)
        logger.info(f"✅ Loaded {len(df)} products")

        products = []

        for idx, row in df.iterrows():
            # Use combined_text for embedding (created by preprocessing script)
            content = str(row.get("combined_text", ""))

            if not content or content == "nan":
                logger.warning(f"Skipping product at index {idx} - no content")
                continue

            # Extract metadata
            metadata = {
                "name": str(row.get("Title", "")),
                "brand": str(
                    row.get(
                        "Vendor",
                        row.get(
                            "Metafield: my_fields.brand_name [single_line_text_field]",
                            "Unknown",
                        ),
                    )
                ),
                "price": float(row.get("Variant Price", 0))
                if pd.notna(row.get("Variant Price"))
                else 0.0,
                "category": str(row.get("Type", row.get("Category", "General"))),
                "tags": str(row.get("Tags", "")),
                "rating": parse_rating(row.get("Metafield: reviews.rating [rating]")),
                "rating_count": int(
                    row.get("Metafield: reviews.rating_count [number_integer]", 0)
                )
                if pd.notna(row.get("Metafield: reviews.rating_count [number_integer]"))
                else 0,
                "url": str(row.get("URL", "")),
                "type": "product",
            }

            # Clean metadata - remove nan strings
            for key in metadata:
                if isinstance(metadata[key], str) and metadata[key] in ["nan", ""]:
                    metadata[key] = ""

            products.append(
                {"id": f"product_{idx}", "content": content, "metadata": metadata}
            )

        logger.info(f"✅ Prepared {len(products)} products for embedding")
        return products

    except Exception as e:
        logger.error(f"❌ Failed to load products: {e}")
        raise


# ========================================
# BLOG PROCESSING
# ========================================


def load_blogs() -> List[Dict[str, Any]]:
    """
    Recursively load blogs from folder structure.
    Each folder contains: content_plain.txt and metadata.json

    Returns:
        List of blog records (possibly chunked) with content and metadata
    """
    logger.info(f"📂 Loading blogs from: {BLOGS_DIR}")

    blog_records = []
    blog_folders = [d for d in BLOGS_DIR.iterdir() if d.is_dir()]

    logger.info(f"Found {len(blog_folders)} blog folders")

    for folder in tqdm(blog_folders, desc="Processing blogs"):
        try:
            # Look for content file (try different names)
            content_file = None
            for name in ["content_plain.txt", "content.txt"]:
                potential_file = folder / name
                if potential_file.exists():
                    content_file = potential_file
                    break

            if not content_file:
                logger.warning(f"No content file found in {folder.name}")
                continue

            # Read content
            with open(content_file, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                logger.warning(f"Empty content in {folder.name}")
                continue

            # Read metadata
            metadata_file = folder / "metadata.json"
            metadata = {}

            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

            # Extract and clean metadata
            title = metadata.get("title", folder.name)
            author = metadata.get("author", "")
            created_at = metadata.get("created_at", "")
            tags = metadata.get("tags", "")
            url = metadata.get("link", "")

            # Parse date
            date_str = created_at
            try:
                if created_at:
                    date_obj = datetime.fromisoformat(created_at.replace("+05:30", ""))
                    date_str = date_obj.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                date_str = ""

            # Chunk the content if needed
            token_count = count_tokens(content)

            if token_count > MAX_CHUNK_THRESHOLD:
                # Content is long, chunk it
                chunks = chunk_text(content, title=title)
                logger.debug(f"Chunked '{title}' into {len(chunks)} chunks")

                for chunk_idx, chunk in enumerate(chunks):
                    chunk_metadata = {
                        "title": title,
                        "author": author,
                        "date": date_str,
                        "tags": tags,
                        "url": url,
                        "chunk_index": chunk_idx,
                        "total_chunks": len(chunks),
                        "type": "blog",
                    }

                    blog_records.append(
                        {
                            "id": f"blog_{folder.name}_{chunk_idx}",
                            "content": chunk,
                            "metadata": chunk_metadata,
                        }
                    )
            else:
                # Content is short enough, single record
                single_metadata = {
                    "title": title,
                    "author": author,
                    "date": date_str,
                    "tags": tags,
                    "url": url,
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "type": "blog",
                }

                blog_records.append(
                    {
                        "id": f"blog_{folder.name}_0",
                        "content": content if not title else f"{title}\n\n{content}",
                        "metadata": single_metadata,
                    }
                )

        except Exception as e:
            logger.warning(f"Failed to process {folder.name}: {e}")
            continue

    logger.info(f"✅ Prepared {len(blog_records)} blog records (chunks) for embedding")
    return blog_records


# ========================================
# EMBEDDING GENERATION
# ========================================


def generate_embeddings_batch(
    client: OpenAI, texts: List[str], model: str = EMBEDDING_MODEL
) -> List[List[float]]:
    """
    Generate embeddings for a batch of texts with retry logic.

    Args:
        client: OpenAI client
        texts: List of texts to embed
        model: Embedding model name

    Returns:
        List of embedding vectors
    """
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            response = client.embeddings.create(
                input=texts,
                model=model,
                dimensions=EMBEDDING_DIMENSIONS,  # Explicitly set dimensions to 1024
            )

            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Embedding generation failed (attempt {attempt + 1}), retrying in {retry_delay}s: {e}"
                )
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(
                    f"Failed to generate embeddings after {max_retries} attempts: {e}"
                )
                raise

    return []


def process_embeddings(
    client: OpenAI, records: List[Dict[str, Any]], desc: str = "Generating embeddings"
) -> List[Tuple[str, List[float], Dict[str, Any]]]:
    """
    Process records to generate embeddings in batches.

    Args:
        client: OpenAI client
        records: List of records with id, content, metadata
        desc: Description for progress bar

    Returns:
        List of tuples (id, embedding, metadata)
    """
    results = []

    # Process in batches
    for i in tqdm(range(0, len(records), BATCH_SIZE), desc=desc):
        batch = records[i : i + BATCH_SIZE]

        # Extract texts
        texts = [record["content"] for record in batch]

        # Generate embeddings
        try:
            embeddings = generate_embeddings_batch(client, texts)

            # Combine with IDs and metadata
            for record, embedding in zip(batch, embeddings):
                results.append((record["id"], embedding, record["metadata"]))

        except Exception as e:
            logger.error(f"Failed to process batch starting at index {i}: {e}")
            # Continue with next batch
            continue

        # Small delay to respect rate limits
        time.sleep(0.1)

    return results


# ========================================
# PINECONE UPLOAD
# ========================================


def upload_to_pinecone(
    index,
    vectors: List[Tuple[str, List[float], Dict[str, Any]]],
    namespace: str,
    desc: str = "Uploading to Pinecone",
):
    """
    Upload vectors to Pinecone in batches.

    Args:
        index: Pinecone index
        vectors: List of (id, embedding, metadata) tuples
        namespace: Namespace to upload to
        desc: Description for progress bar
    """
    logger.info(f"📤 Uploading {len(vectors)} vectors to namespace '{namespace}'")

    success_count = 0
    fail_count = 0

    # Upload in batches
    for i in tqdm(range(0, len(vectors), BATCH_SIZE), desc=desc):
        batch = vectors[i : i + BATCH_SIZE]

        try:
            # Format for Pinecone upsert
            upsert_data = [
                {"id": vec_id, "values": embedding, "metadata": metadata}
                for vec_id, embedding, metadata in batch
            ]

            # Upsert to Pinecone
            index.upsert(vectors=upsert_data, namespace=namespace)

            success_count += len(batch)

        except Exception as e:
            logger.error(f"Failed to upload batch starting at index {i}: {e}")
            fail_count += len(batch)
            continue

        # Small delay
        time.sleep(0.1)

    logger.info(f"✅ Successfully uploaded {success_count} vectors to '{namespace}'")
    if fail_count > 0:
        logger.warning(f"⚠️  Failed to upload {fail_count} vectors")


# ========================================
# COST ESTIMATION
# ========================================


def estimate_cost(total_tokens: int, model: str = EMBEDDING_MODEL) -> float:
    """
    Estimate OpenAI API cost for embeddings.

    Pricing (as of 2024):
    - text-embedding-3-small: $0.02 per 1M tokens
    - text-embedding-3-large: $0.13 per 1M tokens
    """
    pricing = {
        "text-embedding-3-small": 0.02 / 1_000_000,
        "text-embedding-3-large": 0.13 / 1_000_000,
        "text-embedding-ada-002": 0.10 / 1_000_000,
    }

    price_per_token = pricing.get(model, 0.02 / 1_000_000)
    return total_tokens * price_per_token


def calculate_total_tokens(records: List[Dict[str, Any]]) -> int:
    """Calculate total tokens across all records."""
    total = 0
    for record in records:
        total += count_tokens(record["content"])
    return total


# ========================================
# MAIN EXECUTION
# ========================================


def main():
    """Main execution function."""
    print("\n" + "=" * 60)
    print("  DermaGPT - Embedding Creation & Pinecone Upload")
    print("=" * 60 + "\n")

    # Step 1: Validate configuration
    logger.info("Step 1: Validating configuration...")
    validate_config()

    # Step 2: Initialize clients
    logger.info("\nStep 2: Initializing OpenAI and Pinecone clients...")
    openai_client, pinecone_index = initialize_clients()

    # Step 3: Load products
    logger.info("\nStep 3: Loading products...")
    products = load_products()

    # Step 4: Load blogs
    logger.info("\nStep 4: Loading blogs...")
    blogs = load_blogs()

    # Step 5: Cost estimation
    logger.info("\nStep 5: Estimating costs...")
    product_tokens = calculate_total_tokens(products)
    blog_tokens = calculate_total_tokens(blogs)
    total_tokens = product_tokens + blog_tokens

    estimated_cost = estimate_cost(total_tokens, EMBEDDING_MODEL)

    print("\n📊 Processing Summary:")
    print(f"  - Products: {len(products)} items ({product_tokens:,} tokens)")
    print(f"  - Blogs: {len(blogs)} chunks ({blog_tokens:,} tokens)")
    print(f"  - Total tokens: {total_tokens:,}")
    print(f"  - Estimated cost: ${estimated_cost:.4f}")
    print(f"  - Model: {EMBEDDING_MODEL}")

    # Confirm before proceeding
    response = (
        input("\n⚠️  Proceed with embedding generation? (yes/no): ").strip().lower()
    )
    if response != "yes":
        logger.info("❌ Operation cancelled by user")
        return

    # Step 6: Generate product embeddings
    logger.info("\nStep 6: Generating product embeddings...")
    product_vectors = process_embeddings(openai_client, products, desc="Products")

    # Step 7: Generate blog embeddings
    logger.info("\nStep 7: Generating blog embeddings...")
    blog_vectors = process_embeddings(openai_client, blogs, desc="Blogs")

    # Step 8: Upload products to Pinecone
    logger.info("\nStep 8: Uploading products to Pinecone...")
    upload_to_pinecone(
        pinecone_index, product_vectors, namespace="products", desc="Products"
    )

    # Step 9: Upload blogs to Pinecone
    logger.info("\nStep 9: Uploading blogs to Pinecone...")
    upload_to_pinecone(pinecone_index, blog_vectors, namespace="blogs", desc="Blogs")

    # Final summary
    print("\n" + "=" * 60)
    print("  ✅ COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print("\n📊 Final Summary:")
    print(f"  - Products uploaded: {len(product_vectors)} to namespace 'products'")
    print(f"  - Blogs uploaded: {len(blog_vectors)} to namespace 'blogs'")
    print(f"  - Total vectors: {len(product_vectors) + len(blog_vectors)}")
    print(f"  - Pinecone index: {PINECONE_INDEX_NAME}")
    print("\n💡 You can now query these namespaces in your RAG application!")
    print("   - Products: index.query(namespace='products', ...)")
    print("   - Blogs: index.query(namespace='blogs', ...)")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Operation cancelled by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
