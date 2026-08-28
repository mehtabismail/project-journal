#!/usr/bin/env python3
"""Build the client-facing HTML report from the project journal markdown files.

Usage:  python3 skill/scripts/build_reports.py [project_root]

Reads   docs/worklog.md, docs/meetings.md
Writes  docs/public/report.html   (one file: work log + meeting record, with a toggle)

Standard library only. Fails loudly on malformed entries or dead cross-references.
"""

import html
import re
import sys
from datetime import date, datetime
from pathlib import Path

SEP = "\u00b7"

WORK_TYPES = ["New feature", "Change request", "Enhancement", "Bug fix"]

TYPE_SLUG = {
    "New feature": "feature",
    "Change request": "change",
    "Enhancement": "enhancement",
    "Bug fix": "bugfix",
}

STATUS_SLUG = {
    "Delivered": "delivered",
    "In progress": "progress",
    "Blocked": "blocked",
    "Reverted": "reverted",
}


class FormatError(Exception):
    pass


# ---------------------------------------------------------------- parsing


def split_metadata(text, path):
    """Pull the leading --- fenced block off the top of the file."""
    text = text.replace("\r\n", "\n").lstrip("\ufeff").strip("\n")
    if not text.startswith("---"):
        raise FormatError(f"{path}: file must open with a --- metadata block")
    end = text.find("\n---", 3)
    if end == -1:
        raise FormatError(f"{path}: metadata block is not closed with ---")
    raw = text[3:end]
    body = text[end + 4 :]
    meta = {}
    for line in raw.strip().splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise FormatError(f"{path}: bad metadata line: {line!r}")
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body


def split_entries(body, path):
    """Split the body into (heading_line, chunk) pairs on level-2 headings."""
    parts = re.split(r"^## ", body, flags=re.M)
    entries = []
    for chunk in parts[1:]:
        head, _, rest = chunk.partition("\n")
        entries.append((head.strip(), rest))
    if not entries:
        raise FormatError(f"{path}: no entries found (expected '## ' headings)")
    return entries


def parse_worklog_heading(head, path):
    """`YYYY-MM-DD · Type · WL-0001` — three parts."""
    bits = [b.strip() for b in head.split(SEP)]
    if len(bits) != 3:
        raise FormatError(
            f"{path}: heading must be 'YYYY-MM-DD {SEP} Type {SEP} WL-0001', got: {head!r}"
        )
    raw_date, wtype, entry_id = bits
    try:
        parsed = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        raise FormatError(f"{path}: bad date {raw_date!r} in heading: {head!r}")
    if not re.fullmatch(r"WL-\d{4}", entry_id):
        raise FormatError(f"{path}: bad id {entry_id!r}, expected WL-0001 form")
    return parsed, wtype, entry_id


def parse_meeting_heading(head, path):
    """`YYYY-MM-DD · MTG-0001` — two parts. Meetings are a verbatim archive now,
    so there is no meeting-kind segment."""
    bits = [b.strip() for b in head.split(SEP)]
    if len(bits) != 2:
        raise FormatError(
            f"{path}: meeting heading must be 'YYYY-MM-DD {SEP} MTG-0001', got: {head!r}"
        )
    raw_date, entry_id = bits
    try:
        parsed = datetime.strptime(raw_date, "%Y-%m-%d").date()
    except ValueError:
        raise FormatError(f"{path}: bad date {raw_date!r} in meeting heading: {head!r}")
    if not re.fullmatch(r"MTG-\d{4}", entry_id):
        raise FormatError(f"{path}: bad id {entry_id!r}, expected MTG-0001 form")
    return parsed, entry_id


def parse_fields(chunk):
    """Read the leading run of **Key:** value lines. Returns (fields, remainder)."""
    fields = {}
    lines = chunk.split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines):
        m = re.match(r"\*\*(.+?):\*\*\s*(.*)$", lines[i].strip())
        if not m:
            break
        fields[m.group(1).strip()] = m.group(2).strip()
        i += 1
    return fields, "\n".join(lines[i:]).strip("\n")


