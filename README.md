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

### Current Status
- **Batch 15 of 32 completed** (August 31, 2023 at 12:12 PM)
- 190 out of 351 recipes have been processed
- Last processed recipe: recipe_0190.json
- Next batch (Batch 16) will start from recipe_0191.json

### Last Batch Details
Batch 15 included the following recipes:
1. recipe_0181.json - "Globe Lunch 2" (Published: 2024-09-10)
2. recipe_0182.json - "Chicken Citrus Crabstick Pear Salad" (Published: 2024-09-09)
3. recipe_0183.json - "2018/10/26 Lunch Eggplant Salad" (Published: 2024-09-08)
4. recipe_0184.json - "Yellow Zucchini Pesto Past" (Published: 2024-09-07)
5. recipe_0185.json - "No Milk Chicken Sopas" (Published: 2024-09-06)
6. recipe_0186.json - "Dory Blossom Salad" (Published: 2024-09-05)
7. recipe_0187.json - "Orange "Soy" Salmon" (Published: 2024-09-04)
8. recipe_0188.json - "Cream dory Bellpepper Basil" (Published: 2024-09-03)
9. recipe_0189.json - "Cream dory Bellpepper Basil" (Published: 2024-09-02)
10. recipe_0190.json - "Beef with mushroom" (Published: 2024-09-01)

The next publication date will be: 2024-08-31

## Usage

### To continue processing from where it left off:

```python
cd ghost
python3 publish_all_recipes.py
```

### To specify exactly where to resume:

```python
cd ghost
python3 -c "import publish_all_recipes; publish_all_recipes.publish_all_remaining_recipes(start_index=190)"
```

### To process a specific batch:

You can modify the start_index parameter to start from a different point:
- Batch 16 (recipes 191-200): start_index=190
- Batch 17 (recipes 201-210): start_index=200
- Batch 18 (recipes 211-220): start_index=210
- And so on... 