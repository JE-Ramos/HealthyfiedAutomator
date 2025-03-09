#!/usr/bin/env python3
import jwt
import time
import requests
import json
import os
import glob
from datetime import datetime, timedelta

# Configuration
ADMIN_API_URL = "https://healthyfied.ghost.io/ghost/api/admin/"
ADMIN_API_KEY = "67cd6027edc031000157487b:eb9304d2cb866ad6902f88efb11ad43012f40f05015281ecce75cff229093cce"
RECIPES_DIR = "../final"

def create_token():
    """Create a JWT token for authentication with Ghost Admin API."""
    # Split the key into ID and SECRET
    key_parts = ADMIN_API_KEY.split(':')
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

def get_headers():
    """Get headers for API requests."""
    token = create_token()
    return {
        'Authorization': f'Ghost {token}',
        'Content-Type': 'application/json'
    }

def create_recipe_html_template(recipe_data):
    """Create HTML content for a recipe post using the Healthyfied template design."""
    recipe_name = recipe_data.get('name', 'Untitled Recipe')
    description = recipe_data.get('description', '')
    
    # Extract key recipe details
    prep_time = recipe_data.get('prepTime', '').replace('PT', '')
    cook_time = recipe_data.get('cookTime', '').replace('PT', '')
    total_time = recipe_data.get('totalTime', '').replace('PT', '')
    
    yield_value = recipe_data.get('recipeYield', '')
    category = recipe_data.get('recipeCategory', '')
    cuisine = recipe_data.get('recipeCuisine', '')
    
    # Extract tags
    tags = []
    diets = recipe_data.get('suitableForDiet', [])
    for diet in diets:
        if diet.startswith("https://schema.org/"):
            diet_name = diet.replace("https://schema.org/", "").replace("Diet", "")
            # Add spaces before capital letters
            diet_name = ''.join([' '+c if c.isupper() else c for c in diet_name]).strip()
            tags.append(diet_name)
    
    # Add the recipe category as a tag if present
    if category:
        tags.append(category)
    
    # Add the cuisine as a tag if present
    if cuisine:
        tags.append(cuisine)
    
    # Extract nutrition information
    nutrition = recipe_data.get('nutrition', {})
    calories = nutrition.get('calories', 'N/A').replace('calories', '').strip()
    carbs = nutrition.get('carbohydrateContent', '0g')
    protein = nutrition.get('proteinContent', '0g')
    fat = nutrition.get('fatContent', '0g')
    sugar = nutrition.get('sugarContent', '0g')
    sodium = nutrition.get('sodiumContent', '0mg')
    
    # Calculate percentages (approximate) for the macros
    try:
        # Extract numeric values from carbs, protein, and fat
        carbs_g = float(''.join(filter(str.isdigit, carbs.replace('.', ''))))
        protein_g = float(''.join(filter(str.isdigit, protein.replace('.', ''))))
        fat_g = float(''.join(filter(str.isdigit, fat.replace('.', ''))))
        
        # Calculate total and percentages
        total_g = carbs_g + protein_g + fat_g
        if total_g > 0:
            carbs_pct = int((carbs_g / total_g) * 100)
            protein_pct = int((protein_g / total_g) * 100)
            fat_pct = int((fat_g / total_g) * 100)
        else:
            carbs_pct = 0
            protein_pct = 0
            fat_pct = 0
    except:
        # Default values if calculation fails
        carbs_pct = 33
        protein_pct = 33
        fat_pct = 34
    
    # Get ingredients and instructions
    ingredients = recipe_data.get('recipeIngredient', [])
    instructions = recipe_data.get('recipeInstructions', [])
    
    # Build tags HTML
    tags_html = ""
    for tag in tags:
        tags_html += f'<span class="tag">{tag}</span>\n        '
    
    # Build ingredients HTML
    ingredients_html = ""
    for ingredient in ingredients:
        ingredients_html += f'<li>{ingredient}</li>\n                '
    
    # Build instructions HTML
    instructions_html = ""
    for i, instruction in enumerate(instructions):
        step_text = instruction.get('text', '')
        instructions_html += f'<li>{step_text}</li>\n                '
    
    # Build HTML content
    html_content = f"""
<!--kg-card-begin: html-->
<div class="recipe-container">
    <!-- Description -->
    <div class="recipe-description">
        <p>{description}</p>
    </div>

    <!-- Tags -->
    <div class="tags">
        {tags_html}
    </div>

    <!-- Nutrition Heading and Serving Count Caption -->
    <h2 class="nutrition-heading">Nutrition Per Serving</h2>
    <div class="serving-caption">Serves {yield_value}</div>

    <!-- Nutrition Section -->
    <div class="nutrition-section">
        <div class="calories-circle">
            <div class="calories-text">
                <span class="cal-number">{calories}</span>
                <span class="cal-unit">cal</span>
            </div>
        </div>

        <div class="nutrient">
            <div class="percentage percentage-carbs">{carbs_pct}%</div>
            <div class="gram-value">{carbs}</div>
            <div class="macro-name">Carbs</div>
        </div>

        <div class="nutrient">
            <div class="percentage percentage-fat">{fat_pct}%</div>
            <div class="gram-value">{fat}</div>
            <div class="macro-name">Fat</div>
        </div>

        <div class="nutrient">
            <div class="percentage percentage-protein">{protein_pct}%</div>
            <div class="gram-value">{protein}</div>
            <div class="macro-name">Protein</div>
        </div>
    </div>

    <!-- Pills for Sugar and Sodium -->
    <div class="pill-container">
        <div class="pill">
            <span>{sugar}</span><span class="pill-label">Sugar</span>
        </div>
        <div class="pill">
            <span>{sodium}</span><span class="pill-label">Sodium</span>
        </div>
    </div>
    
    <!-- Prep and Cook Time -->
    <div class="time-container">
        <div class="time-item">
            <span class="time-label">Prep Time:</span>
            <span class="time-value">{prep_time}</span>
        </div>
        <div class="time-item">
            <span class="time-label">Cook Time:</span>
            <span class="time-value">{cook_time}</span>
        </div>
        <div class="time-item">
            <span class="time-label">Total Time:</span>
            <span class="time-value">{total_time}</span>
        </div>
    </div>

    <!-- Print Section for Ingredients and Steps -->
    <div id="print-section">
        <!-- Ingredients Section -->
        <div class="ingredients-section">
            <h2 class="ingredients-title">Ingredients</h2>
            <ul class="ingredients-list">
                {ingredients_html}
            </ul>
        </div>

        <!-- Insert Ad Block after Ingredients -->
        <div class="ad-container">
            <p class="ad-label">Advertisement</p>
            <div class="ad-content">
                <p>Support Healthyfied by checking out our sponsors</p>
            </div>
        </div>

        <!-- Steps Section -->
        <div class="steps-section">
            <h2 class="steps-title">Instructions</h2>
            <ol class="steps-list">
                {instructions_html}
            </ol>
        </div>
    </div>
</div>
<!--kg-card-end: html-->
"""
    
    return html_content

