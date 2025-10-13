import pandas as pd
from pymongo import MongoClient, ASCENDING, DESCENDING
import json
from datetime import datetime

def import_to_mongodb():
    MONGO_URI = "mongodb://localhost:27017/" 
    DATABASE_NAME = "items_database"
    COLLECTION_NAME = "items"
    
    try:
        client = MongoClient(MONGO_URI)
        
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        print("📁 Reading items_10000.json...")
        with open('items_10000.json', 'r') as file:
            data = []
            for line in file:
                item = json.loads(line)
                item['created_date'] = datetime.fromisoformat(item['created_date'])
                data.append(item)
        
        result = collection.insert_many(data)
        
        print("🔨 Creating indexes...")
        collection.create_index("id")
        collection.create_index("name")
        collection.create_index("color")
        collection.create_index("size")
        collection.create_index("price")
        collection.create_index("created_date")
        collection.create_index({ "id": ASCENDING, "price": ASCENDING, "created_date": DESCENDING })

        
        print(f"Successfully inserted {len(result.inserted_ids)} documents")
        print(f"Database: {DATABASE_NAME}")
        print(f"Collection: {COLLECTION_NAME}")
        
        count = collection.count_documents({})
        print(f"Total documents in collection: {count}")
        
        sample = collection.find_one()
        print(f"\nSample document:")
        print(json.dumps(sample, indent=2, default=str))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import_to_mongodb()