# Entry formats

The build script parses these files with a strict reader. Deviating from these shapes will fail the build. The strictness is deliberate — it is what lets the HTML be generated reliably instead of hand-maintained.

The build produces a single file, `docs/public/report.html`, containing both the work log and the meeting record with a toggle between them. It is regenerated on request, not on every edit.

---

## docs/worklog.md

### File header

```markdown
---
project: Acme Portal
client: Acme Corp
started: 2026-06-04
---

# Work log
```

Everything between the `---` fences is metadata rendered into the report header. `project` and `client` are required; `started` is optional but makes the report read better.

### Entry

```markdown
## 2026-08-17 · Change request · WL-0042
**Title:** Checkout now completes on a single page
**Requested by:** Ayesha Khan (client) — MTG-0018
**Modules:** Checkout, Orders API
**Effort:** 6h
**Status:** Delivered

The three-step checkout was collapsed into one page at the client's request
after the 14 August call. Address, delivery and payment now sit on one form
with inline validation.

**Impact:** The step-2 and step-3 analytics events no longer fire. Funnel
reporting in the admin panel needs re-wiring before the next reporting cycle.
```

**The heading line** is `## ` then three parts separated by ` · ` (space, middle dot U+00B7, space):

1. Date, `YYYY-MM-DD` — the date the entry is attributed to. For work logged on completion this is the completion date; for work logged while still in progress it is the day it was started.
2. Type, exactly one of: `New feature`, `Change request`, `Enhancement`, `Bug fix`
3. Entry ID, `WL-` plus four digits, incrementing, never reused

**The field block** follows immediately, one `**Key:** value` per line, no blank lines between them:

| Field | Required | Notes |
|---|---|---|
| `Title` | yes | One line, client-readable, no trailing period |
| `Requested by` | yes | Person and source. Append ` — MTG-XXXX` when it came from a meeting; the build turns that ID into a link to the meeting |
| `Modules` | yes | Comma-separated areas of the system |
| `Effort` | yes | `6h`, `2d`, or `—` if genuinely unknown |
| `Status` | yes | `Delivered`, `In progress`, `Blocked`, or `Reverted` |
| `Delivered` | no | `YYYY-MM-DD`. Only used when an entry was first logged `In progress` and later delivered. When present and different from the heading date, the report shows both — "logged X, delivered Y" |

**The body** is one blank line after the field block, then free prose. Two or three sentences. Written for the client, not the repo. If there is a meaningful before → after, open the body with the before.

**Impact** is optional and goes last, as a `**Impact:** …` paragraph. Use it when the change created follow-on work, broke an assumption, or has a cost the client should see coming. This field is why change requests stop being free.

Entries are newest first, directly under `# Work log`.

**The `MTG-XXXX` reference is validated at build time.** If a work entry points at a meeting ID that is not in `docs/meetings.md`, the build fails and names the entry. A reference that looks like evidence but resolves to nothing is worse than no reference at all, so a dead link is never published.

---

## docs/meetings.md

The meeting record is a **verbatim archive**. The minutes are stored exactly as they were pasted — nothing is reworded, reordered, or classified. A verbatim copy cannot be accused of being selectively edited, which is what makes it strong evidence.

### File header

Same fenced metadata block, then `# Meeting record`.

### Entry

```markdown
## 2026-08-14 · MTG-0018
**Recording:** https://meet.example.com/rec/2026-08-14-weekly

<the minutes, exactly as the PM sent them — numbered points, bullets, prose,
whatever shape they came in. Left untouched.>
```

**The heading line** is `## ` then two parts separated by ` · `:

1. Date, `YYYY-MM-DD` — read from the top of the pasted minutes when the skill logs the meeting
2. Meeting ID, `MTG-` plus four digits

There is **no meeting-kind segment** and there are **no parsed sections** (no `### Discussed`, `### Decisions`, etc.). That structure belonged to the old format; the record is now a faithful copy, not a parsed document.

**The field block** is a single optional field:

| Field | Required | Notes |
|---|---|---|
| `Recording` | no | Full URL. Renders as a "Watch the recording" link. If the minutes arrive without one, the skill asks for it once — a meeting record without the recording is much weaker evidence |

**Everything after the optional `Recording` line is the minutes, stored verbatim.** The report renders them faithfully: line breaks and spacing are preserved, `**bold**` and bare URLs are honoured, and nothing else is added. Bugs, change requests and new features raised in a meeting are **not** extracted here — they are logged separately in `docs/worklog.md` as the work is actually done, each tagged with this meeting's ID so the two records link up.

Entries are newest first, under `# Meeting record`.

---

## How the two files link

The link is **one-way: a work entry points back to the meeting it came from.** A `Requested by: … — MTG-0018` line becomes a clickable reference in the report; clicking it switches to the meeting record and jumps to that meeting, where the minutes and the recording are. There is no link in the other direction — the meeting record is a plain archive with nothing to link out from — and that is the direction that matters: one hop from a disputed change to the call where it was agreed.

---

## ID allocation

Read the file, take the highest existing number, add one. IDs are never reused, never renumbered, and never deleted — a `Reverted` status exists precisely so that abandoned work stays visible in the record rather than disappearing from it. (The one moment renumbering is acceptable is resolving a merge conflict between two branches that both allocated the same new ID, and only before that ID has been referenced anywhere.)
