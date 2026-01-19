#!/usr/bin/env python3

from itertools import chain
import logging
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from ghapi.all import *
from ghapi.all import GhApi

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


def fatal(message: str, *args: object) -> None:
    logger.error(message, *args)
    sys.exit(1)


def usage() -> None:
    """Display usage information and exit."""
    print("Usage: track_followers.py <github_username>")
    sys.exit(1)


def validate_username(username: str) -> bool:
    """Validate GitHub username format (alphanumeric and hyphens only)."""
    return bool(re.match(r"^[a-zA-Z0-9-]+$", username))


def _f(rem,quota): logger.debug("Quota remaining: %s of %s", rem, quota)


def fetch_followers(api: GhApi, username: str) -> list[str]:
    """Fetch all followers for a GitHub user using ghapi."""
    logger.info("Fetching followers for %s...", username)
    try:
        all_followers=[]
        all_followers.extend([f.login for f in chain.from_iterable(paged(api.users.list_followers_for_user, username=username))])
        logger.debug("%s",all_followers)
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            fatal("User '%s' not found", username)
        elif "401" in error_msg or "403" in error_msg:
            fatal("GitHub API requires authentication. Please set GH_TOKEN or GITHUB_TOKEN environment variable.")
        else:
            fatal("GitHub API error: %s", error_msg)
    
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
            logger.warning("%s already in changelog", date_str)
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
    
    logger.info("Changelog updated: %s", changelog_path)


def main() -> None:
    """Main entry point."""
    # Parse arguments
    if len(sys.argv) < 2:
        usage()
    
    github_username = sys.argv[1]
    
    # Validate username
    if not validate_username(github_username):
        fatal("Invalid GitHub username format. Username must contain only alphanumeric characters and hyphens.")
    
    # Configuration
    data_dir = Path(".followers_data")
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
    api = GhApi(owner="vladdoster", authenticate=False, limit_cb=_f)
    
    # Fetch current followers
    logger.info("Retrieving followers...")
    followers = fetch_followers(api, github_username)
    logger.info("Found %d followers", len(followers))
    
    # Save current followers
    save_followers_to_file(followers, current_file)
    
    # Check if previous day's file exists
    if prev_file.exists():
        logger.info("Previous day's file found (%s). Comparing...", prev_file)
        
        prev_followers = load_followers_from_file(prev_file)
        current_followers = set(followers)
        
        # Find new followers (in current but not in previous)
        new_followers = current_followers - prev_followers
        
        # Find removed followers (in previous but not in current)
        removed_followers = prev_followers - current_followers
        
        new_count = len(new_followers)
        removed_count = len(removed_followers)
        
        if new_count > 0 or removed_count > 0:
            logger.info("Changes detected: +%d new, -%d removed", new_count, removed_count)
            update_changelog(new_followers, removed_followers, changelog_path, today)
        else:
            logger.info("No changes in followers")
    else:
        logger.info("No previous day's file found. This is the first run or first day of tracking.")
    
    logger.info("Followers saved to: %s", current_file)
    logger.info("Done!")


if __name__ == "__main__":
    main()
