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
        print("Successfully connected to MongoDB")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        print("Reading items_10000.json...")
        with open('items_10000.json', 'r') as file:
            data = []
            for line in file:
                item = json.loads(line)
                item['created_date'] = datetime.fromisoformat(item['created_date'])
                data.append(item)
        
        result = collection.insert_many(data)
        
        collection.create_index({ "price": ASCENDING, "id": ASCENDING })

        
        print(f"Successfully inserted {len(result.inserted_ids)} documents")
        print(f"Database: {DATABASE_NAME}")
        print(f"Collection: {COLLECTION_NAME}")
        
        count = collection.count_documents({})
        print(f"Total documents in collection: {count}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import_to_mongodb()