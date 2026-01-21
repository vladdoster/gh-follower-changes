#!/usr/bin/env python3
"""
test_track_followers.py
Test script for track_followers.py
This creates mock data to test the changelog functionality
"""

import shutil
from datetime import date, timedelta
from pathlib import Path

# Import functions from track_followers
from track_followers import (
    compare_followers,
    get_date_id,
    load_followers_from_file,
    save_followers_to_file,
    update_changelog,
)


def main() -> None:
    """Run the test scenario."""
    data_dir = Path("followers_data")
    changelog_path = Path("CHANGELOG.md")

    print("Setting up test scenario...")

    # Clean up any previous test data
    if data_dir.exists():
        shutil.rmtree(data_dir)
    if changelog_path.exists():
        changelog_path.unlink()

    data_dir.mkdir(exist_ok=True)

    # Get current and previous date identifiers
    today = date.today()
    yesterday = today - timedelta(days=1)

    current_day = get_date_id(today)
    prev_day = get_date_id(yesterday)

    print(f"Current day: {current_day}")
    print(f"Previous day: {prev_day}")

    # Create mock data for previous day
    prev_followers = [
        "alice123",
        "bob_developer",
        "charlie_coder",
        "david_smith",
        "eve_hacker",
    ]

    print(f"Creating mock data for previous day ({prev_day})...")
    prev_file = data_dir / prev_day
    save_followers_to_file(prev_followers, prev_file)

    print("Previous day followers:")
    for f in prev_followers:
        print(f"  {f}")
    print()

    # Create mock data for current day (with some changes)
    current_followers = [
        "alice123",
        "bob_developer",
        "charlie_coder",
        "frank_newbie",
        "grace_developer",
    ]

    print(f"Creating mock data for current day ({current_day})...")
    current_file = data_dir / current_day
    save_followers_to_file(current_followers, current_file)

    print("Current day followers:")
    for f in current_followers:
        print(f"  {f}")
    print()

    # Test the comparison logic
    print("Testing changelog generation...")

    prev_set = load_followers_from_file(prev_file)
    current_set = set(current_followers)

    changes = compare_followers(current_set, prev_set)

    print(f"New followers ({len(changes.new)}):")
    for f in sorted(changes.new):
        print(f"  {f}")
    print()

    print(f"Removed followers ({len(changes.removed)}):")
    for f in sorted(changes.removed):
        print(f"  {f}")
    print()

    if changes.new or changes.removed:
        update_changelog(changes.new, changes.removed, changelog_path, today)
        print("Changelog created successfully!")

    print()
    print("Generated CHANGELOG.md:")
    print("=======================")
    print(changelog_path.read_text())
    print("=======================")
    print()
    print("Test completed successfully!")


if __name__ == "__main__":
    main()
