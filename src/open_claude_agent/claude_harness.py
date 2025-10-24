"""
Reusable harness for interacting with Claude API with configurable tools.

This module provides a flexible framework for making Claude API calls with
different tool configurations, allowing for easy reuse across different tool types
like memory, bash, etc.
"""

import json
from typing import Dict, Any, List, Callable, Optional
from utils import format_anthropic_tool_call, format_anthropic_tool_result, display_claude_response


class ClaudeHarness:
    """
    A reusable harness for Claude API interactions with configurable tools.

    This class handles the tool execution loop, managing the conversation flow
    between Claude and tool handlers.
    """

    def __init__(
        self,
        client,
        model: str = "claude-sonnet-4-5",
        max_tokens: int = 4096,
        tools: List[Dict[str, Any]] = None,
        betas: List[str] = None,
        context_management: Optional[Dict[str, Any]] = None,
        tool_handlers: Optional[Dict[str, Callable]] = None
    ):
        """
        Initialize the Claude harness.

        Args:
            client: Anthropic API client instance
            model: Model name to use (default: claude-sonnet-4-5)
            max_tokens: Maximum tokens for response (default: 4096)
            tools: List of tool definitions for Claude
            betas: List of beta features to enable
            context_management: Context management configuration
            tool_handlers: Dictionary mapping tool names to handler functions
        """
        self.client = client
        self.model = model
        self.max_tokens = max_tokens
        self.tools = tools or []
        self.betas = betas or []
        self.context_management = context_management
        self.tool_handlers = tool_handlers or {}

    def call(self, user_message: str, max_turns: int = 5):
        """
        Send a message to Claude and handle tool use iterations.

        This method:
        1. Sends the user message to Claude with configured tools
        2. Processes any tool use requests from Claude
        3. Sends tool results back to Claude
        4. Displays Claude's final response

        Args:
            user_message: The message to send to Claude
            max_turns: Maximum number of tool use iterations to prevent infinite loops
        """
        messages = [{"role": "user", "content": user_message}]

        for turn in range(max_turns):
            # Build API call parameters
            api_params = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": messages,
            }

            if self.tools:
                api_params["tools"] = self.tools

            if self.betas:
                api_params["betas"] = self.betas

            if self.context_management:
                api_params["context_management"] = self.context_management

            # Make API call to Claude
            if self.betas:
                response = self.client.beta.messages.create(**api_params)
            else:
                response = self.client.messages.create(**api_params)

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Extract text response (if any) and tool uses
                assistant_message = {"role": "assistant", "content": []}

                for block in response.content:
                    assistant_message["content"].append(block.model_dump())

                    # Process tool use blocks
                    if block.type == "tool_use":
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
