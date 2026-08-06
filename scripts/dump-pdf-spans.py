#!/usr/bin/env python3
"""Extract PDF text spans to JSON for local grouping evaluation.

Local-only tool: writes span data (the same fields the /api/pdf/{id}/structure
endpoint returns) to a directory of your choice, defaulting to /tmp/pdf-eval.
Never uploads anything anywhere.

Usage:
    python scripts/dump-pdf-spans.py /path/to/file.pdf [out_dir]
    python scripts/dump-pdf-spans.py /tmp/*.pdf            # multiple files

Output: <out_dir>/<basename>.json  →  { "pages": [ { "page": 1, "elements": [...] } ] }
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz  # PyMuPDF


def extract(pdf_path: Path) -> dict:
    doc = fitz.open(pdf_path)
    pages = []
    for page_num, page in enumerate(doc, start=1):
        elements = []
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    elements.append(
                        {
                            "text": span["text"],
                            "bbox": list(span["bbox"]),
                            "origin": list(span["origin"]),
                            "font": span["font"],
                            "size": span["size"],
                            "color": span["color"],
                        }
                    )
        pages.append({"page": page_num, "elements": elements})
    doc.close()
    return {"file": pdf_path.name, "pages": pages}


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if len(args) < 1:
        print(__doc__)
        return 2

    out_dir = Path(args[-1]) if len(args) > 1 and args[-1].endswith((".json", ".jsonl")) is False else Path("/tmp/pdf-eval")
    # Heuristic: last arg is the output dir only if it is not a PDF and there
    # are ≥2 args and the first arg(s) are existing files.
    if len(args) >= 2 and Path(args[-1]).suffix != ".pdf":
        out_dir = Path(args[-1])
    else:
        out_dir = Path("/tmp/pdf-eval")

    out_dir.mkdir(parents=True, exist_ok=True)
    inputs = [Path(a) for a in args if Path(a).is_file() and Path(a).suffix.lower() == ".pdf"]
    if not inputs:
        print("[ERROR] no PDF files given", file=sys.stderr)
        return 1

    for pdf in inputs:
        data = extract(pdf)
        dest = out_dir / f"{pdf.stem}.json"
        dest.write_text(json.dumps(data, indent=1), encoding="utf-8")
        n = sum(len(p["elements"]) for p in data["pages"])
        print(f"[OK] {pdf.name}: {len(data['pages'])} pages, {n} spans -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
