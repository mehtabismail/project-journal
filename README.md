<h1 align="center">Project Journal</h1>

<p align="center">
  An Agent Skill for <b>Cursor</b> and <b>Claude Code</b> that keeps a
  <b>client-facing work log and meeting record</b><br>
  for a software project — and generates a single HTML report from them.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License: MIT">
  <img src="https://img.shields.io/badge/python-3.8%2B-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Cursor-Agent_Skill-0098FF?style=for-the-badge" alt="Cursor Agent Skill">
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

This is a standard [Agent Skill](https://docs.cursor.com/docs/skills), so it runs
in both **Cursor** and **Claude Code**. Pick your tool below — each path is
self-contained, and every one gives you the same `/project-journal` command.

<details open>
<summary><b>🟦 Cursor</b> (no Claude Code needed)</summary>

<br>

You do **not** need Claude Code or a `.claude` folder. Clone the skill into your
personal Cursor skills directory:

```bash
git clone https://github.com/mehtabismail/project-journal.git ~/.cursor/skills/project-journal
```

`git clone` creates the `~/.cursor/skills/` folder for you if it doesn't exist yet
— nothing to set up first. Then restart Cursor and invoke it by typing `/` in
Agent chat and picking **project-journal**.

- **Per-project instead?** Clone into `.cursor/skills/project-journal` inside a
  specific repo rather than `~/.cursor/skills/`.
- **Prefer the vendor-neutral location?** `~/.agents/skills/project-journal`
  (or `.agents/skills/project-journal` per-project) works identically.
- **Update later:** `cd ~/.cursor/skills/project-journal && git pull`

</details>

<details>
<summary><b>🟪 Claude Code</b></summary>

<br>

**Option A — Marketplace (in-app, no terminal).** Run these inside Claude Code:

```
/plugin marketplace add mehtabismail/project-journal
/plugin install project-journal@mehtabismail
```

Update later with `/plugin marketplace update mehtabismail`.

**Option B — Git clone into your skills directory:**

```bash
git clone https://github.com/mehtabismail/project-journal.git ~/.claude/skills/project-journal
```

The clone folder name — `project-journal` — is what becomes the command, so keep
it exactly as above. Per-project: clone into `.claude/skills/project-journal`
inside a repo. Update later with `cd ~/.claude/skills/project-journal && git pull`.

</details>

> **Already use it in one tool and want the other?** You don't have to install
> twice. Cursor also loads skills from Claude's directories (`~/.claude/skills/`,
> `.claude/skills/`) for compatibility, so an existing Claude install is picked up
> by Cursor automatically. (It does not work the other way around — Claude Code
> does not read `~/.cursor/skills/`.)

The only runtime difference between the two tools is the report-build command:
Claude Code expands `${CLAUDE_SKILL_DIR}`, while Cursor uses the skill's own
directory path. The skill's own instructions cover both, so you never have to
think about it.

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
├── SKILL.md                  the skill: classification rules + workflow
├── references/
│   └── formats.md            exact entry formats the parser depends on
├── scripts/
│   ├── build_reports.py      markdown → HTML generator (stdlib only)
│   └── test_build.py         parser + renderer test suite
└── .claude-plugin/           Claude Code marketplace/plugin manifests (ignored by Cursor)
    ├── marketplace.json
    └── plugin.json
```

The same root `SKILL.md` drives every install path: cloned into a Cursor or
Claude skills directory it loads as a standalone Agent Skill, and via the Claude
Code marketplace the repo root is installed as a single-skill plugin. Cursor
simply ignores the `.claude-plugin/` folder.

Run the tests (`python3 <skill-dir>/scripts/test_build.py`) — e.g. for a Cursor
personal install:

```bash
python3 ~/.cursor/skills/project-journal/scripts/test_build.py
```

## Troubleshooting

**`/project-journal` doesn't appear after installing.** Restart your editor
(Cursor or Claude Code) so it re-scans its skills directories, then type `/` in
Agent chat and search for it.

**Cursor: clone folder must be right.** Make sure you cloned into a directory
Cursor scans — `~/.cursor/skills/project-journal`, `.cursor/skills/project-journal`,
or the vendor-neutral `~/.agents/skills/project-journal`. The skill's `name`
(`project-journal`) must match its folder name, which the clone command already
ensures.

**Command name is wrong.** The invocation name comes from the skill folder. Make
sure you cloned into `…/skills/project-journal`, not a differently named folder.

**The build errors out instead of producing a report.** That's intended — it
refuses to generate from a malformed entry, a duplicate ID, or a meeting
reference that points at a meeting that doesn't exist. The error names the entry;
fix the markdown and rebuild.

**`python3: command not found`.** Install Python 3.8+ (see
[Prerequisites](#prerequisites)).

## License

[MIT](LICENSE) © Mehtab Ismail
