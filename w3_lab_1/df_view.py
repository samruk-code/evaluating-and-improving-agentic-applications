"""Render a pandas DataFrame to a self-contained, browsable HTML page.

This is plumbing for the lab's "Data Explorer" tab, not something you need to
write yourself — import it and call `save_view(...)` after building or
updating a dataframe, then click **Data Explorer** in the top bar (or reload
it if it's already open) to see a sortable, searchable, color-coded table
instead of a wall of printed text.

Usage (from a script or the OpenCode terminal):

    import pandas as pd
    from df_view import save_view

    df = pd.DataFrame(...)
    save_view(df, title="Labeled failures", subtitle="21 rows", name="task1")

Pass a `name` and the dataframe gets its own page (dataframe_exports/<slug>.html)
*and* a button in the Data Explorer tab's selector row, alongside every other
named dataframe a script in this lab has saved — so you can flip between, say,
the Task 1 labeled benchmark and the Task 6 meta-eval comparison without
re-running anything. Omit `name` and it just overwrites the unnamed
"current" view, same as before.

Nothing here talks to Phoenix directly — it only knows how to turn a
dataframe into HTML and keep dataframe_exports/manifest.json (the list the
selector row reads) up to date.
"""

from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = "dataframe_exports/current.html"
MANIFEST_PATH = Path("dataframe_exports/manifest.json")

# Fixed color mapping so the same category/severity value always renders with
# the same badge color across every re-render (helps side-by-side comparison
# across tasks). Falls back to a neutral gray for anything unrecognized.
_CATEGORY_COLORS = {
    "pass": "#1a7f4f",
    "correct": "#1a7f4f",
    "compliant": "#1a7f4f",
    "hallucination": "#b3261e",
    "incorrect": "#b3261e",
    "non_compliant": "#b3261e",
    "faithfulness_drift": "#b06000",
    "scope_violation": "#7c3aed",
    "reasoning_error": "#1d4ed8",
    "format_inconsistency": "#0f766e",
    "train": "#1d4ed8",
    "test": "#7c3aed",
}
_SEVERITY_COLORS = {
    "high": "#b3261e",
    "medium": "#b06000",
    "low": "#6b7280",
    "n/a": "#9ca3af",
}
_FALLBACK_COLOR = "#52606d"


def _badge_color(value, mapping):
    key = str(value).strip().lower()
    return mapping.get(key, _FALLBACK_COLOR)


def _is_badge_column(col_name: str) -> bool:
    return col_name.lower() in (
        "category", "severity", "source", "policy", "correctness", "split", "label",
    )


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "dataframe"


