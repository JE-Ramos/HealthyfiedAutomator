# HealthyfiedAutomator

A collection of scripts for automating the creation and management of recipe posts on a Ghost CMS blog.

## Features

- Automatically publishes recipes from JSON files to a Ghost blog
- Formats recipes with proper ingredients, instructions, and nutrition information
- Includes schema.org recipe markup for SEO
- Manages tags and categories
- Schedules posts with configurable publication dates

## Project Structure

- `/ghost`: Scripts for interacting with the Ghost CMS API
- `/final`: Contains the recipe JSON files to be published
- `/templates`: HTML templates for recipe formatting

## Progress

Current status:
- 190 out of 351 recipes have been processed
- Last processed recipe: recipe_0190.json
- Next batch will start from recipe_0191.json (batch 16)

## Usage

To continue processing from where it left off:

```python
cd ghost
python3 publish_all_recipes.py
```

Or to specify a custom start index:

```python
cd ghost
python3 -c "import publish_all_recipes; publish_all_recipes.publish_all_remaining_recipes(start_index=190)"
``` 