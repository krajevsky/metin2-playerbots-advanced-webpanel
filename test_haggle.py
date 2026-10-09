"""The haggle switch shares Tieru's live AI file contract."""
from unittest.mock import patch

import app as panel


def test_haggle_defaults_on_and_zero_round_trips(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights), patch.object(panel, "RATES_SPOOL", tmp_path):
        values = panel.read_ai_weights()
        assert values["HAGGLE"] == 1
        values["HAGGLE"] = 0
        panel.write_ai_weights(values)
        assert "HAGGLE\t0" in weights.read_text(encoding="utf-8")
        assert panel.read_ai_weights()["HAGGLE"] == 0
