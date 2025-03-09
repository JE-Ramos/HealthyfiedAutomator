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

def fetch_draft_post():
    """Fetch a draft post from Ghost"""
    url = f"{ADMIN_API_URL}posts/?formats=html,lexical&filter=status:draft"
    
    headers = get_headers()
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        posts = response.json().get('posts', [])
        if posts:
            print(f"Successfully fetched draft post: {posts[0]['title']}")
            return posts[0]
        else:
            print("No draft posts found.")
            return None
    else:
        print(f"Error fetching draft posts: {response.status_code} - {response.text}")
        return None

def save_as_template(post):
    """Save post content as a template"""
    if not post:
        print("No post to save as template.")
        return None

    # Extract the post content and structure
    template = {
        'title': post.get('title', 'Template Post'),
        'html': post.get('html', ''),
        'lexical': post.get('lexical', {}),
        'codeinjection_head': post.get('codeinjection_head', ''),
        'codeinjection_foot': post.get('codeinjection_foot', ''),
        'tags': post.get('tags', []),
        'feature_image': post.get('feature_image', '')
    }
    
    # Save template to file
    template_file = 'post_template.json'
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)
    
    print(f"Template saved to {template_file}")
    return template

def create_post_from_template(template, title=None, tags=None, recipe_data=None):
    """Create a new post from the template"""
    if not template:
        print("No template to create post from.")
        return None

    # Create a new post based on the template
    new_post = {
        "posts": [{
            "title": title if title else template['title'],
            "status": "draft",
            "tags": tags if tags is not None else template['tags'],
            "feature_image": template['feature_image']
        }]
    }
    
    # If recipe data is provided, update the content with recipe data
    if recipe_data:
        # Update the HTML content
        if 'html_content' in recipe_data:
            print("\nDebug - Adding HTML content to new post")
            new_post["posts"][0]["html"] = recipe_data['html_content']
            # Since we're manually updating the HTML, we should not include lexical content 
            # to prevent it from overriding our HTML changes
            new_post["posts"][0]["lexical"] = None
        else:
            new_post["posts"][0]["html"] = template['html']
            new_post["posts"][0]["lexical"] = template['lexical']
            
        # Update the code injection head (for JSON-LD)
        if 'codeinjection_head' in recipe_data:
            new_post["posts"][0]["codeinjection_head"] = recipe_data['codeinjection_head']
        else:
            new_post["posts"][0]["codeinjection_head"] = template.get('codeinjection_head', '')
            
        # Preserve footer injection if present
        if 'codeinjection_foot' in template:
            new_post["posts"][0]["codeinjection_foot"] = template.get('codeinjection_foot', '')
    else:
        # Use template content if no recipe data provided
        new_post["posts"][0]["html"] = template['html']
        new_post["posts"][0]["lexical"] = template['lexical']
        new_post["posts"][0]["codeinjection_head"] = template.get('codeinjection_head', '')
        new_post["posts"][0]["codeinjection_foot"] = template.get('codeinjection_foot', '')
    
    # Print the final post payload for debugging
    print("\nDebug - Final post data:")
    print(f"Title: {new_post['posts'][0]['title']}")
    print(f"HTML Content: {new_post['posts'][0]['html'][:200]}...")
    print(f"Lexical Content present: {'Yes' if new_post['posts'][0].get('lexical') else 'No'}")
    print(f"JSON-LD present: {'Yes' if 'codeinjection_head' in new_post['posts'][0] and new_post['posts'][0]['codeinjection_head'] else 'No'}")
    
    # Send request to Ghost API
    url = f"{ADMIN_API_URL}posts/"
    
    headers = get_headers()
    response = requests.post(url, json=new_post, headers=headers)
    
    if response.status_code == 201:
        created_post = response.json().get('posts', [])[0]
        print(f"Successfully created new post: {created_post['title']}")
        return created_post
    else:
        print(f"Error creating post: {response.status_code} - {response.text}")
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

