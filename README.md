#  Open Claude Agent

Anthropic released the [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview#why-use-the-claude-agent-sdk%3F), a pre-built agent harness that powers [Claude Code](https://www.claude.com/product/claude-code). This is a minimal, simple, and open source agent harness that aims to reproduce some of these features in the Agent SDK. It uses Claude's native support for [filesystem tools](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool), [bash tools](https://docs.claude.com/en/docs/agents-and-tools/tool-use/bash-tool), [web search tools](https://docs.claude.com/en/docs/agents-and-tools/tool-use/web-search-tool), and [context editing](https://www.anthropic.com/news/context-management) together. 

## Quickstart

```bash
# Install uv if you haven't already (https://docs.astral.sh/uv/)
# curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies and install package in editable mode
uv sync
uv pip install -e .

# Set your API key
export ANTHROPIC_API_KEY=your_key_here
```

Now you can use the agent in Python scripts or Jupyter notebooks:

```python
from open_claude_agent import ClaudeAgent
import anthropic

# Create agent with all tools pre-configured
agent = ClaudeAgent(
    client=anthropic.Anthropic(),
    system_message="Your custom instructions here"  # Optional - combined with tool guidelines
)

# Use the agent
# Tool usage guidelines are automatically included
# Memory tool will use ./memories directory
# Bash and text editor tools work from current directory
agent.call("Give me an overview of context engineering.")
```

## Tools

The `ClaudeAgent` class provides a high-level interface with a few generally useful built-in tools (memory, file editing, bash, and web search), as discussed below.

### Memory Tool

Claude's [`memory tool`](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool) supports various filesystem operations, allowing Claude to store and retrieve information across conversations. You can think of this like a scratchpad for Claude.

**Important**: The memory tool is hardcoded to operate in the `./memories` directory (created automatically). This keeps Claude's personal notes separate from your project files. 

| Command | Description | Example Use Case |
|---------|-------------|------------------|
| `view` | List directory contents or read file contents | Check what files exist, read stored data |
| `create` | Create or overwrite a file | Save user preferences, store analysis results |
| `str_replace` | Replace text within a file | Update specific values in config files |
| `insert` | Insert text at a specific line | Add new entries to lists |
| `delete` | Delete a file or directory | Clean up temporary files |
| `rename` | Rename or move a file/directory | Reorganize stored information |

We have a handler for this tool in `src/open_claude_agent/tools/memory_tool.py`, which implements each of these operations locally. Anthropic automatically adds some basic instructions to the system prompt for tool usage (see doc below), which tells it to always view the memory directory before doing anything else.

**Reference**: [Claude Memory Tool Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool)

### Bash Tool

The bash tool gives Claude the ability to execute shell commands in a persistent session.

**Important**:
- The bash tool operates from the **current working directory** (your project root)
- Session state persists across commands (environment variables, working directory)
- All commands should use relative paths (e.g., `./file.txt`) not absolute paths (e.g., `/file.txt`)

| Command | Description | Example Use Case |
|---------|-------------|------------------|
| command | The bash command to run | Running tests, Git operations, System tasks, etc |

**Best Practices:**
- Use relative paths: `cd project_dir && ls` or `./script.sh`
- Session persists within a conversation, so `cd` commands affect subsequent commands
- Avoid absolute paths unless intentionally accessing system directories

We have a handler for this tool in `src/open_claude_agent/tools/bash_tool.py`, which includes command validation to block dangerous patterns, output sanitization, timeout protection, and audit logging.

**Reference**: [Claude Bash Tool Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/bash-tool)

### Text Editor Tool

Claude's [`text_editor tool`](https://docs.claude.com/en/docs/agents-and-tools/tool-use/text-editor-tool) provides file reading and editing capabilities with built-in safety features like automatic backups and exact text matching for replacements.

**Important**: The text editor tool operates from the current working directory (your project root), allowing Claude to read and edit files throughout your project.

| Command | Description | Example Use Case |
|---------|-------------|------------------|
| `view` | Read file contents or list directory contents | Browse codebase, review configurations, list files |
| `str_replace` | Replace specific text with new content | Fix bugs, update configurations, refactor code |
| `create` | Generate new files with content | Create new scripts, write documentation, add configs |
| `insert` | Add text at specific line locations | Add imports, insert functions, update code |
| `undo_edit` | Revert last file modification | Undo mistakes, restore previous version |

We have a handler for this tool in `src/open_claude_agent/tools/text_editor_tool.py`, which implements file operations with automatic backup creation before modifications, path validation to prevent directory traversal attacks, and support for viewing specific line ranges.

**Reference**: [Claude Text Editor Tool Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/text-editor-tool) 

### Web Search Tool

The web search tool is a **server-side tool** executed entirely by Anthropic's infrastructure. Unlike client-side tools (memory, bash, text editor), search requests and results are handled without requiring custom handlers.

**Reference**: [Claude Web Search Tool Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/web-search-tool)

## Skills

Skills extend Claude's capabilities by packaging domain-specific knowledge and tools into modular, reusable resources. Based on [Anthropic's skills architecture](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills), skills use progressive disclosure to manage context efficiently.

### How Skills Work

Skills follow a three-level progressive disclosure pattern:

