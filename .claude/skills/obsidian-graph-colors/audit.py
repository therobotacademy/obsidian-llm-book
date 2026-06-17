"""
Auditoría de Graph View — Obsidian Graph Colors
Uso: python audit.py [--wiki <ruta_wiki>]
Por defecto busca wiki/ relativo al directorio de trabajo.
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")


def find_wiki_root(start: Path) -> Path:
    for candidate in [start / "wiki", start]:
        if (candidate / ".obsidian" / "graph.json").exists():
            return candidate
    sys.exit(f"No se encontró graph.json bajo {start}. Pasa --wiki <ruta>.")


def parse_tags_from_frontmatter(md_path: Path) -> list[str]:
    text = md_path.read_text(encoding="utf-8-sig", errors="replace")
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return []
    fm = m.group(1)
    # inline: tags: [a, b, c]
    m2 = re.search(r"^tags:\s*\[([^\]]+)\]", fm, re.MULTILINE)
    if m2:
        return [t.strip() for t in m2.group(1).split(",")]
    # block:
    # tags:
    #   - a
    #   - b
    m3 = re.search(r"^tags:\s*\n((?:\s*-\s+\S+\n?)+)", fm, re.MULTILINE)
    if m3:
        return [re.sub(r"^\s*-\s+", "", l).strip() for l in m3.group(1).splitlines() if l.strip()]
    return []


def decimal_to_hex(d: int) -> str:
    R = d >> 16
    G = (d >> 8) & 0xFF
    B = d & 0xFF
    return f"#{R:02X}{G:02X}{B:02X}"


def collect_wiki_tags(wiki_root: Path) -> dict[str, list[str]]:
    """Returns {tag: [filename, ...]} for all .md files in wiki/ (excluding .obsidian)."""
    tag_map: dict[str, list[str]] = defaultdict(list)
    for md in wiki_root.rglob("*.md"):
        if ".obsidian" in md.parts:
            continue
        tags = parse_tags_from_frontmatter(md)
        for tag in tags:
            tag_map[tag].append(md.name)
    return dict(tag_map)


def audit(wiki_root: Path) -> None:
    graph_json = wiki_root / ".obsidian" / "graph.json"
    data = json.loads(graph_json.read_text(encoding="utf-8"))
    color_groups: list[dict] = data.get("colorGroups", [])

    wiki_tags = collect_wiki_tags(wiki_root)

    # ── tabla principal ──────────────────────────────────────────────────────
    col_q  = max(len(g["query"]) for g in color_groups) + 2 if color_groups else 30
    col_h  = 10
    col_d  = 12

    header = f"{'Query':<{col_q}} {'Hex':<{col_h}} {'RGB dec':<{col_d}} Artículos"
    print()
    print("Color groups actuales — wiki/.obsidian/graph.json")
    print("─" * len(header))
    print(header)
    print("─" * len(header))

    hex_usage: dict[str, list[str]] = defaultdict(list)   # hex → [queries]
    groups_in_file: set[str] = set()

    for g in color_groups:
        query: str = g["query"]
        rgb: int   = g["color"]["rgb"]
        hex_color  = decimal_to_hex(rgb)
        clean_tag  = query.strip().removeprefix("tag:#")
        articles   = wiki_tags.get(clean_tag, [])
        art_str    = ", ".join(articles) if articles else "—  ⚠ sin artículos"
        print(f"{query:<{col_q}} {hex_color:<{col_h}} {rgb:<{col_d}} {art_str}")
        hex_usage[hex_color].append(query)
        groups_in_file.add(clean_tag)

    print()

    # ── anomalías ────────────────────────────────────────────────────────────
    anomalies: list[str] = []

    # 1. Tags en wiki sin grupo de color
    missing = [f"#{t}" for t in wiki_tags if t not in groups_in_file]
    if missing:
        anomalies.append(f"[SIN COLOR]    Tags en wiki sin grupo: {', '.join(sorted(missing))}")

    # 2. Grupos huérfanos (query apunta a tag inexistente en wiki)
    for g in color_groups:
        clean = g["query"].strip().removeprefix("tag:#")
        if clean not in wiki_tags:
            anomalies.append(f"[HUÉRFANO]     '{g['query']}' no coincide con ningún artículo")

    # 3. Espacios en las queries
    for g in color_groups:
        if g["query"] != g["query"].strip():
            anomalies.append(f"[ESPACIOS]     '{g['query']}' tiene espacios extra (puede fallar en algunas versiones de Obsidian)")

    # 4. Colores duplicados entre grupos distintos
    for hex_color, queries in hex_usage.items():
        if len(queries) > 1:
            anomalies.append(f"[DUPLICADO]    Hex {hex_color} usado en: {', '.join(queries)}")

    if anomalies:
        print("Anomalías detectadas")
        print("─" * 40)
        for a in anomalies:
            print(" •", a)
    else:
        print("Sin anomalías detectadas.")

    print()


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--wiki" in args:
        wiki_root = Path(args[args.index("--wiki") + 1])
    else:
        wiki_root = find_wiki_root(Path.cwd())

    audit(wiki_root)
