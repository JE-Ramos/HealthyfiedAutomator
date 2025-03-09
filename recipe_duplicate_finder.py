#!/usr/bin/env python3
import os
import json
import shutil
import csv
from collections import defaultdict
from difflib import SequenceMatcher
import re

# Create directories if they don't exist
def create_directories():
    # Create a parent 'result' directory
    if not os.path.exists("result"):
        os.makedirs("result")
        
    directories = ["for_publishing", "removed_as_duplicates", "merged_recipes"]
    for directory in directories:
        # Create directories inside the 'result' parent folder
        result_dir = os.path.join("result", directory)
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
    return directories

# Load all recipe files from the recipes directory
def load_recipes(recipes_dir="recipes"):
    recipes = []
    
    # Check if directory exists
    if not os.path.exists(recipes_dir):
        print(f"Error: Directory '{recipes_dir}' does not exist!")
        return recipes
    
    print(f"Reading recipe files from: {os.path.abspath(recipes_dir)}")
    
    # Get list of all JSON files in the directory
    json_files = [f for f in os.listdir(recipes_dir) if f.endswith(".json")]
    print(f"Found {len(json_files)} JSON files in directory")
    
    for filename in json_files:
        file_path = os.path.join(recipes_dir, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                recipe_data = json.load(file)
                recipe_data["file_name"] = filename
                recipe_data["file_path"] = file_path
                recipes.append(recipe_data)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    
    print(f"Successfully loaded {len(recipes)} recipe files")
    return recipes

# Calculate recipe completeness score
def calculate_completeness(recipe):
    """Calculate how complete a recipe is based on schema.org format"""
    score = 0
    schema = recipe.get("schema", {})
    
    # Check for required fields
    if schema.get("name"):
        score += 10
    if schema.get("recipeIngredient") and len(schema.get("recipeIngredient", [])) > 0:
        score += 20
    if schema.get("recipeInstructions") and len(schema.get("recipeInstructions", [])) > 0:
        score += 20
    
    # Check for optional but valuable fields
    if schema.get("description"):
        score += 5
    if schema.get("prepTime"):
        score += 3
    if schema.get("cookTime"):
        score += 3
    if schema.get("totalTime"):
        score += 3
    if schema.get("recipeYield"):
        score += 3
    if schema.get("nutrition"):
        score += 10
    if schema.get("tags") and len(schema.get("tags", [])) > 0:
        score += 5
    if schema.get("suitableForDiet") and len(schema.get("suitableForDiet", [])) > 0:
        score += 5
    if schema.get("keywords"):
        score += 3
    
    # Calculate ingredient completeness
    ingredients = schema.get("recipeIngredient", [])
    instructions = schema.get("recipeInstructions", [])
    
    # Add points for number of ingredients and instructions
    score += min(10, len(ingredients))
    score += min(10, len(instructions) * 2)
    
    return score

# Normalize text for better comparison
def normalize_text(text):
    """Normalize text for comparison by removing special chars, lowercasing, etc."""
    if not text:
        return ""
    # Convert to lowercase and remove special characters
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

# Calculate similarity between two strings
def calculate_similarity(str1, str2):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, normalize_text(str1), normalize_text(str2)).ratio()

