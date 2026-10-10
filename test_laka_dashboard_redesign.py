"""The observatory dashboard is isolated to the Laka theme."""
from unittest.mock import patch

import app as panel


TOTALS = {"characters": 3, "accounts": 2, "item_stacks": 10, "yang": 100}


def dashboard_html(theme, language="pl"):
    prefs = {"setup_complete": "1", "auth_enabled": "0", "ui_language": language,
             "theme": theme, "monitor_mode": "vps", "panel_name": "Test"}
    with patch.object(panel, "settings", return_value=prefs), \
            patch.object(panel, "one", return_value=TOTALS):
        response = panel.app.test_client().get("/")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_observatory_template_styles_and_controls_load_only_for_laka():
    laka = dashboard_html("laka")
    ocean = dashboard_html("ocean")
    assert "laka-observatory.css" in laka
    assert 'class="laka-dashboard-main"' in laka
    assert 'id="laka-filter-toggle"' in laka
    assert 'class="live-shell atlas-stage"' in laka
    assert "laka-observatory.css" not in ocean
    assert 'class="laka-dashboard-main"' not in ocean
    assert 'id="laka-filter-toggle"' not in ocean


def test_mobile_filter_control_translates_to_english():
    assert "Filters" in dashboard_html("laka", "en")
    assert "now." in dashboard_html("laka", "en")
