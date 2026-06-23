"""Finalize a Part folder into the canonical 'rings on a spine' link model.

Usage:
    python finalize_part.py --dir wiki-bda3/Part-2 --roman II

For every chapter in <dir> it enforces:
  - section `parent` is a plain string (no [[ ]]) — metadata, not a graph edge;
  - section See-Also links are delinked to italic plain text;
  - section footer = pure ring  ( first: `← [[Cap]] · [[§next]] →` · middle: `← [[§prev]] · [[§next]] →`
    · last: `← [[§prev]] · [[Cap]] →` );
  - chapter MOC `## Secciones` = single entry link to the first section + a plain-text list;
  - chapter MOC See-Also delinked; chapter MOC footer = chapter ring
    ( `← [[Cap prev]] · ↑ [[Part]] · [[Cap next]] →` ; first omits `←`, last omits `→` ).
Idempotent-ish: run once after the per-chapter agents finish.
"""
import argparse
import glob
import os
import re

import yaml

SEE = ("see also", "véase también", "vease tambien", "relacionado")
WL = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]*))?\]\]")


def fm_body(raw):
    p = raw.split("---", 2)
    return p[1], p[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--roman", required=True)
    ap.add_argument("--lang", choices=["es", "en"], default="es",
                    help="language of generated navigation labels (default: es, preserves the BDA3 case)")
    a = ap.parse_args()

    # Navigation micro-labels are the only generated prose; everything else is the LLM's synthesis.
    L = {
        "es": {"sec": "## Secciones · anillo", "cap": "Cap.", "parte": "Parte",
               "intro": "Entra por **{entry}** y recorre el anillo con los pies de navegación; "
                        "la última sección cierra de vuelta a este capítulo."},
        "en": {"sec": "## Sections · ring", "cap": "Ch.", "parte": "Part",
               "intro": "Enter at **{entry}** and walk the ring via the navigation footers; "
                        "the last section closes back to this chapter."},
    }[a.lang]

    sec_files = glob.glob(os.path.join(a.dir, "S*.md"))
    moc_files = glob.glob(os.path.join(a.dir, "C*.md"))

    title = {}
    for f in sec_files + moc_files:
        d = yaml.safe_load(fm_body(open(f, encoding="utf-8").read())[0])
        title[os.path.splitext(os.path.basename(f))[0]] = d.get("title", "")

    def delink(text):
        return WL.sub(lambda m: f"*{(m.group(2) or title.get(m.group(1), m.group(1))).strip()}*", text)

    def strip_seealso_links(body):
        out, insee = [], False
        for ln in body.split("\n"):
            h = re.match(r"^#{1,6}\s+(.*)$", ln)
            if h:
                insee = h.group(1).strip().lower().startswith(SEE)
                out.append(ln)
                continue
            if re.match(r"^\s*[↑←→]", ln):  # footer line ends the See-Also region
                insee = False
                out.append(ln)
                continue
            out.append(delink(ln) if insee else ln)
        return "\n".join(out)

    def set_footer(text, footer):
        lines = text.rstrip().split("\n")
        while lines and (not lines[-1].strip() or lines[-1].strip() == "---"
                         or re.match(r"^\s*[↑←→]", lines[-1])):
            lines.pop()
        return "\n".join(lines).rstrip() + "\n\n---\n" + footer + "\n"

    # ---- sections grouped by chapter ----
    from collections import defaultdict
    info = {}
    for f in sec_files:
        d = yaml.safe_load(fm_body(open(f, encoding="utf-8").read())[0])
        s = os.path.splitext(os.path.basename(f))[0]
        info[s] = {"toc": d["toc"], "ch": d["chapter"], "f": f}
    bych = defaultdict(list)
    for s, v in info.items():
        bych[v["ch"]].append(s)
    for ch in bych:
        bych[ch].sort(key=lambda s: int(info[s]["toc"].split(".")[1]))

    moc_of = {}  # chapter number -> MOC stem
    for f in moc_files:
        d = yaml.safe_load(fm_body(open(f, encoding="utf-8").read())[0])
        moc_of[d["chapter"]] = os.path.splitext(os.path.basename(f))[0]

    sec_done = 0
    for ch, order in bych.items():
        cap = moc_of[ch]
        cap_a = f"[[{cap}|{L['cap']} {ch}]]"
        n = len(order)
        for i, s in enumerate(order):
            raw = open(info[s]["f"], encoding="utf-8").read()
            raw = re.sub(r'(?m)^parent:\s*"?\[\[([^\]|]+)[^\n]*$', r"parent: \1", raw)  # plain parent
            fm, body = fm_body(raw)
            body = strip_seealso_links(body)
            prev = cap_a if i == 0 else f"[[{order[i-1]}|§{info[order[i-1]]['toc']}]]"
            nxt = cap_a if i == n - 1 else f"[[{order[i+1]}|§{info[order[i+1]]['toc']}]]"
            body = set_footer(body, f"← {prev} · {nxt} →")
            new = "---" + fm + "---" + body
            open(info[s]["f"], "w", encoding="utf-8").write(new)
            sec_done += 1

    # ---- chapter MOCs: rebuild Secciones + ring footer ----
    chapters = sorted(moc_of)
    part_stem = None
    moc_done = 0
    for idx, ch in enumerate(chapters):
        cap = moc_of[ch]
        f = os.path.join(a.dir, cap + ".md")
        raw = open(f, encoding="utf-8").read()
        d = yaml.safe_load(fm_body(raw)[0])
        pm = re.search(r"\[\[([^\]|]+)", str(d.get("parent", "")))
        part_stem = pm.group(1) if pm else str(d.get("parent", "")).strip()
        order = bych[ch]
        first = order[0]

        lines = raw.split("\n")
        out, i = [], 0
        while i < len(lines):
            ln = lines[i]
            if re.match(r"^##\s+(Secciones|Sections)\b", ln):
                entry = f"[[{first}|§{info[first]['toc']}]]"
                out += [L["sec"], "", L["intro"].format(entry=entry), ""]
                out += [f"- {title[s]}" for s in order]
                i += 1
                while i < len(lines) and not re.match(r"^##\s+", lines[i]):
                    i += 1
                continue
            out.append(ln)
            i += 1
        raw = "\n".join(out)
        raw = strip_seealso_links(raw)

        parts = []
        if idx > 0:
            parts.append(f"← [[{moc_of[chapters[idx-1]]}|{L['cap']} {chapters[idx-1]}]]")
        parts.append(f"↑ [[{part_stem}|{L['parte']} {a.roman}]]")
        if idx < len(chapters) - 1:
            parts.append(f"[[{moc_of[chapters[idx+1]]}|{L['cap']} {chapters[idx+1]}]] →")
        raw = set_footer(raw, " · ".join(parts))
        open(f, "w", encoding="utf-8").write(raw)
        moc_done += 1

    print(f"finalized {a.dir}: sections {sec_done}, chapter MOCs {moc_done}")


if __name__ == "__main__":
    main()
