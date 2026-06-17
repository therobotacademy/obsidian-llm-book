---
name: karpathy-llm-wiki-book
description: Use when converting a SINGLE book/ebook source (a PDF that is itself a whole domain) into an Obsidian vault whose node graph mirrors the book's table of contents — a 'main' MOC node per chapter and one node per TOC section, linked into a tree. Advanced single-source variant of karpathy-llm-wiki. Triggers: 'bootstrap a book vault', 'ingest this ebook', 'convert this book to a vault', 'wiki from a book', or any mention of building a vault that follows a book's index/TOC.
---

# Karpathy LLM Wiki — Book variant

Convert **one book** (an ebook/PDF that is itself a whole domain of knowledge) into an Obsidian vault
whose **node graph reproduces the book's table of contents**: a *main* MOC node per chapter, one node
per TOC section, all wired into a tree by hierarchy, reading sequence, and conceptual cross-references.

This is the **single-source** sibling of `karpathy-llm-wiki`. The base skill ingests a *corpus of many
sources* and **invents** structure by topic, deciding compilation by thesis (merge / new / cross-topic).
Here the problem is inverted: one source that **already carries its structure** (the TOC). You do not
invent organization — you **mirror the index** as a graph of nodes.

> Same Karpathy principle: *the LLM writes and maintains the wiki; the human reads and asks questions.*
> Same file-coupling: each phase persists an artifact on disk, so the process is resumable and auditable.

It follows the portable recipe documented in [`PROCESO.md`](../../../PROCESO.md).

| Aspect | `karpathy-llm-wiki` (base) | `karpathy-llm-wiki-book` (this) |
|---|---|---|
| Input | N sources, any domain | **1 ebook** = a whole domain |
| Structure | invented by topic | **given by the TOC** |
| Unit | concept article | structural node (root / part / chapter-MOC / section) |
| Compile decision | same thesis→merge · new→article | **deterministic**: TOC entry → node |
| Layout | `wiki/<topic>/art.md`, one level | `<vault>/<part>/…` MOC tree mirroring the TOC |
| Links | See Also | **tree + per-chapter ring**: MOC ↓ children, ↑ parent, sections ringed prev↔next; cross-refs as plain text |
| Ingest cadence | once per source | once **per chapter** (page-range slice) |

What is reused unchanged: the immutable extracted-text layer (`raw-<book>/`), delegation to
`obsidian-vault-builder` (bootstrap) and `obsidian-graph-colors` (graph colors), the `index.md` + `log.md`
pair, and the Query / Lint operations (adapted below).

---

## Artifact layers

Coupling is **by file** — no phase reads the previous one's in-memory output.

| Layer | Location | Owner | Mutability |
|---|---|---|---|
| **Source binary** | the ebook PDF (e.g. `raw/<book>.pdf`) | — | 🔒 immutable, read-only |
| **TOC manifest** | `raw-<book>/_toc.yaml` | this skill (Fase 0) | the deterministic spine; versioned |
| **Raw extracted text** | `raw-<book>/<chapter>.md` | this skill (Fase 2) | 🔒 immutable once created; **gitignored** (near-verbatim) |
| **Vault nodes** | `<vault>/<part>/…` + `index.md` + `log.md` | this skill (Fase 3) | full ownership; **synthesized** knowledge |
| **Obsidian config** | `<vault>/.obsidian/` | `obsidian-vault-builder` · `obsidian-graph-colors` | editable (⚠ Obsidian closed) |

**Copyright.** The vault publishes **synthesized** knowledge in the LLM's own words — never verbatim
transcription. The `raw-<book>/*.md` extracted text is gitignored; only `_toc.yaml` (structure: titles +
page numbers) is versioned.

---

## Fase 0 · Map — extract the TOC to a manifest

Parse the book's table of contents into `raw-<book>/_toc.yaml`: the deterministic backbone. One entry per
unit with `type` (root|part|chapter|section|appendix), `toc` (e.g. "5.2"), `title`, `page` (book page),
`slug` (chapters), and `pages: [start, end]` (chapters).

**Calibrate the page offset (mandatory).** TOC numbers are *book pages*, not 0-based PDF indices. Find the
PDF index of a known chapter heading and set `offset = pdf_index − book_page`; then `pdf_index = book_page
+ offset` everywhere. Verify the offset against ≥3 chapters spread across the book (PDFs sometimes insert
plates that break a constant offset). Read the TOC pages with pdfplumber via PowerShell (see the project
`CLAUDE.md` extraction pattern); transcribe sections from the TOC, not from body text.

