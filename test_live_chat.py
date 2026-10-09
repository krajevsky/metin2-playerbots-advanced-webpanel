"""The Global-chat density is independent of the overhead CHAT switch."""
from unittest.mock import patch

import app as panel


def test_live_chat_defaults_and_bounds(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights):
        assert panel.read_ai_weights()["LIVE_CHAT"] == 100
        weights.write_text("LIVE_CHAT\t999\n", encoding="utf-8")
        assert panel.read_ai_weights()["LIVE_CHAT"] == 200


def test_live_chat_zero_survives_round_trip(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("CHAT\t1\n", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights), patch.object(panel, "RATES_SPOOL", tmp_path):
        values = panel.read_ai_weights()
        values["LIVE_CHAT"] = 0
        panel.write_ai_weights(values)
        body = weights.read_text(encoding="utf-8")
        assert "LIVE_CHAT\t0" in body
        assert "CHAT\t1" in body
