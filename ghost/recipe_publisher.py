#!/usr/bin/env python3
import jwt
import time
import requests
import json
import os
import glob
import datetime
import shutil
import traceback
from datetime import timedelta, datetime
import re
import html
import markdown
from bs4 import BeautifulSoup

# Configuration
ADMIN_API_URL = "https://healthyfied.ghost.io/ghost/api/admin/"
ADMIN_API_KEY = os.environ.get("GHOST_ADMIN_API_KEY", "")
RECIPES_DIR = "../final"
MARKDOWN_DIR = "recipe-markdown"

# Debug mode - set to True for more verbose output
DEBUG = True

# Ensure markdown directory exists
os.makedirs(MARKDOWN_DIR, exist_ok=True)

def create_token():
    """Create a JWT token for authentication with Ghost Admin API."""
    if DEBUG:
        print(f"Creating token with API key: {ADMIN_API_KEY[:5]}...{ADMIN_API_KEY[-5:] if len(ADMIN_API_KEY) > 10 else ''}")
    
    try:
        # Split the key into ID and SECRET
        key_parts = ADMIN_API_KEY.split(':')
        
        if len(key_parts) != 2:
            print("ERROR: API key format is invalid. It should be in the format 'id:secret'")
            return None
        
        # Extract the Key ID and Secret
        key_id = key_parts[0]
        secret = key_parts[1]
        
        # Current time in seconds
        iat = int(time.time())
        
        # Create the header and payload
        header = {'alg': 'HS256', 'typ': 'JWT', 'kid': key_id}
        payload = {
            'iat': iat,
            'exp': iat + 5 * 60,  # Expiration time (5 minutes)
            'aud': '/admin/'      # Audience
        }
        
        # Create the token
        token = jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)
        
        # Make sure token is a string
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        return token
    except Exception as e:
        print(f"ERROR creating token: {str(e)}")
        if DEBUG:
            traceback.print_exc()
        return None

def get_headers():
    """Get headers for API requests."""
    token = create_token()
    if not token:
        return None
    
    return {
        'Authorization': f'Ghost {token}',
        'Content-Type': 'application/json'
    }

def sanitize_slug(text):
    """Convert text to a sanitized slug format."""
    # Replace spaces with hyphens and convert to lowercase
    slug = text.lower().replace(' ', '-')
    # Remove special characters
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug

def format_diet_tag(diet_url):
    """Convert schema.org diet URL to a readable tag."""
    if not diet_url.startswith("https://schema.org/"):
        return diet_url
    
    # Extract the diet name from the URL
    diet_name = diet_url.replace("https://schema.org/", "").replace("Diet", "")
    
    # Add spaces before capital letters
    diet_name = re.sub(r'([A-Z])', r' \1', diet_name).strip()
    
    return diet_name

def markdown_to_html(markdown_content):
    """Convert markdown content to HTML."""
    try:
        # Use a markdown library to convert to HTML
        import markdown as md
        html_content = md.markdown(markdown_content, extensions=['extra'])
        return html_content
    except ImportError:
        # If markdown library isn't available, do a basic conversion
        html_content = markdown_content.replace('\n\n', '</p><p>').replace('\n', '<br>')
        html_content = f"<p>{html_content}</p>"
        return html_content

