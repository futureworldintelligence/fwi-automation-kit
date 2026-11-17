import html
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def load_config(base_dir: Path) -> dict:
    config_path = base_dir / "feeds.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing feeds config at {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def clean_html(raw_text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw_text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def fetch_feed(feed_name: str, url: str, max_items: int, keywords: list[str]) -> list[dict]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (SolopreneurOpportunityRadar/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml_bytes = resp.read()

    root = ET.fromstring(xml_bytes)
    items = root.findall(".//item")[:max_items]

    matches = []
    for item in items:
        title = clean_html(item.findtext("title", default=""))
        link = (item.findtext("link", default="") or "").strip()
        pub_date = (item.findtext("pubDate", default="") or "").strip()
        desc = clean_html(item.findtext("description", default=""))

        searchable = f"{title} {desc}".lower()
        matched_kws = [kw for kw in keywords if kw in searchable]

        if not keywords or matched_kws:
            matches.append({
                "source": feed_name,
                "title": title,
                "link": link,
                "published": pub_date,
                "matched_keywords": matched_kws,
                "snippet": desc[:180] + ("..." if len(desc) > 180 else ""),
            })
    return matches


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    config = load_config(base_dir)

    output_dir = base_dir / config.get("output_folder", "output_digests")
    output_dir.mkdir(parents=True, exist_ok=True)

    keywords = [kw.lower() for kw in config.get("include_keywords", [])]
    max_items = int(config.get("max_items_per_feed", 15))

    all_matches = []
    seen_links = set()

    for feed in config.get("feeds", []):
        name = feed.get("name", "Unnamed Feed")
        url = feed.get("url", "")
        if not url:
            continue
        print(f"Scanning: {name}...")
        try:
            entries = fetch_feed(name, url, max_items, keywords)
            for entry in entries:
                if entry["link"] not in seen_links:
                    seen_links.add(entry["link"])
                    all_matches.append(entry)
        except Exception as exc:
            print(f"  [Warning] Could not fetch {name}: {exc}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_out = output_dir / f"opportunities_{timestamp}.json"
    md_out = output_dir / f"digest_{timestamp}.md"

    with json_out.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "total_matches": len(all_matches),
                "opportunities": all_matches,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    lines = [
        f"# Daily Opportunity Radar ({datetime.now(timezone.utc).strftime('%Y-%m-%d UTC')})",
        f"**Total Matching Leads:** {len(all_matches)}\n",
    ]
    for idx, item in enumerate(all_matches, start=1):
        tags = ", ".join(f"`{k}`" for k in item["matched_keywords"]) or "`all`"
        lines.append(f"### {idx}. [{item['title']}]({item['link']})")
        lines.append(f"- **Source:** {item['source']} | **Tags:** {tags}")
        if item["snippet"]:
            lines.append(f"- **Summary:** {item['snippet']}")
        lines.append("")

    md_out.write_text("\n".join(lines), encoding="utf-8")

    print(f"\nDone! Found {len(all_matches)} matching item(s).")
    print(f"Markdown digest: {md_out}")
    print(f"JSON export:     {json_out}")


if __name__ == "__main__":
    main()