def _update_manifest(slug: str, file_name: str, title: str, subtitle: str, rows: int) -> None:
    entries = []
    if MANIFEST_PATH.exists():
        try:
            entries = json.loads(MANIFEST_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            entries = []

    entry = {
        "slug": slug,
        "file": file_name,
        "title": title,
        "subtitle": subtitle,
        "rows": rows,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    for i, existing in enumerate(entries):
        if existing.get("slug") == slug:
            entries[i] = entry
            break
    else:
        entries.append(entry)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def save_view(
    df,
    title: str = "Dataframe",
    subtitle: str | None = None,
    name: str | None = None,
    path: str | os.PathLike | None = None,
):
    """Render `df` to a standalone HTML file (created if missing).

    With `name="task1"`, writes to dataframe_exports/task1.html and adds/updates
    an entry in dataframe_exports/manifest.json so it shows up as its own
    button in the Data Explorer tab. Without `name`, writes to `path`
    (dataframe_exports/current.html by default) with no manifest entry — the
    always-available fallback view.

    Returns the resolved Path that was written, so callers can print it.
    """
    if name:
        slug = _slugify(name)
        out_path = Path(f"dataframe_exports/{slug}.html")
    else:
        out_path = Path(path or DEFAULT_PATH)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    columns = list(df.columns)
    # NaN/None-safe records; keep everything as strings for simple, predictable
    # rendering (this is a viewer, not a data pipeline).
    records = []
    for _, row in df.iterrows():
        record = {}
        for col in columns:
            val = row[col]
            if val is None or (isinstance(val, float) and val != val):  # NaN check w/o pandas import
                record[col] = ""
            else:
                record[col] = str(val)
        records.append(record)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    subtitle_text = subtitle or f"{len(records)} row{'s' if len(records) != 1 else ''} · {len(columns)} columns"

    payload = {
        "title": title,
        "columns": columns,
        "rows": records,
        "badgeColumns": [c for c in columns if _is_badge_column(c)],
        "categoryColors": _CATEGORY_COLORS,
        "severityColors": _SEVERITY_COLORS,
        "fallbackColor": _FALLBACK_COLOR,
    }

    html_doc = _TEMPLATE.format(
        title=html.escape(title),
        subtitle=html.escape(subtitle_text),
        generated_at=generated_at,
        payload_json=json.dumps(payload),
    )
    out_path.write_text(html_doc, encoding="utf-8")

    if name:
        # Also mirror to current.html so the no-name fallback view (and the
        # plain "Data Explorer" button) always shows the most recent save too.
        Path(DEFAULT_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(DEFAULT_PATH).write_text(html_doc, encoding="utf-8")
        _update_manifest(slug, out_path.name, title, subtitle_text, len(records))

    return out_path.resolve()


_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title} — Data Explorer</title>
<style>
  :root {{
    color-scheme: light dark;
    --bg: #ffffff;
    --fg: #1f2933;
    --muted: #52606d;
    --border: #e4e7eb;
    --row-alt: #f8fafc;
    --header-bg: #f5f7fa;
    --input-bg: #ffffff;
    --input-border: #cbd2d9;
    --link: #2b6cb0;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #0f172a;
      --fg: #e5e7eb;
      --muted: #94a3b8;
      --border: #1f2937;
      --row-alt: #131f34;
      --header-bg: #16223a;
      --input-bg: #0b1120;
      --input-border: #334155;
      --link: #93c5fd;
    }}
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    height: 100%;
  }}
  body {{
    margin: 0;
    display: flex;
    flex-direction: column;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--fg);
  }}
  header {{
    flex-shrink: 0;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
    padding: 0.9rem 1.1rem 0.75rem;
  }}
  h1 {{
    margin: 0 0 0.15rem;
    font-size: 1.15rem;
  }}
  .subtitle {{
    color: var(--muted);
    font-size: 0.82rem;
    margin-bottom: 0.6rem;
  }}
  .controls {{
    display: flex;
    gap: 0.6rem;
    align-items: center;
    flex-wrap: wrap;
  }}
  #search {{
    flex: 1;
    min-width: 200px;
    padding: 0.4rem 0.6rem;
    border: 1px solid var(--input-border);
    border-radius: 6px;
    background: var(--input-bg);
    color: var(--fg);
    font-size: 0.85rem;
  }}
  .meta {{
    font-size: 0.75rem;
    color: var(--muted);
    white-space: nowrap;
  }}
  .columns-menu-wrap {{
    position: relative;
  }}
  #columns-toggle {{
    padding: 0.4rem 0.7rem;
    border: 1px solid var(--input-border);
    border-radius: 6px;
    background: var(--input-bg);
    color: var(--fg);
    font-size: 0.82rem;
    cursor: pointer;
    white-space: nowrap;
  }}
  #columns-toggle:hover {{ color: var(--link); }}
  .columns-menu {{
    position: absolute;
    top: calc(100% + 4px);
    right: 0;
    z-index: 20;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    min-width: 170px;
    max-height: 260px;
    overflow-y: auto;
    padding: 0.55rem 0.7rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
  }}
  .columns-menu[hidden] {{ display: none; }}
  .columns-menu label {{
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.82rem;
    cursor: pointer;
    white-space: nowrap;
  }}
  .columns-menu .columns-menu-actions {{
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    padding-bottom: 0.35rem;
    margin-bottom: 0.15rem;
    border-bottom: 1px solid var(--border);
  }}
  .columns-menu .columns-menu-actions button {{
    background: none;
    border: none;
    color: var(--link);
    font-size: 0.76rem;
    cursor: pointer;
    padding: 0;
  }}
  .col-hidden {{ display: none !important; }}
  .table-wrap {{
    flex: 1;
    min-height: 0;
    overflow: auto;
    padding: 0 1.1rem 1.5rem;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    font-size: 0.85rem;
  }}
  thead th {{
    position: sticky;
    top: 0;
    background: var(--header-bg);
    text-align: left;
    padding: 0.5rem 0.7rem;
    border-bottom: 2px solid var(--border);
    cursor: pointer;
    user-select: none;
    white-space: nowrap;
  }}
  thead th:hover {{ color: var(--link); }}
  thead th .arrow {{ opacity: 0.5; font-size: 0.7em; margin-left: 0.2rem; }}
  tbody td {{
    position: relative;
    padding: 0.45rem 1.5rem 0.45rem 0.7rem;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
    max-width: 420px;
  }}
  .copy-cell {{
    position: absolute;
    top: 0.3rem;
    right: 0.28rem;
    z-index: 1;
    width: 0.85rem;
    height: 0.85rem;
    padding: 0;
    border: none;
    background: transparent;
    color: var(--muted);
    opacity: 0.22;
    cursor: pointer;
  }}
  .copy-cell svg {{
    display: block;
    width: 100%;
    height: 100%;
  }}
  .copy-cell:hover,
  .copy-cell:focus-visible {{
    opacity: 0.7;
  }}
  .copy-cell.copied {{
    opacity: 0.8;
    color: #1a7f4f;
  }}
  tbody tr:nth-child(even) {{ background: var(--row-alt); }}
  tbody tr.hidden {{ display: none; }}
  .cell-text {{
    white-space: pre-wrap;
    word-break: break-word;
  }}
  .badge {{
    display: inline-block;
    padding: 0.12rem 0.55rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #fff;
    white-space: nowrap;
  }}
  .empty {{
    padding: 2rem;
    text-align: center;
    color: var(--muted);
  }}
  footer {{
    flex-shrink: 0;
    padding: 0.75rem 1.1rem 1.5rem;
    color: var(--muted);
    font-size: 0.72rem;
  }}
