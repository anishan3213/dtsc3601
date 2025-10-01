import json
from src.loader import json_to_df, upsert_articles
from dotenv import load_dotenv

load_dotenv()

payload = json.load(open("data/structured.json","r",encoding="utf-8"))
df = json_to_df(payload)
print(df.head())
res = upsert_articles(df)
print("Upsert result:", res)
