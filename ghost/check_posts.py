#!/usr/bin/env python3

from cleanup_posts import fetch_all_posts

def check_posts():
    posts = fetch_all_posts()
    print(f"Number of posts: {len(posts)}")
    
    for post in posts:
        title = post.get('title', 'No Title')
        status = post.get('status', 'unknown')
        published_at = post.get('published_at', '')
        published_date = published_at[:10] if published_at else 'No date'
        
        print(f" - {title} (Published: {published_date}, Status: {status})")

if __name__ == "__main__":
    check_posts() 