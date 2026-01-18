#!/bin/bash

# track_followers.sh
# Script to track GitHub followers and maintain a changelog

set -euo pipefail

# Configuration
GITHUB_USERNAME="${1:-}"
DATA_DIR="followers_data"
CHANGELOG="CHANGELOG.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo "Usage: $0 <github_username>"
    echo "Example: $0 vladdoster"
    exit 1
}

# Function to log messages
log() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

# Validate input
if [ -z "$GITHUB_USERNAME" ]; then
    usage
fi

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Get current day of year (001-366)
CURRENT_DAY=$(date +%j)
CURRENT_FILE="$DATA_DIR/$CURRENT_DAY"

# Get previous day of year
if [ "$CURRENT_DAY" = "001" ]; then
    # If it's the first day of year, previous day is last day of previous year
    PREV_YEAR=$(date -d "yesterday" +%Y)
    if [ $((PREV_YEAR % 4)) -eq 0 ] && { [ $((PREV_YEAR % 100)) -ne 0 ] || [ $((PREV_YEAR % 400)) -eq 0 ]; }; then
        PREV_DAY="366"
    else
        PREV_DAY="365"
    fi
else
    PREV_DAY=$(date -d "yesterday" +%j)
fi
PREV_FILE="$DATA_DIR/$PREV_DAY"

# Function to fetch followers from GitHub API using gh CLI
fetch_followers() {
    local username=$1
    local page=1
    local per_page=100
    local all_followers=()
    
    log "Fetching followers for $username..."
    
    # Check if gh CLI is available
    if ! command -v gh &> /dev/null; then
        error "GitHub CLI (gh) is not installed. Please install it from https://cli.github.com/"
    fi
    
    # Check if jq is available for JSON parsing
    if ! command -v jq &> /dev/null; then
        error "jq is not installed. Please install it for JSON parsing."
    fi
    
    # Check if authenticated with gh
    if ! gh auth status &> /dev/null; then
        warn "Not authenticated with GitHub CLI. Run 'gh auth login' to authenticate."
        warn "You may hit rate limits for unauthenticated requests."
    fi
    
    while true; do
        # Fetch followers page by page using gh api
        local response=$(gh api "/users/$username/followers?per_page=$per_page&page=$page" 2>&1)
        local exit_code=$?
        
        # Check if gh api failed
        if [ $exit_code -ne 0 ]; then
            if echo "$response" | grep -q "HTTP 404"; then
                error "User '$username' not found"
            elif echo "$response" | grep -q "set the GH_TOKEN"; then
                error "GitHub CLI requires authentication. Please run 'gh auth login' or set GH_TOKEN environment variable."
            else
                error "GitHub API error: $response"
            fi
        fi
        
        # Extract usernames from JSON response using jq
        local followers=$(echo "$response" | jq -r '.[].login' 2>/dev/null)
        
        # Break if no more followers
        if [ -z "$followers" ]; then
            break
        fi
        
        # Add followers to array
        while IFS= read -r follower; do
            if [ -n "$follower" ]; then
                all_followers+=("$follower")
            fi
        done <<< "$followers"
        
        # Count followers in this page
        local count=$(echo "$followers" | wc -l)
        if [ "$count" -lt "$per_page" ]; then
            break
        fi
        
        ((page++))
    done
    
    # Return all followers, one per line, sorted
    printf '%s\n' "${all_followers[@]}" | sort
}

# Fetch current followers
log "Retrieving followers..."
fetch_followers "$GITHUB_USERNAME" > "$CURRENT_FILE"
FOLLOWER_COUNT=$(wc -l < "$CURRENT_FILE")
log "Found $FOLLOWER_COUNT followers"

# Check if previous day's file exists
if [ -f "$PREV_FILE" ]; then
    log "Previous day's file found ($PREV_FILE). Comparing..."
    
    # Find new followers (in current but not in previous)
    NEW_FOLLOWERS=$(comm -13 "$PREV_FILE" "$CURRENT_FILE")
    
    # Find removed followers (in previous but not in current)
    REMOVED_FOLLOWERS=$(comm -23 "$PREV_FILE" "$CURRENT_FILE")
    
    # Count changes
    NEW_COUNT=$(echo "$NEW_FOLLOWERS" | grep -c . || true)
    REMOVED_COUNT=$(echo "$REMOVED_FOLLOWERS" | grep -c . || true)
    
    if [ "$NEW_COUNT" -gt 0 ] || [ "$REMOVED_COUNT" -gt 0 ]; then
        log "Changes detected: +$NEW_COUNT new, -$REMOVED_COUNT removed"
        
        # Get current date for changelog
        CURRENT_DATE=$(date +"%Y-%m-%d")
        
        # Create changelog if it doesn't exist
        if [ ! -f "$CHANGELOG" ]; then
            echo "# Follower Changelog" > "$CHANGELOG"
            echo "" >> "$CHANGELOG"
            echo "This file tracks changes in GitHub followers over time." >> "$CHANGELOG"
            echo "" >> "$CHANGELOG"
        fi
        
        # Prepare changelog entry
        CHANGELOG_ENTRY="### $CURRENT_DATE\n\n"
        
        if [ "$NEW_COUNT" -gt 0 ]; then
            CHANGELOG_ENTRY+="#### New Followers\n\n"
            while IFS= read -r follower; do
                if [ -n "$follower" ]; then
                    CHANGELOG_ENTRY+="- @$follower\n"
                fi
            done <<< "$NEW_FOLLOWERS"
            CHANGELOG_ENTRY+="\n"
        fi
        
        if [ "$REMOVED_COUNT" -gt 0 ]; then
            CHANGELOG_ENTRY+="#### Removed Followers\n\n"
            while IFS= read -r follower; do
                if [ -n "$follower" ]; then
                    CHANGELOG_ENTRY+="- @$follower\n"
                fi
            done <<< "$REMOVED_FOLLOWERS"
            CHANGELOG_ENTRY+="\n"
        fi
        
        # Create temporary file with new entry at the top
        TEMP_CHANGELOG=$(mktemp)
        
        # Read existing changelog
        if [ -f "$CHANGELOG" ]; then
            # Find the first h3 header or end of file
            if grep -q "^### " "$CHANGELOG"; then
                # Insert before first h3 header
                awk -v entry="$CHANGELOG_ENTRY" '
                    BEGIN { inserted=0 }
                    /^### / && !inserted { print entry; inserted=1 }
                    { print }
                ' "$CHANGELOG" > "$TEMP_CHANGELOG"
            else
                # Append after header section
                {
                    head -n 4 "$CHANGELOG"
                    echo -e "$CHANGELOG_ENTRY"
                    tail -n +5 "$CHANGELOG"
                } > "$TEMP_CHANGELOG"
            fi
        else
            echo -e "$CHANGELOG_ENTRY" > "$TEMP_CHANGELOG"
        fi
        
        mv "$TEMP_CHANGELOG" "$CHANGELOG"
        log "Changelog updated: $CHANGELOG"
    else
        log "No changes in followers"
    fi
else
    log "No previous day's file found. This is the first run or first day of tracking."
fi

log "Followers saved to: $CURRENT_FILE"
log "Done!"