def create_recipe_html(recipe_data):
    """Create HTML content for a recipe post."""
    recipe_name = recipe_data.get('name', 'Untitled Recipe')
    description = recipe_data.get('description', '')
    
    # Extract key recipe details
    prep_time = recipe_data.get('prepTime', '').replace('PT', '')
    cook_time = recipe_data.get('cookTime', '').replace('PT', '')
    total_time = recipe_data.get('totalTime', '').replace('PT', '')
    
    yield_value = recipe_data.get('recipeYield', '')
    category = recipe_data.get('recipeCategory', '')
    cuisine = recipe_data.get('recipeCuisine', '')
    
    # Get dietary information
    suitable_diets = recipe_data.get('suitableForDiet', [])
    # Convert diet URLs to readable names
    readable_diets = [format_diet_tag(diet) for diet in suitable_diets]
    diet_labels = ', '.join(diet for diet in readable_diets) if readable_diets else 'None'
    
    # Extract nutrition information
    nutrition = recipe_data.get('nutrition', {})
    calories = nutrition.get('calories', 'N/A')
    carbs = nutrition.get('carbohydrateContent', 'N/A')
    protein = nutrition.get('proteinContent', 'N/A')
    fat = nutrition.get('fatContent', 'N/A')
    
    # Get ingredients and instructions
    ingredients = recipe_data.get('recipeIngredient', [])
    instructions = recipe_data.get('recipeInstructions', [])
    
    # Build HTML content
    html_content = f"""
<div class="recipe-card">
    <div class="recipe-header">
        <h1>{recipe_name}</h1>
        <p class="recipe-description">{description}</p>
    </div>
    
    <div class="recipe-meta">
        <div class="recipe-meta-item">
            <span class="recipe-meta-label">Prep Time</span>
            <span class="recipe-meta-value">{prep_time}</span>
        </div>
        <div class="recipe-meta-item">
            <span class="recipe-meta-label">Cook Time</span>
            <span class="recipe-meta-value">{cook_time}</span>
        </div>
        <div class="recipe-meta-item">
            <span class="recipe-meta-label">Total Time</span>
            <span class="recipe-meta-value">{total_time}</span>
        </div>
        <div class="recipe-meta-item">
            <span class="recipe-meta-label">Servings</span>
            <span class="recipe-meta-value">{yield_value}</span>
        </div>
        <div class="recipe-meta-item">
            <span class="recipe-meta-label">Category</span>
            <span class="recipe-meta-value">{category}</span>
        </div>
        <div class="recipe-meta-item">
            <span class="recipe-meta-label">Cuisine</span>
            <span class="recipe-meta-value">{cuisine}</span>
        </div>
    </div>
    
    <div class="nutrition-info">
        <h2>Nutrition Information</h2>
        <div class="nutrition-grid">
            <div class="nutrition-item">
                <span class="nutrition-label">Calories</span>
                <span class="nutrition-value">{calories}</span>
            </div>
            <div class="nutrition-item">
                <span class="nutrition-label">Carbohydrates</span>
                <span class="nutrition-value">{carbs}</span>
            </div>
            <div class="nutrition-item">
                <span class="nutrition-label">Protein</span>
                <span class="nutrition-value">{protein}</span>
            </div>
            <div class="nutrition-item">
                <span class="nutrition-label">Fat</span>
                <span class="nutrition-value">{fat}</span>
            </div>
        </div>
    </div>
    
    <div class="ingredients">
        <h2>Ingredients</h2>
        <ul>
"""
    
    # Add ingredients
    for ingredient in ingredients:
        html_content += f"<li>{ingredient}</li>\n"
    
    html_content += """
        </ul>
    </div>
    
    <div class="instructions">
        <h2>Instructions</h2>
        <ol>
"""
    
    # Add instructions with ad block after middle instruction
    instruction_count = len(instructions)
    middle_index = instruction_count // 2
    
    for i, instruction in enumerate(instructions):
        step_text = instruction.get('text', '')
        html_content += f"<li>{step_text}</li>\n"
        
        # Insert ad block after the middle instruction
        if i == middle_index:
            html_content += """
        </ol>
        
        <!-- Ad Block -->
        <div class="ad-container">
            <p class="ad-label">Advertisement</p>
            <div class="ad-content">
                <!-- Ad code here -->
                <p>Support Healthyfied by checking out our sponsors</p>
            </div>
        </div>
        
        <ol start="{next_num}">
""".format(next_num=i+2)
    
    html_content += """
        </ol>
    </div>
    
    <div class="recipe-tags">
"""
    
    # Add diet tags
    for diet in readable_diets:
        html_content += f'<span class="diet-tag">{diet}</span>\n'
    
    html_content += """
    </div>
</div>
"""
    
    return html_content

