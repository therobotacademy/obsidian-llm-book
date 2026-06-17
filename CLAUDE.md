# CLAUDE.md — ebook → Obsidian vault

## Role
You build and maintain an **Obsidian vault from a single ebook**, so that the vault's graph **reproduces
the book's table of contents**. Principle (Karpathy): *the LLM writes the vault; the human reads and asks*.
This repo is **domain-agnostic** — adapt to whatever book you are given.

## Read first, every session
1. This file.
2. `.claude/skills/karpathy-llm-wiki-book/SKILL.md` (the orchestrating skill — five phases + the link model).
3. `PROCESO.md` (full design) and `README.md` (quick start).
4. `<vault>/index.md` if a vault already exists (to see current state).

## Skills (in `.claude/skills/`)
| Skill | When | What |
|---|---|---|
| `karpathy-llm-wiki-book` | entry point · per chapter | Map → Bootstrap → Raw → Compile → Color; orchestrates the others |
| `obsidian-vault-builder` | once, at start | creates `<vault>/` + `.obsidian/` without opening Obsidian |
| `obsidian-graph-colors` | maintenance | colors the Graph view by tag |

## The invariant — "rings on a spine" (do not break)
Each chapter is a **pure ring**: `Cap.MOC → S1 ↔ S2 ↔ … ↔ Sn → Cap.MOC`.
- The chapter MOC links **only to the first section**; its `## Secciones` list is **plain text**.
- First section footer `← [[Cap]] · [[§next]] →`; middle `← [[§prev]] · [[§next]] →`; last `← [[§prev]] · [[Cap]] →`.
  **Only the first and last section touch the chapter.**
- `parent` frontmatter is a **plain string** (no `[[ ]]` → no graph edge).
- **See-Also cross-refs are plain text**, never clickable wikilinks (they were the mesh).
- The deterministic `engine/finalize_part.py` enforces all of the above after the LLM synthesizes content —
  agents only need to write good synthesis + a simple `↑ [[chapter]]` footer.

## Rules of behavior
- **Synthesize, never transcribe** the source (copyright + the Karpathy principle). Keep extracted source
  text in `raw-<book>/` (gitignored); publish only synthesized nodes.
- **Calibrate the page offset** in Phase 0 and verify it across ≥3 chapters before extracting.
- **Mirror, don't invent**: the TOC is authoritative for structure.
- **Obsidian closed** before editing `graph.json`; **never** hand-edit `workspace.json`.
- Color the graph **by Part** (`tag:#part-N`); `#moc` / `ch<NN>` tags exist for filtering, not color.
- Engine tools: `extract_pages.py` (Phase 2), `finalize_part.py` (Phase 3), `gen_index.py` (Phase 4).

## Documentation
Full process (phases, artifact layers, link model, triggers, decisions) is in `PROCESO.md`.
