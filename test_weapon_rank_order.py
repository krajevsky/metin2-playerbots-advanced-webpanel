"""Weapon ranking groups base levels before upgrades and avoids cross-type attack."""
from unittest.mock import patch

import app as panel


def test_default_weapon_order_uses_base_level_band_then_upgrade_for_owner_and_rank():
    with patch.object(panel, "ranking_scope_sql", return_value="1=1"), patch.object(panel, "rows", return_value=[]) as read:
        panel.bot_ranking("weapon", sort_by="level")
    sql = read.call_args.args[0]
    assert "LEFT JOIN player.item_proto base_ip ON base_ip.vnum=i.vnum-MOD(i.vnum,10)" in sql
    assert "ROW_NUMBER() OVER (PARTITION BY i.owner_id ORDER BY CEIL(" in sql
    assert "MOD(i.vnum,10) DESC" in sql
    assert "ORDER BY best.progress_band DESC,best.upgrade_level DESC,best.base_level DESC,p.level DESC" in sql
    assert "ip2.subtype<>6" in sql


def test_attack_sort_remains_available_and_subtype_filter_is_applied():
    with patch.object(panel, "ranking_scope_sql", return_value="1=1"), patch.object(panel, "rows", return_value=[]) as read:
        panel.bot_ranking("weapon", sort_by="attack", weapon_type="bow")
    sql = read.call_args.args[0]
    assert "ORDER BY power_score DESC,best.req_level DESC,best.upgrade_level DESC" in sql
    assert "ip2.subtype=2" in sql
    assert "ORDER BY COALESCE(ip2.value4,0)+COALESCE(ip2.value5,0) DESC" in sql


def test_weapon_page_defaults_to_level_sort_and_keeps_sort_in_filters():
    current = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "en", "theme": "laka"}
    with patch.object(panel, "settings", return_value=current), \
         patch.object(panel, "include_real_players_in_rankings", return_value=False), \
         patch.object(panel, "bot_ranking", return_value=[]) as ranking:
        response = panel.app.test_client().get("/rankings?type=weapon&weapon_type=bow")
    assert response.status_code == 200
    assert b"Weapon tier" in response.data
    assert b"sort=level" in response.data and b"sort=attack" in response.data
    ranking.assert_called_once_with("weapon", "level", False, "bow", "all")


def test_attack_sort_is_not_available_across_weapon_types():
    current = {"setup_complete": "1", "auth_enabled": "0", "ui_language": "en", "theme": "laka"}
    with patch.object(panel, "settings", return_value=current), \
         patch.object(panel, "include_real_players_in_rankings", return_value=False), \
         patch.object(panel, "bot_ranking", return_value=[]) as ranking:
        response = panel.app.test_client().get("/rankings?type=weapon&sort=attack")
    assert response.status_code == 200
    assert b">Attack value<" not in response.data
    ranking.assert_called_once_with("weapon", "level", False, None, "all")
