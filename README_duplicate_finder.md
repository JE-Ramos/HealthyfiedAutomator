# Recipe Duplicate Finder

This script analyzes recipe JSON files to identify potential duplicates, organize them by completeness, and create merged versions for comparison.

## What It Does

1. **Identifies Duplicate Recipes**: Uses both recipe ID matching and similarity analysis (title and ingredient list) to detect potential duplicates.
2. **Organizes Recipes**:
   - Places the most complete version of each recipe in the `result/for_publishing` directory
   - Moves potential duplicates to the `result/removed_as_duplicates` directory
   - Creates merged versions in the `result/merged_recipes` directory
3. **Creates a Summary Report**: Generates a CSV file listing all duplicate groups, with details about which files were published, removed, or merged.

## How to Use

1. Make sure your recipe JSON files are in the `recipes` directory (this is the default).
2. Run the script:

```bash
python3 recipe_duplicate_finder.py
```

3. Check the results in the `result` directory:
   - `result/for_publishing/`: Contains the most complete version of each unique recipe
   - `result/removed_as_duplicates/`: Contains recipes identified as duplicates
   - `result/merged_recipes/`: Contains smart-merged versions of duplicate recipes
   - `result/duplicate_report.csv`: A detailed report of all duplicates found

## How It Works

### Duplicate Detection

The script identifies potential duplicates using two methods:

1. **Exact Match**: Recipes with the same post_id are automatically considered duplicates
2. **Similarity Match**: For remaining recipes, the following measures are used:
   - Title similarity (default threshold: 80%)
   - Ingredient list similarity (default threshold: 70%)

If either threshold is met, the recipes are considered potential duplicates.

### Completeness Scoring

Recipes are scored based on their schema.org format completeness:
- Essential fields like name, ingredients, and instructions get higher scores
- Optional fields like description, prep time, and nutrition information add additional points
- The number and detail of ingredients and instructions also contribute to the score

### Smart Merging

When duplicates are found, the script creates a merged version that:
- Uses the most complete recipe as a base
- Adds any missing ingredients from other versions
- Takes the longer description, if available
- Combines tags, suitable diets, and other metadata

## Customizing

You can modify these parameters in the code if needed:
- `title_threshold`: Minimum similarity (0.0-1.0) for titles to be considered duplicates
- `ingredient_threshold`: Minimum similarity (0.0-1.0) for ingredient lists to be considered duplicates

## Requirements

- Python 3.6+
- No external libraries are required (only standard library) 