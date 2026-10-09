"""Supply scaling uses Tieru's reference population contract."""
from unittest.mock import patch

import app as panel


def test_supply_scale_defaults_and_bounds(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights):
        values = panel.read_ai_weights()
        assert values["SUPPLY_SCALE"] == 0
        assert values["SUPPLY_REF_BOTS"] == 1000
        weights.write_text("SUPPLY_SCALE\t1\nSUPPLY_REF_BOTS\t90000\n", encoding="utf-8")
        values = panel.read_ai_weights()
        assert values["SUPPLY_SCALE"] == 1
        assert values["SUPPLY_REF_BOTS"] == 50000


def test_supply_scale_round_trip(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights), patch.object(panel, "RATES_SPOOL", tmp_path):
        values = panel.read_ai_weights()
        values.update(SUPPLY_SCALE=1, SUPPLY_REF_BOTS=2500)
        panel.write_ai_weights(values)
        body = weights.read_text(encoding="utf-8")
        assert "SUPPLY_SCALE\t1" in body
        assert "SUPPLY_REF_BOTS\t2500" in body
