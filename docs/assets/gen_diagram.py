"""Generate architecture SVG diagram for SQL Merge Tool."""

WIDTH = 900
HEIGHT = 540
BG = "#0d1b2a"
SURFACE = "#112233"
SURFACE_ALT = "#162840"
PANEL = "#1a2f45"
ACCENT = "#52d6b8"
ACCENT2 = "#4a9eff"
TEXT = "#e8f4f0"
MUTED = "#7a9ab0"
BORDER = "#1e3a50"
GREEN = "#52d6b8"
BLUE = "#4a9eff"
ORANGE = "#f0a04a"
RED = "#e05a5a"


def rect(x, y, w, h, fill, rx=10, stroke=None, stroke_w=1.5, opacity=1.0):
    s = f'stroke="{stroke}" stroke-width="{stroke_w}"' if stroke else 'stroke="none"'
    op = f'opacity="{opacity}"' if opacity < 1 else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {s} {op}/>'


def text(x, y, content, fill=TEXT, size=13, anchor="middle", weight="normal", family="monospace"):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" font-family="{family}">{content}</text>'


def arrow(x1, y1, x2, y2, color=MUTED, dashed=False):
    dash = 'stroke-dasharray="6,3"' if dashed else ""
    return (
        f'<defs><marker id="ah_{x1}_{y1}" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">'
        f'<polygon points="0 0, 8 3, 0 6" fill="{color}"/></marker></defs>'
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.8" '
        f'marker-end="url(#ah_{x1}_{y1})" {dash}/>'
    )


