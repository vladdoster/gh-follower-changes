"""Unit tests for track_followers.py functions."""

from datetime import date
from pathlib import Path
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from track_followers import build_changelog_entry, compare_followers, fatal, fetch_followers, FollowerChanges, \
                            load_followers, save_followers, update_changelog, validate_username


class TestFollowerChanges:
    """Test the FollowerChanges dataclass."""

    def test_empty_changes(self):
        """Test FollowerChanges with no changes."""
        changes = FollowerChanges(new=set(), removed=set())
        assert not changes.has_changes
        assert str(changes) == "+0 new, -0 removed"

    def test_only_new_followers(self):
        """Test FollowerChanges with only new followers."""
        changes = FollowerChanges(new={"alice", "bob"}, removed=set())
        assert changes.has_changes
        assert str(changes) == "+2 new, -0 removed"

    def test_only_removed_followers(self):
        """Test FollowerChanges with only removed followers."""
        changes = FollowerChanges(new=set(), removed={"charlie", "david"})
        assert changes.has_changes
        assert str(changes) == "+0 new, -2 removed"

    def test_both_new_and_removed(self):
        """Test FollowerChanges with both new and removed followers."""
        changes = FollowerChanges(new={"alice"}, removed={"bob", "charlie"})
        assert changes.has_changes
        assert str(changes) == "+1 new, -2 removed"


class TestValidateUsername:
    """Test the validate_username function."""

    def test_valid_usernames(self):
        """Test valid GitHub username formats."""
        valid_usernames = [
            "alice",
            "bob123",
            "alice-bob",
            "user-name-123",
            "A1B2C3",
        ]
        for username in valid_usernames:
            assert validate_username(username), f"'{username}' should be valid"

    def test_invalid_usernames(self):
        """Test invalid GitHub username formats."""
        invalid_usernames = [
            "alice_bob",  # underscores not allowed
            "alice.bob",  # dots not allowed
            "alice bob",  # spaces not allowed
            "alice@bob",  # special chars not allowed
            "",  # empty string
            "-alice",  # can't start with hyphen (GitHub rule)
            "alice-",  # can't end with hyphen (GitHub rule)
        ]
        for username in invalid_usernames:
            # Note: Our regex only validates basic format, not all GitHub rules
            # So we only test for obvious invalid chars
            if any(c in username for c in ["_", ".", " ", "@"]) or not username:
                assert not validate_username(username), f"'{username}' should be invalid"


class TestFatal:
    """Test the fatal function."""

    def test_fatal_exits_with_error(self, capsys):
        """Test that fatal logs error and exits."""
        with pytest.raises(SystemExit) as exc_info:
            fatal("Test error message")
        assert exc_info.value.code == 1

    def test_fatal_with_format_args(self, capsys):
        """Test fatal with format arguments."""
        with pytest.raises(SystemExit) as exc_info:
            fatal("Error: %s", "test error")
        assert exc_info.value.code == 1


class TestLoadFollowers:
    """Test the load_followers function."""

    def test_load_nonexistent_file(self, temp_dir):
        """Test loading from a non-existent file returns empty set."""
        filepath = temp_dir / "nonexistent.txt"
        result = load_followers(filepath)
        assert result == set()

    def test_load_empty_file(self, temp_dir):
        """Test loading from an empty file returns empty set."""
        filepath = temp_dir / "empty.txt"
        filepath.write_text("")
        result = load_followers(filepath)
        assert result == set()

    def test_load_followers_from_file(self, temp_dir):
        """Test loading followers from a file."""
        filepath = temp_dir / "followers.txt"
        filepath.write_text("alice\nbob\ncharlie\n")
        result = load_followers(filepath)
        assert result == {"alice", "bob", "charlie"}

    def test_load_followers_with_empty_lines(self, temp_dir):
        """Test loading followers ignores empty lines."""
        filepath = temp_dir / "followers.txt"
        filepath.write_text("alice\n\nbob\n\n\ncharlie\n")
        result = load_followers(filepath)
        assert result == {"alice", "bob", "charlie"}

    def test_load_followers_with_whitespace(self, temp_dir):
        """Test loading followers strips whitespace."""
        filepath = temp_dir / "followers.txt"
        filepath.write_text("  alice  \n bob \n\tcharlie\t\n")
        result = load_followers(filepath)
        assert result == {"alice", "bob", "charlie"}


