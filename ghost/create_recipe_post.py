#!/usr/bin/env python3
import jwt
import time
import requests
import json
import os
from datetime import datetime

# Configuration
ADMIN_API_URL = 'https://healthyfied.ghost.io/ghost/api/admin/'
ADMIN_API_KEY = '67472f3b02b637000105c5b3:0d7cacc062c371d3bd12e0994d85d059d8ca358b20ab7ea1dec28aa9e32d9e92'  # Format: 'id:secret'

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
    # Make sure token is a string
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token

def get_headers():
    """Get headers for Ghost API requests"""
    token = create_token()
    return {
        'Authorization': f'Ghost {token}',
        'Content-Type': 'application/json',
        'Accept-Version': 'v5.99'  # Specify the API version
    }

def create_or_fetch_tag(name, preferred_format=None):
    """Create a tag if it doesn't exist, or fetch it if it does"""
    slug = name.lower().replace(' ', '-').replace(',', '').replace(':', '')
    url = f"{ADMIN_API_URL}tags/slug/{slug}/"
    
    headers = get_headers()
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Tag exists
        tag = response.json().get('tags', [])[0]
        
        # If preferred_format is provided and different from current name, update the tag
        if preferred_format and tag.get('name') != preferred_format:
            print(f"Updating tag '{tag.get('name')}' to '{preferred_format}'")
            
            update_data = {
                "tags": [{
                    "id": tag.get('id'),
                    "name": preferred_format
                }]
            }
            
            update_url = f"{ADMIN_API_URL}tags/{tag.get('id')}/"
            update_response = requests.put(update_url, json=update_data, headers=headers)
            
            if update_response.status_code == 200:
                return update_response.json().get('tags', [])[0]
            else:
                print(f"Error updating tag: {update_response.status_code} - {update_response.text}")
                return tag  # Return original tag if update fails
        
        return tag
    elif response.status_code == 404:
        # Create new tag with preferred format or original name
        new_tag = {
            "tags": [{
                "name": preferred_format if preferred_format else name,
                "slug": slug
            }]
        }
        response = requests.post(f"{ADMIN_API_URL}tags/", json=new_tag, headers=headers)
        
        if response.status_code == 201:
            return response.json().get('tags', [])[0]
        else:
            print(f"Error creating tag: {response.status_code} - {response.text}")
            return None
    else:
        print(f"Error fetching tag: {response.status_code} - {response.text}")
        return None

def fetch_post_by_id(post_id):
    """Fetch a post by its ID"""
    url = f"{ADMIN_API_URL}posts/{post_id}/?formats=html,lexical,mobiledoc"
    
    headers = get_headers()
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        post = response.json().get('posts', [])[0]
        print(f"Successfully fetched post: {post['title']}")
        
        # Debug the post formats
        formats = []
        if 'html' in post and post['html']:
            formats.append('html')
        if 'lexical' in post and post['lexical']:
            formats.append('lexical')
        if 'mobiledoc' in post and post['mobiledoc']:
            formats.append('mobiledoc')
        print(f"Post formats available: {', '.join(formats)}")
        
        return post
    else:
        print(f"Error fetching post: {response.status_code} - {response.text}")
        return None

