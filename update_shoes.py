from pymongo import MongoClient
import os

client = MongoClient('mongodb+srv://vishakhkt:vishakh2003@cluster0.hkgog.mongodb.net/aurawear?retryWrites=true&w=majority')
db = client['aurawear_db']
items_collection = db['items']

# Find items that are shoes but categorized as Accessories (or potentially just update all shoes)
query = {
    'name': {'$regex': 'shoe', '$options': 'i'},
    'category': {'$regex': 'Accessories', '$options': 'i'}
}

items_to_update = items_collection.find(query)

count = 0
for item in items_to_update:
    print(f"Updating item: {item['name']} (Category: {item['category']})")
    
    # Preserve the main category prefix (e.g. "Men - ")
    parts = item['category'].split('-')
    if len(parts) > 1:
        main_cat = parts[0].strip()
        new_category = f"{main_cat} - Footwear"
    else:
        new_category = "Footwear" # Fallback if format is unexpected
        
    items_collection.update_one({'_id': item['_id']}, {'$set': {'category': new_category}})
    print(f"Updated to: {new_category}")
    count += 1

print(f"Total items updated: {count}")
