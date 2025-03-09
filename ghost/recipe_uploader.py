#!/usr/bin/env python3
import jwt
import time
import requests
import json
import os
import glob
from datetime import datetime

# Configuration
ADMIN_API_URL = 'https://healthyfied.ghost.io/ghost/api/admin/'
ADMIN_API_KEY = '67472f3b02b637000105c5b3:0d7cacc062c371d3bd12e0994d85d059d8ca358b20ab7ea1dec28aa9e32d9e92'  # Format: 'id:secret'
RECIPES_DIR = '../final'  # Path to the directory containing the recipe JSON files

# Split the Admin API key into ID and SECRET
id, secret = ADMIN_API_KEY.split(':')

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
    return token

def get_headers():
    """Get headers for Ghost API requests"""
    token = create_token()
    return {
        'Authorization': f'Ghost {token}',
        'Content-Type': 'application/json',
        'Accept-Version': 'v5.99'  # Specify the API version
    }

def format_recipe_html(recipe_data):
    """Format recipe data into HTML for Ghost post"""
    recipe = recipe_data
    
    # Format dietary information
    diet_info = []
    for diet in recipe.get('suitableForDiet', []):
        # Extract the diet type from the URL
        diet_type = diet.split('/')[-1]
        # Convert from camelCase to readable form
        diet_type = diet_type.replace('Diet', '').replace('Low', 'Low-').replace('Free', '-Free')
        # Insert space before each capital letter
        for i in range(len(diet_type)-1, 0, -1):
            if diet_type[i].isupper() and diet_type[i-1] != '-' and diet_type[i-1] != ' ':
                diet_type = diet_type[:i] + ' ' + diet_type[i:]
        diet_info.append(diet_type)
    
    # Format ingredients
    ingredients_html = ""
    for ingredient in recipe.get('recipeIngredient', []):
        ingredients_html += f"<li>{ingredient}</li>\n"
    
    # Format instructions
    instructions_html = ""
    for i, instruction in enumerate(recipe.get('recipeInstructions', []), 1):
        text = instruction.get('text', '')
        instructions_html += f"<li><strong>Step {i}:</strong> {text}</li>\n"
    
    # Main recipe image
    image_url = recipe.get('image', [''])[0] if isinstance(recipe.get('image', []), list) else recipe.get('image', '')
    
    # Nutrition information
    nutrition = recipe.get('nutrition', {})
    
    # Generate HTML for the post content
    html = f"""
    <div class="recipe-card">
        <div class="recipe-header">
            <h1>{recipe.get('name', '')}</h1>
            <img src="{image_url}" alt="{recipe.get('name', '')}">
            <p class="recipe-description">{recipe.get('description', '')}</p>
        </div>
        
        <div class="recipe-meta">
            <div class="meta-item">
                <strong>Prep Time:</strong> {recipe.get('prepTime', '').replace('PT', '')}
            </div>
            <div class="meta-item">
                <strong>Cook Time:</strong> {recipe.get('cookTime', '').replace('PT', '')}
            </div>
            <div class="meta-item">
                <strong>Total Time:</strong> {recipe.get('totalTime', '').replace('PT', '')}
            </div>
            <div class="meta-item">
                <strong>Servings:</strong> {recipe.get('recipeYield', '')}
            </div>
            <div class="meta-item">
                <strong>Cuisine:</strong> {recipe.get('recipeCuisine', '')}
            </div>
        </div>
        
        <div class="recipe-nutrition">
            <h2>Nutrition Information</h2>
            <ul>
                <li><strong>Calories:</strong> {nutrition.get('calories', '')}</li>
                <li><strong>Carbohydrates:</strong> {nutrition.get('carbohydrateContent', '')}g</li>
                <li><strong>Protein:</strong> {nutrition.get('proteinContent', '')}g</li>
                <li><strong>Fat:</strong> {nutrition.get('fatContent', '')}g</li>
                <li><strong>Fiber:</strong> {nutrition.get('fiberContent', '')}g</li>
                <li><strong>Sugar:</strong> {nutrition.get('sugarContent', '')}g</li>
                <li><strong>Sodium:</strong> {nutrition.get('sodiumContent', '')}mg</li>
            </ul>
        </div>
        
        <div class="recipe-ingredients">
            <h2>Ingredients</h2>
            <ul>
                {ingredients_html}
            </ul>
        </div>
        
        <div class="recipe-instructions">
            <h2>Instructions</h2>
            <ol>
                {instructions_html}
            </ol>
        </div>
        
        <div class="recipe-tags">
            <p><strong>Dietary Information:</strong> {', '.join(diet_info)}</p>
        </div>
    </div>
    
    <!-- Recipe Schema (hidden) -->
    <p id="recipe-schema" style="display: none;">{json.dumps(recipe)}</p>
    """
    
    return html

