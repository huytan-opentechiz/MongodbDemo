from pymongo import MongoClient
import pandas as pd
import numbers

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "items_database"
COLLECTION_NAME = "items"
EXPORT_JSON = "exported_items.json"
EXPORT_CSV = "exported_items.csv"
LIMIT = 5000

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

query = {
    "id": {"$gt": 100},
    "price": {"$gt": 100}
}

try:
    count = collection.count_documents(query)
except Exception as e:
    print("count_documents raised:", repr(e))
    count = None

print(f"Initial count for query {query}: {count}")

cursor = collection.find(query, projection=None).limit(LIMIT)
docs = list(cursor)
print(f"Fetched {len(docs)} documents (limit {LIMIT}).")

if len(docs) == 0:
    for d in collection.find().limit(5):
        print(" - _id:", d.get("_id"), "  type(_id):", type(d.get("_id")).__name__,
              "  id:", d.get("id"), "  type(id):", type(d.get("id")).__name__,
              "  price:", d.get("price"), "  type(price):", type(d.get("price")).__name__)
    raise SystemExit("Exit")

df = pd.DataFrame(docs)
if "_id" in df.columns:
    df["_id"] = df["_id"].apply(lambda x: str(x))

df.to_json(EXPORT_JSON, orient="records", indent=4, force_ascii=False)
df.to_csv(EXPORT_CSV, index=False)

print(f"\nExported {len(df)} items to '{EXPORT_JSON}' and '{EXPORT_CSV}'")
print("Sample exported ids (first 10):", df.get("id", pd.Series()).head(10).tolist())