def process_recipe_json(recipe_file_path, template):
    """Process a recipe JSON file and map its data to the template structure"""
    try:
        with open(recipe_file_path, 'r', encoding='utf-8') as f:
            recipe_data = json.load(f)
        
        # Extract recipe information
        title = recipe_data.get('name', '')
        description = recipe_data.get('description', '')
        
        # Process tags
        tags = []
        
        # Add "Recipes" as the first tag
        recipes_tag = create_or_fetch_tag("Recipes")
        if recipes_tag:
            tags.append({"id": recipes_tag.get('id')})
        
        # Add diet tags
        for diet in recipe_data.get('suitableForDiet', []):
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
        category = recipe_data.get('recipeCategory')
        if category:
            category_tag = create_or_fetch_tag(category)
            if category_tag:
                tags.append({"id": category_tag.get('id')})
        
        # Add cuisine as a tag
        cuisine = recipe_data.get('recipeCuisine')
        if cuisine:
            cuisine_tag = create_or_fetch_tag(cuisine)
            if cuisine_tag:
                tags.append({"id": cuisine_tag.get('id')})
        
        # Create JSON-LD script for header
        json_ld = f"""
<script type="application/ld+json">
{json.dumps(recipe_data, indent=2)}
</script>
"""
        
        # Extract recipe details for mapping
        ingredients = recipe_data.get('recipeIngredient', [])
        instructions = recipe_data.get('recipeInstructions', [])
        prep_time = recipe_data.get('prepTime', '').replace('PT', '')
        cook_time = recipe_data.get('cookTime', '').replace('PT', '')
        total_time = recipe_data.get('totalTime', '').replace('PT', '')
        yield_value = recipe_data.get('recipeYield', '')
        category = recipe_data.get('recipeCategory', '')
        cuisine = recipe_data.get('recipeCuisine', '')
        
        # Nutrition information
        nutrition = recipe_data.get('nutrition', {})
        calories = nutrition.get('calories', '')
        carbs = nutrition.get('carbohydrateContent', '')
        protein = nutrition.get('proteinContent', '')
        fat = nutrition.get('fatContent', '')
        
        print(f"\nRecipe ingredients from JSON: {len(ingredients)} items")
        print(f"Sample ingredients: {ingredients[:3]}")
        
        print(f"Recipe instructions from JSON: {len(instructions)} items")
        print(f"Sample instruction: {instructions[0].get('text', '')}")
        
        # Create a completely new lexical structure from scratch
        lexical_dict = {
            "root": {
                "children": [
                    # Ingredients section as markdown
                    {
                        "type": "markdown",
                        "version": 1,
                        "markdown": f"""
## Ingredients

{chr(10).join([f'- {ingredient}' for ingredient in ingredients])}
"""
                    },
                    
                    # Instructions section
                    {
                        "children": [
                            {
                                "detail": 0,
                                "format": 0,
                                "mode": "normal",
                                "style": "",
                                "text": "Instructions",
                                "type": "extended-text",
                                "version": 1
                            }
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "extended-heading",
                        "version": 1,
                        "tag": "h2"
                    },
                    {
                        "children": [],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "list",
                        "version": 1,
                        "listType": "number",
                        "start": 1,
                        "tag": "ol"
                    },
                    
                    # Details section
                    {
                        "children": [
                            {
                                "detail": 0,
                                "format": 0,
                                "mode": "normal",
                                "style": "",
                                "text": "Details",
                                "type": "extended-text",
                                "version": 1
                            }
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "extended-heading",
                        "version": 1,
                        "tag": "h2"
                    },
                    {
                        "children": [],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "list",
                        "version": 1,
                        "listType": "bullet",
                        "start": 1,
                        "tag": "ul"
                    },
                    
                    # Nutrition section
                    {
                        "children": [
                            {
                                "detail": 0,
                                "format": 0,
                                "mode": "normal",
                                "style": "",
                                "text": "Nutrition Information",
                                "type": "extended-text",
                                "version": 1
                            }
                        ],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "extended-heading",
                        "version": 1,
                        "tag": "h2"
                    },
                    {
                        "children": [],
                        "direction": "ltr",
                        "format": "",
                        "indent": 0,
                        "type": "list",
                        "version": 1,
                        "listType": "bullet",
                        "start": 1,
                        "tag": "ul"
                    },
                    
                    # Horizontal rule at the end
                    {
                        "type": "horizontalrule",
                        "version": 1
                    }
                ],
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "root",
                "version": 1
            }
        }
        
        # Add instructions to the list
        instructions_list = lexical_dict["root"]["children"][2]
        for i, instruction in enumerate(instructions, 1):
            instructions_list["children"].append({
                "children": [
                    {
                        "detail": 0,
                        "format": 0,
                        "mode": "normal",
                        "style": "",
                        "text": instruction.get('text', ''),
                        "type": "extended-text",
                        "version": 1
                    }
                ],
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "listitem",
                "version": 1,
                "value": i
            })
        
        # Add details to the list
        details_list = lexical_dict["root"]["children"][4]
        details = [
            {"label": "Prep Time", "value": prep_time},
            {"label": "Cook Time", "value": cook_time},
            {"label": "Total Time", "value": total_time},
            {"label": "Servings", "value": yield_value},
            {"label": "Category", "value": category},
            {"label": "Cuisine", "value": cuisine}
        ]
        
        for i, detail in enumerate(details, 1):
            details_list["children"].append({
                "children": [
                    {
                        "detail": 0,
                        "format": 1,  # Bold
                        "mode": "normal",
                        "style": "",
                        "text": detail["label"] + ":",
                        "type": "extended-text",
                        "version": 1
                    },
                    {
                        "detail": 0,
                        "format": 0,
                        "mode": "normal",
                        "style": "",
                        "text": " " + detail["value"],
                        "type": "extended-text",
                        "version": 1
                    }
                ],
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "listitem",
                "version": 1,
                "value": i
            })
        
        # Add nutrition info to the list
        nutrition_list = lexical_dict["root"]["children"][6]
        nutrition_items = [
            {"label": "Calories", "value": calories},
            {"label": "Carbohydrates", "value": carbs},
            {"label": "Protein", "value": protein},
            {"label": "Fat", "value": fat}
        ]
        
        for i, item in enumerate(nutrition_items, 1):
            nutrition_list["children"].append({
                "children": [
                    {
                        "detail": 0,
                        "format": 1,  # Bold
                        "mode": "normal",
                        "style": "",
                        "text": item["label"] + ":",
                        "type": "extended-text",
                        "version": 1
                    },
                    {
                        "detail": 0,
                        "format": 0,
                        "mode": "normal",
                        "style": "",
                        "text": " " + item["value"],
                        "type": "extended-text",
                        "version": 1
                    }
                ],
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "type": "listitem",
                "version": 1,
                "value": i
            })
        
        # Create HTML content for fallback
        html_content = f"""
<h2 id="ingredients">Ingredients</h2>
<ul>
  {''.join([f'<li>{ingredient}</li>' for ingredient in ingredients])}
</ul>

<h2 id="instructions">Instructions</h2>
<ol>
  {''.join([f'<li>{instruction.get("text", "")}</li>' for instruction in instructions])}
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
                    
        return {
            'title': title,
            'html_content': html_content,
            'lexical_content': lexical_dict,
            'codeinjection_head': json_ld,
            'tags': tags,
            'feature_image': recipe_data.get('image', [''])[0] if isinstance(recipe_data.get('image', []), list) else recipe_data.get('image', '')
        }
    
    except Exception as e:
        print(f"Error processing recipe JSON: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def fetch_all_posts():
    """Fetch all posts from Ghost"""
    url = f"{ADMIN_API_URL}posts/?formats=html,lexical&limit=all"
    
    headers = get_headers()
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        posts = response.json().get('posts', [])
        print(f"Successfully fetched {len(posts)} posts")
        return posts
    else:
        print(f"Error fetching posts: {response.status_code} - {response.text}")
        return []

def delete_post(post_id):
    """Delete a post by ID"""
    url = f"{ADMIN_API_URL}posts/{post_id}/"
    
    headers = get_headers()
    response = requests.delete(url, headers=headers)
    
    if response.status_code in [200, 204]:
        print(f"Successfully deleted post with ID: {post_id}")
        return True
    else:
        print(f"Error deleting post: {response.status_code} - {response.text}")
        return False

def find_template_and_clean_up():
    """Find the template post and delete all other posts"""
    print("=== Finding Template Post and Cleaning Up ===")
    
    # Step 1: Fetch all posts
    all_posts = fetch_all_posts()
    
    if not all_posts:
        print("No posts found.")
        return
    
    # Step 2: Find the template post
    template_post = None
    for post in all_posts:
        title = post.get('title', '')
        if '[TEMPLATE]' in title:
            template_post = post
            break
    
    if not template_post:
        print("No template post found with '[TEMPLATE]' in the title.")
        return
    
    template_id = template_post.get('id')
    template_title = template_post.get('title')
    print(f"Found template post: {template_title} (ID: {template_id})")
    
    # Step 3: Delete all other posts
    deleted_count = 0
    for post in all_posts:
        post_id = post.get('id')
        post_title = post.get('title', '')
        
        if post_id != template_id:
            print(f"Deleting post: {post_title}")
            if delete_post(post_id):
                deleted_count += 1
    
    print(f"Clean-up complete. Kept template post and deleted {deleted_count} other posts.")
    return template_post

def main():
    """Main function to run the script"""
    print("=== Ghost Template Test ===")
    
    # Find the template post and clean up
    template_post = find_template_and_clean_up()
    
    if not template_post:
        print("No template post found. Exiting.")
        return
    
    # Extract the template content
    template = {
        'title': template_post.get('title', '').replace('[TEMPLATE]', '').strip(),
        'html': template_post.get('html', ''),
        'lexical': template_post.get('lexical', {}),
        'codeinjection_head': template_post.get('codeinjection_head', ''),
        'codeinjection_foot': template_post.get('codeinjection_foot', ''),
        'tags': template_post.get('tags', []),
        'feature_image': template_post.get('feature_image', '')
    }
    
    # Process recipe data
    print("\nProcessing recipe from recipe_0002.json...")
    recipe_path = '../final/recipe_0002.json'
    if os.path.exists(recipe_path):
        # Read the recipe data directly
        with open(recipe_path, 'r', encoding='utf-8') as f:
            recipe_json = json.load(f)
            
        # Extract key information
        recipe_title = recipe_json.get('name', '')
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
        
        print(f"Recipe: {recipe_title}")
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
        
        # Get the lexical content from the template
        lexical_content = template_post.get('lexical', None)
        if lexical_content and isinstance(lexical_content, dict):
            # Already a dict
            lexical_dict = lexical_content
        elif lexical_content and isinstance(lexical_content, str):
            # Parse the string to a dict
            lexical_dict = json.loads(lexical_content)
        else:
            # Create a basic structure
            lexical_dict = {"root": {"children": [], "direction": "ltr", "format": "", "indent": 0, "type": "root", "version": 1}}
            
        print("\nUpdating lexical structure with recipe data...")
            
        # Extract the root children for manipulation
        if 'root' in lexical_dict and 'children' in lexical_dict['root']:
            children = lexical_dict['root']['children']
            
            # Find ingredients and instructions
            ingredients_found = []
            instructions_found = []
            
            if 'root' in lexical_dict and 'children' in lexical_dict['root']:
                children = lexical_dict['root']['children']
                
                # Debug the structure
                print("\nDebug - Lexical structure overview:")
                for i, child in enumerate(children):
                    child_type = child.get('type', 'unknown')
                    if child_type == 'extended-heading' and 'children' in child:
                        heading_text = "unknown"
                        for text in child['children']:
                            if text.get('type') == 'extended-text':
                                heading_text = text.get('text', 'unknown')
                        print(f"  {i}: {child_type} - {heading_text}")
                    else:
                        print(f"  {i}: {child_type}")
                
                # Check for ingredients in markdown card
                for child in children:
                    if child.get('type') == 'markdown' and 'markdown' in child:
                        markdown_content = child.get('markdown', '')
                        print(f"\nFound markdown content: {markdown_content[:100]}...")
                        
                        # Look for ingredients section in markdown
                        if '## Ingredients' in markdown_content:
                            print("Found ingredients section in markdown!")
                            # Extract ingredients list
                            ingredients_section = markdown_content.split('## Ingredients')[1]
                            if '##' in ingredients_section:
                                ingredients_section = ingredients_section.split('##')[0]
                                
                            # Parse ingredient items
                            ingredient_lines = [line.strip() for line in ingredients_section.strip().split('\n') if line.strip().startswith('- ')]
                            if ingredient_lines:
                                ingredients_found = [line[2:].strip() for line in ingredient_lines]  # Remove "- " prefix
                                print(f"Extracted {len(ingredients_found)} ingredients from markdown")
                        
                        # If we didn't find a properly formatted section, look for any bullet list
                        if not ingredients_found:
                            bullet_items = [line.strip()[2:] for line in markdown_content.split('\n') if line.strip().startswith('- ')]
                            if bullet_items:
                                print(f"Found {len(bullet_items)} bullet items in markdown")
                                # Check if these match our expected ingredients
                                match_count = sum(1 for item in bullet_items if any(ingredient in item for ingredient in ingredients))
                                if match_count > 2:
                                    print(f"Found likely ingredients with {match_count} matches")
                                    ingredients_found = bullet_items
                
                # More robust search for instructions
                current_section = None
                
                for i, child in enumerate(children):
                    # Check if this is a heading
                    if child.get('type') == 'extended-heading' and 'children' in child:
                        for text in child['children']:
                            if text.get('type') == 'extended-text':
                                current_section = text.get('text')
                                print(f"Found section: {current_section}")
                    
                    # If this is a list after a heading we care about
                    elif child.get('type') == 'list' and current_section in ['Ingredients', 'Instructions']:
                        list_items = []
                        # Extract list items
                        for item in child.get('children', []):
                            if item.get('type') == 'listitem' and 'children' in item:
                                for text_node in item['children']:
                                    if text_node.get('type') == 'extended-text':
                                        list_items.append(text_node.get('text', ''))
                                        
                        # Add to the appropriate list
                        if current_section == 'Ingredients' and not ingredients_found:
                            ingredients_found = list_items
                        elif current_section == 'Instructions':
                            instructions_found = list_items
                            
                        # Reset current section after processing
                        current_section = None
        
        # Convert lexical_dict to a string as required by the Ghost API
        lexical_string = json.dumps(lexical_dict)
        
        # HTML is a fallback only - Ghost primarily uses lexical content
        html_content = template_post.get('html', '')
        
        # Create the new post
        print("\nCreating new post with HTML only (no lexical content)...")
        new_post = {
            "posts": [{
                "title": recipe_title,
                "status": "draft",
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
""",
                "codeinjection_head": json_ld,
                "codeinjection_foot": template_post.get('codeinjection_foot', ''),
                "tags": tags,
                "feature_image": recipe_json.get('image', [''])[0] if isinstance(recipe_json.get('image', []), list) else recipe_json.get('image', '')
            }]
        }
        
        # Send request to Ghost API
        url = f"{ADMIN_API_URL}posts/"
        headers = get_headers()
        response = requests.post(url, json=new_post, headers=headers)
        
        if response.status_code == 201:
            created_post = response.json().get('posts', [])[0]
            print(f"Successfully created new post: {created_post['title']}")
            print(f"Post ID: {created_post['id']}")
            
            # Fetch the post to verify
            print("\nFetching the post to verify...")
            post_id = created_post['id']
            fetched_post = fetch_post_by_id(post_id)
            
            if fetched_post:
                print("\nVerification successful!")
                print(f"Post title: {fetched_post['title']}")
                print(f"Tags: {[tag.get('name', '') for tag in fetched_post.get('tags', [])]}")
                
                # Print out lexical content to verify
                lexical_str = fetched_post.get('lexical', '')
                if lexical_str:
                    try:
                        # Parse lexical content
                        lexical_data = json.loads(lexical_str)
                        
                        # Find ingredients and instructions
                        ingredients_found = []
                        instructions_found = []
                        
                        if 'root' in lexical_data and 'children' in lexical_data['root']:
                            children = lexical_data['root']['children']
                            
                            # Debug the structure
                            print("\nDebug - Lexical structure overview:")
                            for i, child in enumerate(children):
                                child_type = child.get('type', 'unknown')
                                if child_type == 'extended-heading' and 'children' in child:
                                    heading_text = "unknown"
                                    for text in child['children']:
                                        if text.get('type') == 'extended-text':
                                            heading_text = text.get('text', 'unknown')
                                    print(f"  {i}: {child_type} - {heading_text}")
                                else:
                                    print(f"  {i}: {child_type}")
                            
                            # Check for ingredients in markdown card
                            for child in children:
                                if child.get('type') == 'markdown' and 'markdown' in child:
                                    markdown_content = child.get('markdown', '')
                                    print(f"\nFound markdown content: {markdown_content[:100]}...")
                                    
                                    # Look for ingredients section in markdown
                                    if '## Ingredients' in markdown_content:
                                        print("Found ingredients section in markdown!")
                                        # Extract ingredients list
                                        ingredients_section = markdown_content.split('## Ingredients')[1]
                                        if '##' in ingredients_section:
                                            ingredients_section = ingredients_section.split('##')[0]
                                            
                                        # Parse ingredient items
                                        ingredient_lines = [line.strip() for line in ingredients_section.strip().split('\n') if line.strip().startswith('- ')]
                                        if ingredient_lines:
                                            ingredients_found = [line[2:].strip() for line in ingredient_lines]  # Remove "- " prefix
                                            print(f"Extracted {len(ingredients_found)} ingredients from markdown")
                                    
                                    # If we didn't find a properly formatted section, look for any bullet list
                                    if not ingredients_found:
                                        bullet_items = [line.strip()[2:] for line in markdown_content.split('\n') if line.strip().startswith('- ')]
                                        if bullet_items:
                                            print(f"Found {len(bullet_items)} bullet items in markdown")
                                            # Check if these match our expected ingredients
                                            match_count = sum(1 for item in bullet_items if any(ingredient in item for ingredient in ingredients))
                                            if match_count > 2:
                                                print(f"Found likely ingredients with {match_count} matches")
                                                ingredients_found = bullet_items
                            
                            # More robust search for instructions
                            current_section = None
                            
                            for i, child in enumerate(children):
                                # Check if this is a heading
                                if child.get('type') == 'extended-heading' and 'children' in child:
                                    for text in child['children']:
                                        if text.get('type') == 'extended-text':
                                            current_section = text.get('text')
                                            print(f"Found section: {current_section}")
                                
                                # If this is a list after a heading we care about
                                elif child.get('type') == 'list' and current_section in ['Ingredients', 'Instructions']:
                                    list_items = []
                                    # Extract list items
                                    for item in child.get('children', []):
                                        if item.get('type') == 'listitem' and 'children' in item:
                                            for text_node in item['children']:
                                                if text_node.get('type') == 'extended-text':
                                                    list_items.append(text_node.get('text', ''))
                                                    
                                    # Add to the appropriate list
                                    if current_section == 'Ingredients' and not ingredients_found:
                                        ingredients_found = list_items
                                    elif current_section == 'Instructions':
                                        instructions_found = list_items
                                        
                                    # Reset current section after processing
                                    current_section = None
                        
                        # Print verification
                        print("\nVerifying content mapping:")
                        if ingredients_found:
                            print(f"\nIngredients found ({len(ingredients_found)} items):")
                            for i, ingredient in enumerate(ingredients_found[:5], 1):
                                print(f"  {i}. {ingredient}")
                            if len(ingredients_found) > 5:
                                print(f"  ...and {len(ingredients_found) - 5} more")
                                
                            # Verify ingredients match the recipe
                            match_count = sum(1 for i in ingredients_found if i in ingredients)
                            print(f"\nIngredient mapping accuracy: {match_count}/{len(ingredients)} items match")
                        else:
                            print("No ingredients found in the post content.")
                            
                        if instructions_found:
                            print(f"\nInstructions found ({len(instructions_found)} steps):")
                            for i, instruction in enumerate(instructions_found[:3], 1):
                                print(f"  {i}. {instruction[:100]}..." if len(instruction) > 100 else f"  {i}. {instruction}")
                            if len(instructions_found) > 3:
                                print(f"  ...and {len(instructions_found) - 3} more steps")
                                
                            # Verify instructions match the recipe
                            recipe_instruction_texts = [inst.get('text', '') for inst in instructions]
                            match_count = sum(1 for i in instructions_found if i in recipe_instruction_texts)
                            print(f"\nInstruction mapping accuracy: {match_count}/{len(instructions)} steps match")
                        else:
                            print("No instructions found in the post content.")
                            
                    except json.JSONDecodeError:
                        print("Error parsing lexical content.")
                else:
                    print("No lexical content found in the post.")
        else:
            print(f"Error creating post: {response.status_code} - {response.text}")
    else:
        print(f"Recipe file not found at {recipe_path}. Exiting.")

if __name__ == "__main__":
    main() 