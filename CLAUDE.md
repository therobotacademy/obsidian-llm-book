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

## Autonomy — decide by default, gate only once
This is an **agentic** process: run it end-to-end and stop only at the single human gate.
Do **not** ask the user for choices a default rule resolves. Apply these silently; report
them in the Phase-0 summary:
- **Vault id** — derive `wiki-<code>/` + BOOK `<CODE>` from the title initials
  (*Introduction to Design Science* → `IDS`).
- **Language** — synthesize in the book's source language; structural labels follow the engine/skill templates.
- **Parts** — mirror the TOC. Explicit Parts → use them. Flat TOC → derive 3–5 thematic
  Parts from the book's own Preface/Ch.1 framing (grouping, not inventing topics); record them in `_toc.yaml`.
- **End-matter** (Summary / Review Questions / Answers / Further Reading / References) →
  fold into the chapter MOC, never separate nodes; flag `kind: endmatter` in `_toc.yaml`.
- **PDF location** — move source to `raw/<code>.pdf` (gitignored).
- **Offset** — calibrate + verify (≥3 chapters). If not constant (stripped blank pages),
  record a **per-chapter offset** in `_toc.yaml`; never force a single global offset.
- **Shared tooling** — never fork the engine for one book; if a per-book need arises, parameterize it (e.g. a flag).

**The one gate:** after Phase 0 + bootstrap + the **first chapter** compiled in full (index + colors,
so it is a viewable graph), stop and show it. Resume the rest only on approval. Escalate mid-run only
when a default above genuinely cannot resolve (unreadable TOC, calibration fails verification).

## Model allocation (per phase)
Run the orchestration (this skill) on **Opus** — it parses the TOC, calibrates, holds the gate, and lints.
It does **not** switch its own (main-session) model; instead it **delegates a phase to a subagent with an
explicit `model:` override** (`Agent(..., model: "opus|sonnet|haiku")`). Pure-script phases run inline.

| Phase | Work | Model | Why |
|---|---|---|---|
| 0 · Map / calibrate | TOC parse, offset verification, Part inference | **opus** (`claude-opus-4-8`) | Judgment-heavy; a wrong offset silently extracts the wrong pages |
| 1 · Bootstrap | run `obsidian-vault-builder` | script inline / **haiku** | Deterministic; no synthesis |
| 2 · Raw extract | run `extract_pages.py` per chapter | script inline / **haiku** | Pure pdfplumber; delegate later chapters to haiku for context isolation |
| 3 · Compile (pilot) | synthesize chapter 1, set the template | **opus** | The product; the gate approves this bar |
| 3 · Compile (fan-out) | chapters 2…n replicate the approved pattern | **sonnet** (`claude-sonnet-4-6`) | Pattern-following; cheap + parallelizable |
| 3 · Lint | enforce ring model, check vs `_toc.yaml` | **opus** | Quality gate on the whole tree |
| 4 · Color / index | `obsidian-graph-colors`, `gen_index.py` | script inline / **haiku** | Deterministic scripts |

Rule of thumb: **judgment & creation on Opus (me), replication on Sonnet (subagents), mechanics on scripts/Haiku.**

## Documentation
Full process (phases, artifact layers, link model, triggers, decisions) is in `PROCESO.md`.
