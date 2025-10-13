import json
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from dateutil import parser
import re

INPUT_FILE = "exported_items.json"
PINECONE_API_KEY = ""
INDEX_NAME = "items-embeddings"
BATCH_SIZE = 500
MODEL_NAME = "all-MiniLM-L6-v2"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    items = json.load(f)
print(f"Đã đọc {len(items)} items từ file {INPUT_FILE}")

for item in items:
    cd = item.get("created_date")
    if cd is None:
        continue

    try:
        if isinstance(cd, (int, float)):
            item["created_date"] = int(cd)
        elif isinstance(cd, dict) and "$date" in cd:
            dt = parser.isoparse(cd["$date"])
            item["created_date"] = int(dt.timestamp() * 1000)
        elif isinstance(cd, str):
            dt = parser.isoparse(cd)
            item["created_date"] = int(dt.timestamp() * 1000)
        else:
            item["created_date"] = None
    except Exception as e:
        print(f"Warning: cannot parse created_date for item {item.get('id')}: {e}")
        item["created_date"] = None

texts = [
    f"{item.get('name','')} {item.get('description','')} color:{item.get('color','')} size:{item.get('size','')} price:{item.get('price','')}"
    for item in items
]

print("Đang load model embedding...")
model = SentenceTransformer(MODEL_NAME)
print("Đang tạo embeddings...")
embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = INDEX_NAME.lower()
existing_indexes = [idx["name"] for idx in pc.list_indexes()]

if index_name not in existing_indexes:
    print(f"Creating new index: {index_name}")
    pc.create_index(
        name=index_name,
        dimension=len(embeddings[0]),
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )
else:
    print(f"Index '{index_name}' already exists.")

index = pc.Index(index_name)

vectors = []
for i, (item, emb) in enumerate(zip(items, embeddings)):
    vec_id = str(item.get('_id', i))
    metadata = {k: v for k, v in item.items() if k != '_id'}
    vectors.append({
        "id": vec_id,
        "values": emb.tolist(),
        "metadata": metadata
    })

print("Đang upsert vào Pinecone...")
for i in range(0, len(vectors), BATCH_SIZE):
    batch = vectors[i:i+BATCH_SIZE]
    index.upsert(vectors=batch)
    print(f"Upserted {i + len(batch)}/{len(vectors)} items")

print(f"Hoàn tất: đã import {len(vectors)} items vào Pinecone index '{index_name}'")
