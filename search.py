from fastapi import FastAPI, Body
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from datetime import datetime
import uvicorn

app = FastAPI()

model = SentenceTransformer('all-MiniLM-L6-v2')

PINECONE_API_KEY = "pcsk_7LjB4V_JsWcdH3nGcLDm97sovM45zTXe51rDTE2ha6enHeAjqnMQ4P1bDU888d8vsENni2"
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "items-embeddings"
index = pc.Index(index_name)

@app.post("/search")
def search_similarity(item: dict = Body(...)):
    text = f"{item.get('name','')} {item.get('description','')} color:{item.get('color','')} size:{item.get('size','')} price:{item.get('price','')}"
    
    query_emb = model.encode(text).tolist()

    start_2025_ts = int(datetime(2025, 1, 1).timestamp() * 1000)

    results = index.query(
        vector=query_emb,
        top_k=10,
        include_metadata=True,
        filter={
            "created_date": {"$gte": start_2025_ts}
        }
    )

    similar_items = [match['metadata'] for match in results['matches']]

    return {"text": text, "similar_items": similar_items}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
