"""Pytest configuration and fixtures."""

from datetime import date, timedelta
from pathlib import Path
import tempfile
from unittest.mock import Mock

import pytest

from track_followers import FollowerChanges


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


# FollowerChanges fixtures
@pytest.fixture
def follower_changes_empty():
    """Provide FollowerChanges with no changes."""
    return FollowerChanges(new=set(), removed=set())


@pytest.fixture
def follower_changes_new_only():
    """Provide FollowerChanges with only new followers."""
    return FollowerChanges(new={"alice", "bob"}, removed=set())


@pytest.fixture
def follower_changes_removed_only():
    """Provide FollowerChanges with only removed followers."""
    return FollowerChanges(new=set(), removed={"charlie", "david"})


@pytest.fixture
def follower_changes_both():
    """Provide FollowerChanges with both new and removed followers."""
    return FollowerChanges(new={"alice"}, removed={"bob"})


# Date fixtures
@pytest.fixture
def test_date():
    """Provide a consistent test date."""
    return date(2024, 1, 15)


@pytest.fixture
def yesterday():
    """Provide yesterday's date."""
    return date.today() - timedelta(days=1)


@pytest.fixture
def two_days_ago():
    """Provide date from two days ago."""
    return date.today() - timedelta(days=2)


@pytest.fixture
def three_days_ago():
    """Provide date from three days ago."""
    return date.today() - timedelta(days=3)


# Mock fixtures
@pytest.fixture
def mock_api():
    """Provide a basic mock API object."""
    return Mock()


@pytest.fixture
def mock_follower_objects():
    """Provide mock follower objects with login attributes."""
    return [
        Mock(login="alice"),
        Mock(login="bob"),
        Mock(login="charlie"),
    ]


# File setup fixtures
@pytest.fixture
def initial_changelog(changelog_path):
    """Create a changelog file with an existing entry."""
    content = (
        "# Follower Changelog\n\n"
        "This file tracks changes in GitHub followers over time.\n\n"
        "### 2024-01-14\n"
        "#### New Followers\n"
        "- @charlie\n"
    )
    changelog_path.write_text(content)
    return changelog_path


@pytest.fixture
def prev_day_follower_file(data_dir, yesterday):
    """Create a follower file from yesterday with sample data."""
    prev_file = data_dir / yesterday.strftime("%Y-%j")
    prev_file.write_text("alice\nbob\ncharlie\n")
    return prev_file


@pytest.fixture
def mock_ghapi_instance():
    """Provide a mock GhApi instance."""
    return Mock()
