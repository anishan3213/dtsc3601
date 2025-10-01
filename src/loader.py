import os
import pandas as pd
from datetime import datetime, timezone
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def json_to_df(payload: dict) -> pd.DataFrame:
    return pd.DataFrame(payload["items"])

def upsert_articles(df: pd.DataFrame, table: str = "articles"):
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    df = df.copy()
    df["updated_at"] = datetime.now(timezone.utc).isoformat()
    recs = df.to_dict(orient="records")
    return sb.table(table).upsert(recs, on_conflict="id").execute()