# Detect potential duplicates based on title and ingredients
def detect_duplicates(recipes, title_threshold=0.8, ingredient_threshold=0.7):
    """Group recipes that appear to be duplicates based on title and ingredients"""
    groups = defaultdict(list)
    processed = set()
    
    # First group by post_id (to catch files with same ID but different prefixes)
    id_groups = defaultdict(list)
    for recipe in recipes:
        post_id = recipe.get("post_id", "")
        if post_id:
            id_groups[post_id].append(recipe)
    
    print(f"Grouped recipes by post_id: found {len(id_groups)} unique post IDs")
    print(f"Recipes with multiple files with same post_id: {sum(1 for recipes in id_groups.values() if len(recipes) > 1)}")
    
    # Process groups with same post_id first
    group_counter = 0
    for post_id, id_recipes in id_groups.items():
        if len(id_recipes) > 1:
            # Create a group for recipes with the same post_id
            group_key = f"group_{group_counter}"
            for recipe in id_recipes:
                groups[group_key].append(recipe)
                processed.add(recipe["file_name"])
            group_counter += 1
            print(f"Created duplicate group {group_key} for post_id {post_id} with {len(id_recipes)} files")
    
    print(f"After grouping by post_id: {len(processed)} files processed, {len(recipes) - len(processed)} remaining")
    
    # Now check for title and ingredient similarity among remaining recipes
    for i, recipe1 in enumerate(recipes):
        if recipe1["file_name"] in processed:
            continue
            
        title1 = recipe1.get("title", "") or recipe1.get("schema", {}).get("name", "")
        ingredients1 = " ".join(recipe1.get("schema", {}).get("recipeIngredient", []))
        
        # Create a group for this recipe
        group_key = f"group_{group_counter}"
        group_counter += 1
        groups[group_key].append(recipe1)
        processed.add(recipe1["file_name"])
        
        # Track duplicates found for this group
        duplicates_in_group = 0
        
        # Check all other recipes for similarity
        for recipe2 in recipes:
            if recipe2["file_name"] in processed:
                continue
                
            title2 = recipe2.get("title", "") or recipe2.get("schema", {}).get("name", "")
            ingredients2 = " ".join(recipe2.get("schema", {}).get("recipeIngredient", []))
            
            # Calculate similarities
            title_similarity = calculate_similarity(title1, title2)
            ingredient_similarity = calculate_similarity(ingredients1, ingredients2)
            
            # If either title or ingredients are very similar, consider it a duplicate
            if title_similarity >= title_threshold or ingredient_similarity >= ingredient_threshold:
                print(f"Found duplicate: '{recipe1['file_name']}' and '{recipe2['file_name']}'")
                print(f"  - Title similarity: {title_similarity:.2f}, Ingredient similarity: {ingredient_similarity:.2f}")
                groups[group_key].append(recipe2)
                processed.add(recipe2["file_name"])
                duplicates_in_group += 1
        
        if duplicates_in_group > 0:
            print(f"Group {group_key}: Found {duplicates_in_group} duplicates for '{title1}'")
    
    # Filter out groups with only one recipe (no duplicates)
    duplicate_groups = {k: v for k, v in groups.items() if len(v) > 1}
    single_recipes = []
    
    # Collect all recipes that are not part of any duplicate group
    for group, recipes_in_group in groups.items():
        if len(recipes_in_group) == 1:
            single_recipes.append(recipes_in_group[0])
    
    print(f"Final stats: {len(duplicate_groups)} duplicate groups, {len(single_recipes)} unique recipes")
    for group, recipes_in_group in duplicate_groups.items():
        titles = [r.get("title", "") or r.get("schema", {}).get("name", "") for r in recipes_in_group]
        print(f"Group {group}: {len(recipes_in_group)} recipes - {titles[0]}")
    
    return duplicate_groups, single_recipes

# Merge two duplicate recipes
def merge_recipes(recipe_list):
    """Merge multiple recipes into one, keeping the most complete information"""
    if not recipe_list:
        return None
        
    # Sort recipes by completeness
    sorted_recipes = sorted(recipe_list, key=calculate_completeness, reverse=True)
    
    # Start with the most complete recipe as the base
    base_recipe = sorted_recipes[0]
    merged_recipe = json.loads(json.dumps(base_recipe))  # Deep copy
    
    # If there's only one recipe, just return it
    if len(sorted_recipes) == 1:
        return merged_recipe
        
    # Merge with other recipes
    for recipe in sorted_recipes[1:]:
        schema_base = merged_recipe.get("schema", {})
        schema_other = recipe.get("schema", {})
        
        # Merge ingredients (add missing ingredients)
        base_ingredients = set(schema_base.get("recipeIngredient", []))
        other_ingredients = set(schema_other.get("recipeIngredient", []))
        all_ingredients = list(base_ingredients.union(other_ingredients))
        if all_ingredients:
            merged_recipe["schema"]["recipeIngredient"] = sorted(all_ingredients)
        
        # Use the longer description if available
        base_desc = schema_base.get("description", "")
        other_desc = schema_other.get("description", "")
        if len(other_desc) > len(base_desc):
            merged_recipe["schema"]["description"] = other_desc
            
        # Merge tags
        base_tags = set(schema_base.get("tags", []))
        other_tags = set(schema_other.get("tags", []))
        all_tags = list(base_tags.union(other_tags))
        if all_tags:
            merged_recipe["schema"]["tags"] = sorted(all_tags)
            
        # Merge keywords
        base_keywords = schema_base.get("keywords", "")
        other_keywords = schema_other.get("keywords", "")
        if len(other_keywords) > len(base_keywords):
            merged_recipe["schema"]["keywords"] = other_keywords
            
        # Merge suitable diets
        base_diets = set(schema_base.get("suitableForDiet", []))
        other_diets = set(schema_other.get("suitableForDiet", []))
        all_diets = list(base_diets.union(other_diets))
        if all_diets:
            merged_recipe["schema"]["suitableForDiet"] = sorted(all_diets)
    
    # Create a new file name based on the original name but with "merged_" prefix
    base_filename = base_recipe["file_name"]
    merged_recipe["file_name"] = f"merged_{base_filename}"
    merged_recipe["original_files"] = [r["file_name"] for r in recipe_list]
    
    return merged_recipe

