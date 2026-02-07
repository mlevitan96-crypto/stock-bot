import os
import json
from datetime import datetime
from pathlib import Path

BASE = Path("board/eod/out")

def main():
    BASE.mkdir(parents=True, exist_ok=True)

    # Use today's date; cron will run this after EOD
    today = datetime.utcnow().strftime("%Y-%m-%d")
    day_dir = BASE / today
    day_dir.mkdir(parents=True, exist_ok=True)

    # Collect top-level .md and .json files (ignore subdirectories)
    md_files = []
    json_files = []
    for p in BASE.iterdir():
        if p.is_file():
            if p.suffix.lower() == ".md":
                md_files.append(p)
            elif p.suffix.lower() == ".json":
                json_files.append(p)

    # Combine .md files into one
    combined_md_path = day_dir / "daily_board_review.md"
    with combined_md_path.open("w", encoding="utf-8") as out_md:
        out_md.write(f"# Daily Board Review – {today}\n\n")
        if not md_files:
            out_md.write("_No markdown artifacts found in board/eod/out for this day._\n")
        else:
            for i, md in enumerate(sorted(md_files)):
                out_md.write(f"\n\n---\n\n## Source: {md.name}\n\n")
                out_md.write(md.read_text(encoding="utf-8"))

    # Combine .json files into one array
    combined_json_path = day_dir / "daily_board_review.json"
    combined = []
    for js in sorted(json_files):
        try:
            text = js.read_text(encoding="utf-8").strip()
            if not text:
                continue
            data = json.loads(text)
            combined.append({"source": js.name, "data": data})
        except Exception as e:
            combined.append({"source": js.name, "error": str(e)})

    with combined_json_path.open("w", encoding="utf-8") as out_js:
        json.dump(
            {
                "date": today,
                "artifacts": combined
            },
            out_js,
            indent=2,
            sort_keys=True
        )

    print(f"Packaged daily board outputs into {day_dir}")
    print(f"- Markdown: {combined_md_path}")
    print(f"- JSON:     {combined_json_path}")

if __name__ == "__main__":
    main()
