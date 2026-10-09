"""PvP-set controls reflect the core's Patch 11 defaults and bounds."""
from unittest.mock import patch

import app as panel


def test_pvp_set_defaults_and_bounds(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights):
        values = panel.read_ai_weights()
        assert {key: values[key] for key in ("PVP_SET", "PVP_SET_SHARE", "PVP_SET_MIN_LEVEL", "PVP_SET_BUDGET", "PVP_SET_STRENGTH", "PVP_SET_VS_HUMAN")} == {
            "PVP_SET": 0, "PVP_SET_SHARE": 25, "PVP_SET_MIN_LEVEL": 30,
            "PVP_SET_BUDGET": 20, "PVP_SET_STRENGTH": 1, "PVP_SET_VS_HUMAN": 1,
        }
        weights.write_text("PVP_SET_SHARE\t120\nPVP_SET_MIN_LEVEL\t0\nPVP_SET_STRENGTH\t8\n", encoding="utf-8")
        values = panel.read_ai_weights()
        assert values["PVP_SET_SHARE"] == 100
        assert values["PVP_SET_MIN_LEVEL"] == 1
        assert values["PVP_SET_STRENGTH"] == 2


def test_pvp_set_round_trip(tmp_path):
    weights = tmp_path / "ai.tsv"
    weights.write_text("", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", weights), patch.object(panel, "RATES_SPOOL", tmp_path):
        values = panel.read_ai_weights()
        values.update(PVP_SET=1, PVP_SET_SHARE=45, PVP_SET_MIN_LEVEL=60,
                      PVP_SET_BUDGET=35, PVP_SET_STRENGTH=2, PVP_SET_VS_HUMAN=0)
        panel.write_ai_weights(values)
        body = weights.read_text(encoding="utf-8")
        for line in ("PVP_SET\t1", "PVP_SET_SHARE\t45", "PVP_SET_MIN_LEVEL\t60",
                     "PVP_SET_BUDGET\t35", "PVP_SET_STRENGTH\t2", "PVP_SET_VS_HUMAN\t0"):
            assert line in body
