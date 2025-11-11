"""
Base Retriever for Pinecone vector search.
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

try:
    from openai import OpenAI
    from pinecone import Pinecone
except ImportError as e:
    raise ImportError(
        f"Missing required package: {e}\n"
        "Please run: pip install openai pinecone python-dotenv"
    )


class BaseRetriever:
    """
    Base class for retrieving relevant documents from Pinecone.
    """

    def __init__(
        self,
        namespace: str,
        top_k: int = 5,
        openai_api_key: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        pinecone_index_name: Optional[str] = None,
        embedding_model: str = "text-embedding-3-large",
        embedding_dimensions: int = 1024,
    ):
        """
        Initialize the retriever.

        Args:
            namespace: Pinecone namespace to query (e.g., "products", "blogs")
            top_k: Number of results to retrieve
            openai_api_key: OpenAI API key (defaults to env var)
            pinecone_api_key: Pinecone API key (defaults to env var)
            pinecone_index_name: Pinecone index name (defaults to env var)
            embedding_model: OpenAI embedding model to use
            embedding_dimensions: Embedding dimensions
        """
        load_dotenv()

        self.namespace = namespace
        self.top_k = top_k
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions

        # Initialize OpenAI client
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment or parameters")
        self.openai_client = OpenAI(api_key=api_key)

        # Initialize Pinecone client
        pinecone_key = pinecone_api_key or os.getenv("PINECONE_API_KEY")
        if not pinecone_key:
            raise ValueError(
                "PINECONE_API_KEY not found in environment or parameters"
            )

        pc = Pinecone(api_key=pinecone_key)
        index_name = pinecone_index_name or os.getenv(
            "PINECONE_INDEX_NAME", "dermagpt-rag"
        )
        self.index = pc.Index(index_name)

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query string.

        Args:
            query: The query text

        Returns:
            List of floats representing the embedding
        """
        response = self.openai_client.embeddings.create(
            input=query, model=self.embedding_model, dimensions=self.embedding_dimensions
        )
        return response.data[0].embedding

    def retrieve(
        self, query: str, top_k: Optional[int] = None, filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: The search query
            top_k: Number of results to return (overrides instance default)
            filters: Metadata filters for Pinecone query

        Returns:
            List of dictionaries containing matched documents with metadata
        """
        k = top_k or self.top_k

        # Generate query embedding
        query_embedding = self.generate_query_embedding(query)

        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=k,
            namespace=self.namespace,
            filter=filters,
            include_metadata=True,
        )

        # Format results
        formatted_results = []
        for match in results.matches:
            formatted_results.append(
                {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata,
                }
            )

        return formatted_results

    def retrieve_with_context(
        self, query: str, top_k: Optional[int] = None, filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Retrieve documents and return formatted context for LLM.

        Args:
            query: The search query
            top_k: Number of results to return
            filters: Metadata filters

        Returns:
            Dictionary with results and formatted context string
        """
        results = self.retrieve(query, top_k, filters)

        # Create formatted context
        context_parts = []
        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            context_parts.append(f"[Result {i}]")
            context_parts.append(self._format_result(metadata))
            context_parts.append("")  # Empty line between results

        return {
            "results": results,
            "context": "\n".join(context_parts),
            "num_results": len(results),
        }

    def _format_result(self, metadata: Dict[str, Any]) -> str:
        """
        Format a single result's metadata into readable text.
        Override this in subclasses for specific formatting.

        Args:
            metadata: Result metadata

        Returns:
            Formatted string
        """
        return str(metadata)

