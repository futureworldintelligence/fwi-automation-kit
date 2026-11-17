import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from pypdf import PdfReader


def load_config(base_dir: Path) -> dict:
    config_path = base_dir / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing config file at {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def process_pdf(pdf_path: Path, config: dict) -> dict:
    reader = PdfReader(str(pdf_path))
    keywords = [kw.lower() for kw in config.get("keyword_tags", [])]

    pages_data = []
    matched_tags = set()
    total_words = 0

    for idx, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        words = text.split()
        total_words += len(words)

        lower_text = text.lower()
        page_matches = [kw for kw in keywords if kw in lower_text]
        matched_tags.update(page_matches)

        page_entry = {
            "page_number": idx,
            "word_count": len(words),
            "matched_keywords": page_matches,
        }
        if config.get("include_full_text", True):
            page_entry["text"] = text
        pages_data.append(page_entry)

    metadata = {}
    if config.get("extract_metadata", True) and reader.metadata:
        metadata = {
            "title": reader.metadata.get("/Title", ""),
            "author": reader.metadata.get("/Author", ""),
            "creator": reader.metadata.get("/Creator", ""),
        }

    return {
        "file_name": pdf_path.name,
        "page_count": len(reader.pages),
        "total_words": total_words,
        "matched_keywords": sorted(matched_tags),
        "metadata": metadata,
        "pages": pages_data,
    }


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    config = load_config(base_dir)

    input_dir = base_dir / config.get("input_folder", "input_pdfs")
    output_dir = base_dir / config.get("output_folder", "output_data")
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {input_dir}. Drop PDFs there and re-run.")
        return

    results = []
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}...")
        results.append(process_pdf(pdf_path, config))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_out = output_dir / f"extracted_docs_{timestamp}.json"
    csv_out = output_dir / f"summary_{timestamp}.csv"

    with json_out.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "total_files": len(results),
                "documents": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    with csv_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["file_name", "page_count", "total_words", "matched_keywords", "title"])
        for doc in results:
            writer.writerow([
                doc["file_name"],
                doc["page_count"],
                doc["total_words"],
                ", ".join(doc["matched_keywords"]),
                doc["metadata"].get("title", ""),
            ])

    print(f"\nDone! Processed {len(results)} PDF(s).")
    print(f"JSON saved to: {json_out}")
    print(f"CSV saved to:  {csv_out}")


if __name__ == "__main__":
    main()
