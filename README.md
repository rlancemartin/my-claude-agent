#  Open Claude Agent

Anthropic released the [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/overview#why-use-the-claude-agent-sdk%3F), a pre-built agent harness that powers [Claude Code](https://www.claude.com/product/claude-code). This is a minimal, simple, and open source harness that aims to reproduce some of these features in the Agent SDK. It uses Claude's native support for [filesystem tools](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool), [bash tools](https://docs.claude.com/en/docs/agents-and-tools/tool-use/bash-tool), [web search tools](https://docs.claude.com/en/docs/agents-and-tools/tool-use/web-search-tool), and [context editing](https://www.anthropic.com/news/context-management) together. 

## Quickstart

```bash
# Install uv if you haven't already (https://docs.astral.sh/uv/)
# curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (creates venv and installs everything from pyproject.toml)
uv sync

# Set your API key
export ANTHROPIC_API_KEY=your_key_here

# Placeholder: Later will add the ability to pip install, leave this blank for now.

from open_claude_agent import ClaudeAgent
import anthropic

# Create agent with all tools pre-configured
agent = ClaudeAgent(
    client=anthropic.Anthropic(),
    scratchpad_dir="./scratchpad",  # Where to store memory & run bash
    system_message="Your custom instructions here"  # Optional
)

# Use the agent
agent.call("Give me an overview of context engineering.")
```

## Overview  

The `ClaudeAgent` class provides a high-level interface with a few generally useful built-in tools (filesystem, bash, web search), as discussed below.

### Filesystem Tool
 
*Store and retrieve persistent information across conversations*

This uses Claude's native support for filesystem tools. You supply the scratchpad directory, and it allows Claude to save information across conversations and maintain context even after context management clears old messages. 

**How it works:**

- Files are stored in `{scratchpad_dir}`
- Claude can organize information into subdirectories
- All paths in tool calls are relative to `/scratchpad_dir/` root

**When Claude Uses This Tool:**
- **Storing user preferences**: Save settings, favorite configurations, or personal information
- **Building knowledge bases**: Accumulate facts, research findings, or project context over time
- **Maintaining state**: Track progress on multi-session tasks
- **Learning from interactions**: Remember user feedback, corrections, or specific instructions
- **Data persistence**: Keep structured data (JSON, CSV) that needs to survive conversation resets

Claude proactively uses memory when it recognizes information worth preserving for future interactions.

**Tool Handler:**
Handler for the memory tool is provided in the `src/open_claude_agent/tools/memory_tool.py` file with the following commands for each of the tools that Claude can use.

| Command | Description | Example Use Case |
|---------|-------------|------------------|
| `view` | List directory contents or read file contents | Check what files exist, read stored data |
| `create` | Create or overwrite a file | Save user preferences, store analysis results |
| `str_replace` | Replace text within a file | Update specific values in config files |
| `insert` | Insert text at a specific line | Add new entries to lists |
| `delete` | Delete a file or directory | Clean up temporary files |
| `rename` | Rename or move a file/directory | Reorganize stored information |

**Reference**: [Claude Memory Tool Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool)

### Bash Tool
*Execute shell commands in the scratchpad directory*

The bash tool gives Claude the ability to execute shell commands within your scratchpad directory.

**When Claude Uses This Tool:**
- **File operations**: Create, modify, move, or delete files beyond what memory tool provides
- **Data processing**: Run scripts to transform, analyze, or aggregate data
- **System queries**: Check file sizes, count lines, search text with grep/sed/awk
- **Package management**: Install dependencies or run package managers (npm, pip, etc.)
- **Testing & validation**: Execute test suites, linters, or format checkers
- **Build processes**: Compile code, bundle assets, or generate documentation
- **Version control**: Run git commands to check status, commit changes, or view diffs

Claude uses bash when tasks require:
1. Complex file manipulations beyond simple read/write
2. Existing command-line tools (git, grep, jq, etc.)
3. Scripting or automation workflows
4. Verification of operations (checking file existence, content validation)

**Tool Handler:**
Handler for the bash tool is provided in the `src/open_claude_agent/tools/bash_tool.py` file.

| Feature | Description | Example Use Case |
|---------|-------------|------------------|
| Command execution | Run any bash command with timeout protection | Create files, process data, run scripts |
| Working directory | Commands execute in isolated scratchpad | Keep test files separate from source |
| Output capture | Captures stdout, stderr, and exit codes | Verify command success, read results |

**Reference**: [Claude Bash Tool Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/bash-tool)

### Web Search Tool
*Real-time web search powered by server-side execution*

The web search tool is a **server-side tool** executed entirely by Anthropic's infrastructure. Unlike client-side tools (memory, bash), search requests and results are handled transparently without requiring custom handlers.

| Feature | Description | Example Use Case |
|---------|-------------|------------------|
| Server-side execution | Searches run on Anthropic's servers, not your machine | No local infrastructure needed |
| Real-time results | Access current web information | Research latest developments, verify facts |
| Citation support | Results include source citations | Track information provenance |
| Rate limiting | Configure max searches per request | Control API costs |

**Reference**: [Claude Web Search Tool Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/web-search-tool)

### Context Management
*Automatic conversation history management*

Context editing automatically manages conversation history as it grows, removing older content when prompts exceed configured thresholds. This enables long-running agentic workflows without manual history trimming.

| Feature | Description | Example Use Case |
|---------|-------------|------------------|
| Automatic clearing | Removes old tool results when context grows | Long conversations with many tool calls |
| Smart preservation | Keeps recent tool interactions intact | Maintain working context while clearing old results |
| Memory integration | Pairs with memory tool to persist important info | Save key findings before context is cleared |
| Cache-aware | Configurable clearing thresholds to balance cache hits | Optimize for performance in extended sessions |

**Reference**: [Context Editing Docs](https://docs.claude.com/en/docs/build-with-claude/context-editing)

## Custom Instructions

You can guide Claude's behavior by providing custom system instructions. This is particularly powerful for specialized agents like research assistants, code reviewers, or data analysts.

### Basic Example

```python
from open_claude_agent import ClaudeAgent
import anthropic

agent = ClaudeAgent(
    client=anthropic.Anthropic(),
    scratchpad_dir="./scratchpad",
    system_message="""You are a helpful research assistant.

    When conducting research:
    - Start with broad searches, then narrow down
    - Always cite your sources
    - Save important findings to memory
    - Organize results clearly
    """
)

agent.call("Research the latest developments in quantum computing")
```

### Advanced Example with Research Agent

```python
from open_claude_agent import ClaudeAgent
import anthropic

RESEARCH_AGENT_PROMPT = """You are a research assistant with access to web search, memory, and bash tools.

Your goal is to help users research topics by finding high-quality information, synthesizing it, and presenting clear summaries.

## Tool Usage Guidelines

**Web Search Tool:**
- For simple queries: aim for 2-5 searches maximum
- For complex topics: may use up to 10-15 searches
- STOP searching once you have sufficient information
- Critically evaluate source quality and relevance

**Memory Tool:**
- Store important research findings for later reference
- Save key facts, sources, and summaries as you work
- Organize in clearly named files (e.g., "/memories/research_topic.txt")

**Bash Tool:**
- Use for data processing or file organization
- Run analysis scripts when needed

## Research Process
1. Plan: Assess query complexity and estimate tool calls needed
2. Search: Start broad, then get specific
3. Evaluate: Check source reliability
4. Synthesize: Present findings clearly with citations
"""

agent = ClaudeAgent(
    client=anthropic.Anthropic(),
    scratchpad_dir="./scratchpad",
    system_message=RESEARCH_AGENT_PROMPT,
    max_web_searches=15
)

agent.call("Give me an overview of context engineering with popular papers")
```

**Best Practices:**
- Be specific about the agent's role and capabilities
- Define clear workflows and decision criteria
- Include examples of good vs bad behavior
- Set boundaries and stopping conditions
- Reference tool usage patterns

**Reference**: [Anthropic Prompting Best Practices](https://youtu.be/XSZP9GhhuAc?si=mNyuktz7CZRAIcod&t=520)
