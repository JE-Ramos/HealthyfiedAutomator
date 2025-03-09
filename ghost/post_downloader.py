import jwt
import time
import requests
import csv
import pprint
import json
from bs4 import BeautifulSoup
import os

# Configuration
ADMIN_API_URL = 'https://healthyfied.ghost.io/ghost/api/admin/'
ADMIN_API_KEY = '67472f3b02b637000105c5b3:0d7cacc062c371d3bd12e0994d85d059d8ca358b20ab7ea1dec28aa9e32d9e92'  # Format: 'id:secret'

# Split the Admin API key into ID and SECRET
id, secret = ADMIN_API_KEY.split(':')

# Create a JWT (JSON Web Token)
iat = int(time.time())
exp = iat + 5 * 60  # Token valid for 5 minutes
aud = '/admin/'

payload = {
    'iat': iat,
    'exp': exp,
    'aud': aud
}

token = jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers={'kid': id})

# Set up headers
headers = {
    'Authorization': f'Ghost {token}',
    'Accept-Version': 'v5.99'  # Specify the API version
}

# Fetch all posts
def fetch_all_posts():
    url = f"{ADMIN_API_URL}posts/?formats=html,lexical"
    params = {
        'filter': 'status:draft',
        'limit': 'all',
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get('posts', [])
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

def extract_recipe_schema(html_content):
    """Extract recipe schema from HTML content"""
    if not html_content:
        return None
    
    soup = BeautifulSoup(html_content, 'html.parser')
    schema_elem = soup.find('p', id='recipe-schema')
    
    if schema_elem and schema_elem.string:
        try:
            return json.loads(schema_elem.string)
        except json.JSONDecodeError:
            return None
    return None

def save_recipe_schemas(posts, schema_dir='recipes'):
    """Save each recipe schema to a separate JSON file"""
    # Create recipes directory if it doesn't exist
    if not os.path.exists(schema_dir):
        os.makedirs(schema_dir)
    
    count = 1  # Start count at 1
    for post in posts:
        html_content = post.get('html', '')
        schema = extract_recipe_schema(html_content)
        if schema:
            post_id = post.get('id')
            recipe_data = {
                'post_id': post_id,
                'title': post.get('title'),
                'schema': schema
            }
            
            # Create filename with count and post_id
            filename = f"{count:03d}_{post_id}.json"
            filepath = os.path.join(schema_dir, filename)
            
            # Save individual recipe file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(recipe_data, f, indent=2)
            
            count += 1  # Increment counter only when recipe is saved

def save_posts_to_csv(posts, filename='posts.csv'):
    # Define the fields we want to save
    fields = [
        'id', 'title', 'slug', 'status', 'visibility', 
        'created_at', 'updated_at', 'published_at',
        'html', 'lexical', 'excerpt'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        
        for post in posts:
            # Create a row dictionary with only the fields we want
            row = {}
            for field in fields:
                # Get the value, convert nested structures to JSON strings
                value = post.get(field, '')
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                row[field] = value
            
            writer.writerow(row)
    
    save_recipe_schemas(posts)  # Add this line to also save schemas

# Main execution
if __name__ == "__main__":
    posts = fetch_all_posts()

    print(f"Total Posts Retrieved: {len(posts)}")
    save_posts_to_csv(posts)
