import pandas as pd
import random
from datetime import datetime, timedelta

colors = ["red", "blue", "green", "black", "white", "yellow", "purple", "orange", "pink", "gray", "brown", "navy"]
sizes = ["XS", "S", "M", "L", "XL", "XXL"]
product_types = ["T-shirt", "Sweater", "Jeans", "Jacket", "Sneakers", "Boots", "Dress", "Skirt", "Cap", "Backpack", "Watch", "Sunglasses"]
adjectives = ["Classic", "Modern", "Vintage", "Stylish", "Elegant", "Sporty", "Casual", "Premium", "Lightweight", "Durable", "Comfort", "Soft"]
materials = ["cotton", "leather", "polyester", "wool", "denim", "silk", "synthetic", "canvas", "nylon"]
words = [
    "comfortable", "breathable", "waterproof", "lightweight", "stretch", "durable", "soft", "classic", "modern",
    "design", "perfect", "everyday", "travel", "outdoor", "urban", "minimal", "luxury", "affordable", "easy-care",
    "machine-washable", "handmade", "eco-friendly", "limited", "edition", "adjustable", "secure", "stylish", "versatile"
]

def random_name():
    return f"{random.choice(adjectives)} {random.choice(product_types)}"

def random_description(sentences=2):
    parts = []
    for _ in range(sentences):
        n = random.randint(8, 16)
        sentence = " ".join(random.choice(words + materials + adjectives) for _ in range(n)).capitalize() + "."
        parts.append(sentence)
    return " ".join(parts)

def random_created_date(start_year=2019, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 10, 9)
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86399)
    dt = start + timedelta(days=random_days, seconds=random_seconds)
    return dt.isoformat()

N = 10000
items = []
for i in range(N):
    item = {
        "id": i + 1,
        "name": random_name(),
        "color": random.choice(colors),
        "description": random_description(sentences=random.randint(1,3)),
        "size": random.choice(sizes),
        "price": round(random.uniform(5.0, 999.99), 2),
        "created_date": random_created_date()
    }
    items.append(item)

df = pd.DataFrame(items)

out_csv = "items_10000.csv"
out_json = "items_10000.json"
df.to_csv(out_csv, index=False)
df.to_json(out_json, orient="records", lines=True)

print("Sample 10 Fake Items")
print("=" * 50)
print(df.head(10).to_string(index=False))

print(f"\nSaved {len(df)} items to:")
print(f"CSV: {out_csv}")
print(f"JSON (ndjson): {out_json}")
print(f"IDs range from {df['id'].min()} to {df['id'].max()}")