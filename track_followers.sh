#!/bin/bash

# track_followers.sh
# Script to track GitHub followers and maintain a changelog

set -euo pipefail

# Temporary file for cleanup
TEMP_CHANGELOG=""

# Cleanup function
cleanup() {
    if [ -n "$TEMP_CHANGELOG" ] && [ -f "$TEMP_CHANGELOG" ]; then
        rm -f "$TEMP_CHANGELOG"
    fi
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

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

# Validate GitHub username format (alphanumeric and hyphens only)
if ! [[ "$GITHUB_USERNAME" =~ ^[a-zA-Z0-9-]+$ ]]; then
    error "Invalid GitHub username format. Username must contain only alphanumeric characters and hyphens."
fi

# Create data directory if it doesn't exist
mkdir -p "$DATA_DIR"

# Get current date identifier (YYYY-DOY, e.g., 2026-018)
CURRENT_DATE_ID=$(date +%Y-%j)
CURRENT_FILE="$DATA_DIR/$CURRENT_DATE_ID"

# Get previous date identifier (handles leap years and year boundaries automatically)
PREV_DATE_ID=$(date -d "yesterday" +%Y-%j)
PREV_FILE="$DATA_DIR/$PREV_DATE_ID"

# Function to fetch followers from GitHub API using gh CLI
fetch_followers() {
    local username=$1
    local page=1
    local per_page=100
    local all_followers=()
    
    log "Fetching followers for $username..."
    
    # Check if gh CLI is available
    if ! command -v gh > /dev/null; then
        error "GitHub CLI (gh) is not installed. Please install it from https://cli.github.com/"
    fi
    
    # Check if jq is available for JSON parsing
    if ! command -v jq > /dev/null; then
        error "jq is not installed. Please install it for JSON parsing."
    fi
    
    # Check if authenticated with gh
    if ! gh auth status >/dev/null 2>&1; then
        warn "Not authenticated with GitHub CLI. Run 'gh auth login' to authenticate."
        warn "You may hit rate limits for unauthenticated requests."
    fi
    
    while true; do
        # Fetch followers page by page using gh api
        local stderr_file=$(mktemp)
        local response
        local exit_code
        local stderr_output
        
        response=$(gh api "/users/$username/followers?per_page=$per_page&page=$page" 2>"$stderr_file")
        exit_code=$?
        stderr_output=$(cat "$stderr_file" 2>/dev/null || true)
        rm -f "$stderr_file"
        
        # Check if gh api failed
        if [ $exit_code -ne 0 ]; then
            if echo "$stderr_output" | grep -q "HTTP 404"; then
                error "User '$username' not found"
            elif echo "$stderr_output" | grep -Eq "HTTP 401|HTTP 403|set the GH_TOKEN"; then
                error "GitHub CLI requires authentication. Please run 'gh auth login' or set GH_TOKEN environment variable."
            else
                error "GitHub API error: $stderr_output${response:+; }$response"
            fi
        fi
        
        # Extract usernames from JSON response using jq
        local followers=$(echo "$response" | jq -r '.[].login' 2>/dev/null)
        
        # Break if no more followers
        if [ -z "$followers" ]; then
            break
        fi
        
        # Add followers to array
        local before_count=${#all_followers[@]}
        while IFS= read -r follower; do
            if [ -n "$follower" ]; then
                all_followers+=("$follower")
            fi
        done <<< "$followers"
        
        # Count followers in this page using the array length for accuracy
        local page_count=$(( ${#all_followers[@]} - before_count ))
        if [ "$page_count" -lt "$per_page" ]; then
            break
        fi
        
        ((page++))
    done
    
    # Return all followers, one per line, sorted
    if [ "${#all_followers[@]}" -eq 0 ]; then
        # No followers; produce an empty output so downstream comparisons work correctly
        return 0
    fi
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
    
    # Find new followers (in current but not in previous) - sort both files for reliable comparison
    NEW_FOLLOWERS=$(comm -13 <(sort "$PREV_FILE") <(sort "$CURRENT_FILE"))
    
    # Find removed followers (in previous but not in current)
    REMOVED_FOLLOWERS=$(comm -23 <(sort "$PREV_FILE") <(sort "$CURRENT_FILE"))
    
    # Count changes
    NEW_COUNT=$(echo "$NEW_FOLLOWERS" | grep -c . || true)
    REMOVED_COUNT=$(echo "$REMOVED_FOLLOWERS" | grep -c . || true)
    
    if [ "$NEW_COUNT" -gt 0 ] || [ "$REMOVED_COUNT" -gt 0 ]; then
        log "Changes detected: +$NEW_COUNT new, -$REMOVED_COUNT removed"
        
        # Get current date for changelog
        CURRENT_DATE=$(date +"%Y-%m-%d")
        
        # Create temporary file with new entry at the top
        TEMP_CHANGELOG=$(mktemp) || error "Failed to create temporary changelog file"
        if [ -z "$TEMP_CHANGELOG" ]; then
            error "mktemp did not return a filename for temporary changelog"
        fi
        
        # Write the new entry
        {
            printf "### %s\n\n" "$CURRENT_DATE"
            
            if [ "$NEW_COUNT" -gt 0 ]; then
                printf "#### New Followers\n\n"
                while IFS= read -r follower; do
                    if [ -n "$follower" ]; then
                        printf -- "- @%s\n" "$follower"
                    fi
                done <<< "$NEW_FOLLOWERS"
                printf "\n"
            fi
            
            if [ "$REMOVED_COUNT" -gt 0 ]; then
                printf "#### Removed Followers\n\n"
                while IFS= read -r follower; do
                    if [ -n "$follower" ]; then
                        printf -- "- @%s\n" "$follower"
                    fi
                done <<< "$REMOVED_FOLLOWERS"
                printf "\n"
            fi
        } > "$TEMP_CHANGELOG"
        
        # Prepend to existing changelog or create new one
        if [ -f "$CHANGELOG" ]; then
            # Changelog exists - find where to insert
            if grep -q "^### " "$CHANGELOG"; then
                # Insert before first h3 header using awk with getline for security
                if [ ! -f "$TEMP_CHANGELOG" ] || [ ! -r "$TEMP_CHANGELOG" ]; then
                    error "Temporary changelog file is not readable"
                fi
                awk -v temp_file="$TEMP_CHANGELOG" '
                    BEGIN { inserted=0 }
                    /^### / && !inserted {
                        while ((getline line < temp_file) > 0) print line
                        close(temp_file)
                        inserted=1
                    }
                    { print }
                ' "$CHANGELOG" > "${TEMP_CHANGELOG}.final"
                mv "${TEMP_CHANGELOG}.final" "$CHANGELOG"
            else
                # No existing entries, append after the whole file
                cat "$TEMP_CHANGELOG" >> "$CHANGELOG"
            fi
        else
            # No changelog exists yet - create with header
            {
                printf "# Follower Changelog\n\n"
                printf "This file tracks changes in GitHub followers over time.\n\n"
                cat "$TEMP_CHANGELOG"
            } > "$CHANGELOG"
            TEMP_CHANGELOG=""  # Prevent cleanup of content that was already moved
        fi
        
        log "Changelog updated: $CHANGELOG"
    else
        log "No changes in followers"
    fi
else
    log "No previous day's file found. This is the first run or first day of tracking."
fi

log "Followers saved to: $CURRENT_FILE"
log "Done!"
