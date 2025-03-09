#!/usr/bin/env python3
import jwt
import time
import requests
import json
import os
import traceback
from datetime import datetime

# Configuration - using the API key directly for testing
ADMIN_API_URL = "https://healthyfied.ghost.io/ghost/api/admin/"
ADMIN_API_KEY = "67cd6027edc031000157487b:eb9304d2cb866ad6902f88efb11ad43012f40f05015281ecce75cff229093cce"
TEST_RECIPE_PATH = "../final/recipe_0001.json"

def create_token():
    """Create a JWT token for authentication with Ghost Admin API."""
    print(f"Creating token with API key: {ADMIN_API_KEY[:5]}...{ADMIN_API_KEY[-5:]}")
    
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
        now = int(time.time())
        
        # Create the token (payload)
        payload = {
            'iat': now,                    # Issued at time
            'exp': now + (5 * 60),         # Expiration time (5 minutes)
            'aud': '/admin/'               # Audience
        }
        
        # Convert the secret from hex to bytes
        secret_bytes = bytes.fromhex(secret)
        
        # Create the token
        token = jwt.encode(payload, secret_bytes, algorithm='HS256')
        
        # If token is bytes, decode to string (depends on PyJWT version)
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        # The final token is keyId:token
        return f"{key_id}:{token}"
    except Exception as e:
        print(f"ERROR creating token: {str(e)}")
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

def check_api_connection():
    """Test the connection to the Ghost Admin API."""
    try:
        print("Testing connection to Ghost Admin API...")
        
        headers = get_headers()
        if not headers:
            print("ERROR: Failed to create authorization headers. Check your API key format.")
            return False
        
        # Try to get site info as a test
        url = f"{ADMIN_API_URL}site/"
        print(f"Sending request to {url}")
        print(f"Using Authorization header: {headers['Authorization'][:30]}...")
        
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
        traceback.print_exc()
        return False

def create_simple_post():
    """Create a simple test post to verify API is working."""
    try:
        # Create a simple post data
        post_data = {
            "posts": [{
                "title": "Test Post - Please Delete",
                "slug": "test-post-please-delete",
                "html": "<p>This is a test post to verify the API is working correctly.</p>",
                "status": "draft"  # Set as draft so it doesn't appear on the site
            }]
        }
        
        # Get headers
        headers = get_headers()
        if not headers:
            print("Failed to get authorization headers. Check your API key.")
            return False
        
        # Send request to Ghost API
        url = f"{ADMIN_API_URL}posts/"
        print(f"Sending POST request to {url}")
        
        response = requests.post(url, json=post_data, headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text[:200]}..." if len(response.text) > 200 else response.text)
        
        if response.status_code >= 200 and response.status_code < 300:
            print("Successfully created test post!")
            post_data = response.json()
            if 'posts' in post_data and len(post_data['posts']) > 0:
                post_id = post_data['posts'][0].get('id')
                print(f"Created post ID: {post_id}")
            return True
        else:
            print(f"Failed to create test post. Status: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"ERROR creating post: {str(e)}")
        traceback.print_exc()
        return False

def upload_recipe():
    """Upload a single recipe to test the full functionality."""
    try:
        # Load the recipe data
        with open(TEST_RECIPE_PATH, 'r') as f:
            recipe_data = json.load(f)
        
        # Extract basic info
        title = recipe_data.get('name', 'Untitled Recipe')
        slug = title.lower().replace(' ', '-').replace(',', '').replace('.', '')
        slug = ''.join(c if c.isalnum() or c == '-' else '' for c in slug)
        description = recipe_data.get('description', '')
        image = recipe_data.get('image', '')
        if isinstance(image, list) and len(image) > 0:
            image = image[0]
        
        # Create HTML content for the post
        instructions_html = ""
        for i, instruction in enumerate(recipe_data.get('recipeInstructions', [])):
            step_text = instruction.get('text', '')
            instructions_html += f"<p><strong>Step {i+1}:</strong> {step_text}</p>\n"
        
        ingredients_html = "<ul>\n"
        for ingredient in recipe_data.get('recipeIngredient', []):
            ingredients_html += f"<li>{ingredient}</li>\n"
        ingredients_html += "</ul>\n"
        
        # JSON-LD for structured data
        json_ld = f"""
<script type="application/ld+json">
{json.dumps(recipe_data, indent=2)}
</script>
"""
        
        # Complete HTML content
        html_content = f"""
<p><em>{description}</em></p>

<h2>Ingredients</h2>
{ingredients_html}

<h2>Instructions</h2>
{instructions_html}

<!-- Ad Block -->
<div class="ad-container">
    <p class="ad-label">Advertisement</p>
    <div class="ad-content">
        <p>Support Healthyfied by checking out our sponsors</p>
    </div>
</div>
"""
        
        # Create the post data
        post_data = {
            "posts": [{
                "title": title,
                "slug": f"recipe/{slug}",
                "html": html_content,
                "status": "draft",  # Set as draft for testing
                "feature_image": image,
                "codeinjection_head": json_ld
            }]
        }
        
        # Get headers
        headers = get_headers()
        if not headers:
            print("Failed to get authorization headers. Check your API key.")
            return False
        
        # Send request to Ghost API
        url = f"{ADMIN_API_URL}posts/"
        print(f"Sending recipe POST request to {url}")
        
        response = requests.post(url, json=post_data, headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text[:200]}..." if len(response.text) > 200 else response.text)
        
        if response.status_code >= 200 and response.status_code < 300:
            print(f"Successfully created recipe post for: {title}!")
            return True
        else:
            print(f"Failed to create recipe post. Status: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"ERROR uploading recipe: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Main function to test the Ghost API connection and upload capabilities."""
    print("\n=== GHOST API TEST SCRIPT ===\n")
    
    # Step 1: Test API connection
    print("\n== Step 1: Testing API Connection ==\n")
    if not check_api_connection():
        print("\nAPI connection test failed. Cannot proceed with further tests.")
        return
    
    # Step 2: Create a simple test post
    print("\n== Step 2: Creating Simple Test Post ==\n")
    if not create_simple_post():
        print("\nCreating a simple post failed. Cannot proceed with recipe upload.")
        return
    
    # Step 3: Upload a recipe
    print("\n== Step 3: Uploading Recipe ==\n")
    if upload_recipe():
        print("\nRecipe upload test was successful!")
    else:
        print("\nRecipe upload test failed.")

if __name__ == "__main__":
    main() 