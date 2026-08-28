---
name: project-journal
description: >-
  Maintain a project's client-facing work log (docs/worklog.md) and meeting
  record (docs/meetings.md), and generate their HTML report. WRITING is explicit:
  a developer runs "/project-journal log: ..." to log finished work, or
  "/project-journal meeting: ..." to store meeting minutes. Also use this skill —
  including on its own when the user ASKS about the record rather than writing to
  it — for questions like "how many change requests since the last invoice", "what
  did we deliver in July", "which meeting did the checkout change come from", and
  when the user asks to "rebuild", "generate", or "build the client report".
  Prefer this skill over editing the files by hand — the entry format is strict
  and the HTML is generated, not written.
---

# Project journal

Two markdown files are the source of truth for everything the client is shown:

| File | Holds | Rebuilt as |
|---|---|---|
| `docs/worklog.md` | One entry per unit of delivered work, typed and dated | part of `docs/public/report.html` |
| `docs/meetings.md` | One entry per client meeting — the minutes, stored verbatim, with the recording link | part of `docs/public/report.html` |

Both render into a **single** generated file, `docs/public/report.html`, which opens on the work log and toggles to the meeting record. It is a **generated artifact** — never hand-edit it. Edit the markdown, then build.

The point of this record is defensibility. When a client says "we never asked for that" or "why did this take three weeks," the answer should be a dated entry that links back to the meeting where it was requested, with the recording one click away. Every decision below serves that.

These files live in the **user's project**, not in this skill. The scripts and the format reference are bundled with the skill; the records are per-project.

---

## First use in a project

Before the first log in a project, check that `docs/worklog.md` and `docs/meetings.md` exist. If either is missing, create it with the metadata header and nothing else, asking the developer once for the project and client name:

```markdown
---
project: <Project name>
client: <Client name>
started: <YYYY-MM-DD, optional>
---

# Work log
```

(The meeting file is the same header followed by `# Meeting record`.) Do not seed sample entries. See `references/formats.md`, bundled with this skill, for the exact shapes — read it before your first write of a session.

---

## How this skill is used

**Writing is explicit.** Developers log at the end of a task by naming the skill, so an entry is only ever created when someone deliberately creates one — the record never fills itself with half-formed entries pulled from mid-task chatter:

- `/project-journal log: <what changed>. requested by <name> (client|team)[, from MTG-XXXX or "the 14 Aug call"]. modules: <areas>. effort <Nh|—>. status <delivered|in progress|blocked>.`
- `/project-journal meeting: <recording url — optional>` followed by the pasted minutes.

**Reading is conversational.** Questions about the record ("how many change requests since June", "what shipped in July") are answered directly from the markdown — no invocation ceremony, no rebuild needed.

---

## Deciding the entry type

**The developer supplies the facts; this skill assigns the type.** Do not ask the developer to declare the type, and do not simply accept a type they assert — classify it here from what they describe and the requester tag. If ten developers each label their own work, the change-request count becomes ten people's opinions, and that count is the whole point of the system.

**New feature** — Something that did not exist in any form, and was in the agreed scope. The baseline the project was quoted against.

**Change request** — The client asked for something to work differently than previously agreed, or asked for something outside the original scope. The evidence of scope movement. If the work exists because the client changed their mind, it is a change request no matter how small.

**Enhancement** — An improvement to something that already worked, initiated by the team. Refactors, performance work, better error states, accessibility fixes.

**Bug fix** — Restoring intended behaviour that was already agreed and already built.

### The tag that decides it

The `(client|team)` tag on the requester is what separates the two types that look identical in a diff:

- **`(client)`** → the client asked → the change-request side of the line.
- **`(team)`** → a teammate asked → the enhancement side of the line.

So "requested by Saad (team)" is an enhancement; "requested by Saad, on behalf of the client (MTG-0021)" is a change request. Same person, different ledger. (New feature vs bug fix is decided separately: a new in-scope capability is a feature; restoring behaviour that was meant to work is a bug fix.)

**Examples:**
- "Redid the dashboard cards to load lazily, they were slow" → Enhancement (team-initiated).
- "Client wanted the dashboard weekly instead of monthly" → Change request (client-initiated).
- "Built the CSV export from the SOW" → New feature (new, in scope).
- "Export was dropping the last row" → Bug fix (restoring intended behaviour).