def create_recipe_summary(recipe_data):
    """Create a detailed text summary of the recipe for the lexical editor."""
    recipe_name = recipe_data.get('name', 'Untitled Recipe')
    description = recipe_data.get('description', 'No description available.')
    
    # Extract key recipe details
    prep_time = recipe_data.get('prepTime', '').replace('PT', '')
    cook_time = recipe_data.get('cookTime', '').replace('PT', '')
    total_time = recipe_data.get('totalTime', '').replace('PT', '')
    yield_value = recipe_data.get('recipeYield', '')
    
    # Get ingredients and instructions
    ingredients = recipe_data.get('recipeIngredient', [])
    instructions = recipe_data.get('recipeInstructions', [])
    
    # Extract nutrition information
    nutrition = recipe_data.get('nutrition', {})
    
    # Separate the content by sections - remove description from details since it's already the intro paragraph
    details_text = f"""
• Prep Time: {prep_time}
• Cook Time: {cook_time}
• Total Time: {total_time}
• Servings: {yield_value}
"""
    
    # Extract all nutrition information
    nutrition_text = ""
    if nutrition:
        for key, value in nutrition.items():
            if key != "@type":  # Skip the @type field
                # Format the key by adding spaces before capital letters and capitalizing first letter
                formatted_key = ''.join([' '+c if c.isupper() else c for c in key]).strip()
                formatted_key = formatted_key.replace('Content', '').capitalize()
                nutrition_text += f"• {formatted_key}: {value}\n"
    else:
        nutrition_text = "• No nutritional information available"
    
    # Create ingredients list text
    ingredients_text = ""
    for ingredient in ingredients:
        ingredients_text += f"• {ingredient}\n"
    
    # Create instructions text
    instructions_text = ""
    for i, instruction in enumerate(instructions):
        step_text = instruction.get('text', '')
        instructions_text += f"{i+1}. {step_text}\n"
    
    return {
        "details": details_text.strip(),
        "nutrition": nutrition_text.strip(),
        "ingredients": ingredients_text.strip(),
        "instructions": instructions_text.strip()
    }

