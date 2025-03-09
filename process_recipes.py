#!/usr/bin/env python3
import os
import json
import shutil
from datetime import datetime

def update_schema_format(recipe_data):
    """
    Update the schema to ensure it follows the latest recipe schema.org format
    """
    # Extract the schema from inside the recipe data
    if "schema" in recipe_data:
        schema = recipe_data["schema"]
    else:
        schema = recipe_data  # Assume it's already a schema

    # Ensure the schema has all the necessary properties and structure
    updated_schema = {
        "@context": "https://schema.org",
        "@type": "Recipe",
    }
    
    # Add 'name' from either schema name or recipe title
    updated_schema["name"] = schema.get("name", recipe_data.get("title", ""))
    
    # Set up default image array if not present
    updated_schema["image"] = schema.get("image", [
        f"https://healthyfied.me/images/recipes/{updated_schema['name'].lower().replace(' ', '-')}.jpg"
    ])
    
    # Add author information
    updated_schema["author"] = schema.get("author", {
        "@type": "Organization",
        "name": "Healthyfied"
    })
    
    # Add publisher information
    updated_schema["publisher"] = schema.get("publisher", {
        "@type": "Organization",
        "name": "Healthyfied",
        "logo": {
            "@type": "ImageObject",
            "url": "https://healthyfied.me/logo.jpg"
        }
    })
    
    # Add date published (use current date if not available)
    updated_schema["datePublished"] = schema.get("datePublished", datetime.now().strftime("%Y-%m-%d"))
    
    # Add description
    updated_schema["description"] = schema.get("description", "")
    
    # Add timing information
    updated_schema["prepTime"] = schema.get("prepTime", "")
    updated_schema["cookTime"] = schema.get("cookTime", "")
    updated_schema["totalTime"] = schema.get("totalTime", "")
    
    # Add keywords
    updated_schema["keywords"] = schema.get("keywords", "")
    
    # Add recipe yield
    updated_schema["recipeYield"] = schema.get("recipeYield", "")
    
    # Add recipe category if available (categorize based on tags if not specified)
    if "recipeCategory" in schema:
        updated_schema["recipeCategory"] = schema["recipeCategory"]
    else:
        tags = schema.get("tags", [])
        if "high-protein" in tags:
            updated_schema["recipeCategory"] = "High Protein"
        elif "low-carb" in tags:
            updated_schema["recipeCategory"] = "Low Carb"
        else:
            updated_schema["recipeCategory"] = "Main Course"
    
    # Add recipe cuisine (default to Filipino/Asian based on Healthyfied's focus)
    updated_schema["recipeCuisine"] = schema.get("recipeCuisine", "Filipino")
    
    # Determine cooking method from instructions if not specified
    if "cookingMethod" in schema:
        updated_schema["cookingMethod"] = schema["cookingMethod"]
    else:
        cooking_methods = ["Baking", "Frying", "Grilling", "Steaming", "Boiling", "Sautéing", "Roasting"]
        instructions_text = " ".join([step.get("text", "") for step in schema.get("recipeInstructions", [])])
        
        for method in cooking_methods:
            if method.lower() in instructions_text.lower():
                updated_schema["cookingMethod"] = method
                break
        else:
            updated_schema["cookingMethod"] = "Cooking"  # Default
    
    # Add nutrition information
    if "nutrition" in schema:
        updated_schema["nutrition"] = schema["nutrition"]
    
    # Add recipe ingredients
    updated_schema["recipeIngredient"] = schema.get("recipeIngredient", [])
    
    # Add recipe instructions
    instructions = schema.get("recipeInstructions", [])
    updated_instructions = []
    
    for i, step in enumerate(instructions):
        if isinstance(step, dict) and "@type" in step:
            # Already in HowToStep format, add name if missing
            if "name" not in step:
                step["name"] = f"Step {i+1}"
            updated_instructions.append(step)
        else:
            # Convert simple text to HowToStep format
            updated_instructions.append({
                "@type": "HowToStep",
                "name": f"Step {i+1}",
                "text": step if isinstance(step, str) else step.get("text", "")
            })
    
    updated_schema["recipeInstructions"] = updated_instructions
    
    # Add suitable diets
    updated_schema["suitableForDiet"] = schema.get("suitableForDiet", [])
    
    # Add tags to keywords if not already included
    if "tags" in schema and schema["tags"]:
        if "keywords" not in updated_schema or not updated_schema["keywords"]:
            updated_schema["keywords"] = ",".join(schema["tags"])
        elif not any(tag in updated_schema["keywords"] for tag in schema["tags"]):
            updated_schema["keywords"] += "," + ",".join(schema["tags"])
    
    return updated_schema

def process_recipes():
    """
    Process all recipes in the merged_recipes directory and save to final directory with incremental IDs
    """
    source_dir = "/Users/je-dev/Documents/Repository/Healthyfied/HealthyfiedAutomator/result/merged_recipes"
    target_dir = "/Users/je-dev/Documents/Repository/Healthyfied/HealthyfiedAutomator/final"
    
    # Get list of all merged recipe files
    recipe_files = [f for f in os.listdir(source_dir) if f.endswith('.json') and f != 'recipe_template.json']
    
    print(f"Found {len(recipe_files)} recipes to process")
    
    # Process each recipe
    for i, filename in enumerate(sorted(recipe_files), 1):
        # Create new filename with incremental ID
        new_filename = f"recipe_{i:04d}.json"
        
        # Load the recipe data
        with open(os.path.join(source_dir, filename), 'r', encoding='utf-8') as f:
            recipe_data = json.load(f)
        
        # Extract title for logging
        title = recipe_data.get('title', '')
        if not title and 'schema' in recipe_data:
            title = recipe_data['schema'].get('name', '')
        
        print(f"Processing [{i}/{len(recipe_files)}] {title} -> {new_filename}")
        
        # Update the schema format
        updated_schema = update_schema_format(recipe_data)
        
        # Save the updated schema to the final directory
        with open(os.path.join(target_dir, new_filename), 'w', encoding='utf-8') as f:
            json.dump(updated_schema, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    process_recipes()
    print("All recipes processed successfully!") 