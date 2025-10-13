from fastapi import FastAPI, Body
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from datetime import datetime
import uvicorn

app = FastAPI()

model = SentenceTransformer('all-MiniLM-L6-v2')

PINECONE_API_KEY = "pcsk_5Js4sw_Tj2iwzYSoYcwBmNrPH11UN7iqjgShTcqQs9vcsZq7GSrBp34k4Q7brmbRB2VSnK"
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "items-embeddings"
index = pc.Index(index_name)

@app.post("/search")
def search_similarity(item: dict = Body(...)):
    text = str(item)
    
    query_emb = model.encode(text).tolist()

    results = index.query(vector=query_emb, top_k=10, include_metadata=True)

    filtered_items = []
    for match in results['matches']:
        metadata = match['metadata']
        create_date_val = metadata.get('created_date')
        if create_date_val is not None:
            try:
                if isinstance(create_date_val, (int, float)):
                    create_date = datetime.utcfromtimestamp(create_date_val / 1000)
                else:
                    create_date = datetime.strptime(str(create_date_val), '%Y-%m-%d')
                
                if create_date.year >= 2025:
                    filtered_items.append(metadata)
            except (ValueError, TypeError):
                pass

    return {"similar_items": filtered_items}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)