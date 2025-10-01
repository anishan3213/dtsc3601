import os, json, uuid, re
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from src.schema import ArticleList

# ---- Provided proxy-style client ----
ENDPOINT = os.getenv("AZURE_PROXY_ENDPOINT", "https://cdong1--azure-proxy-web-app.modal.run")
API_KEY = os.getenv("AZURE_PROXY_KEY", "supersecretkey")
DEPLOYMENT = os.getenv("AZURE_PROXY_DEPLOYMENT", "gpt-4o")

client = OpenAI(base_url=ENDPOINT, api_key=API_KEY)

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def make_id(title: str) -> str:
    return f"{'-'.join(title.lower().split())[:48]}-{uuid.uuid4().hex[:8]}"

def call_llm(messages: List[Dict[str, Any]], *, json_mode: bool = False) -> str:
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    resp = client.chat.completions.create(
        model=DEPLOYMENT, messages=messages, temperature=0, **kwargs
    )
    return resp.choices[0].message.content

# ---- 1) Parse the blob into (title, url) lines (ignore the 3-line header) ----
LINE_RE = re.compile(r"^\s*\d+\.\s+(?P<title>.*?)\s+—\s+(?P<url>\S+)", re.UNICODE)

def extract_story_lines(blob: str, max_items: int = 50) -> List[Tuple[str, str]]:
    lines = blob.splitlines()
    # skip header (first blank line)
    try:
        first_blank = lines.index("")
        content = lines[first_blank + 1 :]
    except ValueError:
        content = lines

    items: List[Tuple[str, str]] = []
    for ln in content:
        m = LINE_RE.match(ln)
        if not m:
            continue
        title = m.group("title").strip()
        url = m.group("url").strip()
        if title:
            items.append((title, url))
        if len(items) >= max_items:
            break
    return items

# ---- 2) Summarize in batches with the LLM (JSON output, 1 summary per input) ----
BATCH_SIZE = 10

def summarize_batch(pairs: List[Tuple[str,str]]) -> List[str]:
    """
    pairs = [(title, url), ...]; returns parallel list of summaries.
    """
    sys = (
        "You write concise, factual 1–2 sentence summaries of tech news items.\n"
        "If details are unknown from title/URL alone, keep it high-level and do not fabricate."
    )
    user_obj = {
        "items": [{"title": t, "url": u} for (t, u) in pairs],
        "rules": [
            "Return JSON ONLY as {'summaries': ['...', '...', ...]}",
            "Length must equal input length",
            "No links in the summary; just text",
        ],
    }
    raw = call_llm(
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": json.dumps(user_obj)},
        ],
        json_mode=True,
    )
    data = json.loads(raw)
    summaries = data.get("summaries", [])
    # Fallback if model gives fewer items
    if len(summaries) != len(pairs):
        # pad with title-only summaries
        missing = len(pairs) - len(summaries)
        summaries += [p[0] for p in pairs[len(summaries):len(summaries)+missing]]
    return summaries

def structure_blob(blob_path: str, source_url: str | None = None) -> dict:
    """
    End-to-end: parse blob -> summarize in batches -> assemble full JSON -> validate -> return JSON-safe dict
    """
    blob = read_text(blob_path)
    extracted_at = datetime.now(timezone.utc).isoformat()

    pairs = extract_story_lines(blob, max_items=50)  # ~30 on HN front page
    if not pairs:
        # last-resort single-item (so assignment still produces JSON)
        fallback = {
            "items": [{
                "id": make_id("hacker-news-snapshot"),
                "title": "Hacker News snapshot",
                "summary": "No story lines were parsed from the blob.",
                "source_url": source_url or "https://news.ycombinator.com/",
                "extracted_at": extracted_at,
            }]
        }
        return fallback

    # summarize in batches
    summaries: List[str] = []
    for i in range(0, len(pairs), BATCH_SIZE):
        chunk = pairs[i:i+BATCH_SIZE]
        summaries.extend(summarize_batch(chunk))

    # assemble records
    records = []
    for (title, url), summary in zip(pairs, summaries):
        records.append({
            "id": make_id(title),
            "title": title,
            "summary": summary,
            "source_url": url or (source_url or None),
            "extracted_at": extracted_at,
        })

    payload = {"items": records}

    # Validate with Pydantic (converts to proper types)
    articles = ArticleList.model_validate(payload)

    # Make JSON-safe (HttpUrl -> str)
    safe_items = [item.model_dump(mode="json") for item in articles.items]
    return {"items": safe_items}

# Optional: quick test
if __name__ == "__main__":
    import glob, os
    base = os.path.dirname(__file__)
    latest = sorted(glob.glob(os.path.join(base, "..", "data", "raw_blob_*.txt")))
    if not latest:
        print("No blobs; run: python -m src.collector")
    else:
        out = structure_blob(latest[-1], source_url="https://news.ycombinator.com/")
        print(json.dumps(out, indent=2))
