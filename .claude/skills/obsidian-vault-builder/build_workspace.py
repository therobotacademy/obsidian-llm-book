#!/usr/bin/env python3
"""
build_workspace.py — genera workspace.json para Obsidian con UUIDs frescos.

Uso:
    python build_workspace.py --layout graph-center [--file <ruta>] [--out <destino>]
    python build_workspace.py --layout editor-center [--file <ruta>] [--out <destino>]
    python build_workspace.py --layout minimal [--file <ruta>] [--out <destino>]

--out  ruta del archivo destino; omitir o pasar "-" para stdout.
--file ruta relativa al vault del archivo a mostrar al abrir (opcional).

Layouts:
    graph-center  Graph View al centro, explorador en panel izquierdo (perfil del vault bayesiano)
    editor-center Editor al centro, Graph View en panel derecho abierto
    minimal       Solo editor al centro, sin paneles laterales desplegados
"""

import argparse
import json
import uuid
import sys
from pathlib import Path


def nid() -> str:
    """ID de 16 chars hex, formato nativo de Obsidian."""
    return uuid.uuid4().hex[:16]


def _left_panel(auto_reveal: bool = False) -> dict:
    return {
        "id": nid(),
        "type": "split",
        "children": [
            {
                "id": nid(),
                "type": "tabs",
                "children": [
                    {
                        "id": nid(),
                        "type": "leaf",
                        "state": {
                            "type": "file-explorer",
                            "state": {"sortOrder": "alphabetical", "autoReveal": auto_reveal},
                            "icon": "lucide-folder-closed",
                            "title": "Explorador de archivos"
                        }
                    },
                    {
                        "id": nid(),
                        "type": "leaf",
                        "state": {
                            "type": "search",
                            "state": {
                                "query": "", "matchingCase": False, "explainSearch": False,
                                "collapseAll": False, "extraContext": False, "sortOrder": "alphabetical"
                            },
                            "icon": "lucide-search",
                            "title": "Buscar"
                        }
                    },
                    {
                        "id": nid(),
                        "type": "leaf",
                        "state": {
                            "type": "bookmarks",
                            "state": {},
                            "icon": "lucide-bookmark",
                            "title": "Marcadores"
                        }
                    }
                ]
            }
        ],
        "direction": "horizontal",
        "width": 300
    }


def _ribbon() -> dict:
    return {
        "hiddenItems": {
            "switcher:Abrir selector rápido": False,
            "graph:Abrir vista gráfica": False,
            "canvas:Crear nuevo lienzo": False,
            "daily-notes:Abrir la nota de hoy": False,
            "templates:Insertar plantilla": False,
            "command-palette:Abrir paleta de comandos": False,
            "bases:Crear nueva base": False
        }
    }


def _editor_leaf(initial_file: str) -> tuple[str, dict]:
    leaf_id = nid()
    if initial_file:
        state = {
            "type": "markdown",
            "state": {"file": initial_file, "mode": "source", "backlinks": False, "source": False},
            "icon": "lucide-file",
            "title": Path(initial_file).stem
        }
    else:
        state = {
            "type": "empty",
            "state": {},
            "icon": "lucide-file",
            "title": "Nueva nota"
        }
    return leaf_id, {"id": leaf_id, "type": "leaf", "state": state}


def build_graph_center(initial_file: str) -> dict:
    graph_leaf_id = nid()
    graph_leaf = {
        "id": graph_leaf_id,
        "type": "leaf",
        "state": {
            "type": "graph",
            "state": {},
            "icon": "lucide-git-fork",
            "title": "Vista gráfica"
        }
    }

    right_children = [
        {"id": nid(), "type": "leaf", "state": {
            "type": "backlink",
            "state": {
                "collapseAll": False, "extraContext": False, "sortOrder": "alphabetical",
                "showSearch": False, "searchQuery": "", "backlinkCollapsed": False, "unlinkedCollapsed": True
            },
            "icon": "links-coming-in", "title": "Enlaces entrantes"
        }},
        {"id": nid(), "type": "leaf", "state": {
            "type": "outgoing-link",
            "state": {"linksCollapsed": False, "unlinkedCollapsed": True},
            "icon": "links-going-out", "title": "Enlaces salientes"
        }},
        {"id": nid(), "type": "leaf", "state": {
            "type": "tag",
            "state": {"sortOrder": "frequency", "useHierarchy": True, "showSearch": False, "searchQuery": ""},
            "icon": "lucide-tags", "title": "Etiquetas"
        }},
        {"id": nid(), "type": "leaf", "state": {
            "type": "all-properties",
            "state": {"sortOrder": "frequency", "showSearch": False, "searchQuery": ""},
            "icon": "lucide-archive", "title": "Todas las propiedades"
        }},
        {"id": nid(), "type": "leaf", "state": {
            "type": "outline",
            "state": {"followCursor": False, "showSearch": False, "searchQuery": ""},
            "icon": "lucide-list", "title": "Esquema"
        }},
    ]

    last_open = [initial_file] if initial_file else []

    return {
        "main": {
            "id": nid(), "type": "split",
            "children": [{"id": nid(), "type": "tabs", "children": [graph_leaf]}],
            "direction": "vertical"
        },
        "left": _left_panel(auto_reveal=False),
        "right": {
            "id": nid(), "type": "split",
            "children": [{"id": nid(), "type": "tabs", "children": right_children}],
            "direction": "horizontal", "width": 300, "collapsed": True
        },
        "left-ribbon": _ribbon(),
        "active": graph_leaf_id,
        "lastOpenFiles": last_open
    }


