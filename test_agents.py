#!/usr/bin/env python3
"""
Test script for DermaGPT multi-agent system.

Tests:
1. Product Agent with various queries
2. Blog Agent with educational queries
3. Supervisor Agent with general queries
4. FastAPI endpoints

Usage:
    python test_agents.py
"""

import sys
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_result(result: dict):
    """Print agent result."""
    print(f"Agent Used: {result.get('agent_used', 'unknown')}")
    print(f"\nResponse:\n{result.get('response', 'No response')}\n")
    
    sources = result.get('sources', [])
    if sources:
        print(f"Sources ({len(sources)}):")
        for i, source in enumerate(sources, 1):
            if isinstance(source, dict):
                print(f"  {i}. {source.get('type', 'unknown')} - {source.get('tool', 'unknown')}")
    
    if result.get('error'):
        print(f"\n⚠️  Error: {result['error']}")


def test_orchestrator():
    """Test the orchestrator directly."""
    print_section("Testing DermaGPT Orchestrator")
    
    try:
        from app.agents.orchestrator import DermaGPTOrchestrator
        
        print("Initializing orchestrator...")
        orchestrator = DermaGPTOrchestrator(model_name="gpt-3.5-turbo")
        
        # Test queries for each agent type
        test_queries = [
            # Product queries
            ("Recommend a moisturizer under 1200 for oily skin", "product"),
            ("Show me affordable sunscreens", "product"),
            
            # Blog queries
            ("What are the benefits of vitamin C serum?", "blog"),
            ("How to treat acne naturally?", "blog"),
            
            # General queries (web search)
            ("What is hyaluronic acid?", "general"),
        ]
        
        for query, expected_agent in test_queries:
            print(f"\n{'─' * 80}")
            print(f"Query: {query}")
            print(f"Expected: {expected_agent} agent")
            print(f"{'─' * 80}\n")
            
            result = orchestrator.process_query(query)
            print_result(result)
            
            time.sleep(1)  # Rate limiting
        
        print("\n✅ Orchestrator tests completed!")
        
    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
        import traceback
        traceback.print_exc()


def test_individual_agents():
    """Test individual agents."""
    print_section("Testing Individual Agents")
    
    # Test Product Agent
    print("Testing Product Agent...")
    try:
        from app.agents.product_agent import invoke_product_agent
        
        query = "moisturizer for dry skin under 1000"
        print(f"Query: {query}\n")
        result = invoke_product_agent(query)
        print(f"Output: {result.get('output', 'No output')[:200]}...\n")
        print("✅ Product Agent working")
        
    except Exception as e:
        print(f"⚠️  Product Agent error: {e}\n")
    
    time.sleep(1)
    
    # Test Blog Agent
    print("\nTesting Blog Agent...")
    try:
        from app.agents.blog_agent import invoke_blog_agent
        
        query = "benefits of niacinamide for skin"
        print(f"Query: {query}\n")
        result = invoke_blog_agent(query)
        print(f"Output: {result.get('output', 'No output')[:200]}...\n")
        print("✅ Blog Agent working")
        
    except Exception as e:
        print(f"⚠️  Blog Agent error: {e}\n")
    
    time.sleep(1)
    
    # Test Supervisor Agent
    print("\nTesting Supervisor Agent...")
    try:
        from app.agents.supervisor_agent import create_supervisor_agent
        
        agent = create_supervisor_agent()
        query = "latest skincare trends 2024"
        print(f"Query: {query}\n")
        result = agent.invoke({"input": query, "chat_history": []})
        print(f"Output: {result.get('output', 'No output')[:200]}...\n")
        print("✅ Supervisor Agent working")
        
    except Exception as e:
        print(f"⚠️  Supervisor Agent error: {e}\n")


def test_intent_classification():
    """Test intent classification."""
    print_section("Testing Intent Classification")
    
    try:
        from app.agents.supervisor_agent import classify_intent
        
        test_cases = [
            ("recommend moisturizer under 1200", "product"),
            ("best sunscreen for oily skin", "product"),
            ("how to use vitamin C serum", "blog"),
            ("what causes acne", "blog"),
            ("latest retinol research", "general"),
        ]
        
        print("Query → Classified Intent\n")
        for query, expected in test_cases:
            intent = classify_intent(query)
            status = "✅" if intent == expected else "⚠️"
            print(f"{status} '{query}'")
            print(f"   Expected: {expected}, Got: {intent}\n")
        
        print("✅ Intent classification tests completed!")
        
    except Exception as e:
        print(f"❌ Error testing intent classification: {e}")


def test_tools():
    """Test individual tools."""
    print_section("Testing Tools")
    
    # Test Product Tools
    print("Testing Product Tools...")
    try:
        from app.tools.product_tools import SemanticProductSearchTool
        
        # Test semantic search
        tool = SemanticProductSearchTool()
        result = tool._run("moisturizer for dry skin", top_k=2)
        print(f"Semantic Search: {result[:150]}...")
        print("✅ Product tools working\n")
        
    except Exception as e:
        print(f"⚠️  Product tools error: {e}\n")
    
    # Test Blog Tool
    print("\nTesting Blog Tool...")
    try:
        from app.tools.blog_tools import BlogSearchTool
        
        tool = BlogSearchTool()
        result = tool._run("benefits of vitamin C", top_k=2)
        print(f"Blog Search: {result[:150]}...")
        print("✅ Blog tool working\n")
        
    except Exception as e:
        print(f"⚠️  Blog tool error: {e}\n")


def test_api_endpoints():
    """Test FastAPI endpoints (requires server to be running)."""
    print_section("Testing FastAPI Endpoints")
    
    print("Note: To test API endpoints, start the server first:")
    print("  uvicorn app.main:app --reload")
    print("\nThen test with:")
    print("  curl -X POST http://localhost:8000/chat \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"query\": \"recommend moisturizer for oily skin\"}'")
    print("\nOr visit: http://localhost:8000/docs for interactive API testing")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("  🧪 DermaGPT Multi-Agent System Test Suite")
    print("=" * 80)
    
    print("\n📋 Test Plan:")
    print("  1. Intent classification")
    print("  2. Individual tools")
    print("  3. Individual agents")
    print("  4. Full orchestrator")
    print("  5. API endpoints (manual)")
    
    # Ask user which tests to run
    print("\n" + "-" * 80)
    response = input("Run all tests? (yes/no, default: yes): ").strip().lower()
    
    if response in ["no", "n"]:
        print("\nWhich tests to run?")
        print("  1. Intent classification")
        print("  2. Tools")
        print("  3. Individual agents")
        print("  4. Full orchestrator")
        print("  5. API info")
        
        choices = input("Enter numbers separated by spaces (e.g., '1 2 4'): ").strip()
        
        if "1" in choices:
            test_intent_classification()
        if "2" in choices:
            test_tools()
        if "3" in choices:
            test_individual_agents()
        if "4" in choices:
            test_orchestrator()
        if "5" in choices:
            test_api_endpoints()
    else:
        # Run all tests
        test_intent_classification()
        test_tools()
        test_individual_agents()
        test_orchestrator()
        test_api_endpoints()
    
    print("\n" + "=" * 80)
    print("  ✅ Test Suite Completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