# Generate report
def generate_csv_report(duplicate_groups, output_file="result/duplicate_report.csv"):
    """Generate a CSV report of duplicate recipes"""
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Group", "Recipe Name", "File Name", "Completeness Score", "Published/Removed/Merged"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for group_id, recipes in duplicate_groups.items():
            # Sort recipes by completeness
            sorted_recipes = sorted(recipes, key=calculate_completeness, reverse=True)
            
            for i, recipe in enumerate(sorted_recipes):
                status = "Published" if i == 0 else "Removed"
                name = recipe.get("title", "") or recipe.get("schema", {}).get("name", "")
                
                writer.writerow({
                    "Group": group_id,
                    "Recipe Name": name,
                    "File Name": recipe["file_name"],
                    "Completeness Score": calculate_completeness(recipe),
                    "Published/Removed/Merged": status
                })
            
            # Add the merged recipe entry
            writer.writerow({
                "Group": group_id,
                "Recipe Name": f"MERGED: {sorted_recipes[0].get('title', '')}",
                "File Name": f"merged_{sorted_recipes[0]['file_name']}",
                "Completeness Score": "N/A",
                "Published/Removed/Merged": "Merged"
            })

def main():
    # Create necessary directories
    create_directories()
    
    # Load all recipes - use absolute path to be explicit
    print("Loading recipes...")
    recipes_dir = "/Users/je-dev/Documents/Repository/Healthyfied/HealthyfiedAutomator/recipes"
    recipes = load_recipes(recipes_dir)
    print(f"Loaded {len(recipes)} recipes.")
    
    # Detect duplicates
    print("Detecting duplicates...")
    duplicate_groups, single_recipes = detect_duplicates(recipes)
    print(f"Found {len(duplicate_groups)} groups of duplicates and {len(single_recipes)} unique recipes.")
    
    # Process and organize recipes
    print("Processing and organizing recipes...")
    for recipe in single_recipes:
        # Copy unique recipes to for_publishing
        shutil.copy2(
            recipe["file_path"], 
            os.path.join("result", "for_publishing", recipe["file_name"])
        )
    
    # Handle duplicate groups
    for group_id, recipe_group in duplicate_groups.items():
        # Sort by completeness
        sorted_group = sorted(recipe_group, key=calculate_completeness, reverse=True)
        
        # The most complete recipe goes to for_publishing
        shutil.copy2(
            sorted_group[0]["file_path"],
            os.path.join("result", "for_publishing", sorted_group[0]["file_name"])
        )
        
        # The rest go to removed_as_duplicates
        for recipe in sorted_group[1:]:
            shutil.copy2(
                recipe["file_path"],
                os.path.join("result", "removed_as_duplicates", recipe["file_name"])
            )
        
        # Create a merged version
        merged_recipe = merge_recipes(recipe_group)
        if merged_recipe:
            merged_file_path = os.path.join("result", "merged_recipes", merged_recipe["file_name"])
            with open(merged_file_path, "w", encoding="utf-8") as f:
                json.dump(merged_recipe, f, indent=2, ensure_ascii=False)
    
    # Generate report
    print("Generating CSV report...")
    generate_csv_report(duplicate_groups)
    
    print("Done! Check result/duplicate_report.csv for a summary of duplicates.")

if __name__ == "__main__":
    main() 