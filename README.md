# project-journal — a Claude Code skill

Keep a **client-facing work log and meeting record** for a software project, and
generate a single HTML report from them. Every change links back to the meeting
the client asked for it in — so when a client says *"we never asked for that"* or
*"why did this take three weeks,"* the answer is a dated entry with the recording
one click away.

It's one self-contained [Claude Code skill](https://code.claude.com/docs/en/skills).
No plugin, no marketplace — drop the folder into your skills directory and type
`/project-journal`.

---

## Install

Clone this repo straight into your personal skills directory:

```bash
git clone https://github.com/mehtabismail/project-journal.git ~/.claude/skills/project-journal
```

That's it. Open (or restart) Claude Code in any project and `/project-journal` is
available. The folder name — `project-journal` — is what becomes the command, so
keep the clone destination exactly as above.

**Per-project instead of personal?** Clone into `.claude/skills/project-journal`
inside a specific project rather than `~/.claude/skills/`.

**Update later:**

```bash
cd ~/.claude/skills/project-journal && git pull
```

Requires Python 3.8+ (standard library only — nothing to `pip install`).

---

## Use

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

- **New feature** — new, and in the agreed scope.
- **Change request** — the client asked for something different or out of scope. *(the one that matters commercially)*
- **Enhancement** — a team-initiated improvement to something that already worked.
- **Bug fix** — restoring behaviour that was already agreed and built.

The requester tag decides the confusable pair: `(client)` → change request,
`(team)` → enhancement.

---

## What's in here

```
project-journal/
├── SKILL.md                 the skill: classification rules + workflow
├── references/
│   └── formats.md           exact entry formats the parser depends on
└── scripts/
    ├── build_reports.py     markdown → HTML generator (stdlib only)
    └── test_build.py        parser + renderer test suite
```

Two markdown files are the single source of truth; the HTML is a **generated
artifact** — built on demand, never hand-edited. The build fails loudly on any
malformed entry, duplicate ID, or dead meeting reference rather than shipping a
broken report to a client.

Run the tests:

```bash
python3 ~/.claude/skills/project-journal/scripts/test_build.py
```
