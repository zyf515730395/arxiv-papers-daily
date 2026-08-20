"""Generate the standalone GitHub Pages paper archive."""

import calendar
from collections import OrderedDict
import datetime
import html
import json
from pathlib import Path
import re
import unicodedata


ENTRY_PATTERN = re.compile(
    r"^\|\*\*(?P<date>[^*]+)\*\*\|\*\*(?P<title>.*?)\*\*\|"
    r"(?P<authors>.*?)\|\[(?P<pdf_label>[^]]+)]\((?P<pdf_url>[^)]+)\)\|"
    r"(?P<code>.*?)\|$"
)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def parse_entry(paper_id: str, entry: str) -> dict:
    match = ENTRY_PATTERN.match(entry.strip())
    if match is None:
        raise ValueError(f"Unexpected paper entry for {paper_id}: {entry[:100]}")

    values = match.groupdict()
    published = datetime.date.fromisoformat(values["date"])
    code_match = re.search(r"\[[^]]*]\(([^)]+)\)", values["code"])
    paper_url = values["pdf_url"].replace("http://arxiv.org/", "https://arxiv.org/")
    return {
        "id": paper_id,
        "date": published,
        "title": values["title"],
        "authors": values["authors"],
        "paper_url": paper_url,
        "code_url": code_match.group(1) if code_match else None,
    }


def build_archive(data: dict) -> tuple[list[dict], OrderedDict]:
    categories = []
    themes = OrderedDict()

    for topic, entries in data.items():
        rows = [parse_entry(paper_id, entry) for paper_id, entry in entries.items()]
        rows.sort(key=lambda row: (row["date"], row["id"]), reverse=True)

        years = OrderedDict()
        for row in rows:
            year = row["date"].year
            month = row["date"].month
            years.setdefault(year, OrderedDict()).setdefault(month, []).append(row)

        category = {
            "topic": topic,
            "theme": topic,
            "subtype": None,
            "slug": slugify(topic),
            "count": len(rows),
            "years": years,
        }
        categories.append(category)
        themes.setdefault(topic, []).append(category)

    return categories, themes


def month_anchor(category: dict, year: int, month: int) -> str:
    return f'{category["slug"]}-{year}-{month:02d}'


def render_sidebar(themes: OrderedDict) -> str:
    output = [
        '<aside class="paper-sidebar" id="paper-sidebar" aria-label="Paper archive">',
        '  <div class="sidebar-brand">',
        '    <a href="#top">ARXIV / DAILY</a>',
        '    <span>Computer vision research index</span>',
        '  </div>',
        '  <div class="sidebar-actions">',
        '    <button type="button" data-sidebar-action="expand">Expand all</button>',
        '    <button type="button" data-sidebar-action="collapse">Collapse all</button>',
        '  </div>',
        '  <nav class="archive-nav">',
    ]

    for theme_index, (theme, categories) in enumerate(themes.items()):
        theme_count = sum(category["count"] for category in categories)
        open_attribute = " open" if theme_index == 0 else ""
        output.append(f'    <details class="nav-theme"{open_attribute}>')
        output.append(
            f'      <summary><span>{html.escape(theme)}</span>'
            f'<span class="nav-count">{theme_count}</span></summary>'
        )

        for category_index, category in enumerate(categories):
            has_subtype = category["subtype"] is not None
            if has_subtype:
                category_open = " open" if theme_index == 0 and category_index == 0 else ""
                output.append(f'      <details class="nav-subtopic"{category_open}>')
                output.append(
                    f'        <summary><span>{html.escape(category["subtype"])}</span>'
                    f'<span class="nav-count">{category["count"]}</span></summary>'
                )

            indent = "        " if has_subtype else "      "
            for year_index, (year, months) in enumerate(category["years"].items()):
                year_count = sum(len(rows) for rows in months.values())
                year_open = " open" if theme_index == 0 and category_index == 0 and year_index == 0 else ""
                output.append(f'{indent}<details class="nav-year"{year_open}>')
                output.append(
                    f'{indent}  <summary><span>{year}</span>'
                    f'<span class="nav-count">{year_count}</span></summary>'
                )
                output.append(f'{indent}  <ul>')
                for month, rows in months.items():
                    anchor = month_anchor(category, year, month)
                    output.append(
                        f'{indent}    <li><a href="#{anchor}">'
                        f'<span>{calendar.month_name[month]}</span>'
                        f'<span class="nav-count">{len(rows)}</span></a></li>'
                    )
                output.append(f'{indent}  </ul>')
                output.append(f'{indent}</details>')

            if has_subtype:
                output.append("      </details>")

        output.append("    </details>")

    output.extend(["  </nav>", "</aside>"])
    return "\n".join(output)


