"""Tieru's session realism uses a 0–100 share, not a goal weight."""
from unittest.mock import patch

import app as panel


def test_session_realism_reads_and_clamps(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("SESSION_REALISM\t73\n", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights):
        assert panel.read_ai_weights()["SESSION_REALISM"] == 73
        weights.write_text("SESSION_REALISM\t999\n", encoding="utf-8")
        assert panel.read_ai_weights()["SESSION_REALISM"] == 100


def test_session_realism_zero_omits_key_and_preserves_new_core_keys(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("NEW_CORE_SETTING\t9\n", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights), patch.object(panel, "RATES_SPOOL", tmp_path):
        values = panel.read_ai_weights()
        values["SESSION_REALISM"] = 0
        panel.write_ai_weights(values)
        assert "SESSION_REALISM\t" not in weights.read_text(encoding="utf-8")
        assert "NEW_CORE_SETTING\t9" in weights.read_text(encoding="utf-8")
        values["SESSION_REALISM"] = 43
        panel.write_ai_weights(values)
        assert "SESSION_REALISM\t43" in weights.read_text(encoding="utf-8")