def box(x, y, w, h, label, sublabel=None, color=ACCENT, fill=SURFACE):
    out = []
    out.append(rect(x, y, w, h, fill, rx=8, stroke=color, stroke_w=1.5))
    ty = y + h // 2 + (5 if sublabel else 5)
    if sublabel:
        ty = y + h // 2 - 2
    out.append(text(x + w // 2, ty, label, fill=color, size=12, weight="bold"))
    if sublabel:
        out.append(text(x + w // 2, ty + 18, sublabel, fill=MUTED, size=10))
    return "\n".join(out)


def pill(x, y, w, h, label, fill=PANEL, color=MUTED):
    out = []
    out.append(rect(x, y, w, h, fill, rx=h // 2, stroke=color, stroke_w=1))
    out.append(text(x + w // 2, y + h // 2 + 4, label, fill=color, size=10))
    return "\n".join(out)


parts = []

# background
parts.append(rect(0, 0, WIDTH, HEIGHT, BG, rx=0))

# title bar
parts.append(rect(0, 0, WIDTH, 56, SURFACE_ALT, rx=0))
parts.append(text(WIDTH // 2, 36, "SQL Merge Tool — Architecture", fill=ACCENT, size=18, weight="bold"))
parts.append(text(WIDTH - 20, 36, "PolyForm NC 1.0", fill=MUTED, size=10, anchor="end"))

# ── Section labels ──────────────────────────────────────────
parts.append(text(120, 90, "INPUT", fill=MUTED, size=11, weight="bold"))
parts.append(text(450, 90, "PROCESSING", fill=MUTED, size=11, weight="bold"))
parts.append(text(790, 90, "OUTPUT", fill=MUTED, size=11, weight="bold"))

# divider lines
for lx in [235, 665]:
    parts.append(f'<line x1="{lx}" y1="70" x2="{lx}" y2="{HEIGHT - 20}" stroke="{BORDER}" stroke-width="1" stroke-dasharray="4,4"/>')

# ── Input column ────────────────────────────────────────────
parts.append(box(30, 110, 190, 44, "main.sql", "主 SQL 查詢", color=BLUE))
parts.append(box(30, 170, 190, 44, "join_1.sql", "JOIN SQL", color=BLUE))
parts.append(box(30, 230, 190, 44, "join_2.sql  …", "JOIN SQL (N)", color=BLUE, fill=SURFACE))
parts.append(box(30, 310, 190, 44, "merge_spec.json", "合併規格", color=ORANGE))
parts.append(box(30, 370, 190, 44, "workspace.json", "工作區快照", color=MUTED, fill=SURFACE))

# ── Processing column ───────────────────────────────────────
# parse box
parts.append(rect(255, 100, 390, 100, PANEL, rx=10, stroke=BLUE, stroke_w=1))
parts.append(text(450, 124, "parse_sql_module()  ×N", fill=BLUE, size=12, weight="bold"))
parts.append(pill(270, 135, 170, 26, "抽出最外層 WITH/CTE", fill=SURFACE_ALT, color=TEXT))
parts.append(pill(455, 135, 175, 26, "module__ 前綴重新命名", fill=SURFACE_ALT, color=TEXT))
parts.append(text(450, 195, "→  ParsedSqlModule × N", fill=MUTED, size=10))

# validate box
parts.append(rect(255, 215, 390, 64, PANEL, rx=10, stroke=ORANGE, stroke_w=1))
parts.append(text(450, 240, "validate_columns_against_schema()", fill=ORANGE, size=12, weight="bold"))
parts.append(text(450, 262, "確認 join key 與輸出欄位皆存在", fill=MUTED, size=10))

# merge box
parts.append(rect(255, 293, 390, 130, PANEL, rx=10, stroke=ACCENT, stroke_w=1.5))
parts.append(text(450, 318, "merge_sql_files()", fill=ACCENT, size=13, weight="bold"))
parts.append(pill(270, 328, 165, 26, "組合所有 CTE 子句", fill=SURFACE_ALT, color=TEXT))
parts.append(pill(450, 328, 180, 26, "建立 LEFT JOIN 主查詢", fill=SURFACE_ALT, color=TEXT))
parts.append(pill(270, 365, 165, 26, "build_select_items()", fill=SURFACE_ALT, color=TEXT))
parts.append(pill(450, 365, 180, 26, "sqlglot 語法驗證", fill=SURFACE_ALT, color=TEXT))
parts.append(text(450, 415, "→  合併後 SQL 字串", fill=MUTED, size=10))

# ── Output column ───────────────────────────────────────────
parts.append(box(685, 170, 190, 44, "merged_output.sql", "合併結果", color=GREEN))
parts.append(box(685, 240, 190, 44, "SQLite 驗證", "執行查詢確認", color=GREEN))
parts.append(box(685, 310, 190, 44, "GUI 預覽", "複製 / 即時顯示", color=ACCENT2))
parts.append(box(685, 380, 190, 44, "CLI stdout", "--dry-run 模式", color=MUTED, fill=SURFACE))

# ── Arrows: Input → Processing ──────────────────────────────
for ay in [132, 192, 252]:
    parts.append(arrow(222, ay, 253, ay, color=BLUE))
parts.append(arrow(222, 332, 253, 248, color=ORANGE))
parts.append(arrow(222, 392, 180, 440, color=MUTED, dashed=True))

# ── Arrows: Processing → Output ─────────────────────────────
parts.append(arrow(647, 340, 683, 192, color=GREEN))
parts.append(arrow(647, 355, 683, 262, color=GREEN))
parts.append(arrow(647, 365, 683, 332, color=ACCENT2))
parts.append(arrow(647, 375, 683, 402, color=MUTED, dashed=True))

# ── Internal flow arrows ─────────────────────────────────────
parts.append(arrow(450, 202, 450, 213, color=BORDER))
parts.append(arrow(450, 280, 450, 291, color=BORDER))

# ── Footer ───────────────────────────────────────────────────
parts.append(rect(0, HEIGHT - 30, WIDTH, 30, SURFACE_ALT, rx=0))
parts.append(text(20, HEIGHT - 10, "gui/app.py  ·  cli.py", fill=MUTED, size=10, anchor="start"))
parts.append(text(WIDTH // 2, HEIGHT - 10, "services/  ·  models.py  ·  workspace_service.py", fill=MUTED, size=10))
parts.append(text(WIDTH - 20, HEIGHT - 10, "github.com/ericlight0025/sql_merge_edit", fill=MUTED, size=10, anchor="end"))

svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  <style>text {{ font-family: 'Segoe UI', 'Microsoft JhengHei UI', 'Helvetica Neue', sans-serif; }}</style>
  {'  '.join(parts)}
</svg>"""

out = "/home/user/sql_merge_edit/docs/assets/architecture.svg"
with open(out, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"SVG written to {out}")
