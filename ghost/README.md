# Healthyfied Ghost Blog Management Tools

This directory contains scripts for managing Healthyfied's Ghost blog, including backing up content, deleting posts, and uploading recipe content.

## Prerequisites

The scripts require the following Python packages:
- `pyjwt` - For authentication with the Ghost Admin API
- `requests` - For making HTTP requests
- `beautifulsoup4` - For HTML parsing

You can install them with:
```bash
pip3 install pyjwt requests beautifulsoup4
```

Or use the provided shell script which will create a virtual environment and install the dependencies.

## Available Scripts

### ghost_manager.py
This script handles backing up and deleting posts:
- Downloads all existing posts and saves them as CSV and JSON files
- Creates timestamped backups of all content
- Can delete all posts (with confirmation)

### recipe_publisher.py
This script manages bulk uploading of recipe JSON files to Ghost:
- Converts JSON recipe files to markdown format with proper formatting
- Creates posts with SEO-friendly slugs in the format `/recipe/recipe-name`
- Schedules posts with publish dates 1 day apart (working backward from Mar 9, 2025)
- Adds JSON-LD structured data to the head of each post
- Includes a non-intrusive ad block in the middle of recipe instructions
- Tags posts based on dietary information

### upload_recipes.sh
A convenience shell script that:
- Creates a Python virtual environment if it doesn't exist
- Prompts for your Ghost Admin API key
- Runs the recipe_publisher.py script

### recipe-styles.css
CSS styles for recipe posts, which should be added to the Ghost admin panel:
1. Go to Ghost Admin → Settings → Code injection
2. Paste the contents of this file into the Site Header or Site Footer section
3. Save changes

The styles make recipe posts look professional and ensure they're mobile and print-friendly.

## Typical Workflow

1. **Backup existing content**:
   ```bash
   cd /path/to/ghost
   python3 ghost_manager.py
   ```

2. **Upload recipes**:
   ```bash
   cd /path/to/ghost
   ./upload_recipes.sh
   ```
   
   Or manually:
   ```bash
   export GHOST_ADMIN_API_KEY="your-api-key"
   python3 recipe_publisher.py
   ```

3. **Add CSS styles**:
   Copy the content of `recipe-styles.css` to your Ghost admin panel's code injection section.

## Notes

- Always back up your Ghost content before making bulk changes.
- The scripts create a `recipe-markdown` folder that contains the converted markdown files.
- You'll need your Ghost Admin API key, which can be found in the Ghost admin panel under Settings → Integrations → Create custom integration.
- The uploader uses a 1-day delay between posts to space out the publishing schedule.

## Troubleshooting

- **ModuleNotFoundError**: Make sure to install the required Python packages.
- **Authentication errors**: Double-check your Admin API key and ensure it has the correct permissions.
- **File not found errors**: Ensure you're running the scripts from the correct directory.
- **API rate limiting**: The script includes a small delay between uploads to avoid hitting rate limits. 