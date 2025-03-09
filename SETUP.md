# Setup Guide for HealthyfiedAutomator

This guide explains how to set up and run the HealthyfiedAutomator project.

## Prerequisites

- Python 3.9+
- Ghost CMS instance with Admin API access

## Installation

1. Clone the repository
   ```bash
   git clone https://github.com/JE-Ramos/HealthyfiedAutomator.git
   cd HealthyfiedAutomator
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Create a `.env` file in the `ghost` directory with your Ghost API credentials:
   ```
   GHOST_URL=https://your-ghost-blog.com
   GHOST_ADMIN_API_KEY=your-admin-api-key
   ```

## Running the Scripts

### Publishing Recipes

To continue publishing recipes from where the process last stopped:

```bash
cd ghost
python publish_all_recipes.py
```

See `CURRENT_STATE.md` for details on the current processing state and how to resume from a specific batch.

### Checking Post Details

To check details of published posts:

```bash
cd ghost
python check_details.py
```

### Cleaning Up Posts

To delete all posts except the template:

```bash
cd ghost
python cleanup_posts.py
```

## File Structure

- `ghost/` - Contains scripts for interacting with Ghost API
- `final/` - Contains recipe JSON files to be published
- `templates/` - HTML templates for formatting recipes
- `requirements.txt` - Python dependencies
- `CURRENT_STATE.md` - Tracks the current processing state
- `README.md` - Project overview and usage instructions 