def create_recipe_post(recipe_path):
    """Create a recipe post directly from a recipe JSON file"""
    if not os.path.exists(recipe_path):
        print(f"Recipe file not found at {recipe_path}")
        return None
    
    try:
        # Read the recipe data
        with open(recipe_path, 'r', encoding='utf-8') as f:
            recipe_json = json.load(f)
        
        # Extract recipe information
        recipe_title = recipe_json.get('name', '')
        description = recipe_json.get('description', '')
        ingredients = recipe_json.get('recipeIngredient', [])
        instructions = recipe_json.get('recipeInstructions', [])
        prep_time = recipe_json.get('prepTime', '').replace('PT', '')
        cook_time = recipe_json.get('cookTime', '').replace('PT', '')
        total_time = recipe_json.get('totalTime', '').replace('PT', '')
        yield_value = recipe_json.get('recipeYield', '')
        category = recipe_json.get('recipeCategory', '')
        cuisine = recipe_json.get('recipeCuisine', '')
        
        # Nutrition information
        nutrition = recipe_json.get('nutrition', {})
        calories = nutrition.get('calories', '')
        carbs = nutrition.get('carbohydrateContent', '')
        protein = nutrition.get('proteinContent', '')
        fat = nutrition.get('fatContent', '')
        
        print(f"Processing recipe: {recipe_title}")
        print(f"Ingredients: {len(ingredients)} items")
        print(f"Instructions: {len(instructions)} steps")
        
        # Create the tags
        tags = []
        # Add "Recipes" as the first tag
        recipes_tag = create_or_fetch_tag("Recipes")
        if recipes_tag:
            tags.append({"id": recipes_tag.get('id')})
        
        # Add diet tags
        for diet in recipe_json.get('suitableForDiet', []):
            if diet.startswith("https://schema.org/"):
                diet_name = diet.replace("https://schema.org/", "").replace("Diet", "")
                preferred_format = None
                
                if "LowCalorie" in diet_name:
                    diet_name = "Low Calorie"
                    preferred_format = "Low-Calorie"
                elif "GlutenFree" in diet_name:
                    diet_name = "Gluten Free"
                    preferred_format = "Gluten-Free"
                else:
                    diet_name = ''.join([' '+c if c.isupper() else c for c in diet_name]).strip()
                
                diet_tag = create_or_fetch_tag(diet_name, preferred_format)
                if diet_tag:
                    tags.append({"id": diet_tag.get('id')})
        
        # Add category as a tag
        if category:
            category_tag = create_or_fetch_tag(category)
            if category_tag:
                tags.append({"id": category_tag.get('id')})
        
        # Add cuisine as a tag
        if cuisine:
            cuisine_tag = create_or_fetch_tag(cuisine)
            if cuisine_tag:
                tags.append({"id": cuisine_tag.get('id')})
        
        # Create JSON-LD script for header
        json_ld = f"""
<script type="application/ld+json">
{json.dumps(recipe_json, indent=2)}
</script>
"""
        
        # Create the post data
        post_data = {
            "posts": [{
                "title": recipe_title,
                "mobiledoc": json.dumps({
                    "version": "0.3.1",
                    "markups": [],
                    "atoms": [],
                    "cards": [
                        ["html", {
                            "html": f"""
<h2 id="ingredients">Ingredients</h2>
<ul>
{chr(10).join([f'<li>{ingredient}</li>' for ingredient in ingredients])}
</ul>

<h2 id="instructions">Instructions</h2>
<ol>
{chr(10).join([f'<li>{instruction.get("text", "")}</li>' for instruction in instructions])}
</ol>

<h2 id="details">Details</h2>
<ul>
<li><strong>Prep Time:</strong> {prep_time}</li>
<li><strong>Cook Time:</strong> {cook_time}</li>
<li><strong>Total Time:</strong> {total_time}</li>
<li><strong>Servings:</strong> {yield_value}</li>
<li><strong>Category:</strong> {category}</li>
<li><strong>Cuisine:</strong> {cuisine}</li>
</ul>

<h2 id="nutrition-information">Nutrition Information</h2>
<ul>
<li><strong>Calories:</strong> {calories}</li>
<li><strong>Carbohydrates:</strong> {carbs}</li>
<li><strong>Protein:</strong> {protein}</li>
<li><strong>Fat:</strong> {fat}</li>
</ul>
<hr>
"""
                        }]
                    ],
                    "sections": [
                        [10, 0]
                    ]
                }),
                "status": "draft",
                "codeinjection_head": json_ld,
                "tags": tags,
                "feature_image": recipe_json.get('image', [''])[0] if isinstance(recipe_json.get('image', []), list) else recipe_json.get('image', '')
            }]
        }
        
        # Send the request to create the post
        print("\nCreating post directly from recipe data...")
        headers = get_headers()
        response = requests.post(f"{ADMIN_API_URL}posts/", json=post_data, headers=headers)
        
        if response.status_code == 201:
            created_post = response.json().get('posts', [])[0]
            print(f"Successfully created post: {created_post['title']}")
            print(f"Post ID: {created_post['id']}")
            
            # Fetch the post to verify the content
            post_id = created_post['id']
            fetched_post = fetch_post_by_id(post_id)
            
            return fetched_post
        else:
            print(f"Error creating post: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        print(f"Error processing recipe: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    recipe_path = '../final/recipe_0002.json'
    post = create_recipe_post(recipe_path)
    
    if post:
        print("\nPost created successfully!")
        
        # Get the original recipe data for comparison
        try:
            with open(recipe_path, 'r', encoding='utf-8') as f:
                recipe_json = json.load(f)
                
            original_ingredients = recipe_json.get('recipeIngredient', [])
            original_instructions = [instruction.get('text', '') for instruction in recipe_json.get('recipeInstructions', [])]
            
            # Verify the content
            if 'html' in post and post['html']:
                html_content = post['html']
                print("\nHTML content snippet:")
                print(html_content[:500] + "...")
                
                # Parse HTML to extract ingredients and instructions
                import re
                
                # Extract ingredients
                ingredients_match = re.search(r'<h2 id="ingredients">Ingredients</h2>\s*<ul>(.*?)</ul>', html_content, re.DOTALL)
                if ingredients_match:
                    ingredients_html = ingredients_match.group(1)
                    ingredients_found = re.findall(r'<li>(.*?)</li>', ingredients_html)
                    
                    print(f"\nFound {len(ingredients_found)} ingredients in the post:")
                    for i, ingredient in enumerate(ingredients_found[:5], 1):
                        print(f"  {i}. {ingredient}")
                    if len(ingredients_found) > 5:
                        print(f"  ...and {len(ingredients_found) - 5} more")
                    
                    # Check if all original ingredients are included
                    missing_ingredients = [ing for ing in original_ingredients if ing not in ingredients_found]
                    if missing_ingredients:
                        print(f"\nWarning: {len(missing_ingredients)} ingredients are missing or different in the post:")
                        for ing in missing_ingredients[:3]:
                            print(f"  - {ing}")
                        if len(missing_ingredients) > 3:
                            print(f"  ...and {len(missing_ingredients) - 3} more")
                    else:
                        print("\nAll ingredients were successfully included in the post!")
                else:
                    print("\nCouldn't find ingredients section in the HTML content.")
                
                # Extract instructions
                instructions_match = re.search(r'<h2 id="instructions">Instructions</h2>\s*<ol>(.*?)</ol>', html_content, re.DOTALL)
                if instructions_match:
                    instructions_html = instructions_match.group(1)
                    instructions_found = re.findall(r'<li>(.*?)</li>', instructions_html)
                    
                    print(f"\nFound {len(instructions_found)} instructions in the post:")
                    for i, instruction in enumerate(instructions_found[:3], 1):
                        print(f"  {i}. {instruction[:100]}..." if len(instruction) > 100 else f"  {i}. {instruction}")
                    if len(instructions_found) > 3:
                        print(f"  ...and {len(instructions_found) - 3} more")
                    
                    # Check if all original instructions are included
                    all_included = True
                    for i, orig_instr in enumerate(original_instructions):
                        if i < len(instructions_found):
                            if orig_instr not in instructions_found[i]:
                                print(f"\nWarning: Instruction {i+1} might be different:")
                                print(f"  Original: {orig_instr[:100]}...")
                                print(f"  In post: {instructions_found[i][:100]}...")
                                all_included = False
                        else:
                            print(f"\nWarning: Missing instruction {i+1}: {orig_instr[:100]}...")
                            all_included = False
                    
                    if all_included:
                        print("\nAll instructions were successfully included in the post!")
                else:
                    print("\nCouldn't find instructions section in the HTML content.")
            else:
                print("\nNo HTML content available.")
        except Exception as e:
            print(f"Error during verification: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 