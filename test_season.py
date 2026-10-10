"""Season details use the engine's event codes and remain readable on mobile."""
from unittest.mock import patch

import app as panel


def test_weekly_deaths_use_tieru_event_code_without_ranking_deaths_only():
    sample = {"id": 7, "name": "Bot", "level": 40, "horse_level": 12,
              "metins": 2, "bosses": 1, "refine7": 0, "deaths": 3}
    with patch.object(panel, "_season_cache", {"at": 0, "weekly": None, "records": None}), \
            patch.object(panel, "rows", return_value=[sample]) as read_rows, \
            patch.object(panel, "one", return_value={}):
        weekly, _ = panel._season_week_rows()
    sql = read_rows.call_args.args[0]
    assert "p.horse_level" in sql
    assert "SUM(l.how='DEAD_BY_NPC') AS deaths" in sql
    assert "HAVING metins>0 OR bosses>0 OR refine7>0" in sql
    assert weekly[0]["deaths"] == 3
    assert weekly[0]["horse_level"] == 12


def test_season_table_has_deaths_and_horse_in_both_languages():
    sample = {"id": 7, "name": "Bot", "level": 40, "horse_level": 12,
              "metins": 2, "bosses": 1, "monsters": 0, "refine7": 0,
              "deaths": 3, "points": 800}
    for language, label in (("pl", "Zgony"), ("en", "Deaths")):
        settings = {"setup_complete": "1", "auth_enabled": "0", "ui_language": language,
                    "theme": "laka"}
        with patch.object(panel, "settings", return_value=settings), \
                patch.object(panel, "_season_week_rows", return_value=([sample], {})), \
                patch.object(panel, "person_ids", return_value=set()), \
                patch.object(panel, "top_level_badge_rank_map", return_value={}):
            response = panel.app.test_client().get("/season")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert f"<th>{label}</th>" in body
        assert "season-table-scroll" in body
        assert "<td>3</td><td>12</td>" in body