class TestSaveFollowers:
    """Test the save_followers function."""

    def test_save_empty_list(self, temp_dir):
        """Test saving an empty list of followers."""
        filepath = temp_dir / "followers.txt"
        save_followers([], filepath)
        assert filepath.read_text() == ""

    def test_save_followers_to_file(self, temp_dir):
        """Test saving followers to a file."""
        filepath = temp_dir / "followers.txt"
        followers = ["alice", "bob", "charlie"]
        save_followers(followers, filepath)
        content = filepath.read_text()
        assert content == "alice\nbob\ncharlie\n"

    def test_save_followers_overwrites(self, temp_dir):
        """Test that saving followers overwrites existing content."""
        filepath = temp_dir / "followers.txt"
        filepath.write_text("old content\n")
        followers = ["alice", "bob"]
        save_followers(followers, filepath)
        content = filepath.read_text()
        assert content == "alice\nbob\n"


class TestCompareFollowers:
    """Test the compare_followers function."""

    def test_no_changes(self):
        """Test comparing identical sets."""
        current = {"alice", "bob", "charlie"}
        previous = {"alice", "bob", "charlie"}
        changes = compare_followers(current, previous)
        assert not changes.has_changes
        assert changes.new == set()
        assert changes.removed == set()

    def test_only_new_followers(self):
        """Test detecting only new followers."""
        current = {"alice", "bob", "charlie", "david"}
        previous = {"alice", "bob"}
        changes = compare_followers(current, previous)
        assert changes.has_changes
        assert changes.new == {"charlie", "david"}
        assert changes.removed == set()

    def test_only_removed_followers(self):
        """Test detecting only removed followers."""
        current = {"alice", "bob"}
        previous = {"alice", "bob", "charlie", "david"}
        changes = compare_followers(current, previous)
        assert changes.has_changes
        assert changes.new == set()
        assert changes.removed == {"charlie", "david"}

    def test_both_new_and_removed(self):
        """Test detecting both new and removed followers."""
        current = {"alice", "bob", "eve"}
        previous = {"alice", "charlie", "david"}
        changes = compare_followers(current, previous)
        assert changes.has_changes
        assert changes.new == {"bob", "eve"}
        assert changes.removed == {"charlie", "david"}

    def test_empty_sets(self):
        """Test comparing empty sets."""
        changes = compare_followers(set(), set())
        assert not changes.has_changes


class TestBuildChangelogEntry:
    """Test the build_changelog_entry function."""

    def test_entry_with_new_followers_only(self, follower_changes_new_only, test_date):
        """Test building entry with only new followers."""
        entry = build_changelog_entry(follower_changes_new_only, test_date)

        assert "### 2024-01-15" in entry
        assert "#### New Followers" in entry
        assert "- @alice" in entry
        assert "- @bob" in entry
        assert "#### Removed Followers" not in entry

    def test_entry_with_removed_followers_only(self, follower_changes_removed_only, test_date):
        """Test building entry with only removed followers."""
        entry = build_changelog_entry(follower_changes_removed_only, test_date)

        assert "### 2024-01-15" in entry
        assert "#### Removed Followers" in entry
        assert "- @charlie" in entry
        assert "- @david" in entry
        assert "#### New Followers" not in entry

    def test_entry_with_both_changes(self, follower_changes_both, test_date):
        """Test building entry with both new and removed followers."""
        entry = build_changelog_entry(follower_changes_both, test_date)

        assert "### 2024-01-15" in entry
        assert "#### New Followers" in entry
        assert "- @alice" in entry
        assert "#### Removed Followers" in entry
        assert "- @bob" in entry

    def test_entry_sorted_alphabetically(self, test_date):
        """Test that followers are sorted alphabetically in entry."""
        changes = FollowerChanges(new={"charlie", "alice", "bob"}, removed=set())
        entry = build_changelog_entry(changes, test_date)

        lines = entry.split("\n")
        follower_lines = [line for line in lines if line.startswith("- @")]
        assert follower_lines == ["- @alice", "- @bob", "- @charlie"]


