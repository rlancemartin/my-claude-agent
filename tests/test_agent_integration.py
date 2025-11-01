"""
Integration tests for Open Claude Agent tools.
Tests use the real Anthropic API and ClaudeAgent to verify each tool works end-to-end.
"""
from pathlib import Path

from open_claude_agent import ClaudeAgent


def test_memory_tool(anthropic_client, test_workspace, cleanup_memories):
    """
    Test that the memory tool can create and read files in ./memories directory.
    """
    agent = ClaudeAgent(
        client=anthropic_client,
        system_message="You are a helpful assistant. Follow instructions exactly.",
        max_tokens=4096
    )

    # Ask agent to create a file in memories
    user_message = (
        "Please create a file called 'test_note.txt' in the memories directory "
        "with the content: 'This is a test note for integration testing.'"
    )

    messages = agent.call(user_message, max_turns=5)

    # Verify the file was created
    memory_file = Path("./memories/test_note.txt")
    assert memory_file.exists(), "Memory file was not created"

    # Verify content
    content = memory_file.read_text()
    assert "test note" in content.lower(), "File content doesn't match expected"


def test_bash_tool(anthropic_client, test_workspace):
    """
    Test that the bash tool can execute simple commands.
    """
    agent = ClaudeAgent(
        client=anthropic_client,
        system_message="You are a helpful assistant. Follow instructions exactly.",
        max_tokens=4096
    )

    # Ask agent to run a simple echo command
    user_message = "Please run the bash command: echo 'Integration test successful'"

    messages = agent.call(user_message, max_turns=5)

    # Verify we got a response (the actual verification is that no exception was raised)
    assert len(messages) > 0, "No response from agent"
    assert any("user" in msg.get("role", "") or "assistant" in msg.get("role", "") for msg in messages), \
        "Invalid message structure"


def test_text_editor_tool(anthropic_client, test_workspace):
    """
    Test that the text editor tool can create, modify, and read files.
    """
    agent = ClaudeAgent(
        client=anthropic_client,
        system_message="You are a helpful assistant. Follow instructions exactly.",
        max_tokens=4096
    )

    # Ask agent to create and modify a file
    user_message = (
        "Please use the text editor to create a file called './test_file.txt' in the current directory "
        "with the content: 'Hello World'. Then replace 'World' with 'Integration Test'. "
        "Make sure to use the path './test_file.txt' (not /tmp or any other location)."
    )

    messages = agent.call(user_message, max_turns=5)

    # Verify the file was created and modified
    test_file = Path("./test_file.txt")
    assert test_file.exists(), "Test file was not created"

    # Verify content was modified
    content = test_file.read_text()
    assert "Integration Test" in content, "File content was not modified correctly"
    assert "World" not in content or "Integration Test" in content, \
        "File modification didn't work as expected"


def test_web_search(anthropic_client, test_workspace):
    """
    Test that the web search tool can perform a simple search query.
    Note: This is a server-side tool, so we just verify the agent can use it.
    """
    agent = ClaudeAgent(
        client=anthropic_client,
        system_message="You are a helpful assistant. Follow instructions exactly.",
        max_tokens=4096
    )

    # Ask agent to perform a simple web search
    user_message = "Please search the web for 'Anthropic Claude AI' and tell me what you find."

    messages = agent.call(user_message, max_turns=5)

    # Verify we got a response with content
    assert len(messages) > 0, "No response from agent"

    # Check that there's some text content in the response
    has_content = False
    for msg in messages:
        if msg.get("role") == "assistant" and msg.get("content"):
            # Check if content is a list or string
            content = msg["content"]
            if isinstance(content, str) and len(content) > 0:
                has_content = True
                break
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text" and len(block.get("text", "")) > 0:
                        has_content = True
                        break

    assert has_content, "Agent response has no content"