def read_markdown_file(markdown_path):
    """Read a markdown file and extract its components."""
    with open(markdown_path, 'r') as f:
        content = f.read()
    
    # Extract frontmatter
    frontmatter_match = re.search(r'---\n(.*?)\n---', content, re.DOTALL)
    if not frontmatter_match:
        print(f"No frontmatter found in {markdown_path}")
        return None, None, None, None, None, None
    
    frontmatter_text = frontmatter_match.group(1)
    
    # Parse frontmatter
    title_match = re.search(r'title: "(.*?)"', frontmatter_text)
    slug_match = re.search(r'slug: "(.*?)"', frontmatter_text)
    tags_match = re.search(r'tags: \[(.*?)\]', frontmatter_text)
    date_match = re.search(r'date: (.*?)$', frontmatter_text, re.MULTILINE)
    
    if not title_match or not slug_match:
        print(f"Could not extract title or slug from {markdown_path}")
        return None, None, None, None, None, None
    
    title = title_match.group(1)
    slug = slug_match.group(1)
    date = date_match.group(1) if date_match else None
    
    # Extract tags
    tags = []
    if tags_match:
        tags_str = tags_match.group(1)
        tag_matches = re.finditer(r'"(.*?)"', tags_str)
        tags = [{"name": match.group(1)} for match in tag_matches]
    
    # Remove frontmatter from content
    content = re.sub(r'---\n.*?\n---\n', '', content, flags=re.DOTALL)
    
    # Extract JSON-LD
    json_ld_match = re.search(r'<!-- json\+ld metadata -->\n<script type="application/ld\+json">\n(.*?)\n</script>', content, re.DOTALL)
    json_ld = ""
    recipe_data = None
    if json_ld_match:
        json_ld = json_ld_match.group(0)
        # Extract recipe data from JSON-LD
        try:
            recipe_json = json_ld_match.group(1)
            recipe_data = json.loads(recipe_json)
        except Exception as e:
            print(f"Error parsing JSON-LD: {str(e)}")
        
        # Remove JSON-LD from content
        content = content.replace(json_ld_match.group(0), '')
    
    # Extract feature image
    feature_image = None
    image_match = re.search(r'!\[.*?\]\((.*?)\)', content)
    if image_match:
        feature_image = image_match.group(1)
        # Clean up any array notation from the image URL
        feature_image = re.sub(r'\[\'(.*?)\'\]', r'\1', feature_image)
    
    return title, slug, tags, date, feature_image, recipe_data

