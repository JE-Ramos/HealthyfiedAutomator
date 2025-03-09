#!/usr/bin/env python3
import json
import os
import sys

# Import our conversion function
from recipe_publisher import convert_recipe_to_markdown

# Load a sample recipe
with open('../final/recipe_0001.json', 'r') as f:
    recipe_data = json.load(f)

# Convert to markdown
output_path = 'sample_recipe.md'
markdown_file = convert_recipe_to_markdown(recipe_data, output_path)

# Display the markdown content
print('\nGenerated markdown:')
print('-' * 60)
with open(output_path, 'r') as f:
    print(f.read())
print('-' * 60)

print(f"\nMarkdown file saved to: {os.path.abspath(output_path)}") 