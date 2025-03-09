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

def fetch_post_details(post_id):
    """Fetch detailed information for a single post"""
    url = f"{ADMIN_API_URL}posts/{post_id}/?formats=mobiledoc,html,lexical&include=tags"
    
    headers = get_headers()
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        post = response.json().get('posts', [])[0]
        print(f"Successfully fetched post: {post.get('title')}")
        return post
    else:
        print(f"Error fetching post: {response.status_code} - {response.text}")
        return None

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

def check_post_details():
    """Check details of all published posts"""
    posts = fetch_all_posts()
    
    if not posts:
        print("No posts found to check.")
        return
    
    published_posts = [post for post in posts if post.get('status') == 'published']
    print(f"\nChecking details for {len(published_posts)} published posts:")
    
    for post in published_posts:
        post_id = post.get('id')
        post_details = fetch_post_details(post_id)
        
        if post_details:
            title = post_details.get('title', 'No Title')
            excerpt = post_details.get('excerpt', '')
            code_injection_head = post_details.get('codeinjection_head', '')
            
            print(f"\n=== {title} ===")
            print(f"Publication date: {post_details.get('published_at', '')[:10]}")
            
            # Check for excerpt
            if excerpt:
                excerpt_preview = excerpt[:100] + "..." if len(excerpt) > 100 else excerpt
                print(f"Excerpt: {excerpt_preview}")
            else:
                print("Warning: No excerpt found")
            
            # Check for code injection
            if code_injection_head:
                has_schema = 'application/ld+json' in code_injection_head
                print(f"Code injection: {'Contains schema.org JSON-LD' if has_schema else 'Present but no schema.org data'}")
            else:
                print("Warning: No code injection found")
            
            # Check tags
            tags = post_details.get('tags', [])
            tag_names = [tag.get('name') for tag in tags]
            print(f"Tags: {', '.join(tag_names)}")
            
            # Check if "Recipes" is the first tag
            if tag_names and tag_names[0] == "Recipes":
                print("Tags order: Correct (Recipes is first)")
            else:
                print("Warning: 'Recipes' is not the first tag")

if __name__ == "__main__":
    check_post_details() 