"""Extract embedded dashboard JSON from an authorized local HTML export.

Usage:
    python -m src.ingestion.extract_dashboard_data path/to/dashboard.html

The source dashboard is not distributed in this repository. Obtain it through
an authorized SoccerSolver data-access route before running this script.
"""
import argparse
import json
from pathlib import Path


MARKERS = {
    "dashboard_data.json": ("/*__DATA_JSON_START__*/", "/*__DATA_JSON_END__*/"),
    "dashboard_models.json": ("/*__MODELS_JSON_START__*/", "/*__MODELS_JSON_END__*/"),
    "dashboard_preview.json": ("/*__PREVIEW_JSON_START__*/", "/*__PREVIEW_JSON_END__*/"),
}


def extract(source: Path, output_dir: Path) -> None:
    text = source.read_text(encoding="utf-8")
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, (start, end) in MARKERS.items():
        if start not in text or end not in text:
            raise ValueError(f"Missing embedded-data markers for {filename}")
        value = json.loads(text.split(start, 1)[1].split(end, 1)[0])
        (output_dir / filename).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote {output_dir / filename}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_html", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    extract(args.source_html.resolve(), args.output_dir)


if __name__ == "__main__":
    main()