def require(fields, names, path, entry_id):
    missing = [n for n in names if not fields.get(n)]
    if missing:
        raise FormatError(f"{path}: {entry_id} is missing field(s): {', '.join(missing)}")


def parse_date_field(value):
    """Optional dates (e.g. Delivered) may be YYYY-MM-DD. Return a date or None."""
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def parse_worklog(path):
    meta, body = split_metadata(path.read_text(encoding="utf-8"), path)
    entries = []
    seen = {}
    for head, chunk in split_entries(body, path):
        when, wtype, entry_id = parse_worklog_heading(head, path)
        if entry_id in seen:
            raise FormatError(
                f"{path}: duplicate id {entry_id} (entries dated {seen[entry_id]} and {when})"
            )
        seen[entry_id] = when
        if wtype not in WORK_TYPES:
            raise FormatError(
                f"{path}: {entry_id} has unknown type {wtype!r}; expected one of {', '.join(WORK_TYPES)}"
            )
        fields, rest = parse_fields(chunk)
        require(fields, ["Title", "Requested by", "Modules", "Effort", "Status"], path, entry_id)

        impact = ""
        m = re.search(r"^\*\*Impact:\*\*\s*(.+)$", rest, flags=re.M | re.S)
        if m:
            impact = " ".join(m.group(1).split())
            rest = rest[: m.start()].strip()

        entries.append(
            {
                "id": entry_id,
                "date": when,
                "delivered": parse_date_field(fields.get("Delivered", "")),
                "type": wtype,
                "fields": fields,
                "body": " ".join(rest.split()),
                "impact": impact,
            }
        )
    entries.sort(key=lambda e: (e["date"], e["id"]), reverse=True)
    return meta, entries


def split_recording(chunk):
    """Pull an optional leading **Recording:** url line; keep the rest verbatim."""
    lines = chunk.split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    recording = ""
    if i < len(lines):
        m = re.match(r"\*\*Recording:\*\*\s*(.+)$", lines[i].strip())
        if m:
            recording = m.group(1).strip()
            i += 1
    mom = "\n".join(lines[i:]).strip("\n")
    return recording, mom


def parse_meetings(path):
    """Meetings are stored as a verbatim archive: date, optional recording, and the
    minutes exactly as pasted. No sections are parsed out of the body."""
    meta, body = split_metadata(path.read_text(encoding="utf-8"), path)
    entries = []
    seen = {}
    for head, chunk in split_entries(body, path):
        when, entry_id = parse_meeting_heading(head, path)
        if entry_id in seen:
            raise FormatError(
                f"{path}: duplicate id {entry_id} (entries dated {seen[entry_id]} and {when})"
            )
        seen[entry_id] = when
        recording, mom = split_recording(chunk)
        entries.append(
            {"id": entry_id, "date": when, "recording": recording, "mom": mom}
        )
    entries.sort(key=lambda e: (e["date"], e["id"]), reverse=True)
    return meta, entries


# ---------------------------------------------------------------- rendering