</style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    <div class="subtitle">{subtitle} · generated {generated_at}</div>
    <div class="controls">
      <input id="search" type="search" placeholder="Filter rows (matches any column)…" />
      <div class="columns-menu-wrap">
        <button type="button" id="columns-toggle">Columns ▾</button>
        <div class="columns-menu" id="columns-menu" hidden></div>
      </div>
      <span class="meta" id="row-count"></span>
    </div>
  </header>
  <div class="table-wrap">
    <table id="df-table">
      <thead><tr id="header-row"></tr></thead>
      <tbody id="body-rows"></tbody>
    </table>
    <div class="empty" id="empty-state" hidden>No rows match your filter.</div>
  </div>
  <footer>Rendered by df_view.py — re-run your script and reload this tab to see updates.</footer>

<script id="payload" type="application/json">{payload_json}</script>
<script>
(function () {{
  const payload = JSON.parse(document.getElementById("payload").textContent);
  const {{ columns, rows, badgeColumns, categoryColors, severityColors, fallbackColor }} = payload;

  const headerRow = document.getElementById("header-row");
  const bodyRows = document.getElementById("body-rows");
  const rowCountEl = document.getElementById("row-count");
  const emptyState = document.getElementById("empty-state");
  const searchInput = document.getElementById("search");
  const columnsToggle = document.getElementById("columns-toggle");
  const columnsMenu = document.getElementById("columns-menu");

  let sortCol = null;
  let sortDir = 1;
  const hiddenCols = new Set();

  function applyColumnVisibility() {{
    document.querySelectorAll("[data-col]").forEach((el) => {{
      el.classList.toggle("col-hidden", hiddenCols.has(el.dataset.col));
    }});
  }}

  function renderColumnsMenu() {{
    columnsMenu.innerHTML = "";

    const actions = document.createElement("div");
    actions.className = "columns-menu-actions";
    const showAllBtn = document.createElement("button");
    showAllBtn.type = "button";
    showAllBtn.textContent = "Show all";
    showAllBtn.addEventListener("click", () => {{
      hiddenCols.clear();
      renderColumnsMenu();
      applyColumnVisibility();
    }});
    actions.appendChild(showAllBtn);
    columnsMenu.appendChild(actions);

    columns.forEach((col) => {{
      const label = document.createElement("label");
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = !hiddenCols.has(col);
      cb.addEventListener("change", () => {{
        if (cb.checked) hiddenCols.delete(col);
        else hiddenCols.add(col);
        applyColumnVisibility();
      }});
      label.appendChild(cb);
      label.appendChild(document.createTextNode(col));
      columnsMenu.appendChild(label);
    }});
  }}

  columnsToggle.addEventListener("click", (event) => {{
    event.stopPropagation();
    columnsMenu.hidden = !columnsMenu.hidden;
  }});
  document.addEventListener("click", (event) => {{
    if (!columnsMenu.hidden && !columnsMenu.contains(event.target) && event.target !== columnsToggle) {{
      columnsMenu.hidden = true;
    }}
  }});

  function badgeColorFor(col, value) {{
    const key = String(value).trim().toLowerCase();
    if (col.toLowerCase() === "severity") return severityColors[key] || fallbackColor;
    return categoryColors[key] || fallbackColor;
  }}

  function renderHeader() {{
    headerRow.innerHTML = "";
    columns.forEach((col) => {{
      const th = document.createElement("th");
      th.dataset.col = col;
      th.textContent = col;
      const arrow = document.createElement("span");
      arrow.className = "arrow";
      th.appendChild(arrow);
      th.addEventListener("click", () => {{
        if (sortCol === col) {{
          sortDir *= -1;
        }} else {{
          sortCol = col;
          sortDir = 1;
        }}
        renderBody();
      }});
      headerRow.appendChild(th);
    }});
  }}

  function currentRows() {{
    let data = rows.slice();
    if (sortCol) {{
      data.sort((a, b) => {{
        const av = (a[sortCol] || "").toLowerCase();
        const bv = (b[sortCol] || "").toLowerCase();
        if (av < bv) return -1 * sortDir;
        if (av > bv) return 1 * sortDir;
        return 0;
      }});
    }}
    return data;
  }}

  function fallbackCopy(text) {{
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.top = "0";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    let ok = false;
    try {{
      ok = document.execCommand("copy");
    }} catch (err) {{
      ok = false;
    }}
    document.body.removeChild(area);
    return ok;
  }}

  const COPY_ICON = '<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="6" y="6" width="8" height="8" rx="1.2" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M10 6V3.2A1.2 1.2 0 0 0 8.8 2H3.2A1.2 1.2 0 0 0 2 3.2V8.8A1.2 1.2 0 0 0 3.2 10H6" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>';
  const CHECK_ICON = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.2 8.3 6.4 11.5 12.8 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function copyCell(text, button) {{
    const finish = (ok) => {{
      button.innerHTML = ok ? CHECK_ICON : COPY_ICON;
      button.classList.toggle("copied", ok);
      button.setAttribute("aria-label", ok ? "Copied" : "Copy failed");
      setTimeout(() => {{
        button.innerHTML = COPY_ICON;
        button.classList.remove("copied");
        button.setAttribute("aria-label", "Copy cell");
      }}, 1200);
    }};
    const write = navigator.clipboard && navigator.clipboard.writeText
      ? navigator.clipboard.writeText(text)
      : Promise.reject();
    write.then(() => finish(true)).catch(() => finish(fallbackCopy(text)));
  }}

  function renderBody() {{
    const query = searchInput.value.trim().toLowerCase();
    const data = currentRows();
    bodyRows.innerHTML = "";
    let visible = 0;

    data.forEach((row) => {{
      const haystack = columns.map((c) => row[c] || "").join(" • ").toLowerCase();
      const matches = !query || haystack.includes(query);
      if (!matches) return;
      visible += 1;

      const tr = document.createElement("tr");
      columns.forEach((col) => {{
        const td = document.createElement("td");
        td.dataset.col = col;
        const value = row[col] || "";
        const copyBtn = document.createElement("button");
        copyBtn.type = "button";
        copyBtn.className = "copy-cell";
        copyBtn.innerHTML = COPY_ICON;
        copyBtn.setAttribute("aria-label", "Copy cell");
        copyBtn.addEventListener("click", (event) => {{
          event.stopPropagation();
          copyCell(value, copyBtn);
        }});
        td.appendChild(copyBtn);
        if (badgeColumns.includes(col) && value) {{
          const badge = document.createElement("span");
          badge.className = "badge";
          badge.textContent = value;
          badge.style.background = badgeColorFor(col, value);
          td.appendChild(badge);
        }} else {{
          const span = document.createElement("span");
          span.className = "cell-text";
          span.textContent = value;
          td.appendChild(span);
        }}
        tr.appendChild(td);
      }});
      bodyRows.appendChild(tr);
    }});

    rowCountEl.textContent = query ? `${{visible}} / ${{rows.length}} rows` : `${{rows.length}} rows`;
    emptyState.hidden = visible !== 0 || rows.length === 0;
    applyColumnVisibility();
  }}

  searchInput.addEventListener("input", renderBody);
  renderHeader();
  renderColumnsMenu();
  renderBody();
}})();
</script>
</body>
</html>
"""
