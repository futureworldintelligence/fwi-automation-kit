#!/usr/bin/env bash
set -e

echo "=== Running Solopreneur Local Automation Kit ==="
python3 tool_1_doc_extractor/doc_to_json.py
echo "-----------------------------------------------"
python3 tool_2_opportunity_radar/radar_bot.py
echo "-----------------------------------------------"
python3 tool_3_content_packager/seo_packager.py
echo "=== All 3 tools completed! Check each tool's output folder. ==="
