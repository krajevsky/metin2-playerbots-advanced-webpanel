# Seban Panel — V2 Redesign Recon

Read-only inventory of `app.py` routes, templates, Jinja globals, and front-end assets, for engineers rebuilding the visual design while preserving 100% of functionality and data wiring. Generated from the codebase at `/opt/seban-panel-custom`.

---

## 1. Context Processor Globals (`@app.context_processor`, app.py ~L3730)

Injected into every template via `globals_for_templates()`. Settings dict (`current_settings`) is loaded once per request.

| Name | Signature | Description |
|---|---|---|
| `tieru_url` | value (str) | URL of the external classic "Tieru" panel, from `TIERU_PANEL_URL` env var, default `http://127.0.0.1:7788`. Used for the "Panel Tieru (klasyczny)" nav link. |
| `panel_brand` | value (str) | Display name of the panel (`settings.panel_name`, default "Metin2 Singleplayer"). Shown in `<title>` and sidebar brand. |
| `settings` | value (dict) | The full current panel settings dict (theme, cursor, ui_language, feature toggles, etc). |
| `map_name` | `map_name(map_id)` | Looks up a human-readable map name for a map id/code. |
| `item_icon` | `item_icon(vnum, ...)` (alias of `item_icon_url`) | Returns the `static/icons/...` URL for an item's icon given its vnum. |
| `job_name` | `job_name(job)` | Returns the display name of a character class (`class_profile(job)["name"]`). |
| `class_label` | `class_label(job, group)` | Like `job_name`, but returns the magic skill-path name instead when `settings.show_skill_paths == "1"` and a path exists for that job/group. |
| `class_profile` | `class_profile(job)` | Returns the full class profile dict (name, portrait filename, etc) for a job id. |
| `class_portrait` | `class_portrait(job)` | Returns the `static/class-portraits/...` URL for a class's portrait image. |
| `empire_info` | `empire_info(empire)` | Returns `{"name": ..., ...}` metadata for an empire id (1/2/3). |
| `empire_flag` | `empire_flag(empire)` | Returns the `static/empires/...` URL for an empire's flag image, or `""` if unknown. |
| `static_asset_url` | `static_asset_url(filename)` | Builds a cache-busted static URL: appends `?v=<sha256-12char>` of the file's content (not mtime, since Docker/git preserve mtimes) so browsers pick up updated CSS/JS after deploys. |
| `level_badge` | `level_badge(pid, level, prefix="")` | Returns an HTML `<span class="top-level-badge">` wrapping the level label if the character is in the top-10 level leaderboard, else plain escaped text. |
| `top_level_rank` | `top_level_rank(pid)` (lambda) | Returns a character's top-level-leaderboard rank (int) or `None`. |
| `feature_enabled` | `feature_enabled(name)` (lambda) | Returns whether a named optional panel feature is enabled (`panel_feature_enabled(name, current_settings)`). |
| `panel_features` | value (dict) | Precomputed dict of all panel feature toggle states (`panel_feature_states(current_settings)`). |
| `ui_language` | value (str) | Current UI language, `"pl"` or `"en"`. |
| `i18n_payload` | value (dict or None) | JSON translation table embedded as `#i18n-data` when `ui_language == "en"`; `None` for Polish. Consumed by `static/i18n-watch.js`. |
| `ui_version` | value | Current UI version marker (`current_ui_version()`). |

Related `@app.after_request` hooks (not Jinja globals, but affect every templated response):
- `compress_response` — gzips JSON/HTML responses over 1KB when the client accepts gzip.
- `translate_response` — when `ui_language == "en"`, rewrites the full rendered HTML body via `translations.translate_html(...)`; Polish responses pass through untouched byte-for-byte.
- `translated_fragment(markup)` — same translation applied to AJAX-returned HTML fragments (`/api/items`, `/api/live-chat`, `/api/world-feed`).

---

## 2. Base Template & Layout

**`templates/base.html`** (32 lines, single file — no separate header/sidebar partial files are used for the shell itself).