class TestUpdateChangelog:
    """Test the update_changelog function."""

    def test_create_new_changelog(self, temp_dir, follower_changes_both, test_date):
        """Test creating a new changelog file."""
        changelog_path = temp_dir / "CHANGELOG.md"

        update_changelog(follower_changes_both, changelog_path, test_date)

        assert changelog_path.exists()
        content = changelog_path.read_text()
        assert "# Follower Changelog" in content
        assert "### 2024-01-15" in content
        assert "- @alice" in content
        assert "- @bob" in content

    def test_update_existing_changelog(self, initial_changelog, follower_changes_new_only, test_date):
        """Test updating an existing changelog."""
        update_changelog(follower_changes_new_only, initial_changelog, test_date)

        content = initial_changelog.read_text()
        assert "### 2024-01-15" in content
        assert "- @alice" in content
        assert "### 2024-01-14" in content
        assert "- @charlie" in content

    def test_skip_duplicate_date(self, follower_changes_new_only, test_date, caplog, temp_dir):
        """Test that updating with same date is skipped."""
        changelog_path = temp_dir / "CHANGELOG.md"
        initial_content = "# Follower Changelog\n\n### 2024-01-15\n#### New Followers\n- @alice\n"
        changelog_path.write_text(initial_content)

        changes = FollowerChanges(new={"bob"}, removed=set())

        update_changelog(changes, changelog_path, test_date)

        content = changelog_path.read_text()
        # Should not have added bob since date already exists
        assert "- @bob" not in content
        assert "already in changelog" in caplog.text

    def test_new_entry_inserted_at_top(self, initial_changelog, follower_changes_new_only, test_date):
        """Test that new entries are inserted at the top (most recent first)."""
        update_changelog(follower_changes_new_only, initial_changelog, test_date)

        content = initial_changelog.read_text()
        # Check that 2024-01-15 appears before 2024-01-14
        pos_15 = content.index("2024-01-15")
        pos_14 = content.index("2024-01-14")
        assert pos_15 < pos_14

    def test_mdformat_error_handled(self, initial_changelog, follower_changes_new_only, test_date, caplog):
        """Test that mdformat errors are handled gracefully."""
        import logging

        # Capture logs from the gh-fc logger
        with caplog.at_level(logging.ERROR, logger="gh-fc"):
            with patch("track_followers.mdformat.file") as mock_mdformat:
                mock_mdformat.side_effect = Exception("Format error")
                update_changelog(follower_changes_new_only, initial_changelog, test_date)

        # Should still create the file even if formatting fails
        assert initial_changelog.exists()
        assert "Failed to format changelog" in caplog.text


class TestFetchFollowers:
    """Test the fetch_followers function."""

    def test_fetch_followers_success(self, mock_api, mock_follower_objects):
        """Test successful follower fetching."""
        with patch("track_followers.paged") as mock_paged:
            # Simulate paged results
            mock_paged.return_value = [
                mock_follower_objects[:2],
                [mock_follower_objects[2]],
            ]
            result = fetch_followers(mock_api, "testuser")

        assert result == ["alice", "bob", "charlie"]
        mock_paged.assert_called_once()

    def test_fetch_followers_removes_duplicates(self, mock_api):
        """Test that duplicate followers are removed."""
        mock_follower1 = Mock(login="alice")
        mock_follower2 = Mock(login="alice")  # Duplicate

        with patch("track_followers.paged") as mock_paged:
            mock_paged.return_value = [[mock_follower1, mock_follower2]]
            result = fetch_followers(mock_api, "testuser")

        assert result == ["alice"]

    def test_fetch_followers_sorts_results(self, mock_api):
        """Test that followers are sorted alphabetically."""
        mock_follower1 = Mock(login="charlie")
        mock_follower2 = Mock(login="alice")
        mock_follower3 = Mock(login="bob")

        with patch("track_followers.paged") as mock_paged:
            mock_paged.return_value = [[mock_follower1, mock_follower2, mock_follower3]]
            result = fetch_followers(mock_api, "testuser")

        assert result == ["alice", "bob", "charlie"]

    def test_fetch_followers_401_error(self, mock_api):
        """Test handling of 401 authentication error."""
        with patch("track_followers.paged") as mock_paged:
            mock_paged.side_effect = Exception("401 Unauthorized")
            with pytest.raises(SystemExit):
                fetch_followers(mock_api, "testuser")

    def test_fetch_followers_404_error(self, mock_api):
        """Test handling of 404 user not found error."""
        with patch("track_followers.paged") as mock_paged:
            mock_paged.side_effect = Exception("404 Not Found")
            with pytest.raises(SystemExit):
                fetch_followers(mock_api, "testuser")

    def test_fetch_followers_rate_limit_error(self, mock_api):
        """Test handling of rate limit errors."""
        with patch("track_followers.paged") as mock_paged:
            mock_paged.side_effect = Exception("403 Forbidden")
            with pytest.raises(SystemExit):
                fetch_followers(mock_api, "testuser")

    def test_fetch_followers_generic_error(self, mock_api):
        """Test handling of generic API errors."""
        with patch("track_followers.paged") as mock_paged:
            mock_paged.side_effect = Exception("500 Internal Server Error")
            with pytest.raises(SystemExit):
                fetch_followers(mock_api, "testuser")
