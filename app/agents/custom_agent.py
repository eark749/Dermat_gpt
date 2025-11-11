"""
Custom Agent implementation using OpenAI function calling.
No LangChain dependencies - just clean Python + OpenAI API.
"""

import os
from typing import List, Dict, Any, Callable, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class CustomTool:
    """Simple tool wrapper for OpenAI function calling."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function: Callable,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.function = function

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def execute(self, **kwargs) -> str:
        """Execute the tool function."""
        try:
            return self.function(**kwargs)
        except Exception as e:
            return f"Error executing {self.name}: {str(e)}"


class CustomAgent:
    """
    Simple custom agent using OpenAI function calling.
    Cleaner and more reliable than LangChain.
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: List[CustomTool],
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_iterations: int = 5,
        openai_api_key: Optional[str] = None,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = {tool.name: tool for tool in tools}
        self.model = model
        self.temperature = temperature
        self.max_iterations = max_iterations

        # Initialize OpenAI client
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=api_key)

    def run(
        self, query: str, chat_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Run the agent on a query.

        Args:
            query: User query
            chat_history: Optional chat history

        Returns:
            Dictionary with response and metadata
        """
        # Initialize messages
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add chat history if provided
        if chat_history:
            messages.extend(chat_history)

        # Add user query
        messages.append({"role": "user", "content": query})

        # Prepare tools for OpenAI
        openai_tools = [tool.to_openai_format() for tool in self.tools.values()]

        # Agent loop
        iterations = 0
        tool_calls_made = []

        while iterations < self.max_iterations:
            iterations += 1

            try:
                # Call OpenAI
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=openai_tools if openai_tools else None,
                    tool_choice="auto" if openai_tools else None,
                    temperature=self.temperature,
                )

                message = response.choices[0].message

                # Check if we're done
                if not message.tool_calls:
                    # No tool calls, we have final answer
                    return {
                        "output": message.content,
                        "tool_calls": tool_calls_made,
                        "iterations": iterations,
                        "success": True,
                    }

                # Process tool calls
                messages.append(
                    {
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in message.tool_calls
                        ],
                    }
                )

                # Execute tools
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = eval(tool_call.function.arguments)  # Parse JSON

                    print(f"🔧 Calling tool: {tool_name}")

                    # Execute tool
                    if tool_name in self.tools:
                        result = self.tools[tool_name].execute(**tool_args)
                    else:
                        result = f"Error: Tool {tool_name} not found"

                    # Add tool result to messages
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": str(result),
                        }
                    )

                    tool_calls_made.append(
                        {
                            "tool": tool_name,
                            "args": tool_args,
                            "result": str(result)[:200],  # Truncate
                        }
                    )

            except Exception as e:
                return {
                    "output": f"Agent error: {str(e)}",
                    "tool_calls": tool_calls_made,
                    "iterations": iterations,
                    "success": False,
                    "error": str(e),
                }

        # Max iterations reached
        return {
            "output": "Max iterations reached. Please try rephrasing your query.",
            "tool_calls": tool_calls_made,
            "iterations": iterations,
            "success": False,
            "error": "Max iterations exceeded",
        }