- **Blocks defined:** `{% block title %}` (default: `{{ panel_brand }} · Seban Panel`), `{% block content %}` (empty, filled by every page template).
- **`<head>`:** loads `style.css`, `manage.css`, `enhancements.css`, `events.css`, `respawns.css`, `live-chat.css`, `world-feed.css`, `notifications-bell.css`, `action-toast.css`, `live-overrides.css` (all via `static_asset_url`, in that fixed order — `live-overrides.css` loads last, intentionally overriding earlier rules), plus Chart.js from a CDN.
- **`<body data-theme="{{settings.theme}}" data-cursor="{{settings.get('cursor','custom')}}">`** — theme and cursor are driven by these two data attributes; all theme-specific CSS variable overrides key off `body[data-theme="..."]`.
- **Ember theme extra markup:** when `settings.theme == 'empire'`, an `.empire-embers` particle-effect div with 12 inline-styled `<span>`s is injected.
- **Nav toggle / backdrop:** `#nav-toggle` (hamburger button) and `#nav-backdrop` drive a mobile slide-out nav via `.nav-open` class on `<body>` (inline `<script>` at bottom of file).
- **Notification bell:** `.notif-bell-wrap` > `#notif-bell` (button) / `#notif-badge` (unread count) / `#notif-dropdown` > `.notif-dropdown-head` + `#notif-mark-all` + `#notif-list`. Driven entirely by `notifications-bell.js`.
- **Toast stacks:** `#notif-toast-stack` and `#action-toast-stack` — empty containers populated at runtime by `notifications-bell.js` and `action-toast.js` respectively.
- **Sidebar nav (`<aside class="site-nav">`):** brand link (`.brand`) to dashboard, then a flat `<nav>` of links and `<details class="nav-group">` collapsible groups (auto-`open` based on `request.endpoint` matching known related routes):
  - Dashboard (⌂)
  - Gracze i boty (♙) — group: Lista graczy (`players`), Osobowości botów (`bot_personalities`)
  - Gildie (⚑) → `guilds`
  - Rankingi (♜) → `rankings`
  - Gospodarka (◇) — group: Stan przedmiotów (`economy`), Sklepy offline (`economy_shops`), ItemShop (`economy_itemshop`)
  - Aktywność map (⌖) → `maps`
  - Sezon (✦) → `season`
  - Eventy (🎉) → `events`
  - Respawny (♨) → `respawns`
  - Wiadomości (✉) — group: Czat na żywo (`live_chat`), Wiadomości ze świata (`world_feed`)
  - Wydajność (▤) → `system`
  - Diagnostyka (⌁) — group: Diagnostyka wędkowania (`diagnostics`), Logi panelu (`panel_logs`)
  - Changelog (☷) → `changelog`
  - Zarządzanie (⚙) — group: Gra i serwer (`manage`), Panel webowy (`manage_panel`)
  - Konta i GM (♧) — group: Konta (`accounts`), Nazwy postaci botów (`bot_names`)
  - Kreator postaci (🧬) → `character_creator`
  - Komendy GM (⌘) → `gm_commands`
  - Baza przedmiotów (▦) → `items_database`
  - External link: Panel Tieru (klasyczny) → `tieru_url`, opens in new tab
  - Logout form (`.nav-logout`) posting to `logout`
- **Flash messages:** rendered as a blocking native `<dialog id="flash-modal">` (not inline banners) — one `.flash-card.error` or `.flash-card.success` div per flashed message (category `"error"` vs anything else), each with an inline SVG icon, closed via a `<form method="dialog">` OK button. Auto-opened via `document.getElementById('flash-modal').showModal()`. Note: `ajax-forms.js` intercepts this for AJAX-submitted forms and converts flashes into toasts instead (via `action-toast.js`), removing `#flash-modal` from the swapped-in response.
- **Scripts loaded at end of body (all `defer`):** `action-toast.js`, `ajax-forms.js`, `notifications-bell.js`, `dashboard-deferred.js`, and conditionally `i18n-watch.js` (only if `ui_language == 'en'` and `i18n_payload` present, paired with an inline `#i18n-data` JSON `<script>`).
- **Partials directory** (`templates/partials/`) contains only AJAX-fragment partials, not layout partials: `items_catalog.html`, `live_chat_messages.html`, `world_feed_events.html` — each rendered server-side and returned as the `html` field of a JSON response for a polling/search endpoint (see routes below).

---

## 3. Routes — Full-Page / Fragment Renders (`render_template` callers)

### `GET, POST /login` — `login`
- Template: `login.html`
- Context kwargs: *(none)*
- Purpose: Lets the operator sign into the admin panel with the panel password.

### `GET, POST /setup` — `setup`
- Template: `setup.html`
- Context kwargs: `current`
- Purpose: First-run wizard to configure display settings and admin password before the panel can be used.

### `GET /` — `dashboard`
- Template: `dashboard.html`
- Context kwargs: `totals`, `bots`, `system`, `map_rows`, `channel_map_rows`, `dashboard_channels`, `shop_map_rows`, `top`, `global_top_id`, `quick_rankings`, `world_summary`, `dashboard_deferred`, `panel_version`, `latest_changelog`, `live_regen`, `live_map_regens`
- Purpose: Main landing page; renders a placeholder shell instantly, then `dashboard-deferred.js` fills in live data via `/api/dashboard-deferred`.

### `GET /players` — `players`
- Template: `players.html`
- Context kwargs: `players`, `query`
- Purpose: Search/browse all characters (human + bot) with level, job, gold, live status.

### `GET /players/personalities` — `bot_personalities`
- Template: `bot_personalities.html`
- Context kwargs: `roster`, `total`, `query`, `selected`, `personalities`
- Purpose: Shows online playerbots grouped/filtered by AI personality type.

