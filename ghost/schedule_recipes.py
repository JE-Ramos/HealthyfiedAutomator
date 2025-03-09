#!/usr/bin/env python3

import os
import json
import jwt
import time
import datetime
import requests
from pathlib import Path

# Ghost API configuration
ADMIN_API_URL = 'https://healthyfied.ghost.io/ghost/api/admin/'
ADMIN_API_KEY = '67472f3b02b637000105c5b3:0d7cacc062c371d3bd12e0994d85d059d8ca358b20ab7ea1dec28aa9e32d9e92'  # Format: 'id:secret'

# Split the Admin API key into ID and SECRET
id, secret = ADMIN_API_KEY.split(':')

# Function to create JWT token for authentication
def create_token():
    """Create a JWT token for Ghost API authentication"""
    iat = int(time.time())
    exp = iat + 5 * 60  # Token valid for 5 minutes
    aud = '/admin/'

    payload = {
        'iat': iat,
        'exp': exp,
        'aud': aud
    }

    token = jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers={'kid': id})
    # Make sure token is a string
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

# Function to get request headers with token
def get_headers():
    """Get headers for Ghost API requests"""
    token = create_token()
    return {
        'Authorization': f'Ghost {token}',
        'Content-Type': 'application/json',
        'Accept-Version': 'v5.99'  # Specify the API version
    }

# Function to fetch all posts
def fetch_all_posts():
    """Fetch all posts from Ghost"""
    url = f"{ADMIN_API_URL}posts/?limit=all"
    
    headers = get_headers()
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        posts = response.json().get('posts', [])
        print(f"Successfully fetched {len(posts)} posts")
        return posts
    else:
        print(f"Error fetching posts: {response.status_code} - {response.text}")
        return []

# Function to fetch or create a tag
def fetch_or_create_tag(tag_name):
    """Fetch an existing tag or create a new one"""
    tag_slug = tag_name.lower().replace(' ', '-')
    url = f"{ADMIN_API_URL}tags/slug/{tag_slug}"
    
    headers = get_headers()
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Tag exists, return its ID
        return response.json().get('tags', [])[0].get('id')
    else:
        # Tag doesn't exist, create it
        create_url = f"{ADMIN_API_URL}tags/"
        payload = {
            "tags": [
                {
                    "name": tag_name
                }
            ]
        }
        response = requests.post(create_url, headers=headers, json=payload)
        if response.status_code == 201:
            return response.json().get('tags', [])[0].get('id')
        else:
            print(f"Error creating tag: {response.status_code} - {response.text}")
            return None

# Function to create a post for a recipe
def create_recipe_post(recipe_file, publish_date):
    """Create a new post from a recipe JSON file"""
    # Read recipe data from the JSON file
    with open(recipe_file, 'r') as f:
        recipe_data = json.load(f)
    
    # Extract recipe details - properly access the schema.org structure
    title = recipe_data.get('name', recipe_data.get('title', 'Untitled Recipe'))
    
    # Extract description to use as excerpt, limit to 300 characters
    description = recipe_data.get('description', '')
    # Truncate to 297 characters and add ellipsis if longer than 300
    if len(description) > 300:
        description = description[:297] + '...'
    
    print(f"Description for excerpt (truncated to 300 chars): {description}")
    
    # Print the structure of the recipe data for debugging
    print(f"Recipe data keys: {recipe_data.keys()}")
    print(f"Extracted title: {title}")
    
    # Extract other recipe details
    ingredients = recipe_data.get('recipeIngredient', recipe_data.get('ingredients', []))
    
    # For instructions, handle both schema.org format and simple array
    instructions_data = recipe_data.get('recipeInstructions', recipe_data.get('instructions', []))
    instructions = []
    if instructions_data and isinstance(instructions_data[0], dict):
        # Schema.org format with HowToStep objects
        instructions = [step.get('text', '') for step in instructions_data]
    else:
        # Simple array of strings
        instructions = instructions_data
    
    nutrition_info = recipe_data.get('nutrition', {})
    if isinstance(nutrition_info, dict) and '@type' in nutrition_info:
        # Remove the @type key from nutrition info
        nutrition_info = {k: v for k, v in nutrition_info.items() if k != '@type'}
    
    # Extract tags from keywords if available
    if 'keywords' in recipe_data:
        keywords = recipe_data.get('keywords', '')
        if isinstance(keywords, str):
            recipe_tags = [tag.strip() for tag in keywords.split(',')]
        else:
            recipe_tags = []
    else:
        recipe_tags = recipe_data.get('tags', [])
    
    # We're not using feature images as requested
    feature_image = None
    
    # Always add "Recipes" as the first tag
    all_tags = ["Recipes"] + recipe_tags
    
    # Create tag objects
    tag_ids = []
    for tag_name in all_tags:
        tag_id = fetch_or_create_tag(tag_name)
        if tag_id:
            tag_ids.append({"id": tag_id})
    
    # Format ingredients
    ingredients_html = "<ul>"
    for ing in ingredients:
        ingredients_html += f"<li>{ing}</li>"
    ingredients_html += "</ul>"
    
    # Format instructions
    instructions_html = "<ol>"
    for idx, step in enumerate(instructions, 1):
        instructions_html += f"<li>{step}</li>"
    instructions_html += "</ol>"
    
    # Format nutrition information
    nutrition_html = "<h3>Nutrition Information</h3><ul>"
    for key, value in nutrition_info.items():
        nutrition_html += f"<li><strong>{key.capitalize()}:</strong> {value}</li>"
    nutrition_html += "</ul>"
    
    # Create the HTML content for the post in mobiledoc format
    mobiledoc = {
        "version": "0.3.1",
        "markups": [],
        "atoms": [],
        "cards": [
            ["html", {"html": "<div class='ingredients-section'><h2>Ingredients</h2>" + ingredients_html + "</div>"}],
            ["html", {"html": "<div class='instructions-section'><h2>Instructions</h2>" + instructions_html + "</div>"}],
            ["html", {"html": "<div class='nutrition-section'>" + nutrition_html + "</div>"}],
        ],
        "sections": [[10, 0], [10, 1], [10, 2]]
    }
    
    # Format the published_at date in ISO-8601 format with timezone
    # Ghost requires the specific Z-format for UTC time
    published_at = publish_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    
    # Use the original recipe data as structured data for SEO
    # Remove any top-level fields that aren't part of schema.org
    schema_data = {k: v for k, v in recipe_data.items() if not k.startswith('_')}
    
    # Create the post data
    post_data = {
        "posts": [{
            "title": title,
            "mobiledoc": json.dumps(mobiledoc),
            "status": "published",  # Use 'published' instead of 'scheduled'
            "published_at": published_at,
            "tags": tag_ids,
            "feature_image": feature_image,  # This will be None as requested
            "custom_excerpt": description,  # Use custom_excerpt (truncated to 300 chars)
            "codeinjection_head": f"<script type=\"application/ld+json\">{json.dumps(schema_data)}</script>"
        }]
    }
    
    # Create the post
    url = f"{ADMIN_API_URL}posts/"
    response = requests.post(url, headers=get_headers(), json=post_data)
    
    if response.status_code == 201:
        post_id = response.json().get('posts', [])[0].get('id')
        print(f"Successfully created post for '{title}' with ID: {post_id}")
        print(f"Published with date: {publish_date.strftime('%Y-%m-%d')}")
        return post_id
    else:
        print(f"Error creating post: {response.status_code} - {response.text}")
        return None

