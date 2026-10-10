"""Keep the release history usable on memory-constrained mobile browsers."""
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl", "theme": "laka"}


def test_changelog_renders_only_twenty_entries_and_preserves_history():
    entries = [{"version": f"Release {number}", "timestamp": "2026-10-10",
                "changes": ["Change"], "via_agent": None} for number in range(45)]
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "changelog_entries", return_value=entries):
        first = panel.app.test_client().get("/changelog")
        last = panel.app.test_client().get("/changelog?page=3")
    assert first.status_code == 200 and last.status_code == 200
    assert first.get_data(as_text=True).count('class="panel changelog-entry"') == 20
    assert "Release 0" in first.get_data(as_text=True)
    assert "Release 20" not in first.get_data(as_text=True)
    assert last.get_data(as_text=True).count('class="panel changelog-entry"') == 5
    assert "Release 44" in last.get_data(as_text=True)
    assert "page=2" in last.get_data(as_text=True)


def test_changelog_tieru_keeps_source_in_page_links():
    entries = [{"version": str(number), "date": "2026-10-10", "html": "Text"}
               for number in range(25)]
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "tieru_changelog_entries", return_value=(entries, None)):
        response = panel.app.test_client().get("/changelog?source=tieru")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert html.count('class="panel changelog-entry"') == 20
    assert "source=tieru&amp;page=2" in html or "page=2&amp;source=tieru" in html
