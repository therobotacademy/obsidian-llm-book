"""Regenerate <vault>/index.md (flat node index) across all built Parts.

Usage:
    python gen_index.py --vault my-book-vault --book MYBOOK

Links ONLY to Chapter MOCs (small footprint); section rows are plain text so the
flat index does not add extra edges to the Graph view.
"""
import argparse
import glob
import os
import re
from datetime import date

import yaml

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
         "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
         "App": 99}


def essence(raw):
    """Extract a one-line summary from the first blockquote-bold line in the node body."""
    for line in raw.split("\n"):
        ls = line.strip()
        if ls.startswith(">") and "**" in ls:
            # strip leading `> **Label:**` pattern if present
            text = re.sub(r"^>\s*\*\*[^*]+\*\*\s*", "", ls).strip()
            if text:
                return text.replace("|", "/")[:150]
    for line in raw.split("\n"):
        ls = line.strip()
        if ls.startswith(">") and len(ls) > 3:
            return ls.lstrip("> ").strip().replace("|", "/")[:150]
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True, help="path to the vault directory")
    ap.add_argument("--book", default="BOOK", help="book id used in frontmatter (e.g. BDA3)")
    a = ap.parse_args()
    V = a.vault
    BOOK = a.book
    today = date.today().isoformat()

    part_meta = {}
    for pmoc in (glob.glob(os.path.join(V, "Part-*", "P*.md")) +
                 glob.glob(os.path.join(V, "Appendixes", "P*.md"))):
        d = yaml.safe_load(open(pmoc, encoding="utf-8").read().split("---", 2)[1])
        part_meta[d["part"]] = {"title": d["title"], "recs": []}

    for f in (glob.glob(os.path.join(V, "Part-*", "[CS]*.md")) +
              glob.glob(os.path.join(V, "Appendixes", "[AS]*.md"))):
        raw = open(f, encoding="utf-8").read()
        d = yaml.safe_load(raw.split("---", 2)[1])
        stem = os.path.splitext(os.path.basename(f))[0]
        part_meta[d["part"]]["recs"].append(
            (d["chapter"], d["toc"], d["type"], stem, d["title"], essence(raw))
        )

    book_lower = BOOK.lower()
    out = [
        "---",
        f'title: "{BOOK} — node index"',
        f"book: {BOOK}",
        "type: index",
        f"tags: [{book_lower}, index]",
        f"updated: {today}",
        "---",
        "",
        f"# {BOOK} — node index",
        "",
        f"Flat index of the vault. Conceptual map of the book: **[[{BOOK}-index]]**.",
        "",
        "> Sections are listed as **plain text** (no wikilink) to keep the Graph view clean —",
        "> this index only links to **Chapter MOCs**. Open a chapter and walk its section ring.",
        "",
    ]

    for roman in sorted(part_meta, key=lambda r: ROMAN.get(r, 50)):
        pm = part_meta[roman]
        out += ["", f"## {pm['title']}"]
        recs = sorted(pm["recs"], key=lambda r: (r[0], int(r[1].split(".")[1]) if "." in r[1] else -1))
        for ch, toc, typ, stem, title, ess in recs:
            if typ == "chapter":
                out += ["", f"### [[{stem}|{title}]]", f"> {ess}", "", "| § | Section | Essence |", "|---|---|---|"]
            else:
                out.append(f"| {toc} | {title} | {ess} |")

    content = "\n".join(out) + "\n"
    open(os.path.join(V, "index.md"), "w", encoding="utf-8").write(content)
    nsec = sum(1 for pm in part_meta.values() for r in pm["recs"] if r[2] == "section")
    print(f"wrote {V}/index.md — {len(part_meta)} parts, {nsec} sections, {len(content)} bytes")


if __name__ == "__main__":
    main()
