#!/usr/bin/env python3
import jwt
import time
import requests
import json
import os

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

def cleanup_posts():
    """Delete all published posts, keeping only the template draft"""
    print("=== Cleaning Up Posts ===")
    
    # Step 1: Fetch all posts
    all_posts = fetch_all_posts()
    
    if not all_posts:
        print("No posts found.")
        return
    
    # Step 2: Find the template post and identify posts to delete
    template_post = None
    posts_to_delete = []
    
    for post in all_posts:
        title = post.get('title', '')
        status = post.get('status', '')
        
        if '[TEMPLATE]' in title and status == 'draft':
            template_post = post
            print(f"Found template post: {title} (ID: {post.get('id')})")
        else:
            posts_to_delete.append(post)
            print(f"Marked for deletion: {title} (Status: {status}, ID: {post.get('id')})")
    
    # Step 3: Delete all non-template posts
    if not template_post:
        print("Warning: No template post found with '[TEMPLATE]' in the title.")
    
    if not posts_to_delete:
        print("No posts to delete.")
        return
    
    print(f"\nDeleting {len(posts_to_delete)} posts...")
    
    deleted_count = 0
    for post in posts_to_delete:
        post_id = post.get('id')
        post_title = post.get('title', '')
        
        print(f"Deleting post: {post_title}")
        if delete_post(post_id):
            deleted_count += 1
    
    print(f"\nClean-up complete. Deleted {deleted_count} posts.")
    
    if template_post:
        print(f"Kept template post: {template_post.get('title')}")
    
    # Step 4: Verify the cleanup
    remaining_posts = fetch_all_posts()
    print(f"\nVerification: {len(remaining_posts)} posts remain")
    
    for post in remaining_posts:
        print(f" - {post.get('title')} (Status: {post.get('status')})")

if __name__ == "__main__":
    cleanup_posts() 