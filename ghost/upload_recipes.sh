#!/bin/bash

# Script to upload recipes to Ghost

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install pyjwt requests beautifulsoup4
else
    source venv/bin/activate
fi

# Set the Ghost Admin API key directly
export GHOST_ADMIN_API_KEY="67cd6027edc031000157487b:eb9304d2cb866ad6902f88efb11ad43012f40f05015281ecce75cff229093cce"
echo "API key set. Will upload recipes to Healthyfied Ghost blog."

# Run the uploader script
echo "Starting recipe upload process..."
python3 recipe_publisher.py

# Keep terminal open to see results
echo "Press Enter to exit"
read 