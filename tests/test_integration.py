"""Integration tests for track_followers main function."""

import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from track_followers import main

@pytest.mark.usefixtures("clean_dir","temp_dir","data_dir")
class TestMainFunction:
    """Integration tests for the main function."""
    def test_main_no_arguments(self, capsys):
        """Test main function with no arguments."""
        with patch.object(sys, "argv", ["track_followers.py"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Usage: track_followers.py <github_username>" in captured.out

    def test_main_invalid_username(self):
        """Test main function with invalid username."""
        with patch.object(sys, "argv", ["track_followers.py", "invalid_user!"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("track_followers.fetch_followers")
    @patch("track_followers.GhApi")
    def test_main_first_run(self, mock_ghapi, mock_fetch, monkeypatch, temp_dir):
        """Test main function on first run (no previous data)."""
        # Change to temp directory
        # Setup mocks
        mock_api_instance = Mock()
        mock_ghapi.return_value = mock_api_instance
        mock_fetch.return_value = ["alice", "bob", "charlie"]

        # Run main
        with patch.object(sys, "argv", ["track_followers.py", "testuser"]):
            main()

        # Verify data directory and files were created
        data_dir = temp_dir / ".followers_data"
        assert data_dir.exists()

        today = date.today()
        current_file = data_dir / today.strftime("%Y-%j")
        assert current_file.exists()

        # Verify followers were saved
        content = current_file.read_text()
        assert "alice" in content
        assert "bob" in content
        assert "charlie" in content

        # No changelog should be created on first run
        changelog = temp_dir / "CHANGELOG.md"
        assert not changelog.exists()

    @patch("track_followers.fetch_followers")
    @patch("track_followers.GhApi")
    def test_main_with_changes(self, mock_ghapi, mock_fetch, monkeypatch, temp_dir):
        """Test main function detecting changes from previous day."""
        # Setup previous day data
        data_dir = temp_dir / ".followers_data"
        data_dir.mkdir(exist_ok=True)

        yesterday = date.today() - timedelta(days=1)
        prev_file = data_dir / yesterday.strftime("%Y-%j")
        prev_file.write_text("alice\nbob\ncharlie\n")

        # Setup mocks - current followers have changes
        mock_api_instance = Mock()
        mock_ghapi.return_value = mock_api_instance
        mock_fetch.return_value = [
            "alice",
            "bob",
            "david",
        ]  # charlie removed, david added

        # Run main
        with patch.object(sys, "argv", ["track_followers.py", "testuser"]):
            main()

        # Verify changelog was created with changes
        changelog = temp_dir / "CHANGELOG.md"
        assert changelog.exists()

        content = changelog.read_text()
        assert "# Follower Changelog" in content
        assert "New Followers" in content
        assert "@david" in content
        assert "Removed Followers" in content
        assert "@charlie" in content

    @patch("track_followers.fetch_followers")
    @patch("track_followers.GhApi")
    def test_main_no_changes(
        self, mock_ghapi, mock_fetch, monkeypatch, caplog, temp_dir):
        """Test main function with no changes from previous day."""
        # Setup previous day data
        data_dir = temp_dir / ".followers_data"
        data_dir.mkdir(exist_ok=True)

        yesterday = date.today() - timedelta(days=1)
        prev_file = data_dir / yesterday.strftime("%Y-%j")
        prev_file.write_text("alice\nbob\ncharlie\n")

        # Setup mocks - same followers as yesterday
        mock_api_instance = Mock()
        mock_ghapi.return_value = mock_api_instance
        mock_fetch.return_value = ["alice", "bob", "charlie"]

        # Run main
        import logging

        # Capture logs from the gh-fc logger
        with caplog.at_level(logging.INFO, logger="gh-fc"):
            with patch.object(sys, "argv", ["track_followers.py", "testuser"]):
                main()

        # Verify no changelog was created
        changelog = temp_dir / "CHANGELOG.md"
        assert not changelog.exists()

        # Verify log message
        assert "No changes in followers" in caplog.text

    @patch("track_followers.fetch_followers")
    @patch("track_followers.GhApi")
    def test_main_api_error(self, mock_ghapi, mock_fetch, monkeypatch):
        """Test main function handling API errors."""
        # Setup mocks to raise an error
        mock_api_instance = Mock()
        mock_ghapi.return_value = mock_api_instance
        mock_fetch.side_effect = Exception("API Error")

        # Run main - should exit with error
        with patch.object(sys, "argv", ["track_followers.py", "testuser"]):
            with pytest.raises(Exception):
                main()

    @patch("track_followers.fetch_followers")
    @patch("track_followers.GhApi")
    def test_main_saves_to_correct_file(
        self, mock_ghapi, mock_fetch, monkeypatch, temp_dir):
        """Test that main saves data to date-based filename."""
        # Setup mocks
        mock_api_instance = Mock()
        mock_ghapi.return_value = mock_api_instance
        mock_fetch.return_value = ["alice"]

        # Run main
        with patch.object(sys, "argv", ["track_followers.py", "testuser"]):
            main()

        # Verify file has correct date-based name (YYYY-DDD format)
        data_dir = temp_dir / ".followers_data"
        today = date.today()
        expected_filename = today.strftime("%Y-%j")
        expected_file = data_dir / expected_filename

        assert expected_file.exists()

    @patch("track_followers.fetch_followers")
    @patch("track_followers.GhApi")
    def test_main_multiple_runs_accumulate_data(
        self, mock_ghapi, mock_fetch, monkeypatch, temp_dir):
        """Test that multiple runs on different days accumulate data."""
        # Change to temp directory
        data_dir = temp_dir / ".followers_data"
        data_dir.mkdir(exist_ok=True)

        # Setup mocks
        mock_api_instance = Mock()
        mock_ghapi.return_value = mock_api_instance

        # First run - 3 days ago
        three_days_ago = date.today() - timedelta(days=3)
        file1 = data_dir / three_days_ago.strftime("%Y-%j")
        file1.write_text("alice\nbob\n")

        # Second run - 2 days ago
        two_days_ago = date.today() - timedelta(days=2)
        file2 = data_dir / two_days_ago.strftime("%Y-%j")
        file2.write_text("alice\nbob\ncharlie\n")

        # Third run - yesterday
        yesterday = date.today() - timedelta(days=1)
        file3 = data_dir / yesterday.strftime("%Y-%j")
        file3.write_text("alice\ncharlie\n")

        # Current run - today
        mock_fetch.return_value = ["alice", "charlie", "david"]

        with patch.object(sys, "argv", ["track_followers.py", "testuser"]):
            main()

        # Verify all files still exist
        assert file1.exists()
        assert file2.exists()
        assert file3.exists()

        today = date.today()
        current_file = data_dir / today.strftime("%Y-%j")
        assert current_file.exists()
