#!/usr/bin/env python3

from dataclasses import dataclass
from datetime import date, timedelta
from itertools import chain
import logging
from pathlib import Path
import re
import sys
from typing import NoReturn

from ghapi.all import GhApi, github_token
from ghapi.page import paged
import mdformat

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)
logging.getLogger('markdown_it').setLevel(logging.INFO)

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9-]+$")
H3_PATTERN = re.compile(r'(^\n)(^### )', re.MULTILINE)


@dataclass
class FollowerChanges:
    """Represents changes in followers between two time periods."""

    new: set[str]
    removed: set[str]

    @property
    def has_changes(self) -> bool:
        return bool(self.new or self.removed)

    def __str__(self) -> str:
        return f"+{len(self.new)} new, -{len(self.removed)} removed"


def fatal(message: str, *args: object) -> NoReturn:
    logger.error(message, *args)
    sys.exit(1)


def validate_username(username: str) -> bool:
    """Validate GitHub username format (alphanumeric and hyphens only)."""
    return bool(USERNAME_PATTERN.match(username))


def fetch_followers(api: GhApi, username: str) -> list[str]:
    """Fetch all followers for a GitHub user using ghapi."""
    logger.info(f"Fetching followers for {'%s'!r}...", username)

    error_handlers = {
        "404": f"User '{username}' not found",
        "401": "GitHub API requires authentication.  Please set GH_TOKEN or GITHUB_TOKEN.",
        "403": "GitHub API requires authentication. Please set GH_TOKEN or GITHUB_TOKEN.",
    }

    try:
        pages = paged(api.users.list_followers_for_user, username=username)
        followers = sorted(f.login for f in chain.from_iterable(pages))
        logger.debug("%s", followers)
        return followers
    except Exception as e:
        error_msg = str(e)
        for code, msg in error_handlers.items():
            if code in error_msg:
                fatal(msg)
        fatal("GitHub API error:  %s", error_msg)


def load_followers(filepath: Path) -> set[str]:
    """Load followers from a file."""
    if not filepath.exists():
        return set()
    return {line.strip() for line in filepath.read_text().splitlines() if line.strip()}


def save_followers(followers: list[str], filepath: Path) -> None:
    """Save followers to a file, one per line."""
    filepath.write_text("\n".join(followers) + "\n" if followers else "")


def build_changelog_entry(changes: FollowerChanges, current_date: date) -> str:
    """Build a changelog entry for the given changes."""
    date_str = current_date.strftime("%Y-%m-%d")
    sections = [f"### {date_str}"]

    for title, followers in [
        ("New Followers", changes.new),
        ("Removed Followers", changes.removed),
    ]:
        if followers:
            sections.extend(
                [
                    f"#### {title}",
                    *[f"- @{f}" for f in sorted(followers)],
                ]
            )

    return "\n".join(sections)


def update_changelog(
    changes: FollowerChanges, changelog_path: Path, current_date: date
) -> None:
    """Update the changelog with new and removed followers."""
    date_str = current_date.strftime("%Y-%m-%d")
    new_entry = build_changelog_entry(changes, current_date)

    if not changelog_path.exists():
        header = "# Follower Changelog\n\nThis file tracks changes in GitHub followers over time.\n\n"
        changelog_path.write_text(header + new_entry)
        logger.info("Changelog created: %s", changelog_path)
        return

    content = changelog_path.read_text()

    if date_str in content:
        logger.warning("%s already in changelog", date_str)
        return

    match = H3_PATTERN.search(content)
    if match:
        logger.debug('%02d-%02d: %s' % (match.start(), match.end(), f'{match.group(0)!r}'))
    insert_pos = match.start() if match else len(content)
    new_content = content[:insert_pos] + new_entry + content[insert_pos:]

    changelog_path.write_text(new_content)
    mdformat.file(changelog_path)

    logger.info("Changelog updated: %s", changelog_path)



def compare_followers(current: set[str], previous: set[str]) -> FollowerChanges:
    """Compare current and previous followers to find changes."""
    return FollowerChanges(new=current - previous, removed=previous - current)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: track_followers.py <github_username>")
        sys.exit(1)

    github_username = sys.argv[1]

    if not validate_username(github_username):
        fatal(
            "Invalid GitHub username format.  Must contain only alphanumeric characters and hyphens."
        )

    # Configuration
    data_dir = Path(".followers_data")
    changelog_path = Path("CHANGELOG.md")
    data_dir.mkdir(exist_ok=True)

    # Date-based file paths
    today = date.today()
    current_file = data_dir / today.strftime("%Y-%j")
    prev_file = data_dir / (today - timedelta(days=1)).strftime("%Y-%j")

    # Fetch and save current followers
    authenticate=False
    try:
        github_token()
        authenticate=True
        logger.info(f"GH Token found, authenticating to GH API {authenticate}")
    except AttributeError as e:
        logger.warning("GH Token not found, GH API requests might fail due to quota")
        logger.debug(e)

    api = GhApi(
        authenticate=authenticate,
        limit_cb=lambda rem, quota: logger.debug( "Quota remaining: %s of %s", rem, quota),
        owner="vladdoster",
    )
    followers = fetch_followers(api, github_username)
    logger.info("Found %d followers", len(followers))
    save_followers(followers, current_file)

    # Compare with previous day if available
    if prev_file.exists():
        logger.info("Comparing with previous day (%s)...", prev_file.name)
        changes = compare_followers(set(followers), load_followers(prev_file))

        if changes.has_changes:
            logger.info("Changes detected: %s", changes)
            update_changelog(changes, changelog_path, today)
        else:
            logger.info("No changes in followers")
    else:
        logger.info("No previous data found. First run or first day of tracking.")

    logger.info("Followers saved to: %s", current_file)
    logger.info("Done!")


if __name__ == "__main__":
    main()