def render_table(rows: list[dict]) -> str:
    output = [
        '<div class="table-scroll">',
        '  <table class="paper-table">',
        '    <thead><tr><th>Date</th><th>Paper</th><th>Authors</th><th>arXiv</th><th>Code</th></tr></thead>',
        '    <tbody>',
    ]
    for row in rows:
        paper_url = html.escape(row["paper_url"], quote=True)
        code_cell = '<span class="muted">—</span>'
        if row["code_url"]:
            code_url = html.escape(row["code_url"], quote=True)
            code_cell = f'<a href="{code_url}" target="_blank" rel="noopener">Repository</a>'
        output.append(
            "      <tr>"
            f'<td><time datetime="{row["date"].isoformat()}">{row["date"].isoformat()}</time></td>'
            f'<td class="paper-title"><a href="{paper_url}" target="_blank" rel="noopener">'
            f'{html.escape(row["title"])}</a></td>'
            f'<td>{html.escape(row["authors"])}</td>'
            f'<td><a href="{paper_url}" target="_blank" rel="noopener">{html.escape(row["id"])}</a></td>'
            f"<td>{code_cell}</td>"
            "</tr>"
        )
    output.extend(["    </tbody>", "  </table>", "</div>"])
    return "\n".join(output)


def render_content(categories: list[dict]) -> str:
    output = []
    for category in categories:
        eyebrow = category["theme"]
        heading = category["subtype"] or category["theme"]
        output.extend([
            f'<section class="topic-section" id="{category["slug"]}">',
            '  <header class="topic-header">',
            f'    <p>{html.escape(eyebrow)}</p>',
            f'    <h2>{html.escape(heading)}</h2>',
            f'    <span>{category["count"]} papers</span>',
            '  </header>',
        ])
        for year_index, (year, months) in enumerate(category["years"].items()):
            year_count = sum(len(rows) for rows in months.values())
            year_open = " open" if year_index == 0 else ""
            output.append(f'  <details class="archive-year"{year_open}>')
            output.append(
                f'    <summary><span>{year}</span><span>{year_count} papers</span></summary>'
            )
            for month_index, (month, rows) in enumerate(months.items()):
                anchor = month_anchor(category, year, month)
                month_open = " open" if year_index == 0 and month_index == 0 else ""
                output.append(f'    <details class="archive-month" id="{anchor}"{month_open}>')
                output.append(
                    f'      <summary><span>{calendar.month_name[month]}</span>'
                    f'<span>{len(rows)} papers</span></summary>'
                )
                output.append(render_table(rows))
                output.append("    </details>")
            output.append("  </details>")
        output.append("</section>")
    return "\n".join(output)


def generate_site(json_path: str | Path, output_path: str | Path) -> None:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    categories, themes = build_archive(data)
    updated = datetime.date.today().isoformat()
    total_papers = sum(category["count"] for category in categories)
    years = {
        year
        for category in categories
        for year in category["years"]
    }

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="A daily index of image, video, and 3D generation, neural rendering, and depth estimation papers from arXiv.">
  <title>Arxiv Papers Daily</title>
  <script>
    (() => {{
      const storageKey = "arxiv-theme";
      let theme = null;
      try {{ theme = window.localStorage.getItem(storageKey); }} catch (error) {{ /* Storage can be unavailable. */ }}
      if (theme !== "light" && theme !== "dark") {{
        theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
      }}
      document.documentElement.dataset.theme = theme;
    }})();
  </script>
  <link rel="stylesheet" href="assets/css/site.css">
  <script src="assets/js/sidebar.js" defer></script>
</head>
<body>
  <button class="sidebar-toggle" type="button" aria-controls="paper-sidebar" aria-expanded="false">
    <span aria-hidden="true">&#9776;</span> Browse archive
  </button>
  <button class="theme-toggle" type="button" aria-label="Switch color theme" aria-pressed="false">
    <span data-theme-icon aria-hidden="true"></span>
  </button>
  <div class="sidebar-scrim" data-sidebar-close></div>
{render_sidebar(themes)}
  <main class="page-content" id="top">
    <header class="hero">
      <h1>Arxiv Papers Daily</h1>
      <div class="hero-stats" aria-label="Archive statistics">
        <div><strong>{total_papers:,}</strong><span>Papers</span></div>
        <div><strong>{len(themes)}</strong><span>Topics</span></div>
        <div><strong>{len(years)}</strong><span>Years</span></div>
      </div>
      <p class="updated">Updated {updated}</p>
    </header>
{render_content(categories)}
    <footer>Generated from arXiv metadata · <a href="https://github.com/zyf515730395/arxiv-papers-daily">View source on GitHub</a></footer>
  </main>
</body>
</html>
"""
    Path(output_path).write_text(document, encoding="utf-8")
