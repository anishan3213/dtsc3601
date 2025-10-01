import glob, json, os
from src.structurer import structure_blob

BASE_DIR = os.path.dirname(__file__)
data_path = os.path.join(BASE_DIR, "data", "raw_blob_*.txt")

latest_files = sorted(glob.glob(data_path))
if not latest_files:
    raise SystemExit("❌ No blobs found in data/. Run: python -m src.collector")

latest = latest_files[-1]
print(f"Using blob: {latest}")

payload = structure_blob(latest, source_url="https://news.ycombinator.com/")
print(json.dumps(payload, indent=2))

out_path = os.path.join(BASE_DIR, "data", "structured.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
print(f"✅ Wrote structured JSON to {out_path}")

