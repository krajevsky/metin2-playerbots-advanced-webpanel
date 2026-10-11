"""The obsolete browser-driven updater must not return to game management."""

import app as panel


def test_manage_no_longer_exposes_seban_updater_actions():
    routes = {rule.rule for rule in panel.app.url_map.iter_rules()}
    assert "/manage/update" not in routes
    assert "/manage/overrides" not in routes
    assert "seban_updater" not in panel.PANEL_FEATURES
    panel.app.jinja_env.get_template("manage.html")
