"""
Shared pytest fixtures for Open Claude Agent integration tests.
"""
import os
import shutil
from pathlib import Path

import pytest
import anthropic


@pytest.fixture(scope="session")
def anthropic_client():
    """
    Creates a real Anthropic API client for integration testing.
    Requires ANTHROPIC_API_KEY environment variable to be set.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set - skipping integration tests")

    return anthropic.Anthropic(api_key=api_key)


@pytest.fixture
def test_workspace(tmp_path):
    """
    Creates a temporary workspace directory for test operations.
    Automatically cleaned up after test completion.
    """
    workspace = tmp_path / "test_workspace"
    workspace.mkdir(exist_ok=True)

    # Change to the test workspace for the duration of the test
    original_dir = os.getcwd()
    os.chdir(workspace)

    yield workspace

    # Restore original directory and cleanup
    os.chdir(original_dir)
    if workspace.exists():
        shutil.rmtree(workspace, ignore_errors=True)


@pytest.fixture
def cleanup_memories():
    """
    Ensures ./memories directory is cleaned up after tests.
    """
    yield

    memories_dir = Path("./memories")
    if memories_dir.exists():
        shutil.rmtree(memories_dir, ignore_errors=True)
