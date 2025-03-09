# Quick Start Guide

## Getting Started in 5 Minutes

1. **Clone the repository**
   ```bash
   git clone https://github.com/JE-Ramos/HealthyfiedAutomator.git
   cd HealthyfiedAutomator
   ```

2. **Set up your environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Ghost API credentials**
   
   Create a file `ghost/.env` with:
   ```
   GHOST_URL=https://your-ghost-blog.com
   GHOST_ADMIN_API_KEY=your-admin-api-key
   ```

4. **Continue publishing recipes**
   ```bash
   cd ghost
   python publish_all_recipes.py
   ```

## Key Files

- `CURRENT_STATE.md` - Check this to see where processing left off
- `SETUP.md` - Detailed setup instructions
- `README.md` - Project overview

## Common Tasks

### Publish a specific batch

```bash
cd ghost
python -c "import publish_all_recipes; publish_all_recipes.publish_all_remaining_recipes(start_index=190)"
```

### Check published posts

```bash
cd ghost
python check_details.py
```

### Clean up (delete) all posts except template

```bash
cd ghost
python cleanup_posts.py
``` 