# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open Claude Agent is a minimal, open-source agent harness that reproduces key features from Anthropic's Claude Agent SDK. It implements a simple agent framework using Claude's native tool support (filesystem, bash, web search) combined with context management features.

## Development Setup

```bash
# Install dependencies using uv (required)
uv sync

# Install package in editable mode
uv pip install -e .

# Set API key
export ANTHROPIC_API_KEY=your_key_here

# Run the agent (typically in Jupyter notebook)
# See sandbox/run_agent.ipynb for examples
```

## Architecture

### Core Components

**ClaudeAgent** (`src/open_claude_agent/claude_agent.py`):
- Main agent class orchestrating tool usage and API interactions
- Automatically configures 4 built-in tools: memory, bash, text_editor, web_search
- Implements conversation loop with tool use iterations (max 15 turns by default)
- Uses context management via Claude's context editing feature (clear_tool_uses_20250919)
- System messages automatically composed: `GENERAL_TOOL_USAGE_GUIDELINES + custom_message`
- Three response handling paths in the loop:
  1. Server-side tools only: Display results, continue loop
  2. Client-side tools only: Execute locally, add results to messages, continue loop
  3. Mixed server/client tools: Handle both in sequence
  4. No tools: Extract final response, display, exit loop

**Tool Handlers** (`src/open_claude_agent/tools/`):
- Each handler implements `handle(tool_input)` method returning result dict
- `MemoryToolHandler`: Operates exclusively in `./memories` directory (hardcoded, auto-created)
- `BashToolHandler`: Persistent session, command validation, timeout protection, audit logging
- `TextEditorToolHandler`: Automatic backups before modifications, path validation
- Web search is server-side (no local handler needed)

**Utilities** (`src/open_claude_agent/utils.py`):
- Rich console formatting using panels and styled text
- `format_anthropic_tool_call()`: Displays both client-side (tool_use) and server-side (server_tool_use) tool calls
- `format_anthropic_tool_result()`: Shows success/error states with color coding
- `display_claude_response()`: Final response display

**Prompts** (`src/open_claude_agent/prompts.py`):
- `GENERAL_TOOL_USAGE_GUIDELINES`: Core instructions automatically included in every system message
- `RESEARCH_AGENT_PROMPT`: Pre-built research assistant with planning guidance
- `SIMPLE_RESEARCH_INSTRUCTIONS`: Lightweight research guidance

### Context Engineering

Three context management principles:

1. **Context Reduction**: Automatically clears oldest tool results when approaching token limits
   - Trigger: 100k input tokens
   - Keep: 5 most recent tool uses
   - Cleared results replaced with placeholders

2. **Context Offloading**: Memory tool saves important information before context is cleared
   - Claude receives warning when approaching clearing threshold
   - Encouraged to preserve key information to `./memories` directory

3. **Context Isolation**: Placeholder - not yet implemented

### Tool Architecture Details

**Memory Tool** (Client-side):
- Path normalization: removes `/memories` or `/scratchpad` virtual root prefixes
- Security: validates paths stay within `./memories` directory
- Commands: view, create, str_replace, insert, delete, rename
- Path handling: `/memories/file.txt` → `./memories/file.txt`

**Bash Tool** (Client-side):
- Working directory: current directory (project root)
- Session persists across commands within a conversation
- Safety: blocks dangerous patterns (rm -rf, etc.), enforces timeouts
- Always use relative paths: `./file.txt` not `/file.txt`

**Text Editor Tool** (Client-side):
- Working directory: current directory (project root)
- Backup system: creates `.backup` files before modifications
- Commands: view, str_replace, create, insert, undo_edit
- Path validation prevents directory traversal attacks

**Web Search Tool** (Server-side):
- Executed entirely by Anthropic infrastructure
- No local handler needed
- Configurable `max_uses` parameter (default: 15)
- Results returned as text blocks following `server_tool_use` blocks

### Message Flow

1. User calls `agent.call(user_message)`
2. Agent builds API params:
   - Tools configuration
   - System message (guidelines + custom)
   - Context management config
   - Betas: `["context-management-2025-06-27"]`
3. Calls `client.beta.messages.create()`
4. Response handling loop:
   - Server-side tools: Already executed, display results, continue
   - Client-side tools: Execute locally via handlers, add results to messages, continue
   - Mixed tools: Handle server results first, then client tools
   - No tools: Extract text, display, return messages
5. Loop continues up to `max_turns` (default: 15) or until final response

## Key Patterns

### Adding Custom Tools

To add a custom client-side tool:
1. Create handler class in `src/open_claude_agent/tools/` with `handle(tool_input)` method
2. Add tool definition to `self.tools` in `ClaudeAgent.__init__` (specify type and name)
3. Register handler in `self.tool_handlers` dict: `{tool_name: handler.handle}`
4. Import and export from `tools/__init__.py`

Example tool definition:
```python
{
    "type": "custom_tool_20240101",
    "name": "my_custom_tool"
}
```

### Custom System Messages

```python
agent = ClaudeAgent(
    client=anthropic.Anthropic(),
    system_message="Your custom instructions"  # Appended after GENERAL_TOOL_USAGE_GUIDELINES
)
```

### Tool Result Format

Handlers should return dicts with consistent structure:
- Success: `{"message": "operation successful", "type": "file|directory", ...}`
- Error: `{"error": "error message"}`
- Bash: `{"exit_code": 0, "output": "stdout", "message": "...", "error": "stderr"}`

## Important Constraints

- Memory tool path (`./memories`) is **hardcoded** and cannot be configured
- Bash and text editor tools operate from **current working directory** (configurable but defaults to None = cwd)
- Virtual paths like `/memories` are normalized to `./memories` by the memory handler
- Server-side tools (web_search) don't need local handlers - executed by Anthropic
- Context management always enabled with `"context-management-2025-06-27"` beta
- All system messages automatically include `GENERAL_TOOL_USAGE_GUIDELINES`
- Bash commands should use relative paths (e.g., `./file.txt`) not absolute paths (e.g., `/file.txt`)

## Dependencies

- `anthropic>=0.40.0` - Claude API client with beta features
- `rich>=13.0.0` - Terminal formatting and display
- `jupyter>=1.0.0`, `ipykernel>=6.29.0` - Notebook support for interactive use
