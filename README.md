# reimagined-guacamole

GitHub Followers Tracker - A bash script to track GitHub followers and maintain a changelog of changes.

## Features

- Retrieves followers for a specified GitHub user
- Saves followers to a file named by day of year (001-366)
- Automatically detects new and removed followers by comparing with previous day
- Generates a markdown changelog with h3 headers for each date
- Lists new and removed followers in separate subsections
- Automated daily tracking via GitHub Actions workflow

## Usage

### Manual Execution

```bash
./track_followers.sh <github_username>
```

Example:
```bash
./track_followers.sh vladdoster
```

### Automated Tracking

The repository includes a GitHub Actions workflow that automatically runs the script every day at midnight UTC. The workflow:
- Runs `track_followers.sh` for the repository owner
- Commits and pushes any changes to `followers_data/` and `CHANGELOG.md`
- Can also be triggered manually from the Actions tab

To enable automated tracking:
1. Ensure the workflow file `.github/workflows/track-followers.yml` is present
2. The workflow has `contents: write` permission to commit changes
3. The workflow will automatically track the repository owner's followers

## How It Works

1. **Fetch Followers**: The script uses the GitHub CLI (`gh api`) to fetch all followers for the specified user
2. **Save to File**: Followers are saved to `followers_data/XXX` where XXX is the current day of year (001-366)
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
├── track_followers.sh           # Main script
├── test_track_followers.sh      # Test script with mock data
├── followers_data/              # Directory containing daily follower snapshots
│   ├── 001                      # Jan 1st followers
│   ├── 002                      # Jan 2nd followers
│   └── ...
└── CHANGELOG.md                 # Changelog of follower changes
```

## Testing

A test script is provided to demonstrate the functionality with mock data (no GitHub authentication required):

```bash
./test_track_followers.sh
```

This creates sample follower data and generates a changelog showing the comparison logic.

## Requirements

- bash 4.0+
- GitHub CLI (`gh`) - Install from https://cli.github.com/
- `jq` - JSON parser for processing API responses
- Standard Unix utilities (date, comm, sort, grep, awk)

## Authentication

The script uses the GitHub CLI (`gh`) to make API calls. You need to authenticate with:

```bash
gh auth login
```

Follow the prompts to authenticate with your GitHub account.

## Notes

- The script validates GitHub usernames to ensure they contain only alphanumeric characters and hyphens
- The script handles leap years and year boundaries automatically using the `date` command
- Followers are sorted alphabetically in the data files for reliable comparison
- The changelog shows the most recent changes at the top
- Each run overwrites the current day's file with fresh data
- Temporary files are automatically cleaned up on script exit
- The script uses `printf` for safe output handling, avoiding issues with special characters