### `GET /guilds` — `guilds`
- Template: `guilds.html`
- Context kwargs: `guilds`, `query`, `summary`, `player_guilds`, `next_wars`, `status_written_at`
- Purpose: Lists all guilds (online counts, wars, exp) for monitoring guild activity.

### `GET /guild/<int:guild_id>` — `guild`
- Template: `guild.html`
- Context kwargs: `guild`, `members`
- Purpose: Detail page for one guild (leader, stats, member roster).

### `GET /player/<int:pid>` — `player`
- Template: `player.html`
- Context kwargs: `character`, `equipment`, `inventory`, `safebox`, `has_safebox`, `horse_bag`, `has_horse_bag`, `dragon_soul_inventory`, `dragon_soul_decks`, `gear_history`, `offline_shop`, `character_stats`, `mission_progress`, `gm_ranks`, `admin_warps`
- Purpose: Full admin/detail page for one character — stats, gear, GM actions, VIP grants.

### `GET /api/player/<int:pid>/inventory-fragment` — `api_player_inventory_fragment`
- Template: `_inventory_fragment.html`
- Context kwargs: `gold`, `equipment`, `inventory`, `safebox`, `has_safebox`, `horse_bag`, `has_horse_bag`, `dragon_soul_inventory`, `dragon_soul_decks`
- Purpose: Returns refreshed gear/inventory markup so the player page can live-update without a full reload.

### `GET /economy` — `economy`
- Template: `economy.html`
- Context kwargs: `latest`, `items`, `query`, `trend`
- Purpose: Server-wide item economy snapshot (top held items, 7-day yang trend).

### `GET /economy/item/<int:vnum>` — `economy_item`
- Template: `economy_item.html`
- Context kwargs: `item`, `history`
- Purpose: One item's held-quantity history over the last 14 days.

### `GET /economy/shops` — `economy_shops`
- Template: `economy_shops.html`
- Context kwargs: `latest`, `by_map`, `query`, `empire_totals`, `kpi`, `value_trend`, `market_items`, `fastest_items_limit`, `sales_velocity`, `skillbook_velocity`, `recent_sales`
- Purpose: Player-run shop market dashboard — per-map/empire counts, value trends, fastest sellers, recent sales.

### `GET /items` — `items_database`
- Template: `items.html`
- Context kwargs: `items`, `types`, `selected_type`, `query`, `total`
- Purpose: Browsable/searchable catalog of all item definitions (item_proto).

### `GET /api/items` — `api_items`
- Template: `partials/items_catalog.html` (rendered inline into JSON)
- Context kwargs: `items` (to the partial); JSON response: `ok`, `html`, `count_label`
- Purpose: Live-search backend for the items database page.

### `GET /live-chat` — `live_chat`
- Template: `live_chat.html`
- Context kwargs: `messages`
- Purpose: Live feed of in-game chat for moderation/monitoring.

### `GET /api/live-chat` — `api_live_chat`
- Template: `partials/live_chat_messages.html` (inline into JSON)
- Context kwargs: `messages` (to the partial); JSON response: `ok`, `html`
- Purpose: Polling refresh for the live chat feed.

### `GET /world-feed` — `world_feed`
- Template: `world_feed.html`
- Context kwargs: `events`
- Purpose: Chronological feed of notable world events (boss kills, drops, etc).

### `GET /api/world-feed` — `api_world_feed`
- Template: `partials/world_feed_events.html` (inline into JSON)
- Context kwargs: `events` (to the partial); JSON response: `ok`, `html`, `next_before`, `has_more`
- Purpose: Paginated "load more" / polling endpoint for the world feed.

### `GET /gm-commands` — `gm_commands`
- Template: `gm_commands.html`
- Context kwargs: `commands`
- Purpose: Reference list of available in-game GM commands.

### `GET, POST /accounts` — `accounts`
- Template: `accounts.html`
- Context kwargs: `accounts`, `authorities`, `jobs`, `genders`, `account_query`, `display`
- Purpose: Lists game accounts; lets operator create new player/GM accounts with a starting character.

### `GET /accounts/bot-names` — `bot_names`
- Template: `bot_names.html`
- Context kwargs: `entries`, `search`, `empire`, `status`, `page`, `pages`, `total`, `stats`, `pending`, `empires`
- Purpose: Browse/search/paginate the bot-name pool (free/used/blocked/custom) used to name playerbots.

### `GET, POST /character-creator` — `character_creator`
- Template: `character_creator.html`
- Context kwargs: `authorities`, `jobs`, `genders`, `preselect_account_id`
- Purpose: Create a new character (optionally with GM rank) on an existing or new account.

### `GET /account/<int:aid>` — `account_detail`
- Template: `account_detail.html`
- Context kwargs: `account`, `characters`
- Purpose: One account's detail — VIP/premium status, cash, character list.

### `GET /maps` — `maps`
- Template: `maps.html`
- Context kwargs: `charts`, `latest`, `channels`, `heat_map_options`, `level_now`, `level_history`
- Purpose: Per-channel population charts, current counts per map, level-bracket stats, and the standalone heatmap tool.