CSS = """
:root{
  --paper:#FCFCFA; --ink:#191C1F; --muted:#5C636B; --faint:#8A9098;
  --rule:#E4E3DD; --rail:#D6D5CE; --panel:#F5F4F0; --flash:#FBF3E7;
  --feature:#1C6B49; --change:#8C3D14; --enhancement:#2A5580; --bugfix:#7E2B3A;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
  --mono:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif);
  font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:960px;margin:0 auto;padding:56px 32px 96px}

header.doc{border-bottom:1px solid var(--ink);padding-bottom:20px;margin-bottom:8px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--faint);margin:0 0 10px}
h1{font-size:34px;font-weight:400;letter-spacing:-.015em;margin:0 0 6px}
.sub{color:var(--muted);font-size:15px;margin:0}
.sub b{font-weight:600;color:var(--ink)}

/* view toggle — work log <-> meeting record */
.views{display:flex;gap:0;border-bottom:1px solid var(--rule);margin:22px 0 28px}
.views .view-tab{font-family:var(--mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;
  background:none;border:none;border-bottom:2px solid transparent;color:var(--muted);
  padding:10px 2px;margin-right:28px;cursor:pointer;transition:color .15s,border-color .15s}
.views .view-tab:hover{color:var(--ink)}
.views .view-tab[aria-selected=true]{color:var(--ink);border-bottom-color:var(--ink)}
.views .view-tab:focus-visible{outline:2px solid var(--ink);outline-offset:2px}
.view{display:none}
.view.active{display:block}

.tally{display:flex;flex-wrap:wrap;gap:0;border-bottom:1px solid var(--rule);margin-bottom:28px}
.tally div{padding:16px 26px 16px 0;margin-right:26px}
.tally .n{font-family:var(--mono);font-size:26px;line-height:1;display:block;margin-bottom:6px}
.tally .k{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.n.feature{color:var(--feature)} .n.change{color:var(--change)}
.n.enhancement{color:var(--enhancement)} .n.bugfix{color:var(--bugfix)}

.filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:34px}
.filters button{font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  background:none;border:1px solid var(--rule);color:var(--muted);padding:7px 13px;border-radius:2px;
  cursor:pointer;transition:border-color .15s,color .15s}
.filters button:hover{border-color:var(--rail);color:var(--ink)}
.filters button[aria-pressed=true]{border-color:var(--ink);color:var(--ink);background:var(--panel)}
.filters button:focus-visible{outline:2px solid var(--ink);outline-offset:2px}

/* the date rail — chronology as the spine of the document */
.log{position:relative;padding-left:132px}
.log::before{content:"";position:absolute;left:104px;top:6px;bottom:6px;width:1px;background:var(--rail)}
.entry{position:relative;padding:0 0 40px}
.entry::before{content:"";position:absolute;left:-33px;top:11px;width:9px;height:9px;border-radius:50%;
  background:var(--paper);border:1px solid var(--rail)}
.entry[data-type=change]::before{background:var(--change);border-color:var(--change)}
.stamp{position:absolute;left:-132px;top:2px;width:76px;text-align:right;font-family:var(--mono);
  font-size:12px;line-height:1.5;color:var(--muted)}
.stamp .yr{display:block;color:var(--faint);font-size:11px}

.kind{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  display:block;margin-bottom:5px}
.kind.feature{color:var(--feature)} .kind.change{color:var(--change)}
.kind.enhancement{color:var(--enhancement)} .kind.bugfix{color:var(--bugfix)}
.kind.meeting{color:var(--muted)}
.entry h2{font-size:20px;font-weight:400;line-height:1.35;margin:0 0 10px;letter-spacing:-.01em}
.entry h2 .ref{font-family:var(--mono);font-size:11px;color:var(--faint);letter-spacing:.06em;
  margin-left:9px;vertical-align:2px}
.entry p{margin:0 0 12px;color:#2E3338}
.impact{border-left:2px solid var(--change);background:var(--panel);padding:11px 15px;border-radius:0;
  font-size:15px;color:#2E3338;margin:0 0 12px}
.impact b{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--change);display:block;margin-bottom:4px;font-weight:400}

dl.meta{display:grid;grid-template-columns:auto 1fr;gap:3px 16px;margin:0;font-size:14px}
dl.meta dt{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;
  color:var(--faint);padding-top:3px}
dl.meta dd{margin:0;color:var(--muted)}
.pill{font-family:var(--mono);font-size:10px;letter-spacing:.07em;text-transform:uppercase;
  border:1px solid var(--rule);padding:2px 7px;border-radius:2px;color:var(--muted)}
.pill.delivered{border-color:var(--feature);color:var(--feature)}
.pill.blocked,.pill.reverted{border-color:var(--bugfix);color:var(--bugfix)}
.pill.progress{border-color:var(--enhancement);color:var(--enhancement)}
a.mtg{font-family:var(--mono);color:var(--enhancement);text-decoration:underline;
  text-underline-offset:2px;text-decoration-thickness:1px;text-decoration-color:var(--rule);cursor:pointer}
a.mtg:hover{text-decoration-color:currentColor}

/* meeting record — verbatim minutes, rendered faithfully */
.mom{white-space:pre-wrap;font-family:var(--serif);font-size:15px;line-height:1.7;color:#2E3338;margin:2px 0 0}
.mom strong{font-weight:600;color:var(--ink)}
.rec{font-family:var(--mono);font-size:12px;margin-bottom:12px}
a{color:var(--enhancement);text-decoration:underline;text-underline-offset:2px;
  text-decoration-thickness:1px;text-decoration-color:var(--rule)}
a:hover{text-decoration-color:currentColor}
.empty{color:var(--faint);font-style:italic;padding:40px 0}
.entry.flash{animation:flash 1.5s ease-out}
@keyframes flash{0%{background:var(--flash)}100%{background:transparent}}
footer{margin-top:56px;padding-top:18px;border-top:1px solid var(--rule);
  font-family:var(--mono);font-size:11px;color:var(--faint);letter-spacing:.04em}

@media (max-width:680px){
  .wrap{padding:34px 20px 64px}
  .log{padding-left:0}
  .log::before{display:none}
  .entry::before{display:none}
  .stamp{position:static;width:auto;text-align:left;margin-bottom:7px}
  .stamp .yr{display:inline;margin-left:5px}
  h1{font-size:27px}
}
@media print{
  .filters,.views{display:none}
  .view{display:block!important}
  body{background:#fff;font-size:12pt}
  .wrap{max-width:none;padding:0}
  .entry{break-inside:avoid;page-break-inside:avoid}
}
"""

