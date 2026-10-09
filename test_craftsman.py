"""The Craftsman share is a 0–100 population percentage."""
from unittest.mock import patch

import app as panel


def test_craftsman_default_and_bounds(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights):
        assert panel.read_ai_weights()["CRAFTSMAN"] == 30
        weights.write_text("CRAFTSMAN\t200\n", encoding="utf-8")
        assert panel.read_ai_weights()["CRAFTSMAN"] == 100


def test_craftsman_zero_round_trip(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights), patch.object(panel, "RATES_SPOOL", tmp_path):
        values = panel.read_ai_weights()
        values["CRAFTSMAN"] = 0
        panel.write_ai_weights(values)
        assert "CRAFTSMAN\t0" in weights.read_text(encoding="utf-8")