### `GET /changelog` — `changelog`
- Template: `changelog.html`
- Context kwargs: `entries`, `panel_version`, `source`, `tieru_entries`, `tieru_error`
- Purpose: Panel's (and optionally Tieru's) version/changelog history.

### `GET /system` — `system`
- Template: `system.html`
- Context kwargs: `samples`, `current`
- Purpose: Host health (CPU/RAM/disk) over the last 24 hours.

### `GET /rankings` — `rankings`
- Template: `rankings.html`
- Context kwargs: `kinds`, `kind`, `ranking`, `weapon30_sort`, `per_page`, `page`, `total_pages`, `page_numbers`, `people_ranked`, `people_only`
- Purpose: Paginated leaderboards across many stat categories (level, gold, PVP, etc).

### `GET /season` — `season`
- Template: `season.html`
- Context kwargs: `weekly`, `records`
- Purpose: Weekly "season" leaderboard scored from metin/boss kills and +7/+8/+9 refines.

### `GET /economy/itemshop` — `economy_itemshop`
- Template: `economy_itemshop.html`
- Context kwargs: `totals`, `top_cash`, `top_mileage`, `purchases`, `popular`, `daily`
- Purpose: Cash-shop economy monitor — top spenders, recent purchases, popular items, daily volume.

### `GET /diagnostics/panel-logs` — `panel_logs`
- Template: `panel_logs.html`
- Context kwargs: `log_tail`, `log_size`
- Purpose: Tail the panel's own application log.

### `GET /diagnostics` — `diagnostics`
- Template: `diagnostics.html`
- Context kwargs: `diagnostic`
- Purpose: Fishing-feature diagnostic data for debugging.

### `GET /daily-summary/<int:summary_id>` — `daily_summary`
- Template: `daily_summary.html`
- Context kwargs: `s`, `details`
- Purpose: One day's automated activity summary (reached via notification link; no nav entry).

### `GET /respawns` — `respawns`
- Template: `respawns.html`
- Context kwargs: `regen`, `count_choices`, `map_options`, `stone_maps`, `map_status`
- Purpose: Configure monster/boss respawn delay/count multipliers and per-map respawn seconds.

### `GET, POST /events` — `events`
- Template: `events.html`
- Context kwargs (exact call): `rows=shown`, `nows`, `status`, `world_runs`, `event_kinds`, `event_labels`, `day_names`, `now_minutes`, `now_epoch`, `event_history`, `event_icons`, `world_kinds`, `world_defaults`, `world_max`, `event_maps`, `event_settings`
- Purpose: Schedule/trigger world events (Tanaka, Zuo, chest drops, etc.), view history, set bot participation share. POST action branches (bots/save/now/stop) redirect back to GET — no separate template.

### `GET /manage` — `manage`
- Template: `manage.html`
- Context kwargs: `rates`, `rate_presets`, `ai_weights`, `chest_switch`, `ai_weight_keys`, `ai_weight_capped`, `ai_weight_hints`, `engine_mt2009`, `restart`, `settings`, `map_counts`, `bot_count`, `bot_channels`, `map_respawn_options`, `map_stone_respawn_ids`, `map_respawn_status`, `server_settings`, `updater`, `playerbots_release`, `update_csrf`, `bot_count_wanted`, `spawn_plan`, `student_chest_disabled`, `custom_patches_enabled`, `include_real_players`, `announce_plus9`, `bots_held`, `item_policy`, `difficulty`, `autohunt`, `channels`, `channel_shares`, `fresh_counts`
- Purpose: Master admin dashboard — rates, AI behavior weights, restart/update controls, channel/spawn config, bot count, item policy, difficulty. The single most complex page in the panel.

### `GET /manage/panel` — `manage_panel`
- Template: `manage_panel.html`
- Context kwargs: `settings`, `capability_features`, `custom_default`, `top_level_badges_enabled`, `top_level_badge_places`, `full_plus9_badges_enabled`, `shop_explain_enabled`
- Purpose: Panel-level feature toggles and display preferences (badges, announcements, UI capabilities).

---

## 4. Routes — Action / JSON Endpoints (no `render_template`)

