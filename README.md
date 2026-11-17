# The Solopreneur's Local AI & Automation Starter Kit (v1.0)

Three lightweight, privacy-first Python + JSON micro-tools that run 100% locally on your computer—no monthly SaaS subscriptions, no API keys required.

## What's Inside
1. Tool 1 — Local PDF & Document Extractor (tool_1_doc_extractor/)
   - Converts client PDFs, invoices, and reports in input_pdfs/ into structured .json and .csv summaries.
   - Customize keyword tags in config.json.
2. Tool 2 — Automated Opportunity & Lead Radar (tool_2_opportunity_radar/)
   - Scans RSS feeds configured in feeds.json, filters by your target keywords, deduplicates links, and exports a daily Markdown digest + JSON feed.
3. Tool 3 — Bulk Content & SEO Packager (tool_3_content_packager/)
   - Turns Markdown drafts in drafts/ into publish-ready bundles with URL slugs, read times, meta descriptions, social hooks, and Schema.org JSON-LD.

## Quick Start (Linux / macOS / Windows WSL)
1. Create and activate a virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate

2. Install the single lightweight dependency:
   pip install -r requirements.txt

3. Run all three tools at once (with included sample files):
   ./run_all.sh
