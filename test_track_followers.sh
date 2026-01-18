#!/bin/bash

# Test script for track_followers.sh
# This creates mock data to test the changelog functionality

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

DATA_DIR="followers_data"
CHANGELOG="CHANGELOG.md"

echo "Setting up test scenario..."

# Clean up any previous test data
rm -rf "$DATA_DIR" "$CHANGELOG"
mkdir -p "$DATA_DIR"

# Get current day of year
CURRENT_DAY=$(date +%j)

# Calculate previous day (date handles leap years and year boundaries automatically)
PREV_DAY=$(date -d "yesterday" +%j)

echo "Current day: $CURRENT_DAY"
echo "Previous day: $PREV_DAY"

# Create mock data for previous day
echo "Creating mock data for previous day ($PREV_DAY)..."
cat > "$DATA_DIR/$PREV_DAY" << 'EOF'
alice123
bob_developer
charlie_coder
david_smith
eve_hacker
EOF

echo "Previous day followers:"
cat "$DATA_DIR/$PREV_DAY"
echo ""

# Create mock data for current day (with some changes)
echo "Creating mock data for current day ($CURRENT_DAY)..."
cat > "$DATA_DIR/$CURRENT_DAY" << 'EOF'
alice123
bob_developer
charlie_coder
frank_newbie
grace_developer
EOF

echo "Current day followers:"
cat "$DATA_DIR/$CURRENT_DAY"
echo ""

# Now test the comparison logic manually
echo "Testing changelog generation..."

# Find new followers (in current but not in previous)
NEW_FOLLOWERS=$(comm -13 <(sort "$DATA_DIR/$PREV_DAY") <(sort "$DATA_DIR/$CURRENT_DAY"))

# Find removed followers (in previous but not in current)
REMOVED_FOLLOWERS=$(comm -23 <(sort "$DATA_DIR/$PREV_DAY") <(sort "$DATA_DIR/$CURRENT_DAY"))

# Count changes
NEW_COUNT=$(echo "$NEW_FOLLOWERS" | grep -c . || true)
REMOVED_COUNT=$(echo "$REMOVED_FOLLOWERS" | grep -c . || true)

echo "New followers ($NEW_COUNT):"
echo "$NEW_FOLLOWERS"
echo ""

echo "Removed followers ($REMOVED_COUNT):"
echo "$REMOVED_FOLLOWERS"
echo ""

if [ "$NEW_COUNT" -gt 0 ] || [ "$REMOVED_COUNT" -gt 0 ]; then
    # Get current date for changelog
    CURRENT_DATE=$(date +"%Y-%m-%d")
    
    # Create changelog if it doesn't exist
    if [ ! -f "$CHANGELOG" ]; then
        printf "# Follower Changelog\n\n" > "$CHANGELOG"
        printf "This file tracks changes in GitHub followers over time.\n\n" >> "$CHANGELOG"
    fi
    
    # Create temporary file with new entry at the top
    TEMP_CHANGELOG=$(mktemp)
    
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
    
    # Prepend to existing changelog
    if [ -f "$CHANGELOG" ]; then
        # Find where to insert - look for first h3 header
        if grep -q "^### " "$CHANGELOG"; then
            # Insert before first h3 header using awk with getline for security
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
        # No changelog exists yet
        mv "$TEMP_CHANGELOG" "$CHANGELOG"
        TEMP_CHANGELOG=""  # Prevent cleanup of moved file
    fi
    
    echo "Changelog created successfully!"
fi

echo ""
echo "Generated CHANGELOG.md:"
echo "======================="
cat "$CHANGELOG"
echo "======================="
echo ""
echo "Test completed successfully!"