| Route | Function | Purpose |
|---|---|---|
| `POST /logout` | `logout` | Clears session, redirects to login. |
| `GET /api/dashboard-deferred` | `api_dashboard_deferred` | JSON for deferred dashboard widgets. |
| `GET /api/bot-logs/<int:pid>` | `api_bot_logs` | JSON: recent live log lines for one bot. |
| `POST /api/admin/teleport-me` | `api_admin_teleport_me` | JSON: teleports an online GM/human character to a bot's position. |
| `GET /api/admin/item-search` | `api_admin_item_search` | JSON: searches item_proto for the item picker. |
| `POST /player/<int:pid>/action/game` | `player_action_game` | Queues an in-game admin command (give item/gold/level/warp/speed). |
| `POST /player/<int:pid>/action/vip` | `player_action_vip` | Grants/extends VIP/premium flag on the account. |
| `POST /manage/bulk-vip` | `manage_bulk_vip` | Grants VIP/premium flag to every `playerbot_*` account at once. |
| `POST /player/<int:pid>/action/coins` | `player_action_coins` | Adds Dragon Coins (cash) to the account. |
| `POST /player/<int:pid>/action/rename` | `player_action_rename` | Renames a character. |
| `POST /player/<int:pid>/action/gm-rank` | `player_action_gm_rank` | Grants/revokes GM rank. |
| `POST /player/<int:pid>/action/reset-position` | `player_action_reset_position` | Resets position to kingdom capital. |
| `POST /player/<int:pid>/action/delete` | `player_action_delete` | Deletes a character (snapshot backup, confirm-by-name). |
| `GET /api/shop-feed` | `api_shop_feed` | JSON: recent shop sales feed. |
| `POST /accounts/bot-names/add` | `bot_names_add` | Adds custom names to the bot-name pool. |
| `POST /accounts/bot-names/<name>/block` | `bot_names_block` | Blocks a name from assignment. |
| `POST /accounts/bot-names/<name>/unblock` | `bot_names_unblock` | Unblocks a name. |
| `POST /accounts/bot-names/<name>/delete` | `bot_names_delete` | Deletes a custom name from the pool. |
| `POST /accounts/bot-names/<name>/priority` | `bot_names_priority` | Sets a name's assignment priority. |
| `POST /accounts/bot-names/reconcile` | `bot_names_reconcile` | Assigns pool names to existing nameless bots. |
| `GET /api/character-creator/name-status` | `api_character_creator_name_status` | JSON: checks if a character name is available. |
| `GET /api/character-creator/accounts` | `api_character_creator_accounts` | JSON: candidate accounts for the creator's account picker. |
| `GET /accounts/<int:aid>/characters` | `account_characters` | JSON: characters on an account. |
| `GET /api/live-bots` | `api_live_bots` | JSON: slimmed live-bot snapshot for the live map widget. |
| `GET /api/news-feed` | `api_news_feed` | JSON: ticker news feed events. |
| `GET /api/system-current` | `api_system_current` | JSON: latest single CPU/RAM/disk snapshot. |
| `GET /diagnostics/panel-logs/download` | `panel_logs_download` | Downloads the panel log file. |
| `POST /respawns/delay` | `respawns_delay` | Sets boss/mob respawn delay %. |
| `POST /respawns/count` | `respawns_count` | Sets boss/mob respawn count multipliers. |
| `POST /respawns/map` | `respawns_map` | Sets exact respawn seconds for one map. |
| `POST /manage/difficulty` | `manage_difficulty` | Sets difficulty preset/custom hours. |
| `POST /manage/autohunt` | `manage_autohunt` | Toggles player access to autohunt panel. |
| `POST /manage/channels` | `manage_channels` | Writes channel split/fresh-channel config for next restart. |
| `POST /manage/panel/features` | `manage_panel_features` | Toggles optional panel features/integrations. |
| `POST /manage/panel/legendary-announcements` | `manage_panel_legendary_announcements` | Toggles where legendary announcements appear. |
| `POST /manage/panel/skill-paths` | `manage_panel_skill_paths` | Toggles showing magic skill-path in rankings. |
| `POST /manage/panel/reaper-chests` | `manage_panel_reaper_chests` | Toggles Reaper Chest world-feed notices. |
| `POST /manage/update` | `manage_update` | Queues a Playerbots/panel update job. |
| `POST /manage/settings` | `manage_settings` | Saves panel display/auth settings. |
| `POST /manage/overrides` | `manage_overrides` | Saves update-override flags. |
| `POST /manage/restart-config` | `manage_restart_config` | Applies rate/respawn/bot-count changes and/or triggers restart. |
| `POST /manage/spawn-plan` | `manage_spawn_plan` | Saves bot spawn-window/late-joiner plan. |
| `POST /manage/student-chest` | `manage_student_chest` | Toggles Student Chest starter item. |
| `POST /manage/ranking-scope` | `manage_ranking_scope` | Toggles including real players in rankings. |
| `POST /manage/top-level-badges` | `manage_top_level_badges` | Configures top-level gradient badge settings. |
| `POST /manage/panel/full-plus9-badges` | `manage_full_plus9_badges` | Toggles the full +9 equipment badge. |
| `POST /manage/panel/shop-ranking` | `manage_panel_shop_ranking` | Sets fastest-selling-items ranking limit. |
| `POST /manage/panel/shop-explain` | `manage_shop_explain` | Toggles bot shop-decision explanations. |
| `POST /manage/plus9-announce` | `manage_plus9_announce` | Toggles world announcements for +9 refines. |
| `POST /manage/restart-clear-stale` | `manage_restart_clear_stale` | Clears a stuck restart/settings request. |
| `POST /manage/map-respawns` | `manage_map_respawns` | Sets/resets one map's respawn seconds (manage page variant). |
| `POST /manage/behavior` | `manage_behavior` | Saves AI behavior weights. |
| `POST /manage/item-policy` | `manage_item_policy` | Saves per-item keep/stall/merchant/drop AI policy rules. |
| `POST /manage/release-bots` | `manage_release_bots` | Releases bots held at the "door". |
| `POST /manage/hold-bots` | `manage_hold_bots` | Holds bots at the door. |
| `POST /manage/tower-now` | `manage_tower_now` | Forces immediate Demon Tower raid. |
| `POST /manage/catacomb-now` | `manage_catacomb_now` | Forces immediate Azrael catacomb raid. |
| `POST /manage/catacomb` | `manage_catacomb` | Toggles whether bots raid Azrael at all. |
| `POST /manage/restart` | `manage_restart` | Confirms/queues a full server restart. |
| `GET /api/manage-status` | `api_manage_status` | JSON: polling endpoint for restart/update/rates/events/bot/map status. |
| `GET /api/notifications` | `api_notifications` | JSON: notification bell items + unread count. |
| `POST /api/notifications/read` | `api_notifications_read` | Marks given notification ids as read. |
| `POST /api/notifications/read-all` | `api_notifications_read_all` | Marks all notifications read. |
| `POST /api/notifications/pop` | `api_notifications_pop` | Marks notifications as having shown their toast. |
| `GET /api/heat-events` | `api_heat_events` | JSON: heat-map event data (deaths/metins/bosses) for a map. |

