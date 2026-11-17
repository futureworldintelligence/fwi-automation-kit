import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you",
    "are", "was", "were", "have", "has", "had", "into", "once", "every",
    "a", "an", "in", "on", "of", "to", "is", "it", "as", "by", "or", "at",
}


def slugify(text: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9\s-]", "", text).strip().lower()
    return re.sub(r"[\s_-]+", "-", clean) or "untitled-post"


def extract_keywords(text: str, top_n: int = 6) -> list[str]:
    words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    return [word for word, _ in Counter(filtered).most_common(top_n)]


def package_markdown(md_path: Path) -> dict:
    raw = md_path.read_text(encoding="utf-8").strip()
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    title = md_path.stem.replace("_", " ").title()
    body_lines = []
    for line in lines:
        if line.startswith("# ") and title == md_path.stem.replace("_", " ").title():
            title = line[2:].strip()
        else:
            body_lines.append(line)

    body_text = " ".join(body_lines)
    words = body_text.split()
    word_count = len(words)
    read_minutes = max(1, math.ceil(word_count / 200))
    meta_desc = (body_text[:155].rsplit(" ", 1)[0] + "...") if len(body_text) > 155 else body_text
    keywords = extract_keywords(f"{title} {body_text}")
    slug = slugify(title)

    social_hook = (
        f"{title}\n\n"
        f"{body_lines[0] if body_lines else ''}\n\n"
        f"Key takeaways ({read_minutes} min read): " + ", ".join(f"#{k}" for k in keywords[:4])
    )

    return {
        "source_file": md_path.name,
        "title": title,
        "slug": slug,
        "word_count": word_count,
        "estimated_read_minutes": read_minutes,
        "meta_description": meta_desc,
        "seo_keywords": keywords,
        "social_post_ready": social_hook,
        "json_ld_schema": {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": meta_desc,
            "keywords": ", ".join(keywords),
            "wordCount": word_count,
        },
    }


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    drafts_dir = base_dir / "drafts"
    out_dir = base_dir / "published_bundles"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    md_files = sorted(drafts_dir.glob("*.md"))
    if not md_files:
        print(f"No .md drafts found in {drafts_dir}.")
        return

    packages = [package_markdown(p) for p in md_files]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_file = out_dir / f"content_bundle_{timestamp}.json"

    with out_file.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "total_articles": len(packages),
                "articles": packages,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Packaged {len(packages)} draft(s) -> {out_file}")
    for pkg in packages:
        print(f"  - Title: {pkg['title']}")
        print(f"    Slug:  /{pkg['slug']} ({pkg['estimated_read_minutes']} min read)")
        print(f"    Tags:  {', '.join(pkg['seo_keywords'])}")


if __name__ == "__main__":
    main()
