"""
Main orchestrator that manages all custom agents and processes queries.
No LangChain dependencies - clean and simple!
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from app.agents.product_agent import create_product_agent
from app.agents.blog_agent import create_blog_agent
from app.agents.supervisor_agent import create_supervisor_agent, route_query


load_dotenv()


class DermaGPTOrchestrator:
    """
    Main orchestrator for DermaGPT multi-agent system.

    Manages three custom agents:
    - Product Agent: Product recommendations
    - Blog Agent: Educational content
    - Supervisor Agent: General queries with web search
    """

    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize the orchestrator and all agents.

        Args:
            model_name: OpenAI model to use
            temperature: Temperature for generation
            openai_api_key: OpenAI API key (uses env var if not provided)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        # Initialize agents
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all specialist agents."""
        print("🤖 Initializing DermaGPT custom agents...")

        try:
            self.product_agent = create_product_agent(
                model_name=self.model_name,
                temperature=self.temperature,
                openai_api_key=self.api_key,
            )
            print("   ✅ Product Agent ready")
        except Exception as e:
            print(f"   ⚠️ Product Agent initialization failed: {e}")
            self.product_agent = None

        try:
            self.blog_agent = create_blog_agent(
                model_name=self.model_name,
                temperature=self.temperature,
                openai_api_key=self.api_key,
            )
            print("   ✅ Blog Agent ready")
        except Exception as e:
            print(f"   ⚠️ Blog Agent initialization failed: {e}")
            self.blog_agent = None

        try:
            self.supervisor_agent = create_supervisor_agent(
                model_name=self.model_name,
                temperature=0.3,  # Lower temp for routing
                openai_api_key=self.api_key,
            )
            print("   ✅ Supervisor Agent ready")
        except Exception as e:
            print(f"   ⚠️ Supervisor Agent initialization failed: {e}")
            self.supervisor_agent = None

        print("🚀 DermaGPT is ready!\n")

    def process_query(
        self, query: str, chat_history: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Process a user query by routing to the appropriate agent.

        Args:
            query: User query
            chat_history: Optional conversation history

        Returns:
            Dictionary with response, sources, and metadata
        """
        if not query or not query.strip():
            return {
                "response": "I didn't receive a valid query. How can I help you with your skincare needs?",
                "agent_used": "none",
                "sources": [],
                "error": "Empty query",
            }

        # Route the query
        routing_info = route_query(query)
        intent = routing_info["intent"]
        agent_type = routing_info["agent"]

        print(f"\n📋 Query: {query}")
        print(f"🎯 Routing to: {agent_type} agent (intent: {intent})")

        try:
            # Route to appropriate agent
            if agent_type == "product" and self.product_agent:
                return self._invoke_agent(
                    self.product_agent, query, "product", chat_history
                )
            elif agent_type == "blog" and self.blog_agent:
                return self._invoke_agent(self.blog_agent, query, "blog", chat_history)
            else:
                return self._invoke_agent(
                    self.supervisor_agent, query, "supervisor", chat_history
                )

        except Exception as e:
            print(f"❌ Error processing query: {e}")
            return {
                "response": f"I encountered an error processing your request: {str(e)}. Please try again or rephrase your question.",
                "agent_used": agent_type,
                "sources": [],
                "error": str(e),
            }

    def _invoke_agent(
        self, agent, query: str, agent_type: str, chat_history: Optional[list]
    ) -> Dict[str, Any]:
        """Invoke a custom agent."""
        try:
            result = agent.run(query=query, chat_history=chat_history)

            # Extract sources from tool calls
            sources = []
            if "tool_calls" in result:
                for tool_call in result.get("tool_calls", []):
                    sources.append(
                        {
                            "type": agent_type,
                            "tool": tool_call.get("tool", "unknown"),
                            "observation": tool_call.get("result", "")[:200],
                        }
                    )

            return {
                "response": result.get("output", "No response generated"),
                "agent_used": agent_type,
                "sources": sources,
                "success": result.get("success", True),
            }
        except Exception as e:
            raise Exception(f"{agent_type.capitalize()} Agent error: {str(e)}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of all agents.

        Returns:
            Dictionary with health status of each agent
        """
        return {
            "orchestrator": "healthy",
            "product_agent": "healthy" if self.product_agent else "unavailable",
            "blog_agent": "healthy" if self.blog_agent else "unavailable",
            "supervisor_agent": "healthy" if self.supervisor_agent else "unavailable",
            "model": self.model_name,
        }
