<h1 align="center">Project Journal</h1>

<p align="center">
  A Claude Code skill that keeps a <b>client-facing work log and meeting record</b><br>
  for a software project — and generates a single HTML report from them.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License: MIT">
  <img src="https://img.shields.io/badge/python-3.8%2B-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Claude_Code-skill%20%2B%20plugin-8A63D2?style=for-the-badge" alt="Claude Code skill + plugin">
  <img src="https://img.shields.io/badge/dependencies-none-brightgreen?style=for-the-badge" alt="No dependencies">
</p>

---

Every change links back to the meeting the client asked for it in — so when a
client says *"we never asked for that"* or *"why did this take three weeks,"* the
answer is a dated entry with the recording one click away.

You log work through `/project-journal` as you finish it, store meeting minutes
verbatim, and rebuild the report on demand. Two markdown files are the single
source of truth; the HTML is a **generated artifact**, never hand-edited.

## Features

- **Command-driven logging** — `/project-journal log: …` records a unit of
  delivered work; the skill assigns the type and ID for you.
- **Automatic classification** — every entry is typed as **new feature**,
  **change request**, **enhancement**, or **bug fix**, consistently, because the
  change-request count is what a billing conversation turns on.
- **Verbatim meeting record** — minutes stored as-is, each with its recording
  link, cross-linked to the work it produced.
- **Generated HTML report** — one `docs/public/report.html` that opens on the
  work log and toggles to the meeting record.
- **Fails loudly** — the build refuses to ship on a malformed entry, duplicate
  ID, or dead meeting reference instead of handing a client a broken report.
- **Zero dependencies** — pure Python 3 standard library. Nothing to `pip install`.

## Installation

You can install this **two ways** — pick whichever you prefer. Both give you the
same `/project-journal` command.

### Option 1 — Claude Code marketplace (in-app, no terminal)

Run these inside Claude Code:

```
/plugin marketplace add mehtabismail/project-journal
/plugin install project-journal@mehtabismail
```

Claude Code fetches the repo, installs the plugin, and `/project-journal` is
ready. Update later with `/plugin marketplace update mehtabismail`.

### Option 2 — Git clone into your skills directory

```bash
git clone https://github.com/mehtabismail/project-journal.git ~/.claude/skills/project-journal
```

The clone destination folder name — `project-journal` — is what becomes the
command, so keep it exactly as above. Update later with:

```bash
cd ~/.claude/skills/project-journal && git pull
```

> **Per-project instead of personal?** Clone into `.claude/skills/project-journal`
> inside a specific project rather than `~/.claude/skills/`.

## Prerequisites

Python 3.8+ is required for the report generator (standard library only — the
scripts install nothing and make no network calls). Check with:

```bash
python3 --version
```

If it is missing, install it from [python.org](https://www.python.org/downloads/)
or with your OS package manager (Homebrew, apt, winget).

## Usage

Everything runs through `/project-journal` inside a project:

```
# Log finished work — the skill classifies the type and assigns the ID for you
/project-journal log: collapsed checkout into one page. requested by the client, from the 14 Aug call. modules: checkout. effort 6h. status delivered.

# Store meeting minutes, verbatim, with the recording link
/project-journal meeting: https://meet.example.com/rec/2026-08-14
<paste the minutes here>

# Build the client-facing HTML report (docs/public/report.html)
/project-journal build the report

# Just ask — no rebuild needed
/project-journal how many change requests since the last invoice?
```

On first use in a project the skill creates `docs/worklog.md` and
`docs/meetings.md` (asking once for the project and client name). You log work as
you finish it; the report is generated on request.

### The four entry types

The skill — not the developer — assigns the type, because the change-request
count is what a billing conversation counts and it has to be consistent:

| Type | Meaning |
|---|---|
| **New feature** | New, and in the agreed scope. |
| **Change request** | The client asked for something different or out of scope. *(the one that matters commercially)* |
| **Enhancement** | A team-initiated improvement to something that already worked. |
| **Bug fix** | Restoring behaviour that was already agreed and built. |

The requester tag decides the confusable pair: `(client)` → change request,
`(team)` → enhancement.

## What's in here

```
project-journal/
├── .claude-plugin/           marketplace + plugin manifests (Option 1 install)
│   ├── marketplace.json
│   └── plugin.json
├── SKILL.md                  the skill: classification rules + workflow
├── references/
│   └── formats.md            exact entry formats the parser depends on
└── scripts/
    ├── build_reports.py      markdown → HTML generator (stdlib only)
    └── test_build.py         parser + renderer test suite
```

The same root `SKILL.md` powers both install methods: cloned into a skills
directory it loads as a standalone skill, and via the marketplace the repo root
is installed as a single-skill plugin.

Run the tests:

```bash
python3 ~/.claude/skills/project-journal/scripts/test_build.py
```

## Troubleshooting

**`/project-journal` doesn't appear after installing.** Restart Claude Code (or
start a fresh session) so it re-scans skills and plugins.

**Git-clone install: command name is wrong.** The command comes from the clone
folder name. Make sure you cloned into `…/skills/project-journal`, not a
differently named folder.

**The build errors out instead of producing a report.** That's intended — it
refuses to generate from a malformed entry, a duplicate ID, or a meeting
reference that points at a meeting that doesn't exist. The error names the entry;
fix the markdown and rebuild.

**`python3: command not found`.** Install Python 3.8+ (see
[Prerequisites](#prerequisites)).

## License

[MIT](LICENSE) © Mehtab Ismail