### Ask only when genuinely unsure

Apply the rules and log. **Echo the type back** in the reply so the developer can catch a wrong call — "Logged WL-0044 — Change request, Delivered." Only when you genuinely cannot tell change request from enhancement, **ask one short question before writing**. Clear cases: classify and log, no interruption. A misclassified change request is the one error that costs money later, so the ambiguous case is worth the one question.

---

## Logging work

1. Read `docs/worklog.md` for the current state and the highest existing `WL-` id.
2. Classify using the rules above. The developer never types the type or the id — assign both.
3. Append the entry at the **top** of the list, directly under `# Work log` — newest first.
4. Follow the exact format in `references/formats.md`.
5. Resolve the meeting reference. If the developer named a meeting by date ("the 14 Aug call"), look it up in `docs/meetings.md` and put its `MTG-` id in `Requested by`. If they gave the id directly, use it. If they tagged a meeting that has no matching entry, do not invent a link — tell them and offer to log it without one. Tagging a meeting is optional; plenty of work has none.
6. Do not invent effort. If the developer did not say how long it took, ask, or write `—`. A padded hour count in a client document is worse than a blank one.
7. Keep the description in the client's vocabulary. The developer may write in raw technical terms — turning "refactored CheckoutStepper" into "Checkout now completes on one page" and parking the detail in `Modules` is your job.
8. Do **not** rebuild the report automatically. The markdown update is the log; the HTML is generated on request (see below).

### Updating, not duplicating

Log at completion as `status delivered` — that is the default and keeps one entry per unit of work. If a task is logged `in progress` and finished later ("update WL-0044 to delivered"), **update that same entry**: flip its status to `Delivered` and add a `Delivered: YYYY-MM-DD` field. Do not write a second entry — that would double-count the work. The heading date stays as the day it was first logged; the report then shows "logged X, delivered Y."

---

## Logging a meeting

When the developer pastes minutes:

1. Read `docs/meetings.md` for the highest existing `MTG-` id.
2. Store the minutes **verbatim** — exactly as pasted. Do not reword, reorder, summarise, or pull out change requests and action items. The record is a faithful archive.
3. Assign the next `MTG-` id and append the meeting at the top, following `references/formats.md`.
4. Read the meeting date from the top of the minutes. If you cannot find a clear date, ask for it.
5. Capture the recording link if given. If the minutes arrive without one, ask for it once.
6. Do **not** touch the work log, and do **not** rebuild the report. Logging a meeting records the meeting only; the work it produced is logged separately, as it is actually done, each entry tagging this meeting's id.

---

## Generating the report

Run the bundled generator from the **project root** (so it finds `./docs`). The
script lives in this skill's own `scripts/` directory:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/build_reports.py"
```

`${CLAUDE_SKILL_DIR}` is set by Claude Code and expands to this skill's folder.
In other Agent-Skills runtimes (for example Cursor) that variable is **not** set —
run the same bundled script by the absolute path of this skill's own directory
instead (the folder this `SKILL.md` was loaded from):

```bash
python3 "<this-skill-directory>/scripts/build_reports.py"
```

It is the same file either way; only how the path is spelled differs.

Do this **when someone wants to show the client** — not after every log. It parses both markdown files and writes a single `docs/public/report.html` (work log + meeting record with a toggle). Standard library only, so it runs on any Python 3.8+.

The build **fails loudly** on a malformed entry, a duplicate ID, or a dead cross-reference (a work entry pointing at a meeting id that is not in the record) rather than publishing something broken. If it errors, the markdown does not match `references/formats.md` — fix the markdown, do not patch the script.

After building, tell the developer the new type counts. `1 new feature, 3 change requests, 1 enhancement, 1 bug fix` tells them the scope story in one line — that is what they will actually want to see.

---

## Answering questions from the record

The user will often ask rather than write — "what did we do in July", "how many change requests since the last invoice", "which meeting did the checkout change come from". Read the markdown and answer directly. No invocation, no rebuild.

When the answer is about scope movement, give the count and the dates, then offer a summary they can send. `11 change requests since 4 June` lands harder than prose.

---

## Reference

`references/formats.md` (bundled with this skill) — exact entry templates for both files, and the parsing rules the build depends on. Read it before writing your first entry in a session.
