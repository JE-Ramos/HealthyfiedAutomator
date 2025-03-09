#!/usr/bin/env python3
import jwt
import time
import requests
import csv
import json
import os
from datetime import datetime
import shutil

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
    return token

def get_headers():
    """Get headers for Ghost API requests"""
    token = create_token()
    return {
        'Authorization': f'Ghost {token}',
        'Accept-Version': 'v5.99'  # Specify the API version
    }

def fetch_all_posts(status='all'):
    """Fetch all posts with specified status"""
    url = f"{ADMIN_API_URL}posts/?formats=html,lexical"
    params = {'limit': 'all'}
    
    if status != 'all':
        params['filter'] = f'status:{status}'
    
    headers = get_headers()
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json().get('posts', [])
    else:
        print(f"Error fetching posts: {response.status_code} - {response.text}")
        return []

def save_posts_to_csv(posts, filename='posts.csv'):
    """Save posts to CSV file"""
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
    
    print(f"Saved {len(posts)} posts to {filename}")

def save_posts_to_json(posts, filename='posts.json'):
    """Save posts to JSON file for complete backup"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=2)
    
    print(f"Saved complete post data to {filename}")

def backup_posts():
    """Download and back up all posts"""
    # Create backup directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Fetch all published and draft posts
    print("Fetching all posts...")
    posts = fetch_all_posts()
    
    if not posts:
        print("No posts found to back up.")
        return
    
    print(f"Found {len(posts)} posts.")
    
    # Save to CSV and JSON in the backup directory
    save_posts_to_csv(posts, os.path.join(backup_dir, 'posts.csv'))
    save_posts_to_json(posts, os.path.join(backup_dir, 'posts.json'))
    
    # Also save the current posts.csv if it exists
    if os.path.exists('posts.csv'):
        shutil.copy2('posts.csv', os.path.join(backup_dir, 'original_posts.csv'))
    
    print(f"Backup completed successfully to directory: {backup_dir}")
    return posts

def delete_post(post_id):
    """Delete a single post by ID"""
    url = f"{ADMIN_API_URL}posts/{post_id}/"
    headers = get_headers()
    
    response = requests.delete(url, headers=headers)
    
    if response.status_code in [204, 200]:
        return True
    else:
        print(f"Error deleting post {post_id}: {response.status_code} - {response.text}")
        return False

def delete_all_posts(posts=None):
    """Delete all posts (optional: provide posts list to avoid extra API call)"""
    if posts is None:
        posts = fetch_all_posts()
    
    if not posts:
        print("No posts found to delete.")
        return
    
    print(f"Preparing to delete {len(posts)} posts...")
    
    # Ask for confirmation
    confirmation = input(f"Are you sure you want to delete ALL {len(posts)} posts? This cannot be undone. (yes/no): ")
    if confirmation.lower() != 'yes':
        print("Deletion cancelled.")
        return
    
    successful = 0
    failed = 0
    
    for post in posts:
        post_id = post.get('id')
        title = post.get('title')
        print(f"Deleting post: {title} (ID: {post_id})...")
        
        if delete_post(post_id):
            successful += 1
        else:
            failed += 1
    
    print(f"Deletion complete. Successfully deleted: {successful}, Failed: {failed}")

def main():
    """Main function to run the script"""
    print("=== Ghost Blog Manager ===")
    print("1. Backing up all posts...")
    posts = backup_posts()
    
    print("\n2. Deleting all posts...")
    delete_all_posts(posts)
    
    print("\nProcess completed!")

if __name__ == "__main__":
    main() 