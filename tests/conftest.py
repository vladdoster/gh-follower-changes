"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def data_dir(temp_dir):
    """Provide a temporary data directory."""
    data_path = temp_dir / ".followers_data"
    data_path.mkdir(exist_ok=True)
    return data_path


@pytest.fixture
def changelog_path(temp_dir):
    """Provide a temporary changelog file path."""
    return temp_dir / "CHANGELOG.md"


@pytest.fixture
def sample_followers():
    """Provide sample follower data."""
    return ["alice", "bob", "charlie", "david", "eve"]


@pytest.fixture
def sample_previous_followers():
    """Provide sample previous follower data."""
    return ["alice", "bob", "frank", "grace"]