SCRIPT = """
(function(){
  function showView(name){
    document.querySelectorAll('.view').forEach(function(v){
      v.classList.toggle('active', v.id === 'view-' + name);
    });
    document.querySelectorAll('.view-tab').forEach(function(b){
      b.setAttribute('aria-selected', String(b.dataset.view === name));
    });
  }
  var nav = document.querySelector('.views');
  if(nav){
    nav.addEventListener('click', function(e){
      var b = e.target.closest('.view-tab'); if(!b) return;
      showView(b.dataset.view);
    });
  }
  // cross-link: a worklog entry -> the meeting it came from
  document.addEventListener('click', function(e){
    var a = e.target.closest('a[href^="#MTG-"]'); if(!a) return;
    e.preventDefault();
    var id = a.getAttribute('href').slice(1);
    showView('meetings');
    var el = document.getElementById(id);
    if(el){
      el.scrollIntoView({behavior:'smooth', block:'start'});
      el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash');
    }
  });
  // type filter (work log only)
  var bar = document.querySelector('.filters');
  if(bar){
    bar.addEventListener('click', function(e){
      var b = e.target.closest('button'); if(!b) return;
      var want = b.dataset.filter;
      bar.querySelectorAll('button').forEach(function(x){
        x.setAttribute('aria-pressed', String(x === b));
      });
      document.querySelectorAll('#view-worklog .entry').forEach(function(el){
        el.hidden = !(want === 'all' || el.dataset.type === want);
      });
      var vis = document.querySelectorAll('#view-worklog .entry:not([hidden])').length;
      var msg = document.getElementById('none');
      if(msg) msg.hidden = vis > 0;
    });
  }
})();
"""


def esc(s):
    return html.escape(s or "", quote=False)


def linkify_urls(s):
    return re.sub(r"(https?://[^\s<]+)", r'<a href="\1" rel="noopener">\1</a>', s)


def link_mtg(value):
    """Escape a field value, then turn every MTG-#### token into a jump link.
    All references are validated before render, so every token resolves."""
    v = esc(value)
    return re.sub(r"MTG-\d{4}", lambda m: f'<a class="mtg" href="#{m.group(0)}">{m.group(0)}</a>', v)


