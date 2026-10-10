"""A downgrade must not be reported as an item destroyed by the smith."""
from datetime import datetime, timedelta
from unittest.mock import patch

import app as panel


def test_gear_history_hides_removal_when_failed_refine_returned_lower_grade():
    now = datetime(2026, 10, 10, 18, 0, 0)
    events = [
        {"time": now, "how": "REMOVE (REFINE FAIL)", "hint": "", "vnum": 1005, "socket0": None},
        {"time": now + timedelta(seconds=1), "how": "REFINE FAIL", "hint": "", "vnum": 1004, "socket0": None},
        {"time": now - timedelta(minutes=1), "how": "REMOVE (REFINE FAIL)", "hint": "", "vnum": 2005, "socket0": None},
    ]
    with patch.object(panel, "rows", side_effect=[events, []]), \
            patch.object(panel, "_item_display_name", side_effect=lambda vnum, *args: str(vnum)):
        history = panel.bot_gear_history(42)
    assert [(row["kind"], row["item"]) for row in history] == [
        ("refine-fail", "1004"), ("burned", "2005")]