def create_post_from_markdown(markdown_path, publish_date):
    """Create a post in Ghost using a markdown file."""
    try:
        # Extract information from markdown file
        title, slug, tags, date, feature_image, recipe_data = read_markdown_file(markdown_path)
        
        if not title or not recipe_data:
            print(f"Missing required data from {markdown_path}")
            return False
        
        # Create HTML content for the post
        html_content = create_recipe_html(recipe_data)
        
        # Create JSON-LD script
        json_ld = f"""
<script type="application/ld+json">
{json.dumps(recipe_data, indent=2)}
</script>
"""
        
        # Format the date
        formatted_date = publish_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        # Create the post data
        post_data = {
            "posts": [{
                "title": title,
                "slug": slug,
                "html": html_content,
                "status": "published",
                "published_at": formatted_date,
                "tags": tags,
                "codeinjection_head": json_ld,
                "feature_image": feature_image
            }]
        }
        
        if DEBUG:
            print(f"\nPOST DATA for {title}:")
            print(f"- Slug: {slug}")
            print(f"- Tags: {tags}")
            print(f"- Publish date: {formatted_date}")
            print(f"- Feature image: {feature_image}")
        
        # Get headers
        headers = get_headers()
        if not headers:
            print("Failed to get authorization headers. Check your API key.")
            return False
        
        # Send request to Ghost API
        url = f"{ADMIN_API_URL}posts/"
        if DEBUG:
            print(f"Sending request to {url}")
            
        response = requests.post(url, json=post_data, headers=headers)
        
        if DEBUG:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text[:200]}..." if len(response.text) > 200 else response.text)
        
        if response.status_code >= 200 and response.status_code < 300:
            print(f"Successfully published recipe: {title} with publish date {formatted_date}")
            return True
        else:
            print(f"Failed to publish recipe: {title} - Status: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"ERROR creating post from {markdown_path}: {str(e)}")
        if DEBUG:
            traceback.print_exc()
        return False

def check_api_connection():
    """Test the connection to the Ghost Admin API."""
    try:
        print("Testing connection to Ghost Admin API...")
        
        if not ADMIN_API_KEY:
            print("ERROR: Ghost Admin API key is not set. Please set the GHOST_ADMIN_API_KEY environment variable.")
            return False
        
        headers = get_headers()
        if not headers:
            print("ERROR: Failed to create authorization headers. Check your API key format.")
            return False
        
        # Try to get site info as a test
        url = f"{ADMIN_API_URL}site/"
        print(f"Sending request to {url}")
        
        response = requests.get(url, headers=headers)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 300:
            print("Successfully connected to Ghost Admin API!")
            site_data = response.json()
            if 'site' in site_data:
                print(f"Connected to site: {site_data['site'].get('title', 'Unknown')}")
            return True
        else:
            print(f"Failed to connect to Ghost Admin API. Status: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"ERROR testing connection: {str(e)}")
        if DEBUG:
            traceback.print_exc()
        return False

def publish_recipes_from_markdown():
    """Publish recipes from markdown files to Ghost."""
    # First test the API connection
    if not check_api_connection():
        print("API connection test failed. Please check your API key and Ghost installation.")
        return
    
    # Get all markdown files
    markdown_files = sorted(glob.glob(os.path.join(MARKDOWN_DIR, "recipe_*.md")))
    
    if not markdown_files:
        print(f"No markdown files found in {MARKDOWN_DIR}")
        return
    
    print(f"Found {len(markdown_files)} markdown files to process")
    
    # Calculate the publish dates (1 day apart, working backwards from Mar 9, 2025)
    end_date = datetime.strptime("2025-03-09", "%Y-%m-%d")
    
    # Calculate start date (end_date - (num_recipes-1) days)
    start_date = end_date - timedelta(days=len(markdown_files)-1)
    
    # Create a list of dates
    publish_dates = [start_date + timedelta(days=i) for i in range(len(markdown_files))]
    
    print(f"Publishing schedule: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    successful_uploads = 0
    failed_uploads = 0
    
    # Ask if user wants to process all recipes or just one for testing
    if DEBUG:
        print("\nWould you like to:")
        print("1. Process all recipes")
        print("2. Process just one recipe for testing")
        choice = input("Enter your choice (1 or 2): ")
        
        if choice == "2":
            # Process just one recipe
            test_recipe = markdown_files[0]
            print(f"Processing test recipe: {test_recipe}")
            
            try:
                # Publish the post
                print(f"Publishing with date: {publish_dates[0].strftime('%Y-%m-%d')}")
                if create_post_from_markdown(test_recipe, publish_dates[0]):
                    successful_uploads += 1
                else:
                    failed_uploads += 1
            except Exception as e:
                print(f"Error processing {test_recipe}: {str(e)}")
                if DEBUG:
                    traceback.print_exc()
                failed_uploads += 1
                
            print(f"\nTest upload complete. Successfully uploaded: {successful_uploads}, Failed: {failed_uploads}")
            return
    
    # Process all recipes
    for i, markdown_file in enumerate(markdown_files):
        print(f"Processing {i+1}/{len(markdown_files)}: {markdown_file}")
        
        try:
            # Publish the post
            publish_date = publish_dates[i]
            if create_post_from_markdown(markdown_file, publish_date):
                successful_uploads += 1
            else:
                failed_uploads += 1
                
            # Slight delay to avoid API throttling
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing {markdown_file}: {str(e)}")
            if DEBUG:
                traceback.print_exc()
            failed_uploads += 1
    
    print(f"\nUploading complete. Successfully uploaded: {successful_uploads}, Failed: {failed_uploads}")

def main():
    """Main function to handle the recipe publishing process."""
    if not ADMIN_API_KEY:
        print("Error: GHOST_ADMIN_API_KEY environment variable is not set")
        return
    
    print(f"Starting the recipe publishing process...")
    print(f"- Reading markdown from: {MARKDOWN_DIR}")
    print(f"- Publishing to Ghost at: {ADMIN_API_URL}")
    
    publish_recipes_from_markdown()

if __name__ == "__main__":
    main() 