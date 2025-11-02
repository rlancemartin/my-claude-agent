"""
Open Claude Agent - A minimal agent harness using Claude's tool capabilities.
"""

from .claude_agent import ClaudeAgent
from .prompts import (
    GENERAL_TOOL_USAGE_GUIDELINES,
    RESEARCH_AGENT_PROMPT,
    SIMPLE_RESEARCH_INSTRUCTIONS
)
from .skill_loader import SkillLoader, load_skills
from .utils import (
    display_claude_response,
    format_anthropic_tool_call,
    format_anthropic_tool_result,
    show_prompt
)

__version__ = "0.1.0"

__all__ = [
    "ClaudeAgent",
    "GENERAL_TOOL_USAGE_GUIDELINES",
    "RESEARCH_AGENT_PROMPT",
    "SIMPLE_RESEARCH_INSTRUCTIONS",
    "SkillLoader",
    "load_skills",
    "display_claude_response",
    "format_anthropic_tool_call",
    "format_anthropic_tool_result",
    "show_prompt",
]
