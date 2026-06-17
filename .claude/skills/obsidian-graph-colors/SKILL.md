---
name: obsidian-graph-colors
description: Gestiona los grupos de color del Graph view de Obsidian. Triggers: /graph-colors, "colorear el grafo", "grupos de color", "color groups", "añadir color a nodos", "cambiar color de tag".
---

# Obsidian Graph Colors

Gestiona `<vault>/.obsidian/graph.json` para controlar los colores de los nodos en el Graph view de Obsidian.

## Activación — siempre como primer paso

Ejecutar el script de auditoría desde la raíz del proyecto:

```powershell
python .claude/skills/obsidian-graph-colors/audit.py
```

El script (`audit.py`, mismo directorio que este SKILL.md) produce automáticamente:

1. Tabla de estado: query · hex · RGB decimal · artículos que coinciden
2. Detección de anomalías:
   - **[SIN COLOR]** — tags presentes en wiki pero sin grupo de color
   - **[HUÉRFANO]** — grupos cuya query no coincide con ningún artículo
   - **[ESPACIOS]** — queries con espacios extra (pueden fallar en algunas versiones)
   - **[DUPLICADO]** — mismo hex asignado a varios grupos distintos

Argumento opcional `--wiki <ruta>` para apuntar a un vault distinto del directorio de trabajo.

Si `colorGroups` está vacío, indicarlo y ofrecer el esquema de colores por tier (operación 4).

---

## Operaciones

### 1. Añadir grupo de color

Trigger: "añade color X al tag #Y" / "colorea #Y con X"

Pasos:
1. Validar que la query tiene formato `tag:#tagname` (sin espacios, sin mayúsculas)
2. Si ya existe un grupo para ese tag, preguntar si se quiere actualizar en lugar de duplicar
3. Convertir el color a decimal RGB si viene en hex: `decimal = R×65536 + G×256 + B`
4. **Advertir: "¿Tienes Obsidian cerrado? Esta operación modifica graph.json y será revertida si Obsidian está abierto."** Esperar confirmación.
5. Leer `graph.json` de nuevo (por si cambió mientras se esperaba confirmación)
6. Insertar la nueva entrada en `colorGroups`
7. Escribir `graph.json`
8. Ejecutar `audit.py` para mostrar el estado actualizado

### 2. Cambiar color de grupo existente

Trigger: "cambia el color de #Y a X" / "pon #Y en color X"

Pasos:
1. Localizar la entrada con query `tag:#Y` en `colorGroups`
2. Si no existe, preguntar si se quiere crear
3. Convertir color a decimal si viene en hex
4. **Advertir cierre de Obsidian y esperar confirmación**
5. Leer `graph.json`, actualizar `rgb`, escribir
6. Ejecutar `audit.py` para mostrar el estado actualizado

### 3. Eliminar grupo de color

Trigger: "elimina el grupo #Y" / "quita el color de #Y"

Pasos:
1. Localizar la entrada en `colorGroups`
2. Mostrar qué artículos perderían color (dato disponible en la tabla de activación) y pedir confirmación
3. **Advertir cierre de Obsidian y esperar confirmación**
4. Leer `graph.json`, eliminar la entrada, escribir
5. Ejecutar `audit.py` para mostrar el estado actualizado

### 4. Sugerir esquema de colores por tier

Trigger: "esquema de colores por tier" / "paleta por tema" / "sugerencia de colores"

Mostrar la siguiente tabla como punto de partida — los valores hex/decimal son sugerencias, no el estado actual (para el estado actual usar `audit.py`):

| Tag | Suggested color | Hex | RGB dec |
|-----|----------------|-----|---------|
| `#root` | Gold | `#E6A000` | 15114240 |
| `#first` | Black (entry node of each chapter ring) | `#000000` | 0 |
| `#part-1` | Blue | `#4466FF` | 4482815 |
| `#part-2` | Green | `#44AA44` | 4500036 |
| `#part-3` | Purple | `#9944CC` | 10044620 |
| `#part-4` | Red | `#CC4444` | 13386820 |
| `#part-5` | Teal | `#44AAAA` | 4500138 |

Preguntar si se quiere aplicar todo el esquema, un subconjunto, o ajustar colores individuales.

### 5. Conversión RGB ↔ hex ↔ decimal

Trigger: "convierte #RRGGBB" / "convierte DECIMAL a hex" / "qué hex es NNNN"

Calcular y mostrar las tres representaciones. No escribe archivos.

Fórmulas:
- Hex → decimal: `decimal = R×65536 + G×256 + B`
- Decimal → hex: `R = d>>16`, `G = (d>>8) & 0xFF`, `B = d & 0xFF`

---

## Constraints — aplicar siempre

1. **Obsidian debe estar cerrado** antes de escribir `graph.json`. Si está abierto, cualquier escritura será revertida en cuanto el usuario interactúe con el Graph view. Advertir y pedir confirmación antes de cada escritura sin excepción.
2. **Nunca tocar `workspace.json`**. Obsidian genera IDs únicos y texto con tildes en español; un `workspace.json` externo incorrecto hace que Obsidian lo rechace y resetee también `graph.json`.
3. Leer `graph.json` inmediatamente antes de escribirlo (no usar una lectura anterior) para evitar sobrescribir cambios concurrentes.
4. Preservar todos los campos de `graph.json` que no sean `colorGroups` (escala, distancias, flechas, etc.).
5. Después de cualquier escritura, ejecutar siempre `audit.py` para mostrar el estado resultante completo.