> TOC formats vary too much across books for a brittle auto-parser. Extraction is **assisted-manual**:
> read the TOC pages, transcribe into the YAML, validate it parses and the chapter/section counts match.

---

## Fase 1 · Bootstrap the vault (once) — delegate to `obsidian-vault-builder`

Trigger `obsidian-vault-builder` ("bootstrap vault") to create `<vault>/` + `.obsidian/` (Obsidian
**closed**). Recommended choices for a tree vault: plugins enabling `graph`, `backlink`, `outgoing-link`,
`outline`, `tag-pane`; layout `graph-center`; graph template `vacio` (colors come in Fase 4). Add
`raw-<book>/*.md` to `.gitignore`.

---

## Fase 2 · Raw — extract text per chapter (immutable)

For each chapter, extract its page range to `raw-<book>/ch<NN>-<slug>.md` using the engine helper:

```
python .claude/skills/karpathy-llm-wiki-book/engine/extract_pages.py \
  --pdf "raw/<book>.pdf" --from <book_start> --to <book_end> --offset <offset> \
  --out raw-<book>/ch<NN>-<slug>.md
```

Immutable once created; the vault recompiles from here without re-extracting the binary.

---

## Fase 3 · Compile — the node tree (per chapter)

Generate, in TOC order, four node types. Every content node is **synthesized** (Karpathy compile), never
copy-pasted.

- **Root MOC** — `<BOOK>-index.md`: the book's home node → links **down** to every Part + the appendixes.
- **Part MOC** (one per part) — `P<n>-<slug>.md`: summary + links **down** to its chapters · ↑ root.
- **Chapter MOC** (the *main* node, one per chapter) — `C<NN>-<slug>.md`: chapter summary + list of its
  sections (↓ children) · ↑ Part.
- **Section node** (one per TOC section X.Y) — `S<NN>-<MM>-<slug>.md`: synthesized knowledge · ↑ chapter MOC.
  Cross-refs to related sections go in a *Relacionado* block as **plain-text** (italic title), not wikilinks.

Subsections (X.Y.Z) are **headings inside** the section node, not separate nodes.

**Linking model — each chapter is a pure ring, never a wheel or a mesh.** The Obsidian Graph view draws an
edge for every wikilink, so the sections of a chapter are wired as a single clean **cycle** through the
chapter MOC:

```
Cap.MOC → S1 ↔ S2 ↔ … ↔ Sn → Cap.MOC
```

- The **chapter MOC links only to the first section** (the ring entry). Its `## Secciones` block lists every
  section as **plain text** — *not* as wikilinks — so the MOC does **not** spoke to the middle sections.
- **First section**: footer `← [[Cap. N]] · [[§next]] →` (its "prev" is the chapter).
- **Middle sections**: footer `← [[§prev]] · [[§next]] →` — **no link to the chapter** (only their two neighbours).
- **Last section**: footer `← [[§prev]] · [[Cap. N]] →` — its "next" is the chapter; this single outward arrow
  closes the ring. (The chapter never links *back* to the last section.)
- So **only the first and last section touch the chapter node**; the rest are pure ring members.
- The `parent` frontmatter is a **plain string** (`parent: C05-hierarchical-models`, no `[[ ]]`) — metadata for
  tooling, but **not** a graph edge (a bracketed value would re-create a spoke to every section).

**Do NOT** author clickable **See-Also cross-refs** — those *cross-branch* edges (a section linking to one in
another chapter) are what turn the graph into a dense mesh. Keep conceptual cross-refs as **plain text**
(`- *5.4 Normal model with exchangeable parameters* — por qué`). The chapter MOCs themselves are chained by a
chapter-level ring footer (`← [[Cap. prev]] · ↑ [[Part]] · [[Cap. next]] →`).

**Node frontmatter:**
```yaml
---
title: "5.2 Exchangeability and hierarchical models"
book: BDA3
type: section            # root | part | chapter | section | appendix
toc: "5.2"
pages: 104-108
part: "I"
chapter: 5
raw: ../../raw-bda3/ch05-hierarchical-models.md
parent: C05-hierarchical-models   # plain string, NOT [[wikilink]] — metadata only, no graph edge
tags: [bda3, part-1, ch05, section]
updated: YYYY-MM-DD
---
```
(No `prev`/`next` in frontmatter — the sequence lives in the **footer ring**. First section: `← [[Cap. N]] · [[§next]] →`;
middle: `← [[§prev]] · [[§next]] →`; last: `← [[§prev]] · [[Cap. N]] →`.)

