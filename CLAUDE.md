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
- System messages automatically composed: `GENERAL_TOOL_USAGE_GUIDELINES + skills_metadata + custom_message`
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
  - Special visualization for skill loading: detects when bash commands are reading SKILL.md files
  - Shows "📚 Loading Skill: skill-name" with blue border instead of regular bash formatting
- `format_anthropic_tool_result()`: Shows success/error states with color coding
  - Detects skill loading results and displays "✓ Skill Loaded: skill-name" with blue styling
- `detect_skill_usage()`: Helper function to detect when bash commands are loading skills
- `display_claude_response()`: Final response display

**Prompts** (`src/open_claude_agent/prompts.py`):
- `GENERAL_TOOL_USAGE_GUIDELINES`: Core instructions automatically included in every system message

Note: Research guidance is now available through the `web-research` skill (bundled at `src/open_claude_agent/skills/web-research/SKILL.md`).

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

### Skills System

The agent supports modular skills that package domain-specific expertise and tools. Skills follow Anthropic's progressive disclosure architecture for efficient context management.

**Skill Loader** (`src/open_claude_agent/skill_loader.py`):
- `SkillLoader` class scans skills directory for subdirectories containing `SKILL.md`
- Parses YAML frontmatter to extract `name` and `description` metadata
- Formats metadata into system message section (Level 1: Progressive Disclosure)
- Convenience function `load_skills(skills_dir)` returns formatted context string

**Skills Directory Structure** (bundled at `src/open_claude_agent/skills/`):
```
src/open_claude_agent/skills/
└── skill-name/
    ├── SKILL.md         # Required: YAML frontmatter + documentation
    ├── reference.md     # Optional: additional docs
    └── script.py        # Optional: executable code
```

**Progressive Disclosure (3 Levels)**:
1. **Metadata**: Skill name and description loaded into system prompt at initialization
2. **Core Content**: Full `SKILL.md` read via bash tool when skill is relevant
3. **Resources**: Additional files and scripts accessed only as needed

**Integration with ClaudeAgent**:
- New parameters:
  - `skills_dir` (default: `None` - auto-resolves to `src/open_claude_agent/skills/`)
  - `enable_skills` (default: `True`)
- Path resolution: When `skills_dir=None`, automatically resolves to the bundled skills directory at `src/open_claude_agent/skills/`
- System message construction: `GENERAL_TOOL_USAGE_GUIDELINES + skills_metadata + custom_message`
- Skills loaded once during `__init__`, not on every `call()`
- No new tools needed - uses existing bash tool for file reading and script execution

**Usage Pattern**:
```python
# Skills enabled by default (uses bundled skills)
agent = ClaudeAgent(client=client)

# Custom skills directory (absolute or relative to CWD)
agent = ClaudeAgent(client=client, skills_dir="/absolute/path/to/skills")
agent = ClaudeAgent(client=client, skills_dir="./my-custom-skills")

# Disable skills
agent = ClaudeAgent(client=client, enable_skills=False)
```

**Skill Discovery and Execution**:
1. Agent sees all skill names/descriptions in system prompt (Level 1)
2. When task matches a skill, agent reads the SKILL.md using the absolute path from metadata (Level 2)
3. Agent follows instructions, potentially running scripts using paths provided in the skill documentation (Level 3)

**Best Practices for SKILL.md**:
- **File References**: Skills should reference their own resources using absolute paths (provided in metadata)
- **YAML Frontmatter**: Required at the top with `name` and `description` fields
- **Clear Instructions**: Provide explicit usage examples; paths are provided via metadata
- **Resource Organization**: Keep related files in the same skill directory

**Bundled Skills**:
- `arxiv-search`: arXiv paper search with Python script
- `pubmed-search`: PubMed database search with Python script
- `web-research`: Comprehensive web research workflow (prompt-based)
- See `src/open_claude_agent/skills/README.md` for skill creation guide

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
    system_message="Your custom instructions"  # Appended after guidelines and skills
)
```

System message composition order:
1. `GENERAL_TOOL_USAGE_GUIDELINES` (always included)
2. Skills metadata (if `enable_skills=True`)
3. Custom `system_message` (if provided)

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
