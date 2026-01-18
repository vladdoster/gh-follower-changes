#!/bin/bash

# Test script for track_followers.sh
# This creates mock data to test the changelog functionality

set -euo pipefail

DATA_DIR="followers_data"
CHANGELOG="CHANGELOG.md"

echo "Setting up test scenario..."

# Clean up any previous test data
rm -rf "$DATA_DIR" "$CHANGELOG"
mkdir -p "$DATA_DIR"

# Get current day of year
CURRENT_DAY=$(date +%j)

# Calculate previous day
if [ "$CURRENT_DAY" = "001" ]; then
    PREV_YEAR=$(date -d "yesterday" +%Y)
    if [ $((PREV_YEAR % 4)) -eq 0 ] && { [ $((PREV_YEAR % 100)) -ne 0 ] || [ $((PREV_YEAR % 400)) -eq 0 ]; }; then
        PREV_DAY="366"
    else
        PREV_DAY="365"
    fi
else
    PREV_DAY=$(date -d "yesterday" +%j)
fi

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
NEW_FOLLOWERS=$(comm -13 "$DATA_DIR/$PREV_DAY" "$DATA_DIR/$CURRENT_DAY")

# Find removed followers (in previous but not in current)
REMOVED_FOLLOWERS=$(comm -23 "$DATA_DIR/$PREV_DAY" "$DATA_DIR/$CURRENT_DAY")

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
    echo "Changelog created successfully!"
fi

echo ""
echo "Generated CHANGELOG.md:"
echo "======================="
cat "$CHANGELOG"
echo "======================="
echo ""
echo "Test completed successfully!"