def create_simple_lexical(content, recipe_data):
    """
    Create a structured lexical format for the content.
    This will include properly formatted headings for Recipe Details, Ingredients, and Instructions.
    """
    # Get a detailed summary of the recipe
    recipe_sections = create_recipe_summary(recipe_data)
    
    # Get the description
    description = recipe_data.get('description', 'No description available')
    
    # Create a structure with multiple paragraphs and proper headings
    return json.dumps({
        "root": {
            "children": [
                {
                    "children": [
                        {
                            "detail": 0,
                            "format": 0,
                            "mode": "normal",
                            "style": "",
                            "text": description,
                            "type": "text",
                            "version": 1
                        }
                    ],
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "paragraph",
                    "version": 1
                },
                # Recipe Details heading
                {
                    "children": [
                        {
                            "detail": 0,
                            "format": 1,
                            "mode": "normal",
                            "style": "",
                            "text": "Recipe Details",
                            "type": "text",
                            "version": 1
                        }
                    ],
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "heading",
                    "tag": "h2",
                    "version": 1
                },
                # Recipe Details content
                {
                    "children": [
                        {
                            "detail": 0,
                            "format": 0,
                            "mode": "normal",
                            "style": "",
                            "text": recipe_sections["details"],
                            "type": "text",
                            "version": 1
                        }
                    ],
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "paragraph",
                    "version": 1
                },
                # Nutrition Information heading
                {
                    "children": [
                        {
                            "detail": 0,
                            "format": 1,
                            "mode": "normal",
                            "style": "",
                            "text": "Nutrition Information",
                            "type": "text",
                            "version": 1
                        }
                    ],
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "heading",
                    "tag": "h2",
                    "version": 1
                },
                # Nutrition Information content
                {
                    "children": [
                        {
                            "detail": 0,
                            "format": 0,
                            "mode": "normal",
                            "style": "",
                            "text": recipe_sections["nutrition"],
                            "type": "text",
                            "version": 1
                        }
                    ],
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "paragraph",
                    "version": 1
                },
                # Ingredients heading
                {
                    "children": [
                        {
                            "detail": 0,
                            "format": 1,
                            "mode": "normal",
                            "style": "",
                            "text": "Ingredients",
                            "type": "text",
                            "version": 1
                        }
                    ],
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "heading",
                    "tag": "h2",
                    "version": 1
                },
                # Ingredients content
                {
                    "children": [
                        {
                            "detail": 0,
                            "format": 0,
                            "mode": "normal",
                            "style": "",
                            "text": recipe_sections["ingredients"],
                            "type": "text",
                            "version": 1
                        }
                    ],
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "paragraph",
                    "version": 1
                },
                # Instructions heading
                {
                    "children": [
                        {
                            "detail": 0,
                            "format": 1,
                            "mode": "normal",
                            "style": "",
                            "text": "Instructions",
                            "type": "text",
                            "version": 1
                        }
                    ],
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "heading",
                    "tag": "h2",
                    "version": 1
                },
                # Instructions content
                {
                    "children": [
                        {
                            "detail": 0,
                            "format": 0,
                            "mode": "normal",
                            "style": "",
                            "text": recipe_sections["instructions"],
                            "type": "text",
                            "version": 1
                        }
                    ],
                    "direction": "ltr",
                    "format": "",
                    "indent": 0,
                    "type": "paragraph",
                    "version": 1
                }
            ],
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "type": "root",
            "version": 1
        }
    })