def create_post(recipe_data, status='draft'):
    """Create a new post in Ghost with recipe data"""
    url = f"{ADMIN_API_URL}posts/"
    headers = get_headers()
    
    # Extract recipe details
    recipe_name = recipe_data.get('name', '')
    recipe_html = format_recipe_html(recipe_data)
    
    # Generate slug from recipe name
    slug = recipe_name.lower().replace(' ', '-').replace('&', 'and')
    # Remove special characters from slug
    import re
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Format tags based on diet information
    tags = []
    for diet in recipe_data.get('suitableForDiet', []):
        diet_type = diet.split('/')[-1]
        tags.append({"name": diet_type})
    
    # Add cuisine as a tag
    cuisine = recipe_data.get('recipeCuisine', '')
    if cuisine:
        tags.append({"name": cuisine})
    
    # Add recipe category as a tag
    category = recipe_data.get('recipeCategory', '')
    if category:
        tags.append({"name": category})
    
    # Add keywords as tags
    keywords = recipe_data.get('keywords', '').split(',')
    for keyword in keywords:
        if keyword.strip():
            tags.append({"name": keyword.strip()})
    
    # Prepare post data
    post_data = {
        "posts": [{
            "title": recipe_name,
            "slug": slug,
            "status": status,
            "html": recipe_html,
            "tags": tags
        }]
    }
    
    # Make API request
    response = requests.post(url, headers=headers, json=post_data)
    
    if response.status_code in [200, 201]:
        post_id = response.json()['posts'][0]['id']
        print(f"✅ Created post: {recipe_name} (ID: {post_id})")
        return post_id
    else:
        print(f"❌ Error creating post '{recipe_name}': {response.status_code} - {response.text}")
        return None

def publish_all_recipes(recipes_dir=RECIPES_DIR, status='draft'):
    """Publish all recipes from the specified directory"""
    # Get all JSON files in the recipes directory
    recipe_files = glob.glob(os.path.join(recipes_dir, '*.json'))
    
    if not recipe_files:
        print(f"No recipe files found in {recipes_dir}")
        return
    
    print(f"Found {len(recipe_files)} recipe files in {recipes_dir}")
    
    # Process each recipe file
    successful = 0
    failed = 0
    
    for file_path in recipe_files:
        file_name = os.path.basename(file_path)
        print(f"\nProcessing recipe: {file_name}")
        
        try:
            # Load recipe data
            with open(file_path, 'r', encoding='utf-8') as f:
                recipe_data = json.load(f)
            
            # Create post in Ghost
            post_id = create_post(recipe_data, status)
            
            if post_id:
                successful += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"❌ Error processing recipe {file_name}: {str(e)}")
            failed += 1
    
    print(f"\nUpload complete. Successfully published: {successful}, Failed: {failed}")

def main():
    """Main function to run the script"""
    print("=== Ghost Recipe Uploader ===")
    
    # Choose upload mode
    print("\nChoose upload status:")
    print("1. Draft (default)")
    print("2. Published")
    choice = input("Enter your choice (1-2): ")
    
    status = 'published' if choice == '2' else 'draft'
    
    print(f"\nUploading recipes as {status}...")
    publish_all_recipes(status=status)
    
    print("\nProcess completed!")

if __name__ == "__main__":
    main() 