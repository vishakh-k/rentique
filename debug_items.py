from pymongo import MongoClient
import os

client = MongoClient('mongodb+srv://vishakhkt:vishakh2003@cluster0.hkgog.mongodb.net/aurawear?retryWrites=true&w=majority')
db = client['aurawear_db']
items_collection = db['items']

items = items_collection.find({'category': {'$regex': '^Men', '$options': 'i'}})

print("--- Men's Items Categories ---")
for item in items:
    print(f"Name: {item.get('name')}, Category: {item.get('category')}")
