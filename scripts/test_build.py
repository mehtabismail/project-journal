#!/usr/bin/env python3
"""Tests for build_reports.py — plain unittest, standard library only (invariant 5).

Run from anywhere:

    python3 skill/scripts/test_build.py

Covers the parser contract the build depends on: a known-good file parses, every
malformed shape is rejected, duplicate IDs and dead cross-references are rejected,
and the renderer escapes HTML, links meetings, and shows both dates.
"""

import os
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_reports as br


# ---------------------------------------------------------------- fixtures

WL_HEADER = "---\nproject: T\nclient: C\n---\n\n# Work log\n\n"
MT_HEADER = "---\nproject: T\nclient: C\n---\n\n# Meeting record\n\n"

VALID_WL_ENTRY = (
    "## 2026-08-14 · Bug fix · WL-0042\n"
    "**Title:** Fixed the thing\n"
    "**Requested by:** Bilal (client)\n"
    "**Modules:** Reporting\n"
    "**Effort:** 1h\n"
    "**Status:** Delivered\n\n"
    "Body text here.\n"
)

VALID_MT_ENTRY = (
    "## 2026-08-14 · MTG-0018\n"
    "**Recording:** https://example.com/rec\n\n"
    "Meeting: 14 August 2026\n"
    "A line with **bold** and a link https://example.com/x\n"
    "- a bullet\n"
    "1. a numbered point\n"
)


def _tmp(text):
    d = tempfile.mkdtemp()
    p = Path(d) / "f.md"
    p.write_text(text, encoding="utf-8")
    return p


def parse_wl(entry):
    return br.parse_worklog(_tmp(WL_HEADER + entry))


def parse_mt(entry):
    return br.parse_meetings(_tmp(MT_HEADER + entry))


# ---------------------------------------------------------------- good parses

class GoodWorklog(unittest.TestCase):
    def test_parses_fields_and_body(self):
        meta, entries = parse_wl(VALID_WL_ENTRY)
        self.assertEqual(meta["project"], "T")
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e["id"], "WL-0042")
        self.assertEqual(e["type"], "Bug fix")
        self.assertEqual(e["date"], date(2026, 8, 14))
        self.assertEqual(e["fields"]["Title"], "Fixed the thing")
        self.assertEqual(e["body"], "Body text here.")

    def test_newest_first(self):
        two = (
            "## 2026-08-10 · Bug fix · WL-0040\n**Title:** Old\n**Requested by:** X\n"
            "**Modules:** M\n**Effort:** 1h\n**Status:** Delivered\n\nb\n\n"
            "## 2026-08-20 · Bug fix · WL-0041\n**Title:** New\n**Requested by:** X\n"
            "**Modules:** M\n**Effort:** 1h\n**Status:** Delivered\n\nb\n"
        )
        _, entries = parse_wl(two)
        self.assertEqual([e["id"] for e in entries], ["WL-0041", "WL-0040"])

    def test_impact_and_delivered(self):
        entry = (
            "## 2026-08-14 · Change request · WL-0042\n"
            "**Title:** T\n**Requested by:** A (client)\n**Modules:** M\n"
            "**Effort:** 6h\n**Status:** Delivered\n**Delivered:** 2026-08-16\n\n"
            "Body.\n\n**Impact:** A knock-on cost.\n"
        )
        _, entries = parse_wl(entry)
        e = entries[0]
        self.assertEqual(e["impact"], "A knock-on cost.")
        self.assertEqual(e["delivered"], date(2026, 8, 16))


class GoodMeetings(unittest.TestCase):
    def test_verbatim_and_recording(self):
        meta, entries = parse_mt(VALID_MT_ENTRY)
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual(e["id"], "MTG-0018")
        self.assertEqual(e["date"], date(2026, 8, 14))
        self.assertEqual(e["recording"], "https://example.com/rec")
        # minutes stored verbatim; recording line stripped out of the body
        self.assertIn("Meeting: 14 August 2026", e["mom"])
        self.assertIn("1. a numbered point", e["mom"])
        self.assertIn("- a bullet", e["mom"])
        self.assertNotIn("**Recording:**", e["mom"])

    def test_recording_optional(self):
        entry = "## 2026-08-14 · MTG-0018\n\nJust the minutes, no recording.\n"
        _, entries = parse_mt(entry)
        self.assertEqual(entries[0]["recording"], "")
        self.assertIn("Just the minutes", entries[0]["mom"])


# ---------------------------------------------------------------- rejections

