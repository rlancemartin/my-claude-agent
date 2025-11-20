"""
Claude Agent with built-in tools.

This module provides a high-level agent interface that automatically configures
memory, bash, text editor, and web search tools. The memory tool operates in a
dedicated ./memories directory, while bash and text editor tools work from the
current working directory.
"""

import json
import os
from pathlib import Path
from typing import Optional
from .utils import format_anthropic_tool_call, format_anthropic_tool_result, display_claude_response
from .tools import MemoryToolHandler, BashToolHandler, TextEditorToolHandler
from .prompts import GENERAL_TOOL_USAGE_GUIDELINES
from .skill_loader import load_skills


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
        bash_timeout: int = 30,
        skills_dir: Optional[str] = None,
        enable_skills: bool = True
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
            skills_dir: Path to skills directory. If None, defaults to src/open_claude_agent/skills
                       (bundled with the package). Can be overridden with an absolute path or a
                       path relative to CWD.
            enable_skills: Whether to load and use skills (default: True)

        Note:
            - Tool usage guidelines are automatically included in the system message
            - Skills metadata (if enabled) is injected after guidelines, before custom message
            - Memory tool operates in ./memories directory (hardcoded, created automatically)
            - Bash and text editor tools operate in current working directory (project root)
            - Bash commands should use relative paths (./file.txt) not absolute paths (/file.txt)
        """
        self.client = client
        self.model = model
        self.max_tokens = max_tokens

        # Build the complete system message
        # Components: tool usage guidelines + skills metadata + user instructions
        message_components = [GENERAL_TOOL_USAGE_GUIDELINES]

        # Load and inject skills metadata (Level 1: Progressive Disclosure)
        if enable_skills:
            # Resolve skills directory path
            if skills_dir is None:
                # Default: skills directory next to this file
                # This file is at: src/open_claude_agent/claude_agent.py
                # Skills dir is at: src/open_claude_agent/skills
                package_file = Path(__file__)
                resolved_skills_dir = str(package_file.parent / "skills")
            else:
                resolved_skills_dir = skills_dir

            skills_context = load_skills(resolved_skills_dir)
            if skills_context:
                message_components.append(skills_context)

        # Append user's custom system message
        if system_message:
            message_components.append(system_message)

        self.system_message = "\n\n".join(message_components)

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

        This method implements an agent loop that continues until Claude provides a final
        response without using any tools. The loop handles:

        - Client-side tools (bash, memory, text_editor): Executes locally and sends results back
        - Server-side tools (web_search): Already executed by Anthropic, but we continue the loop
          to allow Claude to process results and potentially do more work (e.g., follow-up searches)

        Loop exit conditions:
        - Claude provides a response with stop_reason != "tool_use" AND no server_tool_use blocks
        - Maximum turns reached (default: 15)
        - API error occurs (after adding error to conversation for potential recovery)

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

            # Add system message to API parameters if provided
            if self.system_message:
                api_params["system"] = self.system_message

            try:
                # Make API call to Claude
                response = self.client.beta.messages.create(**api_params)

            except Exception as e:    
                # Create error messages 
                error_msg = f"API Error: {str(e)}"
                
                # Display error message to user 
                display_claude_response(error_msg)
                
                # Add error message to messages to aid in recovery
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": f"Error occurred: {error_msg}. Please try a different approach or ask for clarification."
                    }]
                })

                # Continue the loop to allow recovery
                continue

            # Check what types of tools are in the response
            has_server_tool_use = any(
                block.type == "server_tool_use" for block in response.content
            )
            has_client_tool_use = response.stop_reason == "tool_use"

            # Handle server-side tools only (no client-side tools present)
            if has_server_tool_use and not has_client_tool_use:
                # Build assistant message
                assistant_message = {"role": "assistant", "content": []}

                # Track text blocks and whether we've seen server tools
                seen_server_tool = False
                all_text_blocks = []

                for block in response.content:
                    # Add all content blocks to assistant message
                    assistant_message["content"].append(block.model_dump())

                    # Display text blocks before server tools as thinking
                    if block.type == "text" and not seen_server_tool and block.text.strip():
                        display_claude_response(f"💭 Thinking: {block.text}")

                    # Display server-side tool call when we encounter it
                    elif block.type == "server_tool_use":
                        format_anthropic_tool_call(block)
                        seen_server_tool = True

                    # Collect text blocks after server tools (these are the results)
                    elif block.type == "text" and seen_server_tool:
                        all_text_blocks.append(block.text)

                # Display the collected text as the tool result
                if all_text_blocks:
                    combined_text = "".join(all_text_blocks)
                    format_anthropic_tool_result({
                        "message": "Server-side tool completed",
                        "response_preview": combined_text[:1000] + ("..." if len(combined_text) > 1000 else "")
                    })

                # Add assistant message to conversation
                messages.append(assistant_message)

                # Continue the loop to get Claude's next response
                continue

            # Handle client-side tools only (no server-side tools present)
            if has_client_tool_use and not has_server_tool_use:
                # Build assistant message and collect tool results
                assistant_message = {"role": "assistant", "content": []}
                tool_results = []

                # Process blocks and display thinking/text before tool calls
                for block in response.content:
                    # Add all content blocks to assistant message
                    assistant_message["content"].append(block.model_dump())

                    # Display text blocks (Claude's thought process)
                    if block.type == "text" and block.text.strip():
                        display_claude_response(f"💭 Thinking: {block.text}")

                    # Process client-side tool use blocks
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

                        # Display tool result (pass tool context for skill detection)
                        format_anthropic_tool_result(result, tool_name=tool_name, tool_input=block.input)

                        # Collect tool result for adding to messages
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result)
                        })

                # Add assistant message to conversation
                messages.append(assistant_message)

                # Add all client-side tool results as a single user message
                if tool_results:
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })

                # Continue the loop to get Claude's next response
                continue

            # Handle BOTH server-side and client-side tools in the same response
            if has_server_tool_use and has_client_tool_use:
                # Build assistant message and collect tool results
                assistant_message = {"role": "assistant", "content": []}
                tool_results = []

                # Track whether we've seen server tools and collect text before client tools
                seen_server_tool = False
                server_text_blocks = []

                for block in response.content:
                    # Add all content blocks to assistant message
                    assistant_message["content"].append(block.model_dump())

                    # Display text blocks before any tools as thinking
                    if block.type == "text" and not seen_server_tool and block.text.strip():
                        display_claude_response(f"💭 Thinking: {block.text}")

                    # Display server-side tool call when we encounter it
                    elif block.type == "server_tool_use":
                        format_anthropic_tool_call(block)
                        seen_server_tool = True

                    # Collect text blocks (server tool results) after server tools
                    elif block.type == "text" and seen_server_tool:
                        server_text_blocks.append(block.text)

                    # Process client-side tool use blocks
                    elif block.type == "tool_use":
                        # Display server tool results if we haven't yet
                        if server_text_blocks:
                            combined_text = "".join(server_text_blocks)
                            format_anthropic_tool_result({
                                "message": "Server-side tool completed",
                                "response_preview": combined_text[:500] + ("..." if len(combined_text) > 500 else "")
                            })
                            server_text_blocks = []
                            seen_server_tool = False

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

                        # Display tool result (pass tool context for skill detection)
                        format_anthropic_tool_result(result, tool_name=tool_name, tool_input=block.input)

                        # Collect tool result for adding to messages
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result)
                        })

                # Display any remaining server tool results
                if server_text_blocks:
                    combined_text = "".join(server_text_blocks)
                    format_anthropic_tool_result({
                        "message": "Server-side tool completed",
                        "response_preview": combined_text[:500] + ("..." if len(combined_text) > 500 else "")
                    })

                # Add assistant message to conversation
                messages.append(assistant_message)

                # Add all client-side tool results as a single user message
                if tool_results:
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })

                # Continue the loop to get Claude's next response
                continue

            # No tools used - this is the final response
            else:
                # Claude has provided a final response with no tool use
                # stop_reason is likely "end_turn" or "max_tokens"
                # No tools were used (neither client-side nor server-side)

                # Build assistant message
                assistant_message = {"role": "assistant", "content": []}
                for block in response.content:
                    assistant_message["content"].append(block.model_dump())

                # Extract and display Claude's final answer
                final_text = ""
                for block in response.content:
                    if hasattr(block, 'text'):
                        final_text += block.text

                display_claude_response(final_text)

                # Add final assistant message to conversation
                messages.append(assistant_message)
                return messages

        # If max turns reached, display a message
        display_claude_response("Maximum turns reached without final response")
