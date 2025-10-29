# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open Claude Agent is a minimal, open-source agent harness that reproduces key features from Anthropic's Claude Agent SDK. It implements a simple agent framework using Claude's native tool support (filesystem, bash, web search) combined with context management features.

## Development Setup

```bash
# Install dependencies using uv (required)
uv sync

# Set API key
export ANTHROPIC_API_KEY=your_key_here

# Run the agent (typically in Jupyter notebook)
# See notebooks/run_agent.ipynb for examples
```

## Architecture

### Core Components

**ClaudeAgent** (`src/open_claude_agent/claude_agent.py`):
- Main agent class that orchestrates tool usage and API interactions
- Automatically configures 4 built-in tools: memory, bash, text_editor, web_search
- Handles the conversation loop with Claude API, including tool use iterations
- Implements context management using Claude's context editing feature (clear_tool_uses_20250919)
- System messages are automatically composed: `GENERAL_TOOL_USAGE_GUIDELINES + custom_message`

**Tool Handlers** (`src/open_claude_agent/tools/`):
- `MemoryToolHandler`: Manages persistent storage in `./memories` directory (hardcoded path)
- `BashToolHandler`: Executes shell commands with validation, timeouts, and audit logging
- `TextEditorToolHandler`: Handles file operations with automatic backups and path validation
- Web search is server-side (no local handler needed)

**Utilities** (`src/open_claude_agent/utils.py`):
- Rich console formatting for tool calls, results, and Claude responses
- Functions to format and display Anthropic API messages
- Handles both client-side (tool_use) and server-side (server_tool_use) tool display

**Prompts** (`src/open_claude_agent/prompts.py`):
- `GENERAL_TOOL_USAGE_GUIDELINES`: Core instructions automatically included in every system message
- `RESEARCH_AGENT_PROMPT`: Pre-built research assistant system prompt
- `SIMPLE_RESEARCH_INSTRUCTIONS`: Lightweight research guidance

### Context Engineering

The agent implements three context management principles:

1. **Context Reduction**: Uses Claude's context editing to automatically clear oldest tool results when approaching token limits (configured at 100k tokens, keeping 5 most recent tool uses)

2. **Context Offloading**: Memory tool encourages Claude to save important information to files before context is cleared

3. **Context Isolation**: (Placeholder - not yet implemented)

### Tool Architecture

**Memory Tool** (Client-side):
- Operates exclusively in `./memories` directory
- Supports: view, create, str_replace, insert, delete, rename
- Path normalization removes virtual root prefixes (/memories, /scratchpad)

**Bash Tool** (Client-side):
- Operates from current working directory (project root)
- Persistent session state across commands
- Safety features: command validation, dangerous pattern blocking, timeouts
- Always use relative paths (e.g., `./file.txt`, not `/file.txt`)

**Text Editor Tool** (Client-side):
- Operates from current working directory
- Automatic backups before modifications
- Supports: view, str_replace, create, insert, undo_edit
- Path validation prevents directory traversal

**Web Search Tool** (Server-side):
- Executed entirely by Anthropic infrastructure
- No local handler needed
- Configurable max_uses parameter

### Message Flow

1. User sends message to `ClaudeAgent.call()`
2. Agent constructs API params with tools, system message, context management config
3. Calls `client.beta.messages.create()` with betas=["context-management-2025-06-27"]
4. Response handling:
   - If `stop_reason == "tool_use"`: Process client-side tools, add results to messages, continue loop
   - Server-side tools (web_search) are already executed, just displayed for visibility
   - Otherwise: Extract final text response and display to user
5. Loop continues up to `max_turns` (default: 15)

## Key Patterns

### Adding Custom Tools

To add a custom client-side tool:
1. Create handler class in `src/open_claude_agent/tools/`
2. Implement `handle(tool_input)` method returning result dict
3. Add tool definition to `self.tools` in ClaudeAgent.__init__
4. Register handler in `self.tool_handlers` dict
5. Import and export from `tools/__init__.py`

### Custom System Messages

```python
agent = ClaudeAgent(
    client=anthropic.Anthropic(),
    system_message="Your custom instructions"  # Appended after GENERAL_TOOL_USAGE_GUIDELINES
)
```

### Tool Result Format

Handlers should return dicts with consistent structure:
- Success: `{"message": "...", "type": "...", ...}`
- Error: `{"error": "error message"}`
- Bash: `{"exit_code": 0, "output": "...", "message": "..."}`

## Important Notes

- The memory tool path (`./memories`) is **hardcoded** and cannot be configured
- Bash and text editor tools operate from **current working directory** (not hardcoded)
- Virtual paths like `/memories` are normalized to `./memories` by the memory handler
- Server-side tools (web_search) don't need local handlers
- Context management is always enabled with the "context-management-2025-06-27" beta
- All system messages automatically include GENERAL_TOOL_USAGE_GUIDELINES

## Dependencies

- `anthropic>=0.40.0` - Claude API client
- `rich>=13.0.0` - Terminal formatting
- `jupyter>=1.0.0`, `ipykernel>=6.29.0` - Notebook support