def build_editor_center(initial_file: str) -> dict:
    editor_leaf_id, editor_leaf = _editor_leaf(initial_file)

    right_children = [
        {"id": nid(), "type": "leaf", "state": {
            "type": "graph", "state": {},
            "icon": "lucide-git-fork", "title": "Vista gráfica"
        }},
        {"id": nid(), "type": "leaf", "state": {
            "type": "backlink",
            "state": {
                "collapseAll": False, "extraContext": False, "sortOrder": "alphabetical",
                "showSearch": False, "searchQuery": "", "backlinkCollapsed": False, "unlinkedCollapsed": True
            },
            "icon": "links-coming-in", "title": "Enlaces entrantes"
        }},
        {"id": nid(), "type": "leaf", "state": {
            "type": "outline",
            "state": {"followCursor": True, "showSearch": False, "searchQuery": ""},
            "icon": "lucide-list", "title": "Esquema"
        }},
    ]

    last_open = [initial_file] if initial_file else []

    return {
        "main": {
            "id": nid(), "type": "split",
            "children": [{"id": nid(), "type": "tabs", "children": [editor_leaf]}],
            "direction": "vertical"
        },
        "left": _left_panel(auto_reveal=True),
        "right": {
            "id": nid(), "type": "split",
            "children": [{"id": nid(), "type": "tabs", "children": right_children}],
            "direction": "horizontal", "width": 300, "collapsed": False
        },
        "left-ribbon": _ribbon(),
        "active": editor_leaf_id,
        "lastOpenFiles": last_open
    }


def build_minimal(initial_file: str) -> dict:
    editor_leaf_id, editor_leaf = _editor_leaf(initial_file)

    left = {
        "id": nid(), "type": "split",
        "children": [
            {
                "id": nid(), "type": "tabs",
                "children": [
                    {"id": nid(), "type": "leaf", "state": {
                        "type": "file-explorer",
                        "state": {"sortOrder": "alphabetical", "autoReveal": True},
                        "icon": "lucide-folder-closed", "title": "Explorador de archivos"
                    }}
                ]
            }
        ],
        "direction": "horizontal", "width": 300
    }

    right = {
        "id": nid(), "type": "split",
        "children": [
            {
                "id": nid(), "type": "tabs",
                "children": [
                    {"id": nid(), "type": "leaf", "state": {
                        "type": "outline",
                        "state": {"followCursor": True, "showSearch": False, "searchQuery": ""},
                        "icon": "lucide-list", "title": "Esquema"
                    }}
                ]
            }
        ],
        "direction": "horizontal", "width": 300, "collapsed": True
    }

    last_open = [initial_file] if initial_file else []

    return {
        "main": {
            "id": nid(), "type": "split",
            "children": [{"id": nid(), "type": "tabs", "children": [editor_leaf]}],
            "direction": "vertical"
        },
        "left": left,
        "right": right,
        "left-ribbon": _ribbon(),
        "active": editor_leaf_id,
        "lastOpenFiles": last_open
    }


BUILDERS = {
    "graph-center": build_graph_center,
    "editor-center": build_editor_center,
    "minimal": build_minimal,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera workspace.json para Obsidian con UUIDs frescos")
    parser.add_argument("--layout", choices=list(BUILDERS), default="graph-center",
                        help="Layout del workspace (default: graph-center)")
    parser.add_argument("--file", default="",
                        help="Ruta relativa al vault del archivo inicial (opcional)")
    parser.add_argument("--out", default="-",
                        help="Ruta destino del workspace.json; '-' para stdout (default: -)")
    args = parser.parse_args()

    workspace = BUILDERS[args.layout](args.file)
    output = json.dumps(workspace, ensure_ascii=False, indent=2) + "\n"

    if args.out == "-":
        sys.stdout.write(output)
    else:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"workspace.json → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
