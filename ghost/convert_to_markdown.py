#!/usr/bin/env python3
import json
import os
import glob
import re
from datetime import datetime

# Configuration
RECIPES_DIR = "../final"
MARKDOWN_DIR = "recipe-markdown"

# Ensure markdown directory exists
os.makedirs(MARKDOWN_DIR, exist_ok=True)

def sanitize_slug(text):
    """Convert text to a sanitized slug format."""
    # Replace spaces with hyphens and convert to lowercase
    slug = text.lower().replace(' ', '-')
    # Remove special characters
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug

def format_diet_tag(diet_url):
    """Convert schema.org diet URL to a readable tag."""
    if not diet_url.startswith("https://schema.org/"):
        return diet_url
    
    # Extract the diet name from the URL
    diet_name = diet_url.replace("https://schema.org/", "").replace("Diet", "")
    
    # Add spaces before capital letters
    diet_name = re.sub(r'([A-Z])', r' \1', diet_name).strip()
    
    return diet_name

def convert_recipe_to_markdown(recipe_data, output_path):
    """Convert recipe JSON to markdown format and save to file."""
    recipe_name = recipe_data.get('name', 'Untitled Recipe')
    description = recipe_data.get('description', '')
    
    # Extract key recipe details
    prep_time = recipe_data.get('prepTime', '').replace('PT', '')
    cook_time = recipe_data.get('cookTime', '').replace('PT', '')
    total_time = recipe_data.get('totalTime', '').replace('PT', '')
    
    yield_value = recipe_data.get('recipeYield', '')
    category = recipe_data.get('recipeCategory', '')
    cuisine = recipe_data.get('recipeCuisine', '')
    
    # Get dietary information
    suitable_diets = recipe_data.get('suitableForDiet', [])
    # Convert diet URLs to readable names
    readable_diets = [format_diet_tag(diet) for diet in suitable_diets]
    diet_labels = ', '.join(diet for diet in readable_diets) if readable_diets else 'None'
    
    # Extract nutrition information
    nutrition = recipe_data.get('nutrition', {})
    calories = nutrition.get('calories', 'N/A')
    carbs = nutrition.get('carbohydrateContent', 'N/A')
    protein = nutrition.get('proteinContent', 'N/A')
    fat = nutrition.get('fatContent', 'N/A')
    
    # Get ingredients and instructions
    ingredients = recipe_data.get('recipeIngredient', [])
    instructions = recipe_data.get('recipeInstructions', [])
    
    # Get the image URL (handle both string and list formats)
    image_url = recipe_data.get('image', '')
    if isinstance(image_url, list) and len(image_url) > 0:
        image_url = image_url[0]
    
    # Prepare the markdown content
    markdown = f"""---
title: "{recipe_name}"
date: {recipe_data.get('datePublished', '')}
slug: "recipe/{sanitize_slug(recipe_name)}"
tags: [{', '.join(f'"{tag}"' for tag in readable_diets)}]
---

# {recipe_name}

![{recipe_name}]({image_url})

*{description}*

## Details

- **Prep Time:** {prep_time}
- **Cook Time:** {cook_time}
- **Total Time:** {total_time}
- **Servings:** {yield_value}
- **Category:** {category}
- **Cuisine:** {cuisine}
- **Diet:** {diet_labels}

## Nutrition Information

- **Calories:** {calories}
- **Carbohydrates:** {carbs}
- **Protein:** {protein}
- **Fat:** {fat}

## Ingredients

"""
    
    # Add ingredients
    for ingredient in ingredients:
        markdown += f"- {ingredient}\n"
    
    markdown += "\n## Instructions\n\n"
    
    # Add instructions with ad block after middle instruction
    instruction_count = len(instructions)
    middle_index = instruction_count // 2
    
    for i, instruction in enumerate(instructions):
        step_text = instruction.get('text', '')
        markdown += f"{i+1}. {step_text}\n\n"
        
        # Insert ad block after the middle instruction
        if i == middle_index:
            markdown += """
<!-- Ad Block -->
<div class="ad-container">
    <p class="ad-label">Advertisement</p>
    <div class="ad-content">
        <!-- Ad code here -->
        <p>Support Healthyfied by checking out our sponsors</p>
    </div>
</div>
<!-- End Ad Block -->

"""
    
    # Add JSON-LD script (this will be embedded in the Ghost post's HTML)
    json_ld = f"""
<script type="application/ld+json">
{json.dumps(recipe_data, indent=2)}
</script>
"""
    
    # Add meta section for custom JSON-LD
    markdown += f"""
<!-- json+ld metadata -->
{json_ld}
"""
    
    # Write the markdown to file
    with open(output_path, 'w') as f:
        f.write(markdown)
    
    return output_path

def convert_all_recipes():
    """Process all JSON recipe files and convert them to markdown."""
    # Get all recipe JSON files
    recipe_files = sorted(glob.glob(os.path.join(RECIPES_DIR, "recipe_*.json")))
    
    if not recipe_files:
        print(f"No recipe files found in {RECIPES_DIR}")
        return
    
    print(f"Found {len(recipe_files)} recipe files to convert")
    
    successful_conversions = 0
    failed_conversions = 0
    
    for i, recipe_file in enumerate(recipe_files):
        print(f"Converting {i+1}/{len(recipe_files)}: {recipe_file}")
        
        try:
            # Load the recipe data
            with open(recipe_file, 'r') as f:
                recipe_data = json.load(f)
            
            # Create markdown filename
            filename = os.path.basename(recipe_file).replace('.json', '.md')
            markdown_path = os.path.join(MARKDOWN_DIR, filename)
            
            # Convert to markdown
            markdown_file = convert_recipe_to_markdown(recipe_data, markdown_path)
            
            print(f"  → Created: {markdown_path}")
            successful_conversions += 1
            
        except Exception as e:
            print(f"  → Error processing {recipe_file}: {str(e)}")
            failed_conversions += 1
    
    print(f"\nConversion complete.")
    print(f"Successfully converted: {successful_conversions}")
    print(f"Failed conversions: {failed_conversions}")
    print(f"Markdown files are saved in the {MARKDOWN_DIR} directory")

if __name__ == "__main__":
    print("Starting recipe conversion process...")
    print(f"- Reading recipes from: {RECIPES_DIR}")
    print(f"- Saving markdown files to: {MARKDOWN_DIR}")
    convert_all_recipes() 