"""Guild tower status is merged from all cores like Tieru's guild report."""
import time
from unittest.mock import patch

import app as panel


def test_guild_tower_raid_from_any_channel_is_visible_in_both_languages(tmp_path):
    header = ("guild_id\tonline\tavg_strength\texp_offered_here\tname\tmaster\t"
              "war_with\ttower_raid\ttier\tlevel\tmembers\tempire\n")
    paths = []
    for channel, raid in ((1, 0), (2, 1)):
        path = tmp_path / f"guild-{channel}.tsv"
        path.write_text(header + f"10\t2\t100\t50\tWataha\tHero\t\t{raid}\t1\t7\t5\t1\n",
                        encoding="cp1250")
        paths.append((channel, path))
    with patch.object(panel, "channel_paths", return_value=paths):
        roster, written_at = panel.guild_statuses()
    assert written_at <= time.time()
    assert len(roster) == 1
    assert roster[0]["tower_raid"] is True
    with patch.object(panel, "settings", return_value={
            "setup_complete": "1", "auth_enabled": "0", "ui_language": "en"}), \
            patch.object(panel, "guild_statuses", return_value=(roster, written_at)), \
            patch.object(panel, "player_guild_rows", return_value=[]):
        response = panel.app.test_client().get("/guilds")
    assert response.status_code == 200
    assert "In the Demon Tower" in response.get_data(as_text=True)
