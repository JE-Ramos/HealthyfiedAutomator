#!/usr/bin/env python3

import jwt
import time
import requests
import json
import os
import datetime

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

def update_post(post_id, post):
    """Update a post by ID"""
    url = f"{ADMIN_API_URL}posts/{post_id}/"
    
    # Get the current time in ISO format
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    
    # Prepare update data with minimal required fields
    update_data = {
        "posts": [{
            "id": post_id,
            "updated_at": post.get('updated_at', now),  # Use post's updated_at or current time
            "feature_image": None
        }]
    }
    
    headers = get_headers()
    response = requests.put(url, headers=headers, json=update_data)
    
    if response.status_code == 200:
        print(f"Successfully updated post with ID: {post_id}")
        return True
    else:
        print(f"Error updating post: {response.status_code} - {response.text}")
        return False

def remove_all_feature_images():
    """Remove feature images from all published posts"""
    posts = fetch_all_posts()
    
    if not posts:
        print("No posts found.")
        return
    
    published_posts = [post for post in posts if post.get('status') == 'published']
    print(f"\nRemoving feature images from {len(published_posts)} published posts:")
    
    for post in published_posts:
        post_id = post.get('id')
        title = post.get('title', 'Untitled')
        
        # Skip the template post if it exists
        if '[TEMPLATE]' in title:
            print(f"Skipping template post: {title}")
            continue
        
        print(f"Processing post: {title}")
        update_post(post_id, post)
    
    print("\nFeature image removal completed!")

if __name__ == "__main__":
    remove_all_feature_images() 