---

## 5. CSS Custom Properties

### `static/style.css`
`:root` (global base theme): `--bg`, `--panel`, `--edge`, `--text`, `--muted`, `--blue2` (primary accent), `--gold` (secondary accent), `--fs-h1`, `--fs-h2` (fluid heading sizes), `--space-card`, `--space-gap` (fluid spacing).

`body[data-theme="ember"]` / `body[data-theme="forest"]`: override `--bg`, `--panel`, `--edge`, `--text`, `--muted`, `--blue2`.

Second `:root` block (+ theme overrides): `--leader-ink`, `--leader-ink-2`, `--leader-ink-3` — colors of the animated leaderboard-name shimmer gradient.

`body[data-theme="empire"]`: overrides `--bg`, `--panel`, `--edge`, `--text`, `--muted`, `--blue2`, `--gold`; adds `--hero-accent`, `--hero-accent-soft`, `--hero-fire-hot`, `--hero-fire-deep`, `--hero-title-shadow` (empire hero banner styling; also redefined per ember/forest/empire sub-variant).

### `static/live-overrides.css`
`:root` + per-theme overrides: `--live-surface`, `--live-surface-strong`, `--live-border`, `--live-line`, `--live-accent`, `--live-accent-text`, `--live-number`, `--live-progress-end`, `--live-filter` — all for the live map / dashboard widget chrome.
Component-scoped: `--map-channel-ring` — set inline per `.bot-point.ch-1/2/3/4` (bot dot ring color by channel).

### `static/enhancements.css`
`.ld-shimmer` (loading skeleton): `--ink` — shimmer color, defaults to `var(--blue2)`.

### `static/events.css`
`.switch` (toggle control): `--primary`, `--secondary`, `--surface`, `--on`, `--off`, `--thumb`.
`.week-calendar`/`.calendar-hours`/etc: `--calendar-hour` — height of one hour row in the event calendar grid.

### `static/live-chat.css`
`.metin-chat-window` (+ theme overrides): `--chat-wood`, `--chat-wood-2` (window background gradient), `--chat-rim` (border), `--chat-line` (divider), `--chat-pane` (scroll pane bg), `--chat-ink` (text), `--chat-muted`, `--chat-call` (shout-channel color), `--chat-trade` (trade-channel color).

### `static/world-feed.css`
`--x`, `--y`, `--s` — per-sparkle position/scale, set inline on `.legendary-sparkles i:nth-child(n)` for the twinkle animation.

