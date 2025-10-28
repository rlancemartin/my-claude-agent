from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import json
from typing import Dict, Any, List, Union

console = Console()

def format_anthropic_tool_call(block, console_instance=None):
    """
    Format and display a raw Anthropic API tool use block.
    Handles both client-side (tool_use) and server-side (server_tool_use) tools.

    Args:
        block: The tool use block from Anthropic API response
        console_instance: Optional Rich Console instance (defaults to global console)
    """
    if console_instance is None:
        console_instance = console

    tool_info = Text()
    tool_name = block.name
    is_server_tool = block.type == "server_tool_use"

    # Format based on tool type
    if tool_name == "web_search":
        # Web search tool: show query
        if is_server_tool:
            tool_info.append("🌐 Server Tool Call: ", style="bold magenta")
        else:
            tool_info.append("🔧 Tool Call: ", style="bold yellow")
        tool_info.append(f"web_search\n", style="bold cyan")
        tool_info.append(f"   Query: ", style="white")
        tool_info.append(f"{block.input.get('query', 'N/A')}\n", style="green")

        if is_server_tool:
            tool_info.append(f"   ", style="dim")
            tool_info.append(f"(Executed server-side by Anthropic)\n", style="dim italic")

    elif tool_name == "memory":
        # Memory tool: shows command and path
        tool_info.append("🔧 Tool Call: ", style="bold yellow")
        tool_info.append(f"{block.input.get('command')}\n", style="bold cyan")
        tool_info.append(f"   Path: ", style="white")
        tool_info.append(f"{block.input.get('path', 'N/A')}\n", style="green")

        # Show additional parameters if present
        params_to_show = {k: v for k, v in block.input.items()
                         if k not in ['command', 'path']}
        if params_to_show:
            tool_info.append(f"   Params: ", style="white")
            tool_info.append(f"{json.dumps(params_to_show, indent=6)}\n", style="dim")

    elif tool_name == "bash":
        # Bash tool: shows command directly
        tool_info.append("🔧 Tool Call: ", style="bold yellow")
        tool_info.append(f"bash\n", style="bold cyan")
        tool_info.append(f"   Command: ", style="white")
        command_text = block.input.get('command', 'N/A')
        tool_info.append(f"{command_text}\n", style="green")

        # Show restart flag if present
        if block.input.get('restart'):
            tool_info.append(f"   Restart: ", style="white")
            tool_info.append(f"true\n", style="dim")

    else:
        # Generic tool formatting: show tool name and all inputs
        if is_server_tool:
            tool_info.append("🌐 Server Tool Call: ", style="bold magenta")
        else:
            tool_info.append("🔧 Tool Call: ", style="bold yellow")
        tool_info.append(f"{tool_name}\n", style="bold cyan")
        for key, value in block.input.items():
            tool_info.append(f"   {key}: ", style="white")
            if isinstance(value, str) and len(value) > 100:
                tool_info.append(f"{value[:100]}...\n", style="green")
            else:
                tool_info.append(f"{value}\n", style="green")

        if is_server_tool:
            tool_info.append(f"   ", style="dim")
            tool_info.append(f"(Executed server-side by Anthropic)\n", style="dim italic")

    # Use magenta border for server tools, yellow for client tools
    border_style = "magenta" if is_server_tool else "yellow"
    console_instance.print(Panel(tool_info, border_style=border_style, padding=(0, 1)))


def format_anthropic_tool_result(result, console_instance=None):
    """
    Format and display a raw Anthropic API tool result.

    Args:
        result: The tool result dictionary
        console_instance: Optional Rich Console instance (defaults to global console)
    """
    if console_instance is None:
        console_instance = console

    result_text = Text()

    # Check for error first
    if "error" in result:
        result_text.append("❌ Error: ", style="bold red")
        result_text.append(result["error"], style="red")
        border_style = "red"
    # Bash tool result format
    elif "exit_code" in result:
        if result.get("exit_code") == 0:
            result_text.append("✓ Success: ", style="bold green")
            result_text.append(result.get('message', 'Command executed successfully'), style="green")
            border_style = "green"
        else:
            result_text.append("⚠ Exit Code: ", style="bold yellow")
            result_text.append(f"{result.get('exit_code')}", style="yellow")
            border_style = "yellow"

        # Show stdout if present
        if result.get("output"):
            output_preview = result["output"].strip()
            if len(output_preview) > 200:
                output_preview = output_preview[:200] + "..."
            result_text.append(f"\n   Output: ", style="white")
            result_text.append(output_preview, style="dim")

        # Show stderr if present (in error field)
        if result.get("error") and result.get("exit_code") != 0:
            error_preview = result["error"].strip()
            if len(error_preview) > 200:
                error_preview = error_preview[:200] + "..."
            result_text.append(f"\n   Stderr: ", style="white")
            result_text.append(error_preview, style="dim")
    # Memory tool result format
    else:
        result_text.append("✓ Success: ", style="bold green")
        result_text.append(result.get('message', str(result)), style="green")
        border_style = "green"

        # Show additional result data if present
        if result.get("type") == "directory":
            result_text.append(f"\n   Contents: {result.get('contents', [])}", style="dim")
        elif result.get("type") == "file" and result.get("content"):
            preview = result["content"][:100]
            result_text.append(f"\n   Preview: {preview}...", style="dim")

    console_instance.print(Panel(result_text, border_style=border_style, padding=(0, 1)))