**On-disk layout & naming.** Folder per Part (`<vault>/P1-<slug>/…`) so the file explorer mirrors the tree.
**Unique prefixed filenames** (`C05`, `S05-02`) keep wikilinks stable and unambiguous (avoids Obsidian's
"shortest path" collisions) and sort naturally. Wikilinks are by filename, so they are folder-independent.
Appendix node ids use `AppA`/`AppB`/`AppC` to avoid colliding with the `C<NN>` chapter prefix.

---

## Fase 4 · Color + index/log — delegate to `obsidian-graph-colors`

With Obsidian **closed**, trigger `obsidian-graph-colors` to color the graph **by Part** (`tag:#part-1` …
`tag:#part-5`) plus the root (`tag:#root`). MOC hubs inherit their part's color (so each part is one uniform
cluster; hubs read as the larger, more-connected nodes). The `#moc`/`ch<NN>` tags carry **no colorGroup** —
they exist for filtering/tooling only. Then update `<vault>/index.md` (navigable index,
one row per node grouped by Part) and append to `<vault>/log.md`:
```
## [YYYY-MM-DD] ingest | <book> ch<NN> — <chapter title>  (<k> section nodes)
```

---

## The graph you get

**Rings on a spine.** Each chapter renders as a clean **ring** — a cycle `Cap → S1 ↔ S2 ↔ … ↔ Sn → Cap`
where every section links only to its two neighbours and **only the first and last section touch the chapter
node**. The chapter MOCs are themselves chained in a chapter-level ring and hang off the Part MOC (which still
lists its chapters), and Parts hang off the root — that is the spine. So the graph reads as a string of rings,
not a hairball: you navigate a chapter by walking its ring (or entering at the MOC), and move between chapters
along the chapter ring. **Cross-branch See-Also links are deliberately excluded** (kept as plain text); upward
navigation also uses Obsidian's automatic **backlinks** pane. Net effect: navigable, yet visually legible —
rings on a spine, never spaghetti.

---

## Query — "what does <book> say about X?"

Read `<vault>/index.md` → open relevant nodes → synthesize and **cite** (`[[node]]`), preferring vault
content over training knowledge. Do not write files unless asked to archive (then add a node + index row +
log line, as the base skill).

## Lint — quality

- **Deterministic (auto-fix):** index consistency; broken ring wikilinks (each section's footer `← prev · next →`,
  the MOC→first-section entry link, the last section's `next` → MOC); `parent` must be a **plain string** (delink
  if bracketed — a `[[ ]]` parent re-spokes the chapter); broken `raw:` refs; **clickable See-Also cross-refs**
  (delink to plain text).
- **Heuristic (report only):** a **broken ring** — the chapter's sections, walked by `next` from the first, must
  visit every section in TOC order and close back through the MOC; a chapter MOC linking to any section other than
  the first; a chapter MOC whose plain-text section list is incomplete vs. `_toc.yaml`; sections that contradict
  another node.

Log: `## [YYYY-MM-DD] lint | <N> issues, <M> auto-fixed`.

---

## Conventions & constraints

- **Single source.** One book per vault. A second book → a second vault (or a clearly separated subtree).
- **Mirror, don't invent.** The TOC is authoritative for structure; never reorganize the tree by topic.
- **Synthesize, never transcribe.** Respects copyright and the Karpathy principle.
- **Obsidian closed** before any `.obsidian/` write; **never** hand-edit `workspace.json`.
- **Calibrate the offset** before extracting, and verify it across the book.
- Every chapter Ingest updates both `<vault>/index.md` and `<vault>/log.md`.
- Process/code operations are logged in `sessions/`, not in the vault `log.md` (which is the vault's own).

---

## Components

```
.claude/skills/karpathy-llm-wiki-book/
├── SKILL.md
└── engine/
    ├── extract_pages.py     ← Fase 2: per-chapter PDF→text by book-page range + offset
    ├── finalize_part.py     ← Fase 3: enforce the pure-ring link model on a Part folder
    └── gen_index.py         ← Fase 4: regenerate <vault>/index.md across all built Parts
```

## Delegations

| Task | Skill |
|---|---|
| Create/configure `<vault>/.obsidian/` | `obsidian-vault-builder` |
| Color the graph by tag | `obsidian-graph-colors` |
| Topic-based wiki from a *corpus* (not a single book) | `karpathy-llm-wiki` (base) |

*Derived from [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki) (MIT).
Full process documentation in [`PROCESO.md`](../../../PROCESO.md).*
