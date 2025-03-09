#!/bin/bash

# Update script for HealthyfiedAutomator

echo "=== Updating HealthyfiedAutomator ==="

# Get the current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed. Please install git to use this update script."
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Error: This doesn't appear to be a git repository."
    exit 1
fi

# Pull the latest changes
echo "Pulling latest changes from GitHub..."
git pull

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment and update dependencies
echo "Updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "=== Update Complete ==="
echo "Check CURRENT_STATE.md for the latest processing state."
echo ""
echo "To continue publishing recipes:"
echo "  cd ghost"
echo "  python publish_all_recipes.py" 