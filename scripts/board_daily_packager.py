import argparse
import json
from datetime import datetime
from pathlib import Path

BASE = Path("board/eod/out")


def main() -> None:
    parser = argparse.ArgumentParser(description="Package daily board outputs into dated folder")
    parser.add_argument("--date", type=str, help="Date YYYY-MM-DD (default: today UTC)")
    args = parser.parse_args()

    target_date = args.date or datetime.utcnow().strftime("%Y-%m-%d")
    BASE.mkdir(parents=True, exist_ok=True)
    day_dir = BASE / target_date
    day_dir.mkdir(parents=True, exist_ok=True)

    md_files = []
    json_files = []
    for p in BASE.iterdir():
        if p.is_file() and target_date in p.name:
            if p.suffix.lower() == ".md":
                md_files.append(p)
            elif p.suffix.lower() == ".json":
                json_files.append(p)

    combined_md_path = day_dir / "daily_board_review.md"
    with combined_md_path.open("w", encoding="utf-8") as out_md:
        out_md.write(f"# Daily Board Review - {target_date}\n\n")
        if not md_files:
            out_md.write("_No markdown artifacts found in board/eod/out for this day._\n")
        else:
            for md in sorted(md_files):
                out_md.write(f"\n\n---\n\n## Source: {md.name}\n\n")
                out_md.write(md.read_text(encoding="utf-8"))

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
        json.dump({"date": target_date, "artifacts": combined}, out_js, indent=2, sort_keys=True)

    print(f"Packaged daily board outputs into {day_dir}")
    print(f"- Markdown: {combined_md_path}")
    print(f"- JSON:     {combined_json_path}")

if __name__ == "__main__":
    main()
