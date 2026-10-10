"""The native schema browser remains read-only and requires panel authentication."""
from unittest.mock import patch

import app as panel


def test_database_structure_requires_auth_even_when_panel_is_open():
    with patch.object(panel, "settings", return_value={"setup_complete": "1", "auth_enabled": "0"}), \
            patch.object(panel, "rows") as query:
        response = panel.app.test_client().get("/database/structure")
    assert response.status_code == 403
    query.assert_not_called()


def test_database_structure_reads_only_validated_schema_metadata():
    client = panel.app.test_client()
    with client.session_transaction() as state:
        state["seban_admin"] = True
    tables = [{"name": "item_proto", "engine": "MyISAM"}]
    columns = [{"name": "vnum", "type": "int", "nullable": "NO",
                "column_key": "PRI", "default_value": None, "extra": ""}]
    with patch.object(panel, "settings", return_value={"setup_complete": "1", "auth_enabled": "1"}), \
            patch.object(panel, "rows", side_effect=[tables, columns]) as query, \
            patch.object(panel, "render_template", return_value="ok") as render:
        response = client.get("/database/structure?db=player&table=item_proto")
    assert response.status_code == 200
    assert len(query.call_args_list) == 2
    assert all("information_schema." in call.args[0] for call in query.call_args_list)
    assert query.call_args_list[0].args[1] == ("player",)
    assert query.call_args_list[1].args[1] == ("player", "item_proto")
    assert render.call_args.kwargs["columns"] == columns


def test_database_structure_rejects_other_databases_and_unknown_tables():
    client = panel.app.test_client()
    with client.session_transaction() as state:
        state["seban_admin"] = True
    with patch.object(panel, "settings", return_value={"setup_complete": "1", "auth_enabled": "1"}), \
            patch.object(panel, "rows", return_value=[{"name": "item_proto"}]) as query:
        assert client.get("/database/structure?db=mysql").status_code == 404
        query.assert_not_called()
        assert client.get("/database/structure?db=player&table=secret").status_code == 404
        assert query.call_count == 1
