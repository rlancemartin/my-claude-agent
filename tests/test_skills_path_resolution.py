"""
Test that skills directory path resolution works correctly.

This test ensures that the skills directory is found regardless of the
current working directory when skills_dir is not explicitly set.
"""

import os
import sys
from pathlib import Path
import tempfile


def test_default_skills_path_resolution():
    """Test that skills are found with default path resolution."""
    # Import here to ensure we're using the installed package
    from open_claude_agent import ClaudeAgent

    # Create a mock client
    class MockClient:
        pass

    # Save original CWD
    original_cwd = os.getcwd()

    try:
        # Test from different working directories
        test_dirs = [
            Path(original_cwd),  # Project root
            Path(original_cwd) / "sandbox",  # Subdirectory
            Path(tempfile.gettempdir()),  # Completely different location
        ]

        for test_dir in test_dirs:
            if not test_dir.exists():
                continue

            os.chdir(test_dir)

            # Initialize agent with default skills_dir
            agent = ClaudeAgent(client=MockClient(), enable_skills=True)

            # Verify skills were loaded
            assert "Available Skills" in agent.system_message, \
                f"Skills not loaded from {test_dir}"

            # Verify specific skills are present
            assert "arxiv-search" in agent.system_message
            assert "pubmed-search" in agent.system_message
            assert "web-research" in agent.system_message

    finally:
        # Restore original CWD
        os.chdir(original_cwd)


def test_custom_skills_dir():
    """Test that custom skills_dir parameter works."""
    from open_claude_agent import ClaudeAgent
    from open_claude_agent.skill_loader import SkillLoader

    class MockClient:
        pass

    # Get the actual skills directory
    project_root = Path(__file__).parent.parent
    skills_dir = str(project_root / "skills")

    # Initialize with explicit path
    agent = ClaudeAgent(
        client=MockClient(),
        skills_dir=skills_dir,
        enable_skills=True
    )

    # Verify skills were loaded
    assert "Available Skills" in agent.system_message
    assert "arxiv-search" in agent.system_message


def test_skills_disabled():
    """Test that skills can be disabled."""
    from open_claude_agent import ClaudeAgent

    class MockClient:
        pass

    # Initialize with skills disabled
    agent = ClaudeAgent(client=MockClient(), enable_skills=False)

    # Verify no skills in system message
    assert "Available Skills" not in agent.system_message


if __name__ == "__main__":
    print("Running skills path resolution tests...")

    print("\nTest 1: Default skills path resolution")
    test_default_skills_path_resolution()
    print("✓ Passed")

    print("\nTest 2: Custom skills directory")
    test_custom_skills_dir()
    print("✓ Passed")

    print("\nTest 3: Skills disabled")
    test_skills_disabled()
    print("✓ Passed")

    print("\n✓ All tests passed!")