class MalformedWorklog(unittest.TestCase):
    def _bad(self, text):
        with self.assertRaises(br.FormatError):
            br.parse_worklog(_tmp(text))

    def test_no_metadata_block(self):
        self._bad("# Work log\n\n" + VALID_WL_ENTRY)

    def test_heading_wrong_part_count(self):
        self._bad(WL_HEADER + "## 2026-08-14 · WL-0042\n**Title:** T\n"
                  "**Requested by:** X\n**Modules:** M\n**Effort:** 1h\n**Status:** Delivered\n\nb\n")

    def test_bad_date(self):
        self._bad(WL_HEADER + "## 2026-13-40 · Bug fix · WL-0042\n**Title:** T\n"
                  "**Requested by:** X\n**Modules:** M\n**Effort:** 1h\n**Status:** Delivered\n\nb\n")

    def test_bad_id(self):
        self._bad(WL_HEADER + "## 2026-08-14 · Bug fix · W-42\n**Title:** T\n"
                  "**Requested by:** X\n**Modules:** M\n**Effort:** 1h\n**Status:** Delivered\n\nb\n")

    def test_unknown_type(self):
        self._bad(WL_HEADER + "## 2026-08-14 · Frobnicate · WL-0042\n**Title:** T\n"
                  "**Requested by:** X\n**Modules:** M\n**Effort:** 1h\n**Status:** Delivered\n\nb\n")

    def test_missing_required_field(self):
        self._bad(WL_HEADER + "## 2026-08-14 · Bug fix · WL-0042\n**Title:** T\n"
                  "**Requested by:** X\n**Modules:** M\n**Effort:** 1h\n\nb\n")  # no Status

    def test_duplicate_id(self):
        dup = VALID_WL_ENTRY + "\n" + VALID_WL_ENTRY  # WL-0042 twice
        self._bad(WL_HEADER + dup)


class MalformedMeetings(unittest.TestCase):
    def _bad(self, text):
        with self.assertRaises(br.FormatError):
            br.parse_meetings(_tmp(text))

    def test_heading_has_old_kind_segment(self):
        # old 3-part shape (date · kind · id) is no longer valid
        self._bad(MT_HEADER + "## 2026-08-14 · Weekly sync · MTG-0018\n\nminutes\n")

    def test_bad_id(self):
        self._bad(MT_HEADER + "## 2026-08-14 · MEET-0018\n\nminutes\n")

    def test_duplicate_id(self):
        dup = VALID_MT_ENTRY + "\n" + VALID_MT_ENTRY
        self._bad(MT_HEADER + dup)


class CrossReferences(unittest.TestCase):
    def test_dead_reference_rejected(self):
        _, entries = parse_wl(
            "## 2026-08-14 · Change request · WL-0042\n**Title:** T\n"
            "**Requested by:** A (client) — MTG-9999\n**Modules:** M\n"
            "**Effort:** 1h\n**Status:** Delivered\n\nb\n"
        )
        with self.assertRaises(br.FormatError):
            br.check_cross_references(entries, {"MTG-0018"}, Path("worklog.md"))

    def test_live_reference_ok(self):
        _, entries = parse_wl(
            "## 2026-08-14 · Change request · WL-0042\n**Title:** T\n"
            "**Requested by:** A (client) — MTG-0018\n**Modules:** M\n"
            "**Effort:** 1h\n**Status:** Delivered\n\nb\n"
        )
        br.check_cross_references(entries, {"MTG-0018"}, Path("worklog.md"))  # no raise

    def test_no_reference_ok(self):
        _, entries = parse_wl(VALID_WL_ENTRY)  # Requested by has no MTG token
        br.check_cross_references(entries, set(), Path("worklog.md"))  # no raise


# ---------------------------------------------------------------- rendering

class Rendering(unittest.TestCase):
    def test_html_escaped_in_title(self):
        entry = (
            "## 2026-08-14 · Bug fix · WL-0042\n"
            "**Title:** Fix <script> & things\n**Requested by:** X\n"
            "**Modules:** M\n**Effort:** 1h\n**Status:** Delivered\n\nb\n"
        )
        _, entries = parse_wl(entry)
        out = br.render_worklog(entries)
        self.assertIn("Fix &lt;script&gt; &amp; things", out)
        self.assertNotIn("<script>", out)

    def test_mtg_rendered_as_link(self):
        self.assertIn(
            '<a class="mtg" href="#MTG-0018">MTG-0018</a>',
            br.link_mtg("Ayesha (client) — MTG-0018"),
        )

    def test_both_dates_shown(self):
        entry = (
            "## 2026-08-14 · Change request · WL-0042\n**Title:** T\n"
            "**Requested by:** A (client)\n**Modules:** M\n**Effort:** 6h\n"
            "**Status:** Delivered\n**Delivered:** 2026-08-16\n\nb\n"
        )
        _, entries = parse_wl(entry)
        out = br.render_worklog(entries)
        self.assertIn("logged 14 August 2026, delivered 16 August 2026", out)

    def test_mom_escaped_and_bold(self):
        out = br.render_mom("a < b and **x**")
        self.assertIn("&lt;", out)
        self.assertIn("<strong>x</strong>", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