# Function to schedule recipes in batches
def schedule_recipes_in_batches(batch_size=10, start_index=10):
    """Schedule recipes in batches, continuing from the specified index"""
    # Path to the final folder containing recipe files
    final_folder = Path("/Users/je-dev/Documents/Repository/Healthyfied/HealthyfiedAutomator/final")
    
    # Get all JSON files in the folder
    recipe_files = sorted(list(final_folder.glob("*.json")))
    total_files = len(recipe_files)
    
    # Calculate remaining files and verify start_index
    if start_index >= total_files:
        print(f"Start index {start_index} is beyond the total number of recipes ({total_files})")
        return
    
    remaining_files = total_files - start_index
    print(f"Total recipe files: {total_files}")
    print(f"Already processed: {start_index}")
    print(f"Remaining files: {remaining_files}")
    
    # Calculate how many batches we need
    num_batches = (remaining_files + batch_size - 1) // batch_size  # Ceiling division
    print(f"Will process in {num_batches} batch(es) of {batch_size} recipes each")
    
    # Process one batch at a time
    current_batch = 1
    
    # The next date should be Feb 27, 2025 (since we already used Mar 9 down to Feb 28)
    # Calculate the start date for the next batch
    # March 9, 2025 was the first date, and we've already published 10 recipes
    end_date = datetime.datetime(2025, 3, 9, 12, 0, 0) - datetime.timedelta(days=start_index)
    
    # Process the current batch
    start_idx = start_index
    end_idx = min(start_idx + batch_size, total_files)
    current_batch_files = recipe_files[start_idx:end_idx]
    
    print(f"\nProcessing batch {current_batch} ({len(current_batch_files)} recipes)")
    print(f"Starting with publication date: {end_date.strftime('%Y-%m-%d')}")
    
    print("Files to be processed in this batch:")
    for i, file in enumerate(current_batch_files):
        print(f"{i+1}. {file.name}")
    
    # Publish the recipes with dates going backward from end_date
    for i, recipe_file in enumerate(current_batch_files):
        # Calculate the publish date (i days before end_date)
        publish_date = end_date - datetime.timedelta(days=i)
        
        print(f"\nProcessing recipe {i+1}/{len(current_batch_files)}: {recipe_file.name}")
        print(f"Publication date: {publish_date.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        create_recipe_post(recipe_file, publish_date)
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    print(f"\nBatch {current_batch} completed. {end_idx} of {total_files} recipes have been processed.")
    print(f"To process the next batch, run this script with start_index={end_idx}")

# Main function
if __name__ == "__main__":
    # Comment out the original function
    # schedule_first_10_recipes()
    
    # Use the new batch function instead
    # To process the next batch (recipes 31-40), use start_index=30
    schedule_recipes_in_batches(batch_size=10, start_index=30) 