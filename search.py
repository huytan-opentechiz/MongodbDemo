from fastapi import FastAPI, Body
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from datetime import datetime
from dateutil import parser
import uvicorn

app = FastAPI()

model = SentenceTransformer('all-MiniLM-L6-v2')

PINECONE_API_KEY = "YOUR_PINECONE_API_KEY"
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "items-embeddings"
index = pc.Index(index_name)

@app.post("/search")
def search_similarity(item: dict = Body(...)):
    text = str(item)
    
    query_emb = model.encode(text).tolist()

    results = index.query(vector=query_emb, top_k=10, include_metadata=True)

    start_2025_ts = int(datetime(2025, 1, 1).timestamp() * 1000)

    filtered_items = []
    for match in results['matches']:
        metadata = match.get('metadata', {})
        created_date_val = metadata.get('created_date')

        if created_date_val is not None:
            try:
                if isinstance(created_date_val, (int, float)):
                    if created_date_val >= start_2025_ts:
                        filtered_items.append(metadata)
                else:
                    dt = parser.isoparse(str(created_date_val))
                    if dt.year >= 2025:
                        filtered_items.append(metadata)
            except Exception:
                pass

    return {"similar_items": filtered_items}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
