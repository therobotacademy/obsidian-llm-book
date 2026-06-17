---
name: obsidian-vault-builder
description: Crea y configura vaults de Obsidian desde cero sin necesidad de abrir Obsidian. Triggers: "bootstrap vault", "crear vault", "nuevo vault", "set-layout", "toggle plugin", "inspect vault", "auditar vault".
---

# obsidian-vault-builder

Construye el directorio `.obsidian/` completo (5 archivos JSON) para cualquier ruta destino sin abrir Obsidian. Usa el vault `wiki/.obsidian/` como referencia canónica de sintaxis y estructura.

## Archivos que gestiona

| Archivo | Descripción |
|---|---|
| `app.json` | Configuración global (objeto vacío → Obsidian usa defaults) |
| `appearance.json` | Tema visual (objeto vacío → Obsidian usa defaults) |
| `core-plugins.json` | Mapa booleano de plugins nativos activos/inactivos |
| `graph.json` | Configuración del Graph View (colorGroups, fuerzas, display) |
| `workspace.json` | Layout de paneles con UUIDs — generado siempre via `build_workspace.py` |

## Operaciones

### 1. Bootstrap — crear vault nuevo

**Trigger:** "bootstrap vault", "crear vault", "nuevo vault obsidian"

**Pasos:**
1. Advertir: **Obsidian debe estar cerrado** antes de escribir — esperar confirmación
2. Verificar que el path destino existe; si no, crearlo
3. Crear `<destino>/.obsidian/` si no existe
4. Escribir `app.json` → `{}`
5. Escribir `appearance.json` → `{}`
6. Pedir perfil de plugins: `minimal` | `full` | `book` (default: `book`)
7. Copiar template `core-plugins-<perfil>.json` → `core-plugins.json`
8. Pedir template de grafo: `vacio` | `book` (default: `book`)
9. Copiar template → `graph.json` (si `vacio`: solo campos de control sin colorGroups)
10. Pedir layout: `graph-center` | `editor-center` | `minimal` (default: `graph-center`)
11. Pedir archivo inicial a mostrar (ruta relativa al vault; puede estar vacío)
12. Ejecutar:
    ```
    python .claude/skills/obsidian-vault-builder/build_workspace.py \
      --layout <layout> [--file <ruta>] --out <destino>/.obsidian/workspace.json
    ```
13. Verificar que los 5 archivos existen y son JSON válido
14. Reportar resumen: archivos creados, perfil elegido, layout

**Constraint:** Si ya existe `.obsidian/` con contenido, preguntar antes de sobrescribir.

---

### 2. Add-plugin — toggle de plugin core

**Trigger:** "toggle plugin", "activar plugin", "desactivar plugin", "add-plugin"

**Pasos:**
1. Advertir: cerrar Obsidian
2. Leer `<vault>/.obsidian/core-plugins.json`
3. Mostrar estado actual del plugin pedido
4. Cambiar el booleano
5. Escribir el archivo
6. Confirmar cambio en respuesta

**Claves válidas de plugins:**
`file-explorer`, `global-search`, `switcher`, `graph`, `backlink`, `canvas`, `outgoing-link`,
`tag-pane`, `footnotes`, `properties`, `page-preview`, `daily-notes`, `templates`,
`note-composer`, `command-palette`, `slash-command`, `editor-status`, `bookmarks`,
`markdown-importer`, `zk-prefixer`, `random-note`, `outline`, `word-count`, `slides`,
`audio-recorder`, `workspaces`, `file-recovery`, `publish`, `sync`, `bases`, `webviewer`

---

### 3. Set-layout — regenerar workspace

**Trigger:** "set-layout", "cambiar layout", "regenerar workspace"

**Pasos:**
1. Advertir: **Obsidian debe estar cerrado** — Obsidian sobreescribe `workspace.json` al cerrarse
2. Pedir layout: `graph-center` | `editor-center` | `minimal`
3. Pedir archivo inicial (opcional)
4. Ejecutar `build_workspace.py` con los parámetros elegidos
5. Sobrescribir `workspace.json`

**Nota:** Set-layout SIEMPRE regenera workspace.json completo con UUIDs frescos. No parchea el existente.

---

### 4. Inspect — auditoría de vault existente

**Trigger:** "inspect vault", "auditar vault", "qué tiene este vault"

**Pasos:**
1. Leer los 5 archivos `.obsidian/`
2. Reportar tabla con:
   - Plugins activos / inactivos
   - ColorGroups (query → hex → decimal RGB)
   - Layout detectado (tipo de panel main, paneles laterales, collapsed o no)
   - Último archivo abierto (`lastOpenFiles[0]`)
3. Detectar anomalías:
   - Campos faltantes en `graph.json`
   - IDs duplicados en `workspace.json`
   - Claves desconocidas en `core-plugins.json`

No modifica nada.

---

## Componentes

```
.claude/skills/obsidian-vault-builder/
├── SKILL.md
├── build_workspace.py          ← genera workspace.json con UUIDs frescos
└── templates/
    ├── core-plugins-minimal.json
    ├── core-plugins-full.json
    ├── core-plugins-book.json        ← book vault profile (graph/backlink/outline/tag-pane)
    └── graph-book.json               ← colorGroups by Part (root/first/part-1…part-5)
```

## Delegaciones

| Tarea | Skill |
|---|---|
| Añadir/cambiar colores del grafo en vault existente | `obsidian-graph-colors` |
| Ingestar contenido al wiki | `karpathy-llm-wiki` |
| Crear o reconfigurar `.obsidian/` | **obsidian-vault-builder** |

## Constraints críticos

- **Obsidian DEBE estar cerrado** antes de cualquier escritura — mencionarlo siempre y esperar confirmación
- **`workspace.json` se genera solo via `build_workspace.py`** — nunca editarlo a mano
- **Los templates son inmutables** — leer, nunca modificar
- **Leer antes de escribir** — siempre `Read()` antes de cualquier `Edit()`/`Write()` sobre archivos existentes
- Preservar encoding UTF-8 en todos los archivos JSON
- Los `colorGroups` del grafo se delegan a `obsidian-graph-colors` una vez el vault existe
