# reimagined-guacamole

GitHub Followers Tracker - A bash script to track GitHub followers and maintain a changelog of changes.

## Features

- Retrieves followers for a specified GitHub user
- Saves followers to a file named by day of year (001-366)
- Automatically detects new and removed followers by comparing with previous day
- Generates a markdown changelog with h3 headers for each date
- Lists new and removed followers in separate subsections

## Usage

```bash
./track_followers.sh <github_username>
```

Example:
```bash
./track_followers.sh vladdoster
```

## How It Works

1. **Fetch Followers**: The script uses the GitHub API to fetch all followers for the specified user
2. **Save to File**: Followers are saved to `followers_data/XXX` where XXX is the current day of year (001-366)
3. **Compare with Previous Day**: If a file from the previous day exists, the script compares the two lists
4. **Generate Changelog**: If there are changes, an entry is added to `CHANGELOG.md` with:
   - An h3 header with the current date
   - A "New Followers" subsection listing new followers
   - A "Removed Followers" subsection listing removed followers

## File Structure

```
.
├── track_followers.sh       # Main script
├── test_track_followers.sh  # Test script with mock data
├── followers_data/          # Directory containing daily follower snapshots
│   ├── 001                  # Jan 1st followers
│   ├── 002                  # Jan 2nd followers
│   └── ...
└── CHANGELOG.md             # Changelog of follower changes
```

## Testing

A test script is provided to demonstrate the functionality with mock data:

```bash
./test_track_followers.sh
```

This creates sample follower data and generates a changelog showing the comparison logic.

## Requirements

- bash 4.0+
- curl (for API requests)
- Standard Unix utilities (date, comm, sort, grep, awk)

## Notes

- The script handles leap years correctly when calculating the previous day
- Followers are sorted alphabetically in the data files
- The changelog shows the most recent changes at the top
- Each run overwrites the current day's file with fresh data