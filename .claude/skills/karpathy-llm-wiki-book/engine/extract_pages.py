#!/usr/bin/env python3
"""Extract a book-page range from a PDF to UTF-8 text (karpathy-llm-wiki-book, Fase 2).

Book pages are NOT 0-based PDF indices. Pass --offset so the script maps
    pdf_index (0-based) = book_page + offset
Calibrate the offset once in Fase 0 by finding the PDF index of a known chapter
heading (see SKILL.md). For BDA3 the offset is 9.

Usage:
    python extract_pages.py --pdf "raw/BDA3-Bayesian Data Analysis.pdf" \
        --from 101 --to 138 --offset 9 --out raw-bda3/ch05-hierarchical-models.md

Writes the page text with a `===== book p.N =====` marker before each page so the
compile step can locate where each section starts.
"""
import argparse
import sys

import pdfplumber


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--from", dest="frm", type=int, required=True, help="first book page")
    ap.add_argument("--to", dest="to", type=int, required=True, help="last book page (inclusive)")
    ap.add_argument("--offset", type=int, required=True, help="pdf_index = book_page + offset")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    chunks = []
    with pdfplumber.open(args.pdf) as pdf:
        for bp in range(args.frm, args.to + 1):
            idx = bp + args.offset
            if idx < 0 or idx >= len(pdf.pages):
                print(f"WARN: book p.{bp} -> idx {idx} out of range", file=sys.stderr)
                continue
            text = pdf.pages[idx].extract_text() or ""
            chunks.append(f"===== book p.{bp} =====\n{text}")

    with open(args.out, "w", encoding="utf-8", errors="replace") as f:
        f.write("\n\n".join(chunks) + "\n")
    print(f"OK: book pp.{args.frm}-{args.to} -> {args.out} ({len(chunks)} pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