def fetch_post_template():
    """Fetch an existing post from the Ghost blog to use as a template."""
    try:
        # Configure API endpoint
        url = f"{ADMIN_API_URL}posts/?formats=html"
        
        # Make the request
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            posts = data.get('posts', [])
            
            if posts:
                # Get the first post
                template_post = posts[0]
                print(f"Successfully fetched template post: {template_post['title']}")
                return template_post
            else:
                print("No posts found. Using default template.")
                return None
        else:
            print(f"Failed to fetch posts: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"ERROR fetching post template: {str(e)}")
        return None

def extract_html_template(template_post, recipe_data):
    """Extract the HTML template from an existing post and replace content with new recipe data."""
    if not template_post:
        # If no template post was fetched, use our default template
        return create_recipe_html_template(recipe_data)
    
    try:
        # Get the HTML content from the template post
        template_html = template_post.get('html', '')
        
        if not template_html:
            print("Template post has no HTML content. Using default template.")
            return create_recipe_html_template(recipe_data)
        
        # Print the template for debugging
        print("\nTemplate HTML structure found:")
        print(template_html[:200] + "..." if len(template_html) > 200 else template_html)
            
        # Extract recipe details
        recipe_name = recipe_data.get('name', 'Untitled Recipe')
        description = recipe_data.get('description', '')
        
        # Extract key recipe details
        prep_time = recipe_data.get('prepTime', '').replace('PT', '')
        cook_time = recipe_data.get('cookTime', '').replace('PT', '')
        total_time = recipe_data.get('totalTime', '').replace('PT', '')
        yield_value = recipe_data.get('recipeYield', '')
        category = recipe_data.get('recipeCategory', '')
        cuisine = recipe_data.get('recipeCuisine', '')
        
        # Extract diet information for tags
        tags = []
        diets = recipe_data.get('suitableForDiet', [])
        for diet in diets:
            if diet.startswith("https://schema.org/"):
                diet_name = diet.replace("https://schema.org/", "").replace("Diet", "")
                # Add spaces before capital letters
                diet_name = ''.join([' '+c if c.isupper() else c for c in diet_name]).strip()
                tags.append(diet_name)
        
        # Extract nutrition information
        nutrition = recipe_data.get('nutrition', {})
        calories = nutrition.get('calories', 'N/A')
        carbs = nutrition.get('carbohydrateContent', 'N/A')
        protein = nutrition.get('proteinContent', 'N/A')
        fat = nutrition.get('fatContent', 'N/A')
        
        # Get ingredients and instructions
        ingredients = recipe_data.get('recipeIngredient', [])
        instructions = recipe_data.get('recipeInstructions', [])
        
        # Build ingredients HTML
        ingredients_html = ""
        for ingredient in ingredients:
            ingredients_html += f'<li>{ingredient}</li>\n'
        
        # Build instructions HTML
        instructions_html = ""
        for instruction in instructions:
            step_text = instruction.get('text', '')
            instructions_html += f'<li>{step_text}</li>\n'
        
        # Find and replace content in the template
        # Note: This is a simplified approach and may need to be adjusted based on actual template structure
        # We'll try to identify key sections in the template and replace them
        
        # Placeholder replacement patterns (these need to be adjusted based on the actual template)
        replacements = {
            # Using regex patterns to match common HTML structures
            r'<h1[^>]*>.*?</h1>': f'<h1>{recipe_name}</h1>',
            r'<p class="recipe-description"[^>]*>.*?</p>': f'<p class="recipe-description">{description}</p>',
            r'<ul class="ingredients-list"[^>]*>.*?</ul>': f'<ul class="ingredients-list">\n{ingredients_html}</ul>',
            r'<ol class="steps-list"[^>]*>.*?</ol>': f'<ol class="steps-list">\n{instructions_html}</ol>',
        }
        
        # Apply replacements
        modified_html = template_html
        import re
        for pattern, replacement in replacements.items():
            modified_html = re.sub(pattern, replacement, modified_html, flags=re.DOTALL)
        
        # Add nutrition and details if they exist in the template
        # This is simplified and may need adjustments
        if "nutrition" in modified_html.lower():
            modified_html = re.sub(r'calories:.*?<', f'calories: {calories}<', modified_html, flags=re.DOTALL | re.IGNORECASE)
            modified_html = re.sub(r'carbohydrates:.*?<', f'carbohydrates: {carbs}<', modified_html, flags=re.DOTALL | re.IGNORECASE)
            modified_html = re.sub(r'protein:.*?<', f'protein: {protein}<', modified_html, flags=re.DOTALL | re.IGNORECASE)
            modified_html = re.sub(r'fat:.*?<', f'fat: {fat}<', modified_html, flags=re.DOTALL | re.IGNORECASE)
        
        if "prep time" in modified_html.lower():
            modified_html = re.sub(r'prep time:.*?<', f'prep time: {prep_time}<', modified_html, flags=re.DOTALL | re.IGNORECASE)
            modified_html = re.sub(r'cook time:.*?<', f'cook time: {cook_time}<', modified_html, flags=re.DOTALL | re.IGNORECASE)
            modified_html = re.sub(r'total time:.*?<', f'total time: {total_time}<', modified_html, flags=re.DOTALL | re.IGNORECASE)
            modified_html = re.sub(r'servings:.*?<', f'servings: {yield_value}<', modified_html, flags=re.DOTALL | re.IGNORECASE)
        
        # If tags are present in the template, try to replace them
        if "tag" in modified_html.lower() and tags:
            # Create tag HTML (simplified - adjust based on actual template)
            tags_html = ""
            for tag in tags:
                tags_html += f'<span class="tag">{tag}</span>\n'
            
            # Try to replace tags section
            modified_html = re.sub(r'<div class="tags"[^>]*>.*?</div>', f'<div class="tags">\n{tags_html}</div>', 
                                  modified_html, flags=re.DOTALL)
        
        return modified_html
    
    except Exception as e:
        print(f"ERROR adapting template: {str(e)}")
        # Fallback to our default template
        return create_recipe_html_template(recipe_data)

def create_post(recipe_data, publish_date):
    """Create a post in Ghost using a recipe JSON."""
    try:
        # Extract basic information
        title = recipe_data.get('name', 'Untitled Recipe')
        slug = f"recipe/{title.lower().replace(' ', '-').replace(',', '').replace('.', '')}"
        
        # Get the image URL
        image_url = recipe_data.get('image', '')
        if isinstance(image_url, list) and len(image_url) > 0:
            image_url = image_url[0]
        
        # Extract diet information for tags
        tags = []
        diets = recipe_data.get('suitableForDiet', [])
        for diet in diets:
            if diet.startswith("https://schema.org/"):
                diet_name = diet.replace("https://schema.org/", "").replace("Diet", "")
                # Add spaces before capital letters
                diet_name = ''.join([' '+c if c.isupper() else c for c in diet_name]).strip()
                tags.append({"name": diet_name})
        
        # Fetch a template post from the Ghost blog
        template_post = fetch_post_template()
        
        # Create HTML content using the template from an existing post
        html_content = extract_html_template(template_post, recipe_data)
        
        # Create JSON-LD for structured data
        json_ld = f"""
<script type="application/ld+json">
{json.dumps(recipe_data, indent=2)}
</script>
"""
        
        # Format the date
        formatted_date = publish_date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        # Create a lexical format that includes basic info
        lexical_content = create_simple_lexical(html_content, recipe_data)
        
        # Get the description for the excerpt
        description = recipe_data.get('description', '')
        
        # Create the post data
        post_data = {
            "posts": [{
                "title": title,
                "slug": slug,
                "html": html_content,
                "lexical": lexical_content,
                "status": "published",
                "published_at": formatted_date,
                "tags": tags,
                "codeinjection_head": json_ld,
                "feature_image": image_url,
                "custom_excerpt": description[:300]  # Use custom_excerpt for excerpt
            }]
        }
        
        print(f"\nPOST DATA for {title}:")
        print(f"- Slug: {slug}")
        print(f"- Tags: {tags}")
        print(f"- Publish date: {formatted_date}")
        print(f"- Feature image: {image_url}")
        print(f"- Excerpt: {description[:50]}..." if len(description) > 50 else description)
        
        # Send request to Ghost API
        url = f"{ADMIN_API_URL}posts/"
        print(f"Sending request to {url}")
            
        response = requests.post(url, json=post_data, headers=get_headers())
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 300:
            print(f"Successfully published recipe: {title} with publish date {formatted_date}")
            return True
        else:
            print(f"Failed to publish recipe: {title} - Status: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"ERROR creating post: {str(e)}")
        return False

def publish_recipes():
    """Publish recipes to Ghost."""
    # Get all recipe JSON files
    recipe_files = sorted(glob.glob(os.path.join(RECIPES_DIR, "recipe_*.json")))
    
    if not recipe_files:
        print(f"No recipe files found in {RECIPES_DIR}")
        return
    
    print(f"Found {len(recipe_files)} recipe files")
    
    # Calculate the publish dates (1 day apart, working backwards from Mar 9, 2025)
    end_date = datetime.strptime("2025-03-09", "%Y-%m-%d")
    
    # Calculate start date (end_date - (num_recipes-1) days)
    start_date = end_date - timedelta(days=len(recipe_files)-1)
    
    # Create a list of dates
    publish_dates = [start_date + timedelta(days=i) for i in range(len(recipe_files))]
    
    print(f"Publishing schedule: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Ask if user wants to process all recipes or just one for testing
    print("\nWould you like to:")
    print("1. Process all recipes")
    print("2. Process just one recipe for testing")
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == "2":
        # Process just one recipe
        test_recipe = recipe_files[0]
        print(f"Processing test recipe: {test_recipe}")
        
        try:
            # Load the recipe data
            with open(test_recipe, 'r') as f:
                recipe_data = json.load(f)
            
            # Publish the post
            publish_date = publish_dates[0]
            print(f"Publishing with date: {publish_date.strftime('%Y-%m-%d')}")
            success = create_post(recipe_data, publish_date)
            
            if success:
                print("\nTest upload successful!")
            else:
                print("\nTest upload failed.")
        except Exception as e:
            print(f"Error processing {test_recipe}: {str(e)}")
        
        return
    
    # Process all recipes
    successful_uploads = 0
    failed_uploads = 0
    
    for i, recipe_file in enumerate(recipe_files):
        print(f"Processing {i+1}/{len(recipe_files)}: {recipe_file}")
        
        try:
            # Load the recipe data
            with open(recipe_file, 'r') as f:
                recipe_data = json.load(f)
            
            # Publish the post
            publish_date = publish_dates[i]
            if create_post(recipe_data, publish_date):
                successful_uploads += 1
            else:
                failed_uploads += 1
                
            # Slight delay to avoid API throttling
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing {recipe_file}: {str(e)}")
            failed_uploads += 1
    
    print(f"\nUploading complete. Successfully uploaded: {successful_uploads}, Failed: {failed_uploads}")

if __name__ == "__main__":
    print("Starting the direct recipe publishing process...")
    print(f"- Reading recipes from: {RECIPES_DIR}")
    print(f"- Publishing to Ghost at: {ADMIN_API_URL}")
    
    publish_recipes() 