"""EXPLAIN retention must preserve other engine weights and the absent default."""
from unittest.mock import patch

import app as panel


SETTINGS = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "pl"}


def test_explain_retention_preserves_other_weights_and_can_restore_default(tmp_path):
    path = tmp_path / "playerbot_weights.tsv"
    path.write_text("# custom\nHAGGLE\t1\nFUTURE_KEY\t42\n", encoding="utf-8")
    with patch.object(panel, "AI_WEIGHTS_FILE", path), patch.object(panel, "RATES_SPOOL", tmp_path):
        assert panel.read_ai_explain_days() is None
        panel.write_ai_explain_days(0)
        assert panel.read_ai_explain_days() == 0
        assert "HAGGLE\t1" in path.read_text(encoding="utf-8")
        assert "FUTURE_KEY\t42" in path.read_text(encoding="utf-8")
        panel.write_ai_explain_days(14)
        panel.write_ai_weights(panel.read_ai_weights())
        assert panel.read_ai_explain_days() == 14
        panel.write_ai_explain_days(30)
        assert path.read_text(encoding="utf-8").count("EXPLAIN\t") == 1
        panel.write_ai_explain_days(None)
        assert panel.read_ai_explain_days() is None
        assert "EXPLAIN" not in path.read_text(encoding="utf-8")


def test_explain_retention_route_requires_csrf_and_rejects_invalid_days(tmp_path):
    path = tmp_path / "playerbot_weights.tsv"
    path.write_text("HAGGLE\t1\n", encoding="utf-8")
    with patch.object(panel, "settings", return_value=SETTINGS), \
            patch.object(panel, "AI_WEIGHTS_FILE", path), \
            patch.object(panel, "RATES_SPOOL", tmp_path):
        client = panel.app.test_client()
        assert client.post("/manage/explain-retention", data={"days": "0"}).status_code == 403
        with client.session_transaction() as session:
            session["seban_update_csrf"] = "token"
        assert client.post("/manage/explain-retention", data={"days": "31", "update_csrf": "token"}).status_code == 302
        assert panel.read_ai_explain_days() is None
        assert client.post("/manage/explain-retention", data={"days": "7", "update_csrf": "token"}).status_code == 302
        assert panel.read_ai_explain_days() is None
        assert client.post("/manage/explain-retention", data={"days": "0", "update_csrf": "token"}).status_code == 302
        assert panel.read_ai_explain_days() == 0
        assert client.post("/manage/explain-retention", data={"action": "default", "update_csrf": "token"}).status_code == 302
        assert panel.read_ai_explain_days() is None
