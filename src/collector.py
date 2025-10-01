# src/collector.py
import os, requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from pathlib import Path

HN_URL = "https://news.ycombinator.com/"

def ensure_dir(p: str): Path(p).mkdir(parents=True, exist_ok=True)
def write_text(path: str, text: str):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def collect_hackernews(out_dir: str | None = None, limit: int = 30) -> str:
    out_dir = out_dir or "data"
    ensure_dir(out_dir)

    r = requests.get(
        HN_URL,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (HN ETL student project)"}
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # HN stories appear as tr.athing + next tr (subtext)
    rows = soup.select("tr.athing")
    lines = []
    for athing in rows[:limit]:
        rank_el = athing.select_one(".rank")
        title_a = athing.select_one(".titleline a")
        rank = (rank_el.get_text(strip=True).rstrip(".")) if rank_el else ""
        title = title_a.get_text(strip=True) if title_a else ""
        url = title_a["href"] if title_a and title_a.has_attr("href") else ""

        # subtext row is the next sibling
        sub = athing.find_next_sibling("tr")
        points_el = sub.select_one(".score") if sub else None
        age_el = sub.select_one(".age") if sub else None
        points = points_el.get_text(strip=True) if points_el else ""
        age = age_el.get_text(strip=True) if age_el else ""

        if title:
            meta = " | ".join([m for m in (points, age) if m])
            line = f"{rank}. {title} — {url}"
            if meta:
                line += f"  | {meta}"
            lines.append(line)

    header = (
        "Hacker News — Front Page Snapshot\n"
        "Source: https://news.ycombinator.com/\n"
        f"Extracted at: {datetime.now(timezone.utc).isoformat()}\n\n"
    )
    blob = header + "\n".join(lines)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = f"{out_dir}/raw_blob_{ts}.txt"
    write_text(out_path, blob)
    return out_path

if __name__ == "__main__":
    print("Saved:", collect_hackernews())
