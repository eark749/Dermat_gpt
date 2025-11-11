# Multi-Source RAG System Architecture

Based on your assignment requirements, here's a comprehensive architecture design:

## 1. **Overall System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  - Chat endpoint                                             │
│  - Conversation history management                           │
│  - Request validation & response formatting                  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Agent Orchestrator                         │
│  - Query classification & intent detection                   │
│  - Route to appropriate agent/retriever                      │
│  - Response synthesis                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼─────┐ ┌───▼──────────┐
│  Product     │ │  Blog  │ │  General     │
│  Agent       │ │  Agent │ │  Knowledge   │
│              │ │        │ │  Agent       │
└───────┬──────┘ └──┬─────┘ └───┬──────────┘
        │           │            │
┌───────▼──────┐ ┌──▼─────┐ ┌───▼──────────┐
│  Vector DB   │ │ Vector │ │  Web Search  │
│  (Products)  │ │  DB    │ │  API         │
│  Chroma/     │ │ (Blogs)│ │  (Tavily/    │
│  Pinecone    │ │        │ │  SerpAPI)    │
└──────────────┘ └────────┘ └──────────────┘
```

## 2. **Recommended Tech Stack**

### **Backend & API**
- **FastAPI**: Modern, fast, with automatic API documentation
- **Pydantic**: Request/response validation
- **uvicorn**: ASGI server

### **Agent Framework**
Choose one approach:

**Option A: LangGraph (Recommended)**
```
Benefits:
- Native multi-agent support
- Built-in state management
- Graph-based workflow (easier to visualize)
- Better for complex routing logic
```

**Option B: LangChain**
```
Benefits:
- Mature ecosystem
- Extensive integrations
- Good documentation
- Simpler for linear workflows
```

### **Vector Databases**
- **ChromaDB**: Free, embedded, great for development
- **Pinecone**: Managed, scalable (for production)
- **Weaviate**: Open-source alternative

### **LLM Provider**
- **OpenAI GPT-4/3.5**: Best quality
- **Anthropic Claude**: Great reasoning
- **Local (Ollama)**: Cost-effective, privacy

### **Embedding Models**
- `text-embedding-3-small` (OpenAI)
- `all-MiniLM-L6-v2` (sentence-transformers, free)

### **External Search**
- **Tavily API**: AI-optimized search
- **SerpAPI**: Google search results
- **Scraped data**: Custom solution

## 3. **Detailed Agent Architecture**

### **Multi-Agent Approach (Recommended)**

```python
# Agent Structure

1. Supervisor Agent (Orchestrator)
   ├─ Input: User query + conversation history
   ├─ Task: Classify intent using LLM
   ├─ Output: Route to specialist agent
   └─ Logic:
       - Product keywords: "buy", "recommend", "price", "under X"
       - Blog keywords: "article", "blog", "read about"
       - General: everything else

2. Product Recommendation Agent
   ├─ Retriever: Vector search on product embeddings
   ├─ Filter logic: Price, skin type, category
   ├─ Prompt: Product-specific formatting
   └─ Tools:
       - Semantic search
       - Metadata filtering
       - Price range filtering

3. Blog Agent
   ├─ Retriever: Vector search on blog content
   ├─ Context: Full blog posts or summaries
   └─ Response: Citations with blog titles/links

4. General Knowledge Agent
   ├─ Tools: Web search API
   ├─ Context: Latest skincare information
   └─ Fallback: LLM general knowledge
```

## 4. **Database Schema**

### **Vector Store Structure**

```python
# Products Collection
{
    "id": "product_123",
    "content": "Product Name + Description combined",
    "embedding": [0.123, 0.456, ...],  # 1536 dims
    "metadata": {
        "name": "Moisturizer XYZ",
        "brand": "BrandName",
        "price": 899,
        "category": "moisturizer",
        "skin_type": ["oily", "combination"],
        "key_ingredients": ["hyaluronic acid", "niacinamide"],
        "rating": 4.5,
        "url": "product_url"
    }
}

# Blogs Collection
{
    "id": "blog_456",
    "content": "Full blog text or chunked sections",
    "embedding": [0.789, 0.012, ...],
    "metadata": {
        "title": "How to treat acne",
        "author": "Dr. Smith",
        "date": "2024-01-15",
        "category": "acne-treatment",
        "url": "blog_url",
        "tags": ["acne", "skincare"]
    }
}
```

### **Conversation History (PostgreSQL/MongoDB)**

```python
{
    "session_id": "uuid",
    "user_id": "user_123",
    "messages": [
        {
            "role": "user",
            "content": "I need a moisturizer",
            "timestamp": "2024-01-15T10:30:00"
        },
        {
            "role": "assistant",
            "content": "I'd be happy to help...",
            "timestamp": "2024-01-15T10:30:05",
            "sources": ["product_123", "product_456"],
            "agent_used": "product_agent"
        }
    ],
    "created_at": "2024-01-15T10:30:00"
}
```

## 5. **Query Flow Example**

```
User: "Recommend a moisturizer under 1200 for oily skin"
    ↓
API receives request
    ↓
Supervisor Agent analyzes query
    ├─ Detects: product recommendation
    ├─ Extracts: price_max=1200, skin_type="oily"
    └─ Routes to: Product Agent
    ↓
Product Agent:
    ├─ Generates embedding for query
    ├─ Searches vector DB with filters:
    │   - price <= 1200
    │   - skin_type contains "oily"
    ├─ Retrieves top 5 products
    └─ Passes to LLM with prompt template
    ↓
LLM generates response with recommendations
    ↓
API returns formatted response with product details
```

## 6. **Implementation Recommendations**

### **Phase 1: Core Setup**
1. Set up FastAPI backend
2. Load and preprocess XLSX → create embeddings
3. Load blogs → create embeddings
4. Set up ChromaDB collections
5. Implement basic retrieval

### **Phase 2: Agent System**
1. Implement intent classifier (can use LLM or rule-based initially)
2. Create specialized retrievers for each data source
3. Build prompt templates for each agent type
4. Implement response synthesis

### **Phase 3: Enhancement**
1. Add conversation history
2. Implement external search integration
3. Add metadata filtering logic
4. Fine-tune prompts and retrieval

### **Phase 4: Deployment**
1. Containerize with Docker
2. Deploy to Railway/Render/Fly.io
3. Set up environment variables
4. Add monitoring/logging

## 7. **Code Structure**

```
project/
├── app/
│   ├── main.py              # FastAPI app
│   ├── api/
│   │   └── routes.py        # API endpoints
│   ├── agents/
│   │   ├── orchestrator.py  # Main routing logic
│   │   ├── product_agent.py
│   │   ├── blog_agent.py
│   │   └── general_agent.py
│   ├── retrievers/
│   │   ├── product_retriever.py
│   │   └── blog_retriever.py
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── db/
│   │   ├── vector_store.py
│   │   └── conversation_store.py
│   └── utils/
│       ├── embeddings.py
│       └── preprocessing.py
├── data/
│   ├── products.xlsx
│   └── blogs/
├── requirements.txt
├── Dockerfile
└── README.md
```

do my architecture and the pdf matches the goal to build it???