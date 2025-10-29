"""
Claude Agent with built-in tools.

This module provides a high-level agent interface that automatically configures
memory, bash, text editor, and web search tools. The memory tool operates in a
dedicated ./memories directory, while bash and text editor tools work from the
current working directory.
"""

import json
from typing import Optional
from .utils import format_anthropic_tool_call, format_anthropic_tool_result, display_claude_response
from .tools import MemoryToolHandler, BashToolHandler, TextEditorToolHandler
from .prompts import GENERAL_TOOL_USAGE_GUIDELINES


class ClaudeAgent:
    """
    A simplified Claude agent with built-in memory, bash, text editor, and web search tools.

    This class provides a high-level interface for creating agents with minimal configuration.
    All tools are automatically set up and configured.
    """

    def __init__(
        self,
        client,
        system_message: Optional[str] = None,
        model: str = "claude-sonnet-4-5",
        max_tokens: int = 8192,
        max_web_searches: int = 15,
        bash_timeout: int = 30
    ):
        """
        Initialize the Claude agent with built-in tools.

        Args:
            client: Anthropic API client instance
            system_message: Optional system prompt to guide Claude's behavior.
                          Will be combined with built-in tool usage guidelines.
            model: Model name to use (default: claude-sonnet-4-5)
            max_tokens: Maximum tokens for response (default: 8192)
            max_web_searches: Maximum web searches per request (default: 15)
            bash_timeout: Timeout for bash commands in seconds (default: 30)

        Note:
            - Tool usage guidelines are automatically included in the system message
            - Memory tool operates in ./memories directory (hardcoded, created automatically)
            - Bash and text editor tools operate in current working directory (project root)
            - Bash commands should use relative paths (./file.txt) not absolute paths (/file.txt)
        """
        self.client = client
        self.model = model
        self.max_tokens = max_tokens

        # Build the complete system message
        # Always include tool usage guidelines, optionally append user instructions
        if system_message:
            self.system_message = f"{GENERAL_TOOL_USAGE_GUIDELINES}\n\n{system_message}"
        else:
            self.system_message = GENERAL_TOOL_USAGE_GUIDELINES

        # Initialize tool handlers
        # Memory tool uses hardcoded ./memories directory
        self.memory_handler = MemoryToolHandler()
        # Bash tool operates from current working directory
        self.bash_handler = BashToolHandler(timeout=bash_timeout, working_dir=None)
        # Text editor tool operates from current working directory
        self.text_editor_handler = TextEditorToolHandler(base_path=None)

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
                "type": "text_editor_20250728",
                "name": "str_replace_based_edit_tool"  # API requires this specific name
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
            "memory": self.memory_handler.handle,
            "str_replace_based_edit_tool": self.text_editor_handler.handle
        }

        # Configure betas
        self.betas = ["context-management-2025-06-27"]

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
        # Initialize messages with the user message
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

            # Make API call to Claude with error handling
            try:
                response = self.client.beta.messages.create(**api_params)
            except Exception as e:
                # Handle API errors gracefully
                error_msg = f"API Error: {str(e)}"
                display_claude_response(error_msg)

                # If it's a validation error, provide helpful context
                if "invalid_request_error" in str(e):
                    display_claude_response("\nTip: This may be a configuration issue with tool definitions. Check that tool names and types match API requirements.")
                return

            # Check if Claude wants to use client-side tools
            if response.stop_reason == "tool_use":
                # Claude wants to use tools (client-side tools that need execution)
                # Note: Response may also contain server_tool_use blocks (already executed by Anthropic)
                assistant_message = {"role": "assistant", "content": []}

                for block in response.content:
                    assistant_message["content"].append(block.model_dump())

                    # Display server-side tool uses (like web_search)
                    # These are already executed by Anthropic, just display for visibility
                    if block.type == "server_tool_use":
                        format_anthropic_tool_call(block)

                    # Process client-side tool use blocks (bash, memory, text_editor)
                    # These need to be executed locally and results sent back
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
                # Claude has provided a final response (stop_reason != "tool_use")
                # This means Claude is done, even if it used server-side tools to get here
                # Server-side tools (like web_search) are already executed by Anthropic

                # Check for server-side tool uses and display them for visibility
                has_server_tool_use = any(
                    block.type == "server_tool_use" for block in response.content
                )

                if has_server_tool_use:
                    # Display what server-side tools were used
                    for block in response.content:
                        if block.type == "server_tool_use":
                            format_anthropic_tool_call(block)

                # Extract and display Claude's final answer
                final_text = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        final_text += block.text

                display_claude_response(final_text)
                return

        # If max turns reached, display a message
        display_claude_response("Maximum turns reached without final response")
