#!/usr/bin/env python3
"""
generate_and_import.py
- Calls OpenAI Chat Completions to generate NDJSON product items in batches
- Saves NDJSON file and imports into local MongoDB using pymongo (batch insert)
"""

import os
import time
import json
import requests
from pymongo import MongoClient, InsertOne

OPENAI_API_KEY = "OPENAI_API_KEY"
if not OPENAI_API_KEY:
    raise SystemExit("Set OPENAI_API_KEY environment variable before running.")

MODEL = "gpt-3.5-turbo"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}

TOTAL = 1000
BATCH = 2505
MAX_RETRY = 3
OUTFILE = "items_1000.ndjson"

# Mongo config
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "testdb"
COLLECTION = "items"

def make_prompt(start_id, count):
    prompt = f"""
You are a data generator. Produce EXACTLY {count} product items in NDJSON format (one JSON object per line, no surrounding array, no extra commentary).
Each item must have:
- id: integer (start from {start_id} and increment by 1)
- name: realistic product name (fashion/apparel/accessory)
- color: single color name from [red, blue, green, black, white, yellow, purple, orange, pink, gray, brown, navy]
- description: 1-2 sentences, 8-18 words each, containing material or feature words like "cotton, leather, breathable, waterproof, lightweight"
- size: one of ["XS","S","M","L","XL","XXL"]
- price: floating number with 2 decimals between 5.00 and 999.99 (use .xx format)
- created_date: ISO 8601 datetime string between 2022-01-01 and 2025-10-09 (example: "2024-07-12T14:23:00Z")

Requirements:
- Output EXACTLY {count} lines, each line a single JSON object.
- Do not output any explanatory text, code fences, or additional characters.
- Make sure all ids are unique and sequential from {start_id} to {start_id + count - 1}.
"""
    return prompt.strip()

def call_openai_chat(prompt, model=MODEL, timeout=60):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 2000  
    }
    resp = requests.post(OPENAI_URL, headers=HEADERS, json=body, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def write_lines_to_file(lines, outpath):
    with open(outpath, "a", encoding="utf-8") as f:
        for line in lines:
            f.write(line.rstrip() + "\n")

def parse_ndjson_text(text, expected_count):
    """
    Input text: multiple lines. Each line should be a JSON object.
    Returns list of parsed dicts.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    docs = []
    for i, ln in enumerate(lines):
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError as ex:
            raise ValueError(f"JSON decode error on line {i+1}: {ex}\nLine text: {ln[:200]}")
        docs.append(obj)
    if len(docs) != expected_count:
        raise ValueError(f"Expected {expected_count} objects but parsed {len(docs)}")
    return docs

def generate_batches(total=TOTAL, batch_size=BATCH):
    start = 1
    while start <= total:
        count = min(batch_size, total - start + 1)
        yield start, count
        start += count

def main():
    if os.path.exists(OUTFILE):
        print(f"Removing old {OUTFILE}")
        os.remove(OUTFILE)

    all_docs = []
    for start_id, count in generate_batches(TOTAL, BATCH):
        prompt = make_prompt(start_id, count)
        for attempt in range(1, MAX_RETRY+1):
            try:
                print(f"Requesting items {start_id}..{start_id+count-1} (attempt {attempt})...")
                content = call_openai_chat(prompt)
                docs = parse_ndjson_text(content, expected_count=count)
                write_lines_to_file([json.dumps(d, ensure_ascii=False) for d in docs], OUTFILE)
                all_docs.extend(docs)
                print(f"Got {len(docs)} items.")
                break
            except Exception as e:
                print(f"Batch {start_id}-{start_id+count-1} failed on attempt {attempt}: {e}")
                if attempt == MAX_RETRY:
                    raise
                print("Retrying after backoff...")
                time.sleep(2 ** attempt)

    print(f"Total collected items: {len(all_docs)}. Now inserting into MongoDB...")

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    col = db[COLLECTION]
    col.create_index("id", unique=True)

    ops = []
    BATCH_INSERT = 500
    for i, doc in enumerate(all_docs, 1):
        try:
            doc["id"] = int(doc["id"])
        except Exception:
            pass
        if "price" in doc:
            try:
                doc["price"] = float(doc["price"])
            except Exception:
                pass
        ops.append(InsertOne(doc))
        if i % BATCH_INSERT == 0 or i == len(all_docs):
            res = col.bulk_write(ops, ordered=False)
            print(f"Inserted batch up to {i}. inserted_count ~ {res.inserted_count if hasattr(res,'inserted_count') else 'unknown'}")
            ops = []

    print("Done. Items stored in MongoDB collection:", f"{DB_NAME}.{COLLECTION}")

if __name__ == "__main__":
    main()
