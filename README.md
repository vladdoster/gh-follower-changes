# gh-follower-changes

GitHub Followers Tracker - A Python script to track GitHub followers and maintain a changelog of changes.

## Features

- Retrieves followers for a specified GitHub user
- Saves followers to a file named with year and day of year (YYYY-DOY format, e.g., 2026-018)
- Automatically detects new and removed followers by comparing with previous day
- Generates a markdown changelog with h3 headers for each date
- Lists new and removed followers in separate subsections
- Automated daily tracking via GitHub Actions workflow

## Usage

### Manual Execution

```bash
uv run track_followers.py <github_username>
```

Example:
```bash
uv run track_followers.py vladdoster
```

### Automated Tracking

The repository includes a GitHub Actions workflow that automatically runs the script every day at midnight UTC. The workflow:
- Runs `track_followers.py` for the repository owner
- Commits and pushes any changes to `followers_data/` and `CHANGELOG.md`
- Can also be triggered manually from the Actions tab

To enable automated tracking:
1. Ensure the workflow file `.github/workflows/track-followers.yml` is present
2. The workflow has `contents: write` permission to commit changes
3. The workflow will automatically track the repository owner's followers

## How It Works

1. **Fetch Followers**: The script uses the [ghapi](https://ghapi.fast.ai/) Python library to fetch all followers for the specified user
2. **Save to File**: Followers are saved to `followers_data/YYYY-DOY` where YYYY is the year and DOY is the day of year (e.g., 2026-018 for January 18, 2026)
3. **Compare with Previous Day**: If a file from the previous day exists, the script compares the two lists
4. **Generate Changelog**: If there are changes, an entry is added to `CHANGELOG.md` with:
   - An h3 header with the current date
   - A "New Followers" subsection listing new followers
   - A "Removed Followers" subsection listing removed followers

## File Structure

```
.
├── .github/
│   └── workflows/
│       └── track-followers.yml  # GitHub Actions workflow
├── pyproject.toml               # Python project configuration
├── track_followers.py           # Main script
├── test_track_followers.py      # Test script with mock data
├── followers_data/              # Directory containing daily follower snapshots
│   ├── 2026-001                 # Jan 1st, 2026 followers
│   ├── 2026-002                 # Jan 2nd, 2026 followers
│   └── ...
└── CHANGELOG.md                 # Changelog of follower changes
```

## Testing

A test script is provided to demonstrate the functionality with mock data (no GitHub authentication required):

```bash
uv run test_track_followers.py
```

This creates sample follower data and generates a changelog showing the comparison logic.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer and resolver

Dependencies are managed via `pyproject.toml` and installed automatically by uv:
- [ghapi](https://ghapi.fast.ai/) - Python library for GitHub API

## Authentication

The script uses the `ghapi` library to make GitHub API calls. Authentication is done via environment variables:

```bash
export GH_TOKEN="your_github_token"
# or
export GITHUB_TOKEN="your_github_token"
```

You can create a personal access token at https://github.com/settings/tokens

## Notes

- The script validates GitHub usernames to ensure they contain only alphanumeric characters and hyphens
- The script handles leap years and year boundaries automatically
- Followers are sorted alphabetically in the data files for reliable comparison
- The changelog shows the most recent changes at the top
- Each run overwrites the current day's file with fresh data
