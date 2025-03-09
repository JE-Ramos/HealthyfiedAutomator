# Current Processing State

## Summary
- **Last Updated**: August 31, 2023
- **Batch Completed**: 15 of 32
- **Recipes Processed**: 190 of 351
- **Next Recipe**: recipe_0191.json
- **Next Publication Date**: 2024-08-31
- **Next Batch**: 16

## Last Processed Batch (Batch 15)
This batch included the following recipes, published with dates one day apart:

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

## How to Resume Processing

### Basic Resume (Recommended)
Run:
```
cd ghost
python3 publish_all_recipes.py
```

### Custom Resume
To resume from a specific index:
```
cd ghost
python3 -c "import publish_all_recipes; publish_all_recipes.publish_all_remaining_recipes(start_index=190)"
```

### Batch Processing Reference
- Batch 16 (recipes 191-200): start_index=190
- Batch 17 (recipes 201-210): start_index=200
- Batch 18 (recipes 211-220): start_index=210
- Batch 19 (recipes 221-230): start_index=220
- Batch 20 (recipes 231-240): start_index=230
- Batch 21 (recipes 241-250): start_index=240
- Batch 22 (recipes 251-260): start_index=250
- Batch 23 (recipes 261-270): start_index=260
- Batch 24 (recipes 271-280): start_index=270
- Batch 25 (recipes 281-290): start_index=280
- Batch 26 (recipes 291-300): start_index=290
- Batch 27 (recipes 301-310): start_index=300
- Batch 28 (recipes 311-320): start_index=310
- Batch 29 (recipes 321-330): start_index=320
- Batch 30 (recipes 331-340): start_index=330
- Batch 31 (recipes 341-350): start_index=340
- Batch 32 (recipe 351): start_index=350 