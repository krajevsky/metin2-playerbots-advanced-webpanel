"""Guild-war controls match the live core's bounds."""
from unittest.mock import patch

import app as panel


def test_war_kills_defaults_and_clamps(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights):
        assert panel.read_ai_weights()["WAR_KILLS"] == 100
        weights.write_text("WAR_KILLS\t2000\nWAR_HOURS\t20\nWAR_MINUTES\t10\n", encoding="utf-8")
        values = panel.read_ai_weights()
        assert values["WAR_KILLS"] == 1000
        assert values["WAR_HOURS"] == 4
        assert values["WAR_MINUTES"] == 15


def test_war_kills_zero_and_valid_durations_round_trip(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights), patch.object(panel, "RATES_SPOOL", tmp_path):
        values = panel.read_ai_weights()
        values.update(WAR_KILLS=0, WAR_HOURS=3, WAR_MINUTES=15)
        panel.write_ai_weights(values)
        body = weights.read_text(encoding="utf-8")
        assert "WAR_KILLS\t0" in body
        assert "WAR_HOURS\t3" in body
        assert "WAR_MINUTES\t15" in body