def render_mom(text):
    """Verbatim minutes: escape, honour **bold** and bare URLs, preserve every
    line break and space (the container is white-space:pre-wrap). Nothing is
    reworded, reordered, or classified."""
    out = esc(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = linkify_urls(out)
    return out


def stamp(d):
    return f'<span class="stamp">{d.strftime("%d %b")}<span class="yr">{d.year}</span></span>'


def fmt_long(d):
    return f'{d.day} {d.strftime("%B %Y")}'


def render_worklog(entries):
    counts = {t: sum(1 for e in entries if e["type"] == t) for t in WORK_TYPES}

    tally = ['<div class="tally">']
    tally.append(
        f'<div><span class="n">{len(entries)}</span><span class="k">Entries logged</span></div>'
    )
    for t in WORK_TYPES:
        if counts[t]:
            slug = TYPE_SLUG[t]
            tally.append(
                f'<div><span class="n {slug}">{counts[t]}</span>'
                f'<span class="k">{esc(t)}{"s" if counts[t] != 1 else ""}</span></div>'
            )
    tally.append("</div>")

    filters = ['<div class="filters" role="group" aria-label="Filter by type">']
    filters.append('<button data-filter="all" aria-pressed="true">All</button>')
    for t in WORK_TYPES:
        if counts[t]:
            filters.append(
                f'<button data-filter="{TYPE_SLUG[t]}" aria-pressed="false">{esc(t)}</button>'
            )
    filters.append("</div>")

    rows = ['<div class="log">']
    for e in entries:
        f = e["fields"]
        slug = TYPE_SLUG[e["type"]]
        status = f.get("Status", "")
        rows.append(f'<article class="entry" id="{e["id"]}" data-type="{slug}">')
        rows.append(stamp(e["date"]))
        rows.append(f'<span class="kind {slug}">{esc(e["type"])}</span>')
        rows.append(f'<h2>{esc(f["Title"])}<span class="ref">{esc(e["id"])}</span></h2>')
        if e["body"]:
            rows.append(f'<p>{esc(e["body"])}</p>')
        if e["impact"]:
            rows.append(f'<p class="impact"><b>Knock-on effect</b>{esc(e["impact"])}</p>')
        rows.append("<dl class='meta'>")
        rows.append(f'<dt>Requested by</dt><dd>{link_mtg(f["Requested by"])}</dd>')
        rows.append(f'<dt>Modules</dt><dd>{esc(f["Modules"])}</dd>')
        rows.append(f'<dt>Effort</dt><dd>{esc(f["Effort"])}</dd>')
        if e["delivered"] and e["delivered"] != e["date"]:
            rows.append(
                f'<dt>Delivered</dt><dd>logged {fmt_long(e["date"])}, delivered {fmt_long(e["delivered"])}</dd>'
            )
        rows.append(
            f'<dt>Status</dt><dd><span class="pill {STATUS_SLUG.get(status, "")}">'
            f"{esc(status)}</span></dd>"
        )
        rows.append("</dl></article>")
    rows.append('<p class="empty" id="none" hidden>Nothing matches that filter.</p>')
    rows.append("</div>")

    return "\n".join(tally + filters + rows)


def render_meetings(entries):
    recorded = sum(1 for e in entries if e["recording"])

    tally = ['<div class="tally">']
    tally.append(
        f'<div><span class="n">{len(entries)}</span><span class="k">Meetings held</span></div>'
    )
    tally.append(
        f'<div><span class="n enhancement">{recorded}</span><span class="k">With recording</span></div>'
    )
    tally.append("</div>")

    rows = ['<div class="log">']
    if not entries:
        rows.append('<p class="empty">No meetings recorded yet.</p>')
    for e in entries:
        rows.append(f'<article class="entry meeting-entry" id="{e["id"]}">')
        rows.append(stamp(e["date"]))
        rows.append('<span class="kind meeting">Meeting record</span>')
        rows.append(f'<h2>{esc(fmt_long(e["date"]))}<span class="ref">{esc(e["id"])}</span></h2>')
        if e["recording"]:
            rows.append(
                f'<p class="rec"><a href="{esc(e["recording"])}" rel="noopener">Watch the recording</a></p>'
            )
        rows.append(f'<div class="mom">{render_mom(e["mom"])}</div>')
        rows.append("</article>")
    rows.append("</div>")

    return "\n".join(tally + rows)


def page(meta, worklog_html, meetings_html, wl_count, mtg_count):
    project = esc(meta.get("project", "Project"))
    client = esc(meta.get("client", ""))
    started = meta.get("started", "")
    sub = f"Prepared for <b>{client}</b>" if client else ""
    if started:
        sub += f" &nbsp;{SEP}&nbsp; project started {esc(started)}"
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project record — {project}</title>
<style>{CSS}</style>
</head><body>
<div class="wrap">
<header class="doc">
  <p class="eyebrow">Project record</p>
  <h1>{project}</h1>
  <p class="sub">{sub}</p>
</header>
<nav class="views" role="tablist" aria-label="Switch view">
  <button class="view-tab" data-view="worklog" role="tab" aria-selected="true">Work log</button>
  <button class="view-tab" data-view="meetings" role="tab" aria-selected="false">Meeting record</button>
</nav>
<div class="view active" id="view-worklog" role="tabpanel">
{worklog_html}
</div>
<div class="view" id="view-meetings" role="tabpanel">
{meetings_html}
</div>
<footer>Generated {date.today().strftime("%d %B %Y")} — built from the project record and regenerated on each update. {wl_count} work entries {SEP} {mtg_count} meetings.</footer>
</div>
<script>{SCRIPT}</script>
</body></html>
"""


def check_cross_references(wl_entries, meeting_ids, wl_path):
    """A work entry pointing at a meeting that isn't in the record is worse than
    no link at all — it looks like evidence until someone clicks it. Fail loud."""
    for e in wl_entries:
        for mid in re.findall(r"MTG-\d{4}", e["fields"].get("Requested by", "")):
            if mid not in meeting_ids:
                raise FormatError(
                    f"{wl_path}: {e['id']} references {mid}, which is not in the meeting record"
                )


# ---------------------------------------------------------------- main


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    docs = root / "docs"
    out = docs / "public"
    out.mkdir(parents=True, exist_ok=True)

    wl_path = docs / "worklog.md"
    mt_path = docs / "meetings.md"

    if not wl_path.exists():
        print("Nothing to build — no docs/worklog.md found.", file=sys.stderr)
        raise SystemExit(1)

    try:
        meeting_meta, meeting_entries = (
            parse_meetings(mt_path) if mt_path.exists() else ({}, [])
        )
        wl_meta, wl_entries = parse_worklog(wl_path)

        # Fail loud on a dead cross-reference: a work entry pointing at a meeting
        # that isn't in the record is worse than no link — it looks like evidence
        # until someone clicks it.
        meeting_ids = {e["id"] for e in meeting_entries}
        check_cross_references(wl_entries, meeting_ids, wl_path)

        meta = {**meeting_meta, **wl_meta}  # worklog metadata wins for the header
        html_out = page(
            meta,
            render_worklog(wl_entries),
            render_meetings(meeting_entries),
            len(wl_entries),
            len(meeting_entries),
        )
        (out / "report.html").write_text(html_out, encoding="utf-8")
    except FormatError as err:
        print(f"Build failed.\n  {err}", file=sys.stderr)
        print("  See references/formats.md in the project-journal skill for the required shape.", file=sys.stderr)
        raise SystemExit(1)

    counts = {t: sum(1 for e in wl_entries if e["type"] == t) for t in WORK_TYPES}
    summary = ", ".join(
        f"{n} {t.lower()}{'s' if n != 1 else ''}" for t, n in counts.items() if n
    )
    print("Built docs/public/report.html")
    print(f"  Work log — {len(wl_entries)} entries ({summary})")
    print(f"  Meeting record — {len(meeting_entries)} meetings")


if __name__ == "__main__":
    main()