1. **Level 1 - Metadata**: Skill `name` and `description` appear in the system prompt
2. **Level 2 - Documentation**: Claude reads full `SKILL.md` when the skill is relevant
3. **Level 3+ - Resources**: Additional files and scripts accessed only as needed

This approach allows agents to access "effectively unbounded" context since they don't need to load everything at once.

### Using Skills

Skills are enabled by default:

```python
from open_claude_agent import ClaudeAgent
import anthropic

# Skills automatically loaded from ./skills directory
agent = ClaudeAgent(
    client=anthropic.Anthropic(),
    enable_skills=True,      # Default: True
    skills_dir="./skills"    # Default: ./skills
)

# Claude sees skill metadata and can read full documentation when needed
agent.call("Help me research the history of transformer models")
```

### Creating Skills

Create a new skill by adding a directory under `skills/`:

```
skills/
└── my-skill/
    ├── SKILL.md         # Required: YAML frontmatter + documentation
    ├── reference.md     # Optional: additional docs
    └── script.py        # Optional: executable tools
```

**SKILL.md format:**

```markdown
---
name: my-skill
description: Brief description used for discovery
---

# Skill Title

## When to Use This Skill

Describe scenarios where this skill is relevant...

## How to Use

Step-by-step instructions...

## Scripts

If including executable code:

\`\`\`bash
python skills/my-skill/script.py --input data.csv
\`\`\`
```

### Example: Research Assistant

The included `skills/research-assistant/` demonstrates:
- Structured SKILL.md with workflow guidance
- Python script for report generation
- Integration with memory tool for note-taking
- Best practices for research workflows

See `skills/README.md` for a complete guide to creating skills.

### Skills vs Custom System Messages

- **Skills**: Modular, reusable, discoverable by Claude based on task relevance
- **System Message**: Global instructions that apply to all tasks

Skills complement custom system messages—use both together for specialized agents:

```python
agent = ClaudeAgent(
    client=anthropic.Anthropic(),
    system_message="You are a Python code reviewer",  # Custom role
    enable_skills=True  # Skills available when needed
)
```

**Reference**: [Anthropic: Equipping Agents with Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

## Testing

Integration tests are available to verify that each tool works correctly with the real Anthropic API.

### Running Tests

```bash
# Set your API key
export ANTHROPIC_API_KEY=your_key_here

# Run all tests using the test runner
./run_tests.sh

# Or run directly with pytest
uv run pytest tests/ -v
```

### Test Coverage

The test suite includes integration tests for all four tools:
- **Memory Tool**: Creates and reads files in `./memories`
- **Bash Tool**: Executes shell commands
- **Text Editor Tool**: Creates, modifies, and reads files
- **Web Search Tool**: Performs web searches

**Note**: These are integration tests that call the real Anthropic API, so they will incur API costs and require an active internet connection.

## Context Engineering

ClaudeAgent uses a few context engineering principles, derived from [Manus](https://rlancemartin.github.io/2025/10/15/manus/) and [Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).

### Context Reduction

ClaudeAgent uses Claude's [context editing](https://docs.claude.com/en/docs/build-with-claude/context-editing) feature to automatically clear the oldest tool results in chronological order, replacing them with placeholder text to let Claude know the tool result was removed. 

When context editing is enabled and your conversation approaches the clearing threshold, Claude automatically receives a warning notification. This prompts Claude to preserve any important information from tool results into memory files before those results are cleared from the context window. It will use the memory tool to do this.

### Context Offloading

ClaudeAgent uses Claude's [memory tool]( https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool) to save information in memory files. 

### Context Isolation

Placeholder: need to add this.

## Prompting Guidelines

### 1. Define Clear Concepts and Boundaries
- Be explicit about irreversibility: what actions should the agent avoid?
- Think through edge cases: how might the agent misinterpret instructions?
- Treat prompting like managing a new intern: be crisp and clear about expectations

### 2. Set Resource Budgets
- Simple queries: aim for under 5 tool calls
- Complex queries: may use 10-15 tool calls
- Explicit stopping conditions: tell the agent when it's okay to stop searching

### 3. Guide Tool Selection
- Specify which tools to use for which tasks
- Provide context-specific guidance (e.g., "search Slack for company info")
- Don't assume the model knows which tool is best without guidance

### 4. Guide the Thinking Process
- Ask the agent to plan before acting: complexity, tool budget, sources, success criteria
- Use interleaved thinking to reflect on tool results
- Encourage critical evaluation of web search results (may not be accurate)

### 5. Expect Unintended Side Effects
- Agents are more unpredictable than simple workflows
- Test prompts and be prepared to roll back changes
- Balance quality seeking with practical stopping points

### 6. Manage Context Window
- Use memory tool to write important information externally
- Consider compaction: summarize context when approaching limits
- Use sub-agents for complex tasks to compress information

### 7. Let Claude Be Claude
- Start with minimal prompts and tools
- See where it goes wrong, then iterate
- Claude is already good at being an agent - don't over-engineer

**Best Practices:**
- Be specific about the agent's role and capabilities
- Define clear workflows and decision criteria
- Include examples of good vs bad behavior
- Set boundaries and stopping conditions
- Reference tool usage patterns

**Reference**: [Anthropic Prompting Best Practices](https://youtu.be/XSZP9GhhuAc?si=mNyuktz7CZRAIcod&t=520)