### `static/player-profile.css`
`.shop-inventory`/`.shop-slot`: `--rows` — number of inventory rows (8 normal, 16 for a bot's 2-page shop stand), drives aspect-ratio/slot-position math.

### No custom properties defined
`manage.css`, `respawns.css`, `notifications-bell.css`, `action-toast.css`, `character-creator-page.css`.

---

## 6. JavaScript Files — DOM Dependencies

**Critical:** a redesign must preserve every id/class listed below exactly, or the corresponding widget silently breaks (no JS errors shown to the user in most cases — scripts guard with early `if (!el) return`).

### `action-toast.js`
Global `window.showActionToast(message, category)` — creates an auto-dismissing toast. Used by `ajax-forms.js`.
DOM: `#action-toast-stack` (required container); creates `.action-toast`, `.action-toast.error`/`.success`, `.action-toast-icon`, `.action-toast-body`, `.action-toast-close`, `.is-leaving`.

### `ajax-forms.js`
Intercepts `<form>` submits inside `<main>` on pages with `data-ajax-forms` set on `<body>`; submits via `fetch`, swaps `<main>` innerHTML with the response, converts flash messages to toasts.
DOM: `document.body.dataset.ajaxForms`, `#flash-modal`, `.flash-card`, `main`, `main form:not([data-ajax-ignore])`, `form.dataset.ajaxBound`, `button`/`input[type=submit]`, any `[id]` hash-target.

### `character-creator-page.js`
Drives the 2-step character creation wizard (class/gender orbit picker, nickname check, account picker).
DOM: `#cc-scene`, `.cc-orbit`/`.cc-slot`/`.cc-slot-label`, `.cc-arrow.left/.right`, `.cc-gender-toggle .gender-btn`, `.empire-flag-btn`, `#cc-gm-job`, `#cc-gm-gender`, `#cc-empire`, `#cc-class-name`, `#cc-nick-input`, `#cc-nick-status`, `#cc-next-btn`, `#cc-back-btn`, `#cc-step1-actions`, `#cc-step2`, `#cc-submit-btn`, `#cc-account-mode`, `#cc-account-select`, `#cc-account-search`, `#cc-existing-account`, `#cc-new-account`, `#cc-empire-warning`, `.cc-account-mode .mode-btn`, `.locked`.

### `dashboard-charts.js`
Renders Chart.js widgets: CPU/RAM/disk donuts, "bots by map" donut (auto-rotating to channel/shop bar charts every 8s), quick-ranking carousel.
DOM: `#cpu-donut`, `#ram-donut`, `#disk-donut`, `#i18n-data`, `#map-data`, `#map-donut`, `#shop-map-data`, `#map-tile-title`, `#empire-flags-data`, `#channel-map-data`, `#channels-data`, `.quick-rank-slide`, `.carousel-dots button` (`data-slide`), `#quick-rank-title`, `#quick-rank-subtitle`, `#quick-rank-autoplay`, `#quick-rank-prev`, `#quick-rank-next`, `.rank-enter`.

### `dashboard-deferred.js`
On dashboard load, shows shimmer skeletons, fetches `/api/dashboard-deferred` once, populates every widget, then re-injects `dashboard-charts.js`.
DOM: `#dashboard-widgets`/`.dashboard-widgets` (+ `.dashboard-widgets--loading`), `.panel` (+ `.is-loading`, injected `.dashboard-widget-loader.ld-shimmer`), `.empire-bots-cell`/`.empire-bots-breakdown`, `.channel-bots-cell`/`.channel-bots-breakdown`, `#overview-bots`, `#overview-avg`, `#overview-party`, `#overview-max`, `.panel-installed`, `.panel-release-card` (+ `.current`/`.outdated`/`.unknown`), `.playerbots-installed`, `.playerbots-release-card` (+ `.current`/`.outdated`/`.warning`/`.unknown`), `.fx-shimmer`, `.empire-bots-item`, `.empire-flag-inline`, `.map-legend-channel.map-legend-channel--ch{N}`, `#overview-rate-{exp|drop|yang}`, `.system-dashboard`/`[data-dashboard-widget="system"]`, `#map-data`, `#channel-map-data`, `#channels-data`, `#shop-map-data`, `#live-regen-data`, `#map-donut`, `.ranking-carousel`, `#quick-rank-title`, `#quick-rank-subtitle`, `#quick-rank-slides`, `.carousel-dots`, `.dashboard-widget-error`.

### `heat-layer.js`
Shared primitive `window.SebanHeatmap.render()`/`.clear()` — draws heat dots into a passed-in container. No fixed ids of its own (generic). Injects `.density-heat-layer` > `.density-heat-dot`. Consumed by `heatmap.js` and `live-widget.js`. **Not legacy — must load before either consumer.**

### `heatmap.js`
Standalone maps-page heatmap controller; fetches `/api/heat-events`, delegates rendering to `heat-layer.js`.
DOM: `#heatmap` (+ `data-map-index`, `style.backgroundImage`), `#heat-map` (select), `#heat-kind` (select), `.heat-point`, `#heat-count`, `#heat-caption`.

### `i18n-watch.js`
Client-side English translation pass, loaded only when `ui_language == 'en'`; walks and observes the DOM.
DOM: `#i18n-data` (required), `[translate="no"]` (excluded, used for chat/nicknames), `title`/`alt`/`placeholder`/`aria-label` attrs, `input[type=submit/button]` values, excludes `SCRIPT`/`STYLE`/`TEXTAREA`/`PRE`, observes `document.body`.

### `live-widget.js`
Core live-map dashboard widget: polls `/api/live-bots` every 1.5s, plots bots, supports heatmap sub-mode, renders rankings/insights, syncs sidebar height, polls `/api/manage-status` for restart/rate-bonus countdowns. The largest/most DOM-coupled script.
DOM: `#world-map`, `#map-select`, `#bot-search`, `.live-filters` (+ injected `#channel-select`, `#live-mode`, `.map-autoplay`/`#map-autoplay`), `.live-sidebar`, `.live-insights`, `.live-shell header > div` (+ `#last-restart`), `.live-shell footer span`, `.world-overview`/`.overview-maps`/`.overview-maps-list`, `.overview-page[data-page="2"]`, `.overview-page`, `.overview-dots button`, `.overview-pages`, `#live-activity`, `#world-activity-filter button` (`data-empire`), `#world-activity-chart`, `#world-level-chart`, `#world-insights-tabs` (delegated `button[data-tab]`), `#world-insights-card` (`dataset.worldTab`), `#live-regen-data`, `#map-channel-chart`, `#map-empire-chart`, `#map-respawn-summary`, `[data-insight]`, `[data-insight-page]`, `.bot-point` (+ `.ch-{n}`, `.is-pt`, `.is-stuck`, `.is-metin`, `data-bot-id`), `.bot-point-flag`, `.bot-point-stuck`, `#show-names`, `#party-only`, `[data-level]`, `#stat-visible`, `#stat-pt`, `#stat-avg`, `#stat-max`, `#live-count`, `#map-caption`, `#live-ranking` (+ `a[data-bot-id]`, `.is-global-leader`, `.pt-mark`, `.stuck-mark`, `.muted`), `.class-portrait`/`.class-portrait--live`, `.top-level-badge.top-level-badge--compact`, `#live-insights-toggle` (+ `.show-map-insights` on `.live-shell`), `#live-sidebar-tabs` (delegated `button[data-tab]`, `.live-sidebar` `dataset.sidebarTab`), `.rate-bonus[data-until]`, `.rate-bonus-countdown`, `#rate-row-{exp|drop|yang}`/`.rate-event-active`, `#rate-bonus-{exp|drop|yang}`.

### `news-feed.js`
Polls `/api/news-feed` every 30s, renders a scrolling ticker (rare drops, legendary events), caches last 40 in `localStorage`.
DOM: `#news-feed`, `.news-ticker` (+ `.is-hidden`), `#news-toggle`, `li.refine-rare`.

### `notifications-bell.js`
Polls `/api/notifications` every 30s, populates bell dropdown, auto-pops toasts, marks items read.
DOM: `#notif-bell`, `#notif-badge`, `#notif-dropdown`, `#notif-list`, `#notif-mark-all`, `#notif-toast-stack`, `.notif-item`/`.is-unread` (`data-id`), `.notif-item-title`, `.notif-item-body`, `.notif-item-time`, `.notif-empty`, `.notif-toast`.

### Dead-code check
All 11 JS files are referenced: `action-toast.js`, `ajax-forms.js`, `notifications-bell.js`, `dashboard-deferred.js`, `i18n-watch.js` → `base.html`; `character-creator-page.js` → `character_creator.html`; `heat-layer.js`, `live-widget.js`, `dashboard-charts.js`, `news-feed.js` → `dashboard.html`; `heat-layer.js`, `heatmap.js` → `maps.html`. **None unreferenced.** `heat-layer.js`/`heatmap.js` are both live and intentionally split (shared primitive + two consumers), not legacy duplication.

---

## 7. Game Assets Reused As-Is (static/)

| Directory | Contents |
|---|---|
| `maps/` | 26 map background images (one per game map, PNG) used by the live map and heatmap tool. |
| `class-portraits/` | 9 class portrait bitmaps (warrior/sura/shaman etc, by gender) for character profile display. |
| `empires/` | 3 empire flag PNGs (Shinsoo/Chunjo/Jinno). |
| `icons/` | 1917 item icon PNGs, keyed by vnum — the primary item-icon set. |
| `icons_new/` | 1915 item icon PNGs — an alternate/updated icon set (near-duplicate of `icons/`, check which is actually referenced before consolidating). |
| `skill_icons/` | 220 skill icon PNGs (by skill id, with `_m`/`_p` master/passive suffixes). |
| `char-creator/` | 24 images for the character-creator UI (class/gender preview art). |
| `dragon-soul-ui/` | 34 images for the Dragon Soul inventory UI (slots, buttons, deck tabs). |
| `inventory-ui/` | 4 images for inventory page-tab active/inactive states. |
| `refine-method/` | 1 image (blacksmith/refine icon). |
| `branding/` | 1 image — the panel's custom logo. |
| `downloads/` | 1 file — a downloadable panel release tarball (not a visual asset). |
| `item_icons.json` | Dict (5479 entries) mapping item vnum → icon filename. |
| `item_defs.json` | Dict (5743 entries) of item definition metadata. |
| `item_names_en.json` | Dict (5862 entries) — English item name translations. |
| `mob_names_en.json` | Dict (1056 entries) — English monster name translations. |
| `exp_levels.json` | List (121 entries) — experience-per-level table. |

Backup directories present in both `static/` and `templates/` (e.g. `bak-20260913-*`, `icons.bak-*`, `manage.html.orig`) are prior-version snapshots, not live assets — exclude from the redesign scope.
