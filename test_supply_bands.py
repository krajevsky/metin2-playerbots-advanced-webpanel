"""Forgetting Bands and Spirit Stone supply pricing uses Tieru's switch."""
from unittest.mock import patch

import app as panel


def test_supply_bands_defaults_on_and_zero_round_trips(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights), patch.object(panel, "RATES_SPOOL", tmp_path):
        values = panel.read_ai_weights()
        assert values["SUPPLY_BANDS"] == 1
        values["SUPPLY_BANDS"] = 0
        panel.write_ai_weights(values)
        assert "SUPPLY_BANDS\t0" in weights.read_text(encoding="utf-8")
        assert panel.read_ai_weights()["SUPPLY_BANDS"] == 0
