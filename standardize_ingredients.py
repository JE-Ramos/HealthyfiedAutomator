#!/usr/bin/env python3
import os
import json
import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

# Unit conversion factors to metric
UNIT_CONVERSIONS = {
    # Volume
    'tsp': 5,  # 1 tsp = 5 ml
    'teaspoon': 5,
    'tbsp': 15,  # 1 tbsp = 15 ml
    'tablespoon': 15,
    'cup': 240,  # 1 cup = 240 ml
    'fl oz': 30,  # 1 fl oz = 30 ml
    'fluid ounce': 30,
    'pint': 473,  # 1 pint = 473 ml
    'quart': 946,  # 1 quart = 946 ml
    'gallon': 3785,  # 1 gallon = 3785 ml
    
    # Weight
    'oz': 28,  # 1 oz = 28 g
    'ounce': 28,
    'lb': 454,  # 1 lb = 454 g
    'pound': 454,
}

# Standardize unit names
UNIT_STANDARDIZATION = {
    # Volume
    'ml': 'ml',
    'milliliter': 'ml',
    'milliliters': 'ml',
    'millilitre': 'ml',
    'millilitres': 'ml',
    'mL': 'ml',
    'l': 'l',
    'liter': 'l',
    'liters': 'l',
    'litre': 'l',
    'litres': 'l',
    'L': 'l',
    
    # Weight
    'g': 'g',
    'gram': 'g',
    'grams': 'g',
    'gram(s)': 'g',
    'gm': 'g',
    'kg': 'kg',
    'kilogram': 'kg',
    'kilograms': 'kg',
    'kilo': 'kg',
    'kilos': 'kg',
    
    # Non-metric to keep
    'piece': 'piece',
    'pieces': 'piece',
    'slice': 'slice',
    'slices': 'slice',
    'whole': 'whole',
    'clove': 'clove',
    'cloves': 'clove',
    'pinch': 'pinch',
    'pinches': 'pinch',
    'dash': 'dash',
    'dashes': 'dash',
    'large': 'large',
    'medium': 'medium',
    'small': 'small',
    'bunch': 'bunch',
    'bunches': 'bunch',
    'sprig': 'sprig',
    'sprigs': 'sprig',
    'leaf': 'leaf',
    'leaves': 'leaf',
    'head': 'head',
    'heads': 'head',
    'stalk': 'stalk',
    'stalks': 'stalk',
    'package': 'package',
    'packages': 'package',
    'can': 'can',
    'cans': 'can',
    'scoop': 'scoop',
    'scoops': 'scoop',
    'drop': 'drop',
    'drops': 'drop',
}

def clean_quantity(quantity_str):
    """Clean and standardize quantity string, converting fractions to decimals."""
    # Handle common fractions
    quantity_str = (quantity_str.strip()
                    .replace('½', '0.5')
                    .replace('⅓', '0.333')
                    .replace('⅔', '0.667')
                    .replace('¼', '0.25')
                    .replace('¾', '0.75')
                    .replace('⅕', '0.2')
                    .replace('⅖', '0.4')
                    .replace('⅗', '0.6')
                    .replace('⅘', '0.8'))
    
    # Handle fraction format like "1/2"
    if '/' in quantity_str:
        parts = quantity_str.split('/')
        if len(parts) == 2:
            try:
                numerator = float(parts[0].strip())
                denominator = float(parts[1].strip())
                if denominator != 0:
                    quantity_str = str(numerator / denominator)
            except ValueError:
                pass
    
    # Remove any text that isn't a number or decimal point
    quantity_str = re.sub(r'[^\d.]', '', quantity_str)
    
    try:
        # Convert to Decimal and round to 2 decimal places
        quantity = Decimal(quantity_str)
        quantity = quantity.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Convert to integer if it's a whole number
        if quantity == quantity.to_integral_value():
            return str(int(quantity))
        else:
            return str(quantity)
    except (InvalidOperation, ValueError):
        return quantity_str

def extract_unit_and_ingredient(ingredient_part):
    """Extract unit and ingredient name from the ingredient part."""
    # Find the first word which is likely the unit
    match = re.match(r'^([\w()-]+)(?:\s+(.*))?$', ingredient_part.strip())
    
    if match:
        unit = match.group(1).lower().strip()
        remaining = match.group(2) or ''
        
        # Check if unit exists in our standardization map
        if unit in UNIT_STANDARDIZATION:
            return UNIT_STANDARDIZATION[unit], remaining.strip()
        
        # Check for plurals or variations
        for std_unit, std_value in UNIT_STANDARDIZATION.items():
            if unit.startswith(std_unit) or unit.endswith(std_unit):
                return std_value, remaining.strip()
        
        # If the unit isn't recognized, assume the first word might be part of the ingredient
        return '', f"{unit} {remaining}".strip()
    
    return '', ingredient_part.strip()

