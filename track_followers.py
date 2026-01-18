#!/usr/bin/env python3
"""
track_followers.py
Script to track GitHub followers and maintain a changelog
"""

import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from ghapi.all import GhApi, paged


# Colors for output (ANSI escape codes)
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color


def log(message: str) -> None:
    """Log an info message."""
    print(f"{GREEN}[INFO]{NC} {message}", file=sys.stderr)


def error(message: str) -> None:
    """Log an error message and exit."""
    print(f"{RED}[ERROR]{NC} {message}", file=sys.stderr)
    sys.exit(1)


def warn(message: str) -> None:
    """Log a warning message."""
    print(f"{YELLOW}[WARN]{NC} {message}", file=sys.stderr)


def usage() -> None:
    """Display usage information and exit."""
    print("Usage: track_followers.py <github_username>")
    print("Example: track_followers.py vladdoster")
    sys.exit(1)


def validate_username(username: str) -> bool:
    """Validate GitHub username format (alphanumeric and hyphens only)."""
    return bool(re.match(r"^[a-zA-Z0-9-]+$", username))


def fetch_followers(api: GhApi, username: str) -> list[str]:
    """
    Fetch all followers for a GitHub user using ghapi.
    
    Args:
        api: GhApi instance
        username: GitHub username to fetch followers for
        
    Returns:
        Sorted list of follower usernames
    """
    log(f"Fetching followers for {username}...")
    
    all_followers = []
    
    try:
        # Use paged to handle pagination automatically
        for page in paged(api.users.list_followers_for_user, username=username, per_page=100):
            for follower in page:
                all_followers.append(follower.login)
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            error(f"User '{username}' not found")
        elif "401" in error_msg or "403" in error_msg:
            error("GitHub API requires authentication. Please set GH_TOKEN or GITHUB_TOKEN environment variable.")
        else:
            error(f"GitHub API error: {error_msg}")
    
    return sorted(all_followers)


def get_date_id(d: date) -> str:
    """Get date identifier in YYYY-DOY format (e.g., 2026-018)."""
    return d.strftime("%Y-%j")


def load_followers_from_file(filepath: Path) -> set[str]:
    """Load followers from a file."""
    if not filepath.exists():
        return set()
    
    with filepath.open() as f:
        return {line.strip() for line in f if line.strip()}


def save_followers_to_file(followers: list[str], filepath: Path) -> None:
    """Save followers to a file, one per line."""
    with filepath.open("w") as f:
        for follower in followers:
            f.write(f"{follower}\n")


def update_changelog(
    new_followers: set[str],
    removed_followers: set[str],
    changelog_path: Path,
    current_date: date,
) -> None:
    """Update the changelog with new and removed followers."""
    date_str = current_date.strftime("%Y-%m-%d")
    
    # Build the new entry
    entry_lines = [f"### {date_str}", ""]
    
    if new_followers:
        entry_lines.append("#### New Followers")
        entry_lines.append("")
        for follower in sorted(new_followers):
            entry_lines.append(f"- @{follower}")
        entry_lines.append("")
    
    if removed_followers:
        entry_lines.append("#### Removed Followers")
        entry_lines.append("")
        for follower in sorted(removed_followers):
            entry_lines.append(f"- @{follower}")
        entry_lines.append("")
    
    new_entry = "\n".join(entry_lines)
    
    if changelog_path.exists():
        content = changelog_path.read_text()
        
        # Check if today's date is already in the changelog
        if date_str in content:
            warn(f"{date_str} already in changelog")
            return
        
        # Find the first h3 header and insert before it
        h3_pattern = re.compile(r"^### ", re.MULTILINE)
        match = h3_pattern.search(content)
        
        if match:
            # Insert before the first h3 header
            new_content = content[: match.start()] + new_entry + content[match.start() :]
        else:
            # No existing entries, append to the file
            new_content = content + new_entry
        
        changelog_path.write_text(new_content)
    else:
        # No changelog exists yet - create with header
        header = "# Follower Changelog\n\nThis file tracks changes in GitHub followers over time.\n\n"
        changelog_path.write_text(header + new_entry)
    
    log(f"Changelog updated: {changelog_path}")


def main() -> None:
    """Main entry point."""
    # Parse arguments
    if len(sys.argv) < 2:
        usage()
    
    github_username = sys.argv[1]
    
    # Validate username
    if not validate_username(github_username):
        error("Invalid GitHub username format. Username must contain only alphanumeric characters and hyphens.")
    
    # Configuration
    data_dir = Path("followers_data")
    changelog_path = Path("CHANGELOG.md")
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(exist_ok=True)
    
    # Get current and previous date identifiers
    today = date.today()
    yesterday = today - timedelta(days=1)
    
    current_date_id = get_date_id(today)
    prev_date_id = get_date_id(yesterday)
    
    current_file = data_dir / current_date_id
    prev_file = data_dir / prev_date_id
    
    # Initialize GitHub API client
    # ghapi will automatically use GH_TOKEN or GITHUB_TOKEN from environment
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        warn("No GH_TOKEN or GITHUB_TOKEN found. You may hit rate limits for unauthenticated requests.")
    
    api = GhApi(token=token)
    
    # Fetch current followers
    log("Retrieving followers...")
    followers = fetch_followers(api, github_username)
    log(f"Found {len(followers)} followers")
    
    # Save current followers
    save_followers_to_file(followers, current_file)
    
    # Check if previous day's file exists
    if prev_file.exists():
        log(f"Previous day's file found ({prev_file}). Comparing...")
        
        prev_followers = load_followers_from_file(prev_file)
        current_followers = set(followers)
        
        # Find new followers (in current but not in previous)
        new_followers = current_followers - prev_followers
        
        # Find removed followers (in previous but not in current)
        removed_followers = prev_followers - current_followers
        
        new_count = len(new_followers)
        removed_count = len(removed_followers)
        
        if new_count > 0 or removed_count > 0:
            log(f"Changes detected: +{new_count} new, -{removed_count} removed")
            update_changelog(new_followers, removed_followers, changelog_path, today)
        else:
            log("No changes in followers")
    else:
        log("No previous day's file found. This is the first run or first day of tracking.")
    
    log(f"Followers saved to: {current_file}")
    log("Done!")


if __name__ == "__main__":
    main()