def format_anthropic_content_block(content_block):
    """
    Format a single Anthropic API content block (text or tool_use).

    Args:
        content_block: A content block dict from Anthropic API response

    Returns:
        Formatted string representation
    """
    if content_block.get('type') == 'text':
        return content_block.get('text', '')

    elif content_block.get('type') == 'tool_use':
        parts = [f"\n🔧 Tool Call: {content_block['name']}"]
        tool_input = content_block.get('input', {})

        # Format memory tool calls specially
        if content_block['name'] == 'memory':
            parts.append(f"   Command: {tool_input.get('command', 'N/A')}")
            parts.append(f"   Path: {tool_input.get('path', 'N/A')}")
            # Show other params
            other_params = {k: v for k, v in tool_input.items()
                           if k not in ['command', 'path']}
            if other_params:
                parts.append(f"   Params: {json.dumps(other_params, indent=6)}")
        else:
            parts.append(f"   Args: {json.dumps(tool_input, indent=2)}")

        parts.append(f"   ID: {content_block.get('id', 'N/A')}")
        return "\n".join(parts)

    elif content_block.get('type') == 'tool_result':
        tool_content = content_block.get('content', '')
        try:
            parsed = json.loads(tool_content) if isinstance(tool_content, str) else tool_content
            if isinstance(parsed, dict):
                if 'error' in parsed:
                    return f"❌ Error: {parsed['error']}"
                elif 'message' in parsed:
                    result = [f"✓ {parsed['message']}"]
                    if parsed.get('type') == 'directory':
                        result.append(f"\n   Contents: {parsed.get('contents', [])}")
                    elif parsed.get('type') == 'file' and parsed.get('content'):
                        preview = parsed['content'][:100]
                        result.append(f"\n   Preview: {preview}...")
                    return "".join(result)
                else:
                    return json.dumps(parsed, indent=2)
            else:
                return str(tool_content)
        except (json.JSONDecodeError, TypeError):
            return str(tool_content)

    return str(content_block)


def format_anthropic_message(message_dict):
    """
    Format a raw Anthropic API message dictionary.

    Args:
        message_dict: A message dict with 'role' and 'content' from Anthropic API

    Returns:
        Formatted string representation
    """
    content = message_dict.get('content', '')

    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Handle list of content blocks
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(format_anthropic_content_block(block))
            else:
                parts.append(str(block))
        return "\n".join(parts)
    elif isinstance(content, dict):
        return format_anthropic_content_block(content)
    else:
        return str(content)


def display_anthropic_messages(messages):
    """
    Display a list of raw Anthropic API messages with Rich formatting.

    Args:
        messages: List of Anthropic API message dicts with 'role' and 'content'
    """
    for msg in messages:
        role = msg.get('role', 'unknown')
        content = format_anthropic_message(msg)

        if role == 'user':
            console.print(Panel(content, title="🧑 User", border_style="blue"))
        elif role == 'assistant':
            console.print(Panel(content, title="🤖 Assistant", border_style="green"))
        else:
            console.print(Panel(content, title=f"📝 {role.title()}", border_style="white"))


def display_claude_response(response_text, console_instance=None):
    """
    Display Claude's text response with Rich formatting.

    Args:
        response_text: The text response from Claude
        console_instance: Optional Rich Console instance (defaults to global console)
    """
    if console_instance is None:
        console_instance = console

    console_instance.print(Panel(response_text, title="💬 Claude", border_style="green", padding=(1, 2)))


def show_prompt(prompt_text: str, title: str = "Prompt", border_style: str = "blue"):
    """
    Display a prompt with rich formatting and XML tag highlighting.
    
    Args:
        prompt_text: The prompt string to display
        title: Title for the panel (default: "Prompt")
        border_style: Border color style (default: "blue")
    """
    # Create a formatted display of the prompt
    formatted_text = Text(prompt_text)
    formatted_text.highlight_regex(r'<[^>]+>', style="bold blue")  # Highlight XML tags
    formatted_text.highlight_regex(r'##[^#\n]+', style="bold magenta")  # Highlight headers
    formatted_text.highlight_regex(r'###[^#\n]+', style="bold cyan")  # Highlight sub-headers

    # Display in a panel for better presentation
    console.print(Panel(
        formatted_text, 
        title=f"[bold green]{title}[/bold green]",
        border_style=border_style,
        padding=(1, 2)
    ))

def show_prompt(prompt_text: str, title: str = "Prompt", border_style: str = "blue"):
    """
    Display a prompt with rich formatting and XML tag highlighting.
    
    Args:
        prompt_text: The prompt string to display
        title: Title for the panel (default: "Prompt")
        border_style: Border color style (default: "blue")
    """
    # Create a formatted display of the prompt
    formatted_text = Text(prompt_text)
    formatted_text.highlight_regex(r'<[^>]+>', style="bold blue")  # Highlight XML tags
    formatted_text.highlight_regex(r'##[^#\n]+', style="bold magenta")  # Highlight headers
    formatted_text.highlight_regex(r'###[^#\n]+', style="bold cyan")  # Highlight sub-headers

    # Display in a panel for better presentation
    console.print(Panel(
        formatted_text, 
        title=f"[bold green]{title}[/bold green]",
        border_style=border_style,
        padding=(1, 2)
    ))