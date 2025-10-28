"""
Simplified Claude Agent with built-in tools.

This module provides a high-level agent interface that automatically configures
memory, bash, and web search tools. Users only need to provide instructions and
a scratchpad directory.
"""

import json
from pathlib import Path
from typing import Optional
from utils import format_anthropic_tool_call, format_anthropic_tool_result, display_claude_response
from tools import MemoryToolHandler, BashToolHandler


class ClaudeAgent:
    """
    A simplified Claude agent with built-in memory, bash, and web search tools.

    This class provides a high-level interface for creating agents with minimal configuration.
    All tools are automatically set up and configured.
    """

    def __init__(
        self,
        client,
        scratchpad_dir: str = "./scratchpad",
        system_message: Optional[str] = None,
        model: str = "claude-sonnet-4-5",
        max_tokens: int = 8192,
        max_web_searches: int = 15,
        bash_timeout: int = 60
    ):
        """
        Initialize the Claude agent with built-in tools.

        Args:
            client: Anthropic API client instance
            scratchpad_dir: Directory for persistent storage (memory and bash working dir)
            system_message: Optional system prompt to guide Claude's behavior
            model: Model name to use (default: claude-sonnet-4-5)
            max_tokens: Maximum tokens for response (default: 8192)
            max_web_searches: Maximum web searches per request (default: 15)
            bash_timeout: Timeout for bash commands in seconds (default: 60)
        """
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.system_message = system_message

        # Set up scratchpad directory
        self.scratchpad_path = Path(scratchpad_dir)
        self.scratchpad_path.mkdir(exist_ok=True)

        # Initialize tool handlers
        self.memory_handler = MemoryToolHandler(base_path=scratchpad_dir)
        self.bash_handler = BashToolHandler(timeout=bash_timeout, working_dir=scratchpad_dir)

        # Configure tools
        self.tools = [
            {
                "type": "bash_20250124",
                "name": "bash"
            },
            {
                "type": "memory_20250818",
                "name": "memory"
            },
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": max_web_searches
            }
        ]

        # Map tool names to handlers (web_search handled server-side)
        self.tool_handlers = {
            "bash": self.bash_handler.handle,
            "memory": self.memory_handler.handle
        }

        # Configure betas
        self.betas = ["computer-use-2025-01-24", "context-management-2025-06-27"]

        # Configure context management
        self.context_management = {
            "edits": [
                {
                    "type": "clear_tool_uses_20250919",
                    "trigger": {
                        "type": "input_tokens",
                        "value": 100000
                    },
                    "keep": {
                        "type": "tool_uses",
                        "value": 5
                    }
                }
            ]
        }

    def call(self, user_message: str, max_turns: int = 15):
        """
        Send a message to Claude and handle tool use iterations.

        This method:
        1. Sends the user message to Claude with configured tools
        2. Processes any tool use requests from Claude
        3. Sends tool results back to Claude
        4. Displays Claude's final response

        Args:
            user_message: The message to send to Claude
            max_turns: Maximum number of tool use iterations (default: 15)
        """
        messages = [{"role": "user", "content": user_message}]

        for _ in range(max_turns):
            # Build API call parameters
            api_params = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages,
                "tools": self.tools,
                "betas": self.betas,
                "context_management": self.context_management
            }

            if self.system_message:
                api_params["system"] = self.system_message

            # Make API call to Claude
            response = self.client.beta.messages.create(**api_params)

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Extract text response (if any) and tool uses
                assistant_message = {"role": "assistant", "content": []}

                for block in response.content:
                    assistant_message["content"].append(block.model_dump())

                    # Display server-side tool uses (like web_search) that may be mixed with client-side tools
                    if block.type == "server_tool_use":
                        format_anthropic_tool_call(block)

                    # Process client-side tool use blocks
                    elif block.type == "tool_use":
                        tool_name = block.name

                        # Display tool call
                        format_anthropic_tool_call(block)

                        # Execute the tool if handler exists
                        if tool_name in self.tool_handlers:
                            result = self.tool_handlers[tool_name](block.input)
                        else:
                            result = {
                                "error": f"No handler registered for tool: {tool_name}"
                            }

                        # Display tool result
                        format_anthropic_tool_result(result)

                        # Add tool result to messages
                        messages.append(assistant_message)
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result)
                            }]
                        })

                # Continue the loop to get Claude's next response
                continue

            else:
                # Check for server-side tool uses (like web_search)
                # These are executed by Anthropic and don't need client-side handling
                has_server_tool_use = any(
                    block.type == "server_tool_use" for block in response.content
                )

                if has_server_tool_use:
                    # Display server-side tool calls for visibility
                    for block in response.content:
                        if block.type == "server_tool_use":
                            format_anthropic_tool_call(block)

                # Claude provided a final response without tool use
                final_text = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        final_text += block.text

                # Display the response
                display_claude_response(final_text)
                return

        # If max turns reached, display a message
        display_claude_response("Maximum turns reached without final response")