def convert_to_metric(quantity, unit):
    """Convert the quantity from imperial to metric."""
    try:
        quantity_decimal = Decimal(quantity)
    except InvalidOperation:
        return quantity, unit
    
    # Convert unit to lowercase and remove plurals
    unit_lower = unit.lower().rstrip('s')
    
    # Check if unit needs conversion
    if unit_lower in UNIT_CONVERSIONS:
        conversion_factor = UNIT_CONVERSIONS[unit_lower]
        
        # Determine target unit (volume or weight)
        if unit_lower in ['tsp', 'teaspoon', 'tbsp', 'tablespoon', 'cup', 'fl oz', 'fluid ounce', 'pint', 'quart', 'gallon']:
            # Convert to milliliters
            converted_quantity = quantity_decimal * Decimal(str(conversion_factor))
            
            # Convert to liters if >= 1000 ml
            if converted_quantity >= 1000:
                converted_quantity = converted_quantity / 1000
                return str(converted_quantity.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 'l'
            else:
                return str(converted_quantity.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)), 'ml'
        else:
            # Convert to grams
            converted_quantity = quantity_decimal * Decimal(str(conversion_factor))
            
            # Convert to kilograms if >= 1000 g
            if converted_quantity >= 1000:
                converted_quantity = converted_quantity / 1000
                return str(converted_quantity.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), 'kg'
            else:
                return str(converted_quantity.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)), 'g'
    
    # No conversion needed
    return quantity, unit

def parse_ingredient(ingredient_str):
    """Parse ingredient string and return standardized format."""
    # Common patterns in the ingredient strings
    patterns = [
        # Pattern: "quantity unit, ingredient"
        r'^([\d./]+)\s*([a-zA-Z()]+)[.,]\s*(.+)$',
        # Pattern: "quantity unit ingredient"
        r'^([\d./]+)\s*([a-zA-Z()]+)\s+(.+)$',
        # Pattern: "ingredient, quantity unit"
        r'^(.+?)[.,]\s*([\d./]+)\s*([a-zA-Z()]+)$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, ingredient_str.strip())
        if match:
            if len(match.groups()) == 3:
                # Check which group is likely quantity, unit, and ingredient
                if match.group(1).replace('.', '').replace('/', '').isdigit():
                    # First group is quantity
                    quantity = clean_quantity(match.group(1))
                    unit_and_ingredient = f"{match.group(2)} {match.group(3)}"
                elif match.group(2).replace('.', '').replace('/', '').isdigit():
                    # Second group is quantity
                    quantity = clean_quantity(match.group(2))
                    unit_and_ingredient = f"{match.group(3)} {match.group(1)}"
                else:
                    # Handle other cases or unknown format
                    print(f"  Warning: Complex format - {ingredient_str}")
                    return ingredient_str
                
                unit, ingredient_name = extract_unit_and_ingredient(unit_and_ingredient)
                
                # Convert to metric if non-metric unit
                if unit and unit in UNIT_CONVERSIONS:
                    quantity, unit = convert_to_metric(quantity, unit)
                
                # Return standardized format
                return f"{quantity} {unit} {ingredient_name}".strip()
    
    # Try a more flexible approach for ingredients that didn't match the patterns
    parts = ingredient_str.split(',')
    
    if len(parts) >= 2:
        # Try to find the quantity part
        quantity_part = None
        ingredient_part = None
        
        for part in parts:
            if re.search(r'\d', part):
                # This part contains numbers, likely quantity + unit
                quantity_part = part.strip()
            else:
                # Likely ingredient name
                if ingredient_part:
                    ingredient_part += ", " + part.strip()
                else:
                    ingredient_part = part.strip()
        
        if quantity_part and ingredient_part:
            # Further split quantity part into quantity and unit
            quantity_match = re.match(r'^([\d./]+)\s*([a-zA-Z()]+)?$', quantity_part)
            
            if quantity_match:
                quantity = clean_quantity(quantity_match.group(1))
                unit = quantity_match.group(2) if quantity_match.group(2) else ''
                
                # Standardize unit
                if unit:
                    unit = unit.lower().strip()
                    if unit in UNIT_STANDARDIZATION:
                        unit = UNIT_STANDARDIZATION[unit]
                
                # Convert to metric if non-metric unit
                if unit and unit in UNIT_CONVERSIONS:
                    quantity, unit = convert_to_metric(quantity, unit)
                
                # Return standardized format
                return f"{quantity} {unit} {ingredient_part}".strip()
    
    # If we can't parse it, return original
    print(f"  Warning: Could not parse - {ingredient_str}")
    return ingredient_str

def standardize_ingredients(recipes_dir):
    """Process all recipes in the directory and standardize ingredients."""
    recipe_files = [f for f in os.listdir(recipes_dir) if f.endswith('.json') and f != 'recipe_template.json']
    print(f"Found {len(recipe_files)} recipes to process")
    
    for i, filename in enumerate(sorted(recipe_files), 1):
        filepath = os.path.join(recipes_dir, filename)
        
        # Load recipe
        with open(filepath, 'r', encoding='utf-8') as f:
            recipe = json.load(f)
        
        # Get recipe name for logging
        recipe_name = recipe.get('name', filename)
        print(f"[{i}/{len(recipe_files)}] Processing {recipe_name}")
        
        # Process ingredients
        if 'recipeIngredient' in recipe:
            original_ingredients = recipe['recipeIngredient']
            standardized_ingredients = []
            
            for ingredient in original_ingredients:
                standardized = parse_ingredient(ingredient)
                standardized_ingredients.append(standardized)
                
                # Print out changes for reference
                if standardized != ingredient:
                    print(f"  Changed: '{ingredient}' -> '{standardized}'")
            
            # Update recipe with standardized ingredients
            recipe['recipeIngredient'] = standardized_ingredients
            
            # Save updated recipe
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(recipe, f, indent=2, ensure_ascii=False)
    
    print("All recipes processed successfully!")

if __name__ == "__main__":
    recipes_dir = "/Users/je-dev/Documents/Repository/Healthyfied/HealthyfiedAutomator/final"
    standardize_ingredients(recipes_dir) 