# ebook → Obsidian vault

A **portable recipe** for turning a **single ebook** (a PDF that is itself a whole domain of knowledge)
into a navigable **Obsidian vault whose graph reproduces the book's table of contents** — a *main* MOC
node per chapter, one node per TOC section, wired into **clean rings on a spine** (never a dense mesh).

Driven by an LLM (via [Claude Code](https://claude.com/claude-code)) that writes the vault while you read
and ask. It follows Karpathy's principle — *"the LLM writes and maintains the wiki; the human reads and
asks questions"* — specialized to the **single-source / book** case.

> This is the **book variant** of the corpus-oriented [karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki)
> recipe: instead of *inventing* structure for a corpus of many sources, it **mirrors the index** of one
> source that already carries its own structure.

---

## The idea

A book's table of contents *is* a tree. This recipe reproduces it as an Obsidian graph:

```
<BOOK>-index            (root MOC)
   └─ Part MOC          (one per part)
        └─ Chapter MOC  (the "main" node — a hub)
             └─ Section nodes   (the leaves)
```

Two design choices keep the graph **legible**:

1. **Synthesis, not transcription.** Every node is knowledge written in the LLM's own words (respects
   copyright; the extracted source text stays out of the published vault).
2. **Rings on a spine.** Each chapter renders as a **pure ring** — `Cap → S1 ↔ S2 ↔ … ↔ Sn → Cap` — where
   only the first and last section touch the chapter MOC, and every other section links only to its two
   neighbours. Conceptual cross-references between chapters are kept as **plain text**, not graph edges, so
   the graph never collapses into a hairball.

---

## How it works — five phases

The pipeline is **coupled by file** (each phase persists an artifact; nothing reads the previous phase's
in-memory output), so it is **resumable and auditable**. The entry skill `karpathy-llm-wiki-book`
orchestrates and delegates bootstrap/colors to two companion skills.

| Phase | What it does | Tool |
|---|---|---|
| **0 · Map** | parse the TOC into a manifest `raw-<book>/_toc.yaml`; **calibrate the page offset** (`pdf_idx = book_page + offset`) | assisted-manual |
| **1 · Bootstrap** | create `<vault>/` + `.obsidian/` (once) | `obsidian-vault-builder` |
| **2 · Raw** | extract each chapter's page range to `raw-<book>/ch<NN>.md` (immutable, gitignored) | `engine/extract_pages.py` |
| **3 · Compile** | synthesize the node tree per chapter, then enforce the pure-ring link model | LLM agents + `engine/finalize_part.py` |
| **4 · Color + index** | color the graph by Part; regenerate the flat index | `obsidian-graph-colors` + `engine/gen_index.py` |

Full design rationale, artifact layers, the link model, triggers and decisions are in [`PROCESO.md`](PROCESO.md).

---

## Quick start

**Requirements:** [Obsidian](https://obsidian.md), [Claude Code](https://claude.com/claude-code),
Python 3 with `pyyaml` and `pdfplumber`:

```bash
pip install -r requirements.txt
```

1. Open this folder with Claude Code — the three skills auto-discover under `.claude/skills/`.
2. **Map (Phase 0):** with Claude, read the book's TOC and build `raw-<book>/_toc.yaml` (parts → chapters →
   sections + page numbers). Find a chapter heading's PDF index to calibrate the **offset**, and verify it
   against ≥3 chapters spread across the book.
3. **Bootstrap (Phase 1):** *"bootstrap vault"* → `obsidian-vault-builder` creates `<vault>/` + `.obsidian/`
   (Obsidian **closed**). Use the `book` profile (plugins: graph, backlink, outgoing-link, outline, tag-pane).
4. **Per Part, repeat Phases 2–4:**
   ```bash
   # 2 · extract each chapter (book-page range from _toc.yaml)
   python .claude/skills/karpathy-llm-wiki-book/engine/extract_pages.py \
       --pdf "<book>.pdf" --from <p_start> --to <p_end> --offset <N> \
       --out raw-<book>/ch<NN>-<slug>.md

   # 3 · LLM synthesizes the chapter + section nodes (one agent per chapter), then:
   python .claude/skills/karpathy-llm-wiki-book/engine/finalize_part.py \
       --dir <vault>/Part-<N> --roman <R>

   # 4 · regenerate the flat index
   python .claude/skills/karpathy-llm-wiki-book/engine/gen_index.py \
       --vault <vault> --book <BOOK>
   ```
5. **Color & consume:** *"color the graph"* → `obsidian-graph-colors` writes colorGroups by Part (Obsidian
   closed). Then read the vault and ask questions; your gaps guide what to ingest next.

---

## Naming convention

```
<vault>/<BOOK>-index.md              root MOC + book home
<vault>/index.md                     flat index (links only to Chapter MOCs)
<vault>/Part-<N>/P<N>-<slug>.md      Part MOC
<vault>/Part-<N>/C<NN>-<slug>.md     Chapter MOC  (NN zero-padded)
<vault>/Part-<N>/S<NN>-<MM>-<slug>.md  Section node (MM = TOC minor, zero-padded)
```

Unique prefixed filenames keep wikilinks stable and sort naturally. Wikilinks resolve by filename, so they
are folder-independent.

---

## Components

```
.claude/skills/
├── karpathy-llm-wiki-book/      ← entry skill (this recipe)
│   ├── SKILL.md
│   └── engine/
│       ├── extract_pages.py     ← Phase 2: PDF page-range → text (+ offset)
│       ├── finalize_part.py     ← Phase 3: enforce the pure-ring link model
│       └── gen_index.py         ← Phase 4: regenerate the flat index
├── obsidian-vault-builder/      ← Phase 1: create the vault + .obsidian/ config
└── obsidian-graph-colors/       ← Phase 4: color the Graph view by tag
PROCESO.md                       ← full process documentation
CLAUDE.md                        ← agent bootstrap for this repo
```

---

## Reference implementation

Proven on **Gelman et al., *Bayesian Data Analysis* (3rd ed.)** — 677 pp, 5 parts + 3 appendixes,
23 chapters, 202 sections, ~230 nodes. The book's content is **not shipped here** (copyright);
only the recipe and tooling are.

---

## Obsidian rules (important)

- **Obsidian must be closed** when editing `graph.json` externally — if open, it overwrites external edits.
- **`workspace.json` is never hand-edited** — `obsidian-vault-builder` generates it with a script.

---

## Credits & license

The `karpathy-llm-wiki-book` skill derives from
[Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki) (MIT), here specialized to the
single-source/book case with the TOC-mirroring tree and the rings-on-a-spine link model.
Released under the [MIT License](LICENSE).
