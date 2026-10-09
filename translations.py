"""English translation layer for Seban Panel.

The panel's ~40 templates and app.py have Polish text baked directly into
literal strings everywhere (labels, buttons, flash messages, SQL-built
"detail" columns for rankings/tooltips) rather than routed through gettext.
Rewriting every call site to use _() would touch thousands of lines in a
100KB+ app.py the operator has explicitly asked to keep to minimal, point
diffs -- so instead this translates the fully-rendered HTML response in an
after_request hook, when the panel's ui_language setting is "en". Polish
stays the untouched default; nothing changes for a Polish-language response.

Two lookup tables:
  EXACT     -- a whole trimmed text node (or attribute value) matches this
               Polish phrase exactly -> use this English string verbatim.
  PATTERNS  -- for text nodes assembled from a Python f-string/CONCAT with
               live data baked in ("Konto: eurogabka", "42 zabitych bossów"),
               a regex with $1/$2... capture groups, tried in order (first
               match wins). $-style placeholders (not \\1) so the exact same
               PATTERNS_RAW list can be handed to the client-side translator
               (static/i18n-watch.js) as JSON and used with JS's
               String.replace(RegExp, "...$1...") unchanged.

and, after EXACT, ITEM_NAMES: a text node that is exactly an item's Polish
proto name (as item_proto.locale_name prints it) gets that item's official
English name -- the game's own, from static/item_names_en.json, never a
translation made here. Server-side only: thousands of names are too many
to ship with every page, so a JSON answer whose HTML fragment a page swaps
in is translated before it is sent (app.py's translated_fragment()).

translate_html() below is the entry point: it walks the response body,
leaves <script>/<style>/<textarea>/<pre> blocks completely alone (both to
avoid corrupting inline JS/JSON and to avoid mistranslating raw user-edited
text like the item policy textarea), and any element marked translate="no"
(what players and bots wrote: a chat line and its author's nick, which
the dictionaries would otherwise half-translate), translates plain text between tags,
and translates a short list of user-facing attributes (title, alt,
placeholder, aria-label, and value on submit/button inputs).

Dynamic content that dashboard-deferred.js / live-widget.js / dashboard-
charts.js / news-feed.js render client-side after the initial page load
isn't touched by this server-side pass at all -- static/i18n-watch.js
(loaded from base.html only when ui_language=en) applies the same EXACT +
PATTERNS_RAW tables to the live DOM via a MutationObserver, so a phrase
only needs to be translated once here to cover both the server-rendered
page and anything injected by those scripts afterwards.
"""
import html
import json
import re
from pathlib import Path


def _dollar_to_backslash(repl):
    # PATTERNS_RAW stores replacements as "...$1..." (JS-compatible); Python's
    # re.sub wants "...\g<1>...". \g<N> (not bare \N) so a literal digit
    # right after the group number in the replacement can't be misread as
    # part of the group number.
    return re.sub(r'\$(\d+)', r'\\g<\1>', repl)


# ---------------------------------------------------------------------------
# EXACT: whole-phrase matches. Keys are Polish exactly as they appear in a
# trimmed HTML text node or attribute value (after un-escaping &amp; etc).
# ---------------------------------------------------------------------------
EXACT = {
    "Cena od": "Price from",
    "Cena do": "Price to",
    "Filtruj cenę za sztukę": "Filter by unit price",
    "Nieprawidłowy zakres ceny. Użyj liczby Yang albo skrótu k, kk, kkk.": "Invalid price range. Use a Yang amount or k, kk, kkk shorthand.",
    "Oferty rynku": "Market offers",
    "Przeglądaj aktywne oferty →": "Browse active offers →",
    "GOSPODARKA · SKLEPY OFFLINE": "ECONOMY · OFFLINE SHOPS",
    "Aktywne oferty rynku": "Active market offers",
    "Oferty i ceny są odczytywane bezpośrednio z IkarusShop. Widok pokazuje 50 pozycji na stronę; stan sklepu może zmienić się w grze.": "Offers and prices are read directly from IkarusShop. This view shows 50 listings per page; shop status may change in game.",
    "Przedmiot lub VNUM": "Item or VNUM",
    "Nazwa lub VNUM": "Name or VNUM",
    "Wszyscy": "All",
    "Boty": "Bots",
    "Gracze": "Players",
    "Wszystkie": "All",
    "Sortowanie": "Sort",
    "Cena: od najtańszych": "Price: lowest first",
    "Cena: od najdroższych": "Price: highest first",
    "Cena za sztukę: od najtańszych": "Unit price: lowest first",
    "Pokaż oferty": "Show offers",
    "Brak ofert spełniających filtry.": "No offers match these filters.",
    "← Poprzednia": "← Previous",
    "Następna →": "Next →",
    "Strony ofert": "Offer pages",
    "Aktywne oferty w sklepach offline": "Active offline-shop offers",
    "Ceny pochodzą bezpośrednio z ofert IkarusShop. Pokazujemy do 100 aktywnych pozycji; zakup i stan sklepu mogą zmienić się w grze.": "Prices come directly from IkarusShop offers. Up to 100 active listings are shown; purchases and shop status may change in game.",
    "Sortuj oferty": "Sort offers",
    "Najtańsze najpierw": "Lowest price first",
    "Najdroższe najpierw": "Highest price first",
    "Zastosuj": "Apply",
    "Sprzedawca": "Seller",
    "Sklep": "Shop",
    "Królestwo": "Kingdom",
    "Mapa / CH": "Map / CH",
    "Ilość": "Quantity",
    "Cena": "Price",
    "Cena za sztukę": "Unit price",
    "Brak aktywnych ofert tego przedmiotu.": "No active offers for this item.",
    "🧪 Zestawy PvP botów": "🧪 Bot PvP sets",
    "Eksperymentalne. Część botów buduje osobny zestaw do walki z innymi botami; domyślnie wyłączone.": "Experimental. Some bots build a separate set for fighting other bots; disabled by default.",
    "Włącz zestawy PvP": "Enable PvP sets",
    "Udział botów (%)": "Share of bots (%)",
    "Minimalny poziom": "Minimum level",
    "Siła zestawu": "Set strength",
    "Niska": "Low",
    "Normalna": "Normal",
    "Wysoka": "High",
    "Budżet (%)": "Budget (%)",
    "Używaj także przeciw graczom": "Use against players too",
    "📊 Skaluj progi podaży do liczby botów": "📊 Scale supply thresholds to bot population",
    "Referencyjna liczba botów": "Reference bot population",
    "Domyślnie wyłączone. Po włączeniu progi podaży skalują się do liczby aktywnych botów względem wartości referencyjnej (domyślnie 1000).": "Disabled by default. When enabled, supply thresholds scale with active bots relative to the reference population (1000 by default).",
    "📈 Opaski i Kamień Duchowy wyceniane według podaży": "📈 Price Forgetting Bands and Spirit Stones by supply",
    "Silnik stosuje te same progi podaży co dla ksiąg umiejętności. Domyślnie włączone.": "The core uses the same supply thresholds as for skill books. Enabled by default.",
    "🧺 Miejsce w sklepie offline bota": "🧺 Space in a bot's offline shop",
    "Przy pełnym sklepie bot może sprzedać u handlarki ćwierć najtańszego stosu materiałów lub ksiąg, aby zwolnić miejsce. Nie dotyka wyposażenia.": "When a shop is full, a bot may sell a quarter of its cheapest materials or books stack to the general merchant to free space. Equipment is untouched.",
    "🤝 Targowanie botów z graczami": "🤝 Bots haggle with players",
    "bot może szeptem zaproponować cenę za zbyt drogi przedmiot +6 lub wyższy na sklepie offline gracza": "A bot can whisper an offer for an overpriced +6 or higher item in a player's offline shop",
    "⚔️ Zabójstwa kończące wojnę": "⚔️ Kills to end a guild war",
    "0 = tylko czas wojny": "0 = war timer only",
    "⚒️ Rzemieślnicy (%)": "⚒️ Craftsmen (%)",
    "Udział botów od 35 poziomu kujących przedmioty na sprzedaż. Domyślnie 30%; 0 wyłącza tę cechę.": "Share of bots from level 35 that forge items for sale. The default is 30%; 0 disables this trait.",
    "Gęstość czatu Global (%)": "Global chat density (%)",
    "100% to zwykłe natężenie rozmów botów na Globalu. 0 przywraca dawny czat i wołanie w obrębie królestwa.": "100% is the normal rate of bot conversations on Global. 0 restores the old chat and kingdom-only shouts.",
    "Realizm sesji (%)": "Session realism (%)",
    "Odsetek botów grających według realistycznego rytmu dnia i tygodnia. 0 zachowuje dotychczasowy tryb. Działa niezależnie od przełącznika sesji powyżej.": "Percentage of bots following a realistic daily and weekly rhythm. 0 keeps the previous behaviour. This works independently of the session switch above.",
    "jak dotąd": "as before",
    "Szybkość ruchu postaci (%)": "Character movement speed (%)",
    "100% to tempo z gry. Dotyczy graczy, botów i Towarzysza, pieszo i na wierzchowcu. Potwory zachowują swoje tempo.": "100% is the normal game speed. This affects players, bots and Companions, on foot and on mounts. Monsters keep their normal speed.",
    "Zapisz szybkość ruchu": "Save movement speed",
    "Bonusy w przedmiotach z potworów (%)": "Bonuses on monster drops (%)",
    "100% to szansa z gry. Zmienia tylko nowe bronie i zbroje wypadające z potworów, najwyżej do trzech bonusów; nagrody, skrzynie i sklepy pozostają bez zmian.": "100% is the game's normal chance. This changes only newly dropped weapons and armour, up to three bonuses; rewards, chests and shops are unchanged.",
    "Zapisz bonusy w dropie": "Save drop bonus chance",
    "Obrona przed botami innych królestw": "Defence against foreign kingdom bots",
    "Towarzysz w trybie Atak lub Obrona oraz pomoc gildii i grupy odpowiadają na celowe ataki obcych botów na gracza. Pasywny Towarzysz nie atakuje.": "A Companion in Attack or Defend mode, and guild and party help, respond to deliberate attacks by foreign kingdom bots on a player. A passive Companion does not attack.",
    "Włączona": "Enabled",
    "Wyłączona": "Disabled",
    "Zapisz obronę": "Save defence",
    "Yang z potworów zabitych przez gracza": "Yang from monsters killed by players",
    "Domyślnie trafia prosto do ekwipunku. Opcja „na ziemię” działa jak w oryginalnej grze; podnieść Yang może każdy. Boty i Towarzysz nadal otrzymują je prosto do ekwipunku.": "By default, Yang goes straight into the inventory. The ground option works as in the original game; anyone can pick it up. Bots and Companions still receive it directly.",
    "Do ekwipunku": "Into inventory",
    "Na ziemię": "On the ground",
    "Zapisz ustawienie Yang": "Save Yang setting",
    "Szósty bonus nowych broni 70 poziomu": "Sixth bonus for new level-70 weapons",
    "Zmiana dotyczy tylko nowo tworzonych broni; istniejące przedmioty zachowują bonus. Działa na żywo i zostaje po restarcie.": "The setting affects only newly created weapons; existing items keep their bonus. It applies live and persists after a restart.",
    "Zapisz szósty bonus": "Save sixth bonus",
    "Włączony": "Enabled",
    "Wyłączony dla nowych broni": "Off for new weapons",
    "Usuń przedmiot bota": "Delete bot item",
    "Usuwanie wykonuje silnik gry. Gdy bot jest offline, żądanie czeka do jego wejścia.": "The game engine handles deletion. If the bot is offline, the request waits until it logs in.",
    "Założony": "Equipped",
    "Anuluj": "Cancel",
    "Usuń": "Delete",
    # --- base.html: site chrome, present on every single page ---
    "Otwórz menu": "Open menu",
    "Powiadomienia": "Notifications",
    "🔔 Powiadomienia": "🔔 Notifications",
    "Oznacz wszystkie jako przeczytane": "Mark all as read",
    "Ładowanie…": "Loading…",
    "Seban Control Center": "Seban Control Center",
    "⌂ Dashboard": "⌂ Dashboard",
    "♙ Gracze i boty": "♙ Players & bots",
    "Lista graczy": "Player list",
    "Osobowości botów": "Bot personalities",
    "⚑ Gildie": "⚑ Guilds",
    "♜ Rankingi": "♜ Rankings",
    "◇ Gospodarka": "◇ Economy",
    "Stan przedmiotów": "Item stock",
    "Sklepy offline": "Offline shops",
    "⌖ Aktywność map": "⌖ Map activity",
    "✦ Sezon": "✦ Season",
    "🎉 Eventy": "🎉 Events",
    "♨ Respawny": "♨ Respawns",
    "✉ Wiadomości": "✉ Messages",
    "Czat na żywo": "Live chat",
    "Wiadomości ze świata": "World messages",
    "▤ Wydajność": "▤ Performance",
    "⌁ Diagnostyka": "⌁ Diagnostics",
    "Diagnostyka wędkowania": "Fishing diagnostics",
    "Logi panelu": "Panel logs",
    "☷ Changelog": "☷ Changelog",
    "⚙ Zarządzanie": "⚙ Management",
    "Gra i serwer": "Game & server",
    "Panel webowy": "Web panel",
    "♧ Konta i GM": "♧ Accounts & GM",
    "Konta": "Accounts",
    "Nazwy postaci botów": "Bot character names",
    "🧬 Kreator postaci": "🧬 Character creator",
    "⌘ Komendy GM": "⌘ GM commands",
    "▦ Baza przedmiotów": "▦ Item database",
    "↗ Panel Tieru (klasyczny)": "↗ Tieru panel (classic)",
    "Wyloguj": "Log out",
    "OK": "OK",

    # --- login.html / setup.html ---
    "Panel administracyjny": "Admin panel",
    "Nieprawidłowe hasło.": "Incorrect password.",
    "Hasło administratora": "Administrator password",
    "Zaloguj": "Log in",

    # --- common buttons / labels reused across many forms ---
    "Zapisz": "Save",
    "Zapisz ustawienia": "Save settings",
    "Zapisz ustawienia panelu": "Save panel settings",
    "Anuluj": "Cancel",
    "Szukaj": "Search",
    "Wyszukaj": "Search",
    "Filtruj": "Filter",
    "Odśwież": "Refresh",
    "Wyślij": "Send",
    "Usuń": "Delete",
    "Edytuj": "Edit",
    "Dodaj": "Add",
    "Zamknij": "Close",
    "Poprzedni": "Previous",
    "Następny": "Next",
    "Pierwsza": "First",
    "Ostatnia": "Last",
    "Brak danych.": "No data.",
    "Brak danych": "No data",
    "Wczytywanie...": "Loading...",
    "Wczytywanie…": "Loading…",
    "Tak": "Yes",
    "Nie": "No",
    "Włącz": "Enable",
    "Wyłącz": "Disable",
    "włączone": "enabled",
    "wyłączone": "disabled",
    "włączony": "enabled",
    "wyłączony": "disabled",

    # --- rankings.html ---
    "#": "#",
    "Postać": "Character",
    "Klasa": "Class",
    "Gildia": "Guild",
    "Poziom": "Level",
    "EXP": "EXP",
    "Wynik": "Score",
    "Brak wpisów.": "No entries.",
    "Żaden gracz nie ma jeszcze wpisu w tym rankingu.": "No player has an entry in this ranking yet.",
    "tylko gracze": "players only",
    "Postać gracza": "Player character",
    "Wystawione na sklepie": "Listed on a shop",

    # --- manage_panel.html: appearance form ---
    "✦ Wygląd i działanie": "✦ Appearance & behaviour",
    "Nazwa panelu": "Panel name",
    "Alarm bez ruchu": "Idle alert",
    "minut": "minutes",
    "Kolorystyka": "Colour theme",
    "Ocean": "Ocean",
    "Ember": "Ember",
    "Forest": "Forest",
    "Cesarstwo": "Empire",
    "Źródło monitoringu": "Monitoring source",
    "VPS / host": "VPS / host",
    "Docker / lokalnie": "Docker / local",
    "Kursor": "Cursor",
    "Metin2 (domyślny)": "Metin2 (default)",
    "Systemowy": "System",
    "Ochrona hasłem": "Password protection",
    "Nowe hasło": "New password",
    "co najmniej 8 znaków": "at least 8 characters",
    "opcjonalne": "optional",
    "Hasło jest przechowywane jako bezpieczny skrót. Wyłączenie ochrony usuwa jego skrót z panelu.":
        "The password is stored as a secure hash. Disabling protection removes its hash from the panel.",
    "Język panelu": "Panel language",
    "Polski": "Polish",
    "English": "English",
}

# --- account_detail.html / accounts.html ---
EXACT.update({
    "← Powrót do kont": "← Back to accounts",
    "PODGLĄD KONTA": "ACCOUNT OVERVIEW",
    "Brak przypisanego królestwa": "No kingdom assigned",
    "⭐ Brak aktywnego VIP": "⭐ No active VIP",
    "➕ Stwórz nową postać": "➕ Create new character",
    "Nick": "Nickname",
    "Czas gry": "Playtime",
    "Ostatnie logowanie": "Last login",
    "Yang": "Yang",
    "Brak postaci na tym koncie.": "No characters on this account.",
    "ADMINISTRACJA": "ADMINISTRATION",
    "Nowe konto": "New account",
    "Login": "Login",
    "Hasło": "Password",
    "E-mail": "Email",
    "(opcjonalnie)": "(optional)",
    "Kod usunięcia postaci": "Character deletion code",
    "Dokładnie 7 cyfr": "Exactly 7 digits",
    "Rodzaj konta": "Account type",
    "Królestwo": "Kingdom",
    "Shinsoo": "Shinsoo",
    "Chunjo": "Chunjo",
    "Jinno": "Jinno",
    "Nick postaci GM": "GM character nickname",
    "(tworzona od razu; np. [GM]Seban)": "(created immediately; e.g. [GM]Seban)",
    "Klasa postaci": "Character class",
    "Płeć postaci": "Character gender",
    "Utwórz konto": "Create account",
    "Konta serwera": "Server accounts",
    "🔍 Login lub nick postaci": "🔍 Login or character nickname",
    "Wyświetlaj": "Show",
    "Wszystkie": "All",
    "Szukaj": "Search",
    "ID": "ID",
    "Utworzono": "Created",
    "Ostatnia gra": "Last played",
    "Pokaż konto": "View account",
    "Brak kont pasujących do wyszukiwania.": "No accounts match the search.",
})

# --- _inventory_fragment.html ---
EXACT.update({
    "Ekwipunek postaci": "Character equipment",
    "Ta strona ekwipunku jest pusta.": "This equipment page is empty.",
    "Strona I": "Page I",
    "Strona II": "Page II",
    "Strona III": "Page III",
    "Ta strona magazynu jest pusta.": "This storage page is empty.",
    "Juki konne — widoczne tylko przy przywołanym i odblokowanym u stajennego koniu.":
        "Saddlebags — only visible with a summoned horse unlocked at the stableman.",
    "Smocza Alchemia": "Dragon Soul Alchemy",
    "Alchemia Smoczych Kamieni": "Dragon Soul Alchemy",
    "Smoczy Diament": "Dragon Diamond",
    "Smoczy Rubin": "Dragon Ruby",
    "Smoczy Jadeit": "Dragon Jade",
    "Smoczy Szafir": "Dragon Sapphire",
    "Smoczy Granat": "Dragon Garnet",
    "Smoczy Onyks": "Dragon Onyx",
    "Podgląd": "Preview",
    "Oryginalny układ klienta gry · zestawy i Smocze Kamienie są odczytywane bezpośrednio z postaci.":
        "Original game-client layout · decks and Dragon Stones are read directly from the character.",
})

# --- base.html: site chrome, on every page ---
EXACT.update({
    "ItemShop": "ItemShop",
})

# --- bot_names.html ---
EXACT.update({
    "Pula nicków, z której silnik ubiera każdego bota w momencie, gdy jego konto powstaje w bazie — nie wtedy, gdy go \"wpuszczamy\" (podnosimy limit aktywnych botów). Nick jest przydzielany raz i zostaje na stałe, nawet jeśli lista się zmieni później. Priorytety i blokady poniżej działają więc dopiero na boty, które":
        "The name pool the engine draws from when a bot's account is first created in the database — not when it's \"let in\" (raising the active bot cap). A nickname is assigned once and stays for good, even if the list changes later. So the priorities and blocks below only take effect on bots that",
    "jeszcze nie mają żadnego nicku": "don't have a nickname yet",
    "— to znaczy dopiero po realnym poszerzeniu puli (pełny wipe/reseed), nie na obecnie żyjące boty.":
        "— meaning only after the pool is actually expanded (a full wipe/reseed), not on bots that already exist.",
    "Nicków w puli": "Names in pool",
    "Już przydzielonych": "Already assigned",
    "Zablokowanych": "Blocked",
    "Własnych (dodanych ręcznie)": "Custom (added manually)",
    "➕ Dodaj nowe nicki do kolejki": "➕ Add new names to the queue",
    "Nicki (jeden na linię)": "Names (one per line)",
    "Priorytet": "Priority",
    "(wyższy = wcześniej w kolejce)": "(higher = earlier in the queue)",
    "Dodaj do kolejki": "Add to queue",
    "⚙ Zastosuj teraz": "⚙ Apply now",
    "🔍 Szukaj nicku": "🔍 Search nickname",
    "Wszystkie królestwa": "All kingdoms",
    "Wszystkie statusy": "All statuses",
    "Wolne (w kolejce)": "Free (queued)",
    "Już przydzielone": "Already assigned",
    "Zablokowane": "Blocked",
    "Filtruj": "Filter",
    "Źródło": "Source",
    "Status": "Status",
    "Akcje": "Actions",
    "Zapisz priorytet": "Save priority",
    "⛔ Zablokowany": "⛔ Blocked",
    "⏳ W kolejce": "⏳ Queued",
    "Odblokuj": "Unblock",
    "Zablokuj": "Block",
    "Usuń": "Delete",
    "Brak nicków pasujących do filtrów.": "No names match the filters.",
})

# --- bot_personalities.html ---
EXACT.update({
    "GRACZE I BOTY": "PLAYERS & BOTS",
    "Tylko boty aktualnie zalogowane — osobowość, czynność i mapa są odczytywane na żywo, offline boty tego nie mają.":
        "Only bots currently logged in — personality, activity and map are read live; offline bots don't have this.",
    "Szukaj po nicku": "Search by nickname",
    "Wyczyść": "Clear",
    "Bot": "Bot",
    "Klasa": "Class",
    "Osobowość": "Personality",
    "Czynność": "Activity",
    "Mapa": "Map",
    "Pokaż kartę postaci": "View character card",
    "Brak botów pasujących do filtra.": "No bots match the filter.",
})

# --- changelog.html ---
EXACT.update({
    "Changelog": "Changelog",
    "Źródło changelogu": "Changelog source",
    "🛠 Advanced Seban Webpanel": "🛠 Advanced Seban Webpanel",
    "⚔ Playerbots by Tieru": "⚔ Playerbots by Tieru",
    "Prosto z": "Straight from",
    "repozytorium Tieru": "Tieru's repository",
    "Brak wpisów.": "No entries.",
    "Każdy hotfix i zmiana panelu jest od tej chwili zapisywana z czasem wdrożenia.":
        "Every panel hotfix and change is now logged with its deployment time.",
})

# --- character_creator.html ---
EXACT.update({
    "Kreator postaci": "Character creator",
    "Płeć": "Gender",
    "Mężczyzna": "Male",
    "Kobieta": "Female",
    "Nazwa": "Name",
    "Litery, cyfry i nawiasy [ ], 2-24 znaki": "Letters, digits and [ ] brackets, 2-24 characters",
    "Dalej": "Next",
    "PLAYER": "PLAYER",
    "LOW_WIZARD": "LOW_WIZARD",
    "GOD": "GOD",
    "HIGH_WIZARD": "HIGH_WIZARD",
    "IMPLEMENTOR": "IMPLEMENTOR",
    "Konto": "Account",
    "Istniejące konto": "Existing account",
    "🔍 Szukaj loginu…": "🔍 Search login…",
    "Wstecz": "Back",
    "Stwórz postać": "Create character",
    "Poprzednia klasa": "Previous class",
    "Wojownik": "Warrior",
    "Następna klasa": "Next class",
})

# --- daily_summary.html ---
EXACT.update({
    "← Dashboard": "← Dashboard",
    "📅 Podsumowanie dnia": "📅 Daily summary",
    "Pełna doba 00:00–24:00. Liczniki ryb, rudy, walk, ulepszeń i sprzedaży pochodzą z dziennych logów gry; konta GM i stali towarzysze graczy są pomijani w osiągnięciach.":
        "Full 00:00–24:00 day. Fish, ore, combat, refine and sale counters come from the daily game logs; GM accounts and players' permanent companions are excluded from achievements.",
    "Boty w grze": "Bots in game",
    "Yang w obiegu": "Yang in circulation",
    "Przedmiotów ulepszonych na +9": "Items refined to +9",
    "Zniszczonych kamieni Metin": "Metin stones destroyed",
    "Pokonanych bossów": "Bosses defeated",
    "Otwartych Szkatułek Umarłego Rozpruwacza": "Reaper's Chests opened",
    "tego dnia / ogółem do końca dnia": "today / total by end of day",
    "Wyłowionych ryb": "Fish caught",
    "Wykopanej rudy": "Ore mined",
    "Smoczych Monet w obiegu": "Dragon Coins in circulation",
    "Zorganizowane eventy": "Events run",
    "Najwyższy poziom": "Highest level",
    "Sklepów offline": "Offline shops",
    "LIDERZY DNIA": "TODAY'S LEADERS",
    "🏆 Najlepsze wyniki": "🏆 Top results",
    "brak zdarzeń": "no events",
    "NAJCENNIEJSZE OSIĄGNIĘCIA": "MOST VALUABLE ACHIEVEMENTS",
    "🔨 Najlepsze +9 dnia": "🔨 Best +9 of the day",
    "Złoty Młot Kowala": "Blacksmith's Golden Hammer",
    "Gracz:": "Player:",
    "Ta strona nie ma linku w nawigacji — dociera się tu z powiadomienia albo bezpośredniego linku.":
        "This page has no link in the navigation — you get here from a notification or a direct link.",
})

# --- dashboard.html ---
EXACT.update({
    "CENTRUM KONTROLI": "CONTROL CENTER",
    "Stan świata": "World status",
    "Dane historyczne odświeżają się co 5 minut.": "Historical data refreshes every 5 minutes.",
    "Postacie i konta": "Characters & accounts",
    "postacie / konta": "characters / accounts",
    "suma przy postaciach": "total held by characters",
    "Stosy przedmiotów": "Item stacks",
    "ekwipunek + magazyny": "equipment + storage",
    "Najnowsza zmiana": "Latest change",
    "Szczegóły w changelogu.": "See the changelog for details.",
    "Zobacz changelog →": "See the changelog →",
    "● NA ŻYWO · 1,5 S": "● LIVE · 1.5 S",
    "Mapa świata botów": "World map of bots",
    "Pozycje bezpośrednio z rdzenia Playerbots.": "Positions straight from the Playerbots core.",
    "Nicki i poziomy": "Names & levels",
    "Tylko grupy": "Parties only",
    # The maps by the English names the Playerbots core itself gives them
    # (GetPlayerBotMapNameEn, playerbot_language.h: what the bots say to a
    # player who reads English); the panel's own kingdom and V1/V2
    # qualifiers stay where the game has one name for several maps (the
    # Monkey Dungeons of the three kingdoms, the Grotto of Exile, which the
    # client names "Grotto of Exile" on both floors). A village is called
    # the same in both languages. Inside a longer text a map is translated
    # by the patterns _MAP_NAMES_IN_TEXT makes, near the bottom.
    "Chunjo M1 — Joan": "Chunjo M1 — Joan",
    "Chunjo M2 — Bokjung": "Chunjo M2 — Bokjung",
    "Chunjo M3 — Waryong": "Chunjo M3 — Waryong",
    "Loch Małp Chunjo": "Chunjo Monkey Dungeon",
    "Shinsoo M1 — Yongan": "Shinsoo M1 — Yongan",
    "Shinsoo M2 — Jayang": "Shinsoo M2 — Jayang",
    "Shinsoo M3 — Jungrang": "Shinsoo M3 — Jungrang",
    "Loch Małp Shinsoo": "Shinsoo Monkey Dungeon",
    "Jinno M1 — Pyongmoo": "Jinno M1 — Pyongmoo",
    "Jinno M2 — Bakra": "Jinno M2 — Bakra",
    "Jinno M3 — Imha": "Jinno M3 — Imha",
    "Loch Małp Jinno": "Jinno Monkey Dungeon",
    "Loch Małp Normalny": "Monkey Dungeon II",
    "Loch Małp Trudny": "Monkey Dungeon III",
    "Dolina Orków": "Orc Valley",
    "Pustynia Yongbi": "Yongbi Desert",
    "Góra Sohan": "Mount Sohan",
    "Loch Pająków V1": "Spider Dungeon",
    "Świątynia Hwang": "Hwang Temple",
    "Las": "Ghost Wood",
    "Las Duchów": "Ghost Wood",
    "Czerwony Las": "Red Wood",
    "Szukaj bota…": "Search bot…",
    "▦ Diagramy mapy": "▦ Map charts",
    "Ładowanie pozycji…": "Loading positions…",
    "Gracz": "Player",
    "Grupa": "Party",
    "Możliwie zawieszony": "Possibly stuck",
    "Walka z Metinem": "Fighting a Metin",
    "CH1 · zielona obwódka": "CH1 · green ring",
    "CH2 · różowa obwódka": "CH2 · pink ring",
    "CH3 · biała obwódka": "CH3 · white ring",
    "CH4 · czarna obwódka": "CH4 · black ring",
    "Widoczne": "Visible",
    "W PT": "In party",
    "Śr. poziom": "Avg. level",
    "Maks. poziom": "Max level",
    "Ranking": "Ranking",
    "Aktywności": "Activities",
    "Ranking na mapie": "Map ranking",
    "Aktywności na tej mapie": "Activities on this map",
    "Rozkład kanałów": "Channel distribution",
    "Respawny na mapie": "Map respawns",
    "Królestwa na mapie": "Kingdoms on the map",
    "PLAYERBOTS · ŚWIAT": "PLAYERBOTS · WORLD",
    "Stan serwera": "Server status",
    "Botów w grze": "Bots in game",
    "W grupach": "In parties",
    "Zalogowane boty": "Logged-in bots",
    "Zalogowane boty wg kanału": "Logged-in bots by channel",
    "Wersja panelu": "Panel version",
    "Wersja Playerbots": "Playerbots version",
    "Raty serwerowe": "Server rates",
    "Boty na mapach": "Bots on maps",
    "CPU": "CPU",
    "RAM": "RAM",
    "Dysk": "Disk",
    "Pamięć RAM": "RAM memory",
    "Boty według map": "Bots by map",
    "Automatycznie przełączaj rankingi co 8 sekund": "Automatically switch rankings every 8 seconds",
    "najwyższe poziomy": "highest levels",
    "Ognista Ziemia": "Doyyumhwaji",
    "Loch Pająków V2": "Spider Dungeon 2",
    "Grota Wygnańców V1": "Grotto of Exile V1",
    "Grota Wygnańców V2": "Grotto of Exile V2",
    "⚔ Potwory": "⚔ Monsters",
    "🗿 Metiny i bossy": "🗿 Metins & bosses",
    "🗿 Metiny": "🗿 Metins",
    "👹 Bossowie": "👹 Bosses",
    "✦ Liczebność": "✦ Population",
    "Auto": "Auto",
    "Poprzedni ranking": "Previous ranking",
    "Następny ranking": "Next ranking",
    "Brak danych — jeszcze nikt tego nie zrobił.": "No data — nobody has done this yet.",
    "✦ WIADOMOŚCI ZE ŚWIATA": "✦ WORLD MESSAGES",
    "Ukryj": "Hide",
    "Ładowanie najważniejszych wydarzeń…": "Loading top events…",
})

# --- diagnostics.html ---
EXACT.update({
    "TYLKO DO ODCZYTU": "READ-ONLY",
    "⌁ Diagnostyka Playerbots": "⌁ Playerbots diagnostics",
    "Skrócony odczyt bieżących statusów rdzenia, logów gry i dziennika zdarzeń. Nie zmienia ustawień ani danych świata.":
        "A quick read of the core's current status, game logs and event log. Doesn't change any settings or world data.",
    "Boty online": "Bots online",
    "Łowią teraz": "Fishing right now",
    "Waga wędkowania": "Fishing weight",
    "Zdarzenia FISH w bazie": "FISH events in the database",
    "Wniosek dla wędkowania": "Fishing verdict",
    "Rdzeń raportuje aktywnych wędkarzy. Poniżej znajduje się ich bieżący status.":
        "The core reports active fishers. Their current status is below.",
    "Żaden aktywny bot nie raportuje akcji „Łowi ryby”. W Playerbots decyzja, czy bot będzie wędkarzem, zapada raz na bota; zmiana wagi działa więc dla kolejnej puli botów, a nie od razu dla istniejącej populacji.":
        "No active bot reports a \"Fishing\" action. In Playerbots, whether a bot becomes a fisher is decided once per bot; so a weight change applies to the next batch of bots, not immediately to the existing population.",
    "Boty aktualnie łowiące": "Bots currently fishing",
    "Brak aktywnych wędkarzy.": "No active fishers.",
    "Ostatnie wpisy związane z łowieniem": "Latest fishing-related entries",
    "Przeszukiwane są ostatnie 256 KB każdego logu rdzenia, bez pobierania ani wysyłania całych plików.":
        "The last 256 KB of each core log is searched, without downloading or sending whole files.",
    "Brak wpisów związanych z fishing / wędką / wędkowaniem.": "No entries related to fishing / rod / angling.",
})

# --- economy.html / economy_item.html / economy_itemshop.html / economy_shops.html ---
EXACT.update({
    "GOSPODARKA": "ECONOMY",
    "Przedmioty i balans dropu": "Items & drop balance",
    "Yang w obiegu · 7 dni": "Yang in circulation · 7 days",
    "Nazwa lub VNUM przedmiotu": "Item name or VNUM",
    "Przedmiot": "Item",
    "VNUM": "VNUM",
    "Łączna ilość": "Total quantity",
    "Brak wyników albo pierwszy odczyt jeszcze trwa.": "No results, or the first read is still in progress.",
    "← Wróć do gospodarki": "← Back to economy",
    "HISTORIA PRZEDMIOTU": "ITEM HISTORY",
    "Stan w gospodarce · ostatnie 14 dni": "Economy stock · last 14 days",
    "GOSPODARKA · ITEMSHOP": "ECONOMY · ITEMSHOP",
    "🪙 Smocze Monety i ItemShop": "🪙 Dragon Coins & ItemShop",
    "Stan walut kont oraz historia zakupów z natywnego ItemShopu.": "Account currency balances and native ItemShop purchase history.",
    "Smocze Monety w obiegu": "Dragon Coins in circulation",
    "Smocze Znaki w obiegu": "Dragon Tokens in circulation",
    "Zakupy ItemShop": "ItemShop purchases",
    "ostatnie zarejestrowane transakcje": "latest recorded transactions",
    "Popularne pozycje": "Popular items",
    "różnych kupowanych przedmiotów": "distinct items purchased",
    "Najwięcej Smoczych Monet": "Most Dragon Coins",
    "Zakupy w ostatnich 14 dniach": "Purchases in the last 14 days",
    "Top konta — Smocze Monety": "Top accounts — Dragon Coins",
    "Monety": "Coins",
    "Znaki": "Tokens",
    "Konto gracza": "Player account",
    "Brak kont z monetami.": "No accounts with coins.",
    "Najwięcej Smoczych Znaków": "Most Dragon Tokens",
    "Brak kont ze znakami.": "No accounts with tokens.",
    "Ostatnie zakupy w ItemShopie": "Latest ItemShop purchases",
    "Kiedy": "When",
    "Kupujący": "Buyer",
    "Nie ma jeszcze zapisanych zakupów w ItemShopie.": "No ItemShop purchases recorded yet.",
    "Aktywne sklepy": "Active shops",
    "otwarte stragany": "open market stalls",
    "Oferty / Sztuk towaru": "Listings / Units of stock",
    "pozycji / łączna ilość": "listings / total quantity",
    "Wartość rynku": "Market value",
    "yang, suma ofert": "yang, sum of listings",
    "Transakcji łącznie": "Total transactions",
    "🏪 Sklepy na mapach": "🏪 Shops on maps",
    "Brak aktywnych sklepów w ostatnim odczycie.": "No active shops in the latest read.",
    "📦 Sztuk towaru wg królestwa": "📦 Stock units by kingdom",
    "💰 Wartość rynku w czasie · 7 dni": "💰 Market value over time · 7 days",
    "Za mało odczytów kolektora, żeby pokazać trend — wróć za kilka cykli (co 5 minut).":
        "Not enough collector reads yet to show a trend — check back in a few cycles (every 5 minutes).",
    "🔥 Najszybciej rozchodzące się przedmioty · ostatnie 24h": "🔥 Fastest-moving items · last 24h",
    "Ranking wg liczby faktycznych sprzedaży ze straganów (nie samych ofert) — im wyżej, tym bardziej pożądany towar; wskaźnik ceny porównuje ostatnie 12h z wcześniejszymi 12h w oknie. Punkt odniesienia do podnoszenia cen botom.":
        "Ranked by actual stall sales (not just listings) — the higher, the more in-demand the item; the price indicator compares the last 12h against the previous 12h in the window. A reference point for raising bot prices.",
    "Sprzedaży/24h": "Sales/24h",
    "Tempo": "Pace",
    "Wyświetlane pozycje:": "Displayed entries:",
    "Szukanie przedmiotu…": "Searching for item…",
    "Szukanie…": "Searching…",
    "🔥 Rozmiar rankingu sprzedaży": "🔥 Sales ranking size",
    "GOSPODARKA · WIDOK": "ECONOMY · VIEW",
    "Ustal, ile pozycji pokazuje tabela „Najszybciej rozchodzące się przedmioty · ostatnie 24h”. Limit 100 chroni panel przed zbyt ciężkim widokiem.": "Choose how many entries the ‘Fastest-moving items · last 24h’ table displays. The 100-entry cap keeps the page responsive.",
    "Liczba pozycji": "Number of entries",
    "Zapisz limit rankingu": "Save ranking limit",
    "Sztuk": "Units",
    "Śr. cena/szt.": "Avg. price/unit",
    "Śr. cena: ostatnie 12h vs wcześniejsze 12h": "Avg. price: last 12h vs previous 12h",
    "Brak sprzedaży ze straganów w ostatnich 24h.": "No stall sales in the last 24h.",
    "📚 Najlepiej sprzedające się księgi umiejętności · ostatnie 24h": "📚 Best-selling skill books · last 24h",
    "Wszystkie Księgi mają ten sam VNUM w grze — konkretną umiejętność ustalamy z socketu przedmiotu, co udaje się tylko dla części sprzedaży (reszta to już zużyte przez bota egzemplarze, bez śladu w bazie), więc lista poniżej pokazuje tylko te, które dało się rozpoznać.":
        "All Books share the same in-game VNUM — the specific skill is read from the item's socket, which only works for part of the sales (the rest are copies already consumed by a bot, with no trace left in the database), so the list below only shows the ones that could be identified.",
    "Umiejętność": "Skill",
    "Brak rozpoznanych sprzedaży ksiąg w ostatnich 24h.": "No identifiable book sales in the last 24h.",
    "🧾 Ostatnie sprzedaże na straganach": "🧾 Latest stall sales",
    "Kto sprzedał co i za ile — silnik nie zapisuje tożsamości kupującego przy sprzedaży ze straganu (IkarusShop), więc feed pokazuje wyłącznie stronę sprzedawcy. Odświeża się co 20s.":
        "Who sold what and for how much — the engine doesn't record the buyer's identity for stall sales (IkarusShop), so the feed only shows the seller's side. Refreshes every 20s.",
    "Czas": "Time",
    "Sprzedawca": "Seller",
    "Cena": "Price",
    "Brak zarejestrowanych sprzedaży.": "No recorded sales.",
    "Oferty": "Listings",
    "Zmiana od ~24h": "Change over ~24h",
    "● na rynku": "● on the market",
    "brak danych": "no data",
})

# --- events.html ---
EXACT.update({
    "PLAYERBOTS · NA ŻYWO": "PLAYERBOTS · LIVE",
    "🎉 Planer eventów": "🎉 Event planner",
    "Uruchamiaj eventy od razu albo ustawiaj ich tygodniowy harmonogram. Rdzeń Playerbots odczytuje zmianę w ciągu pięciu sekund — restart nie jest potrzebny.":
        "Trigger events right away or set up their weekly schedule. The Playerbots core reads the change within five seconds — no restart needed.",
    "RDZEŃ": "CORE",
    "Brak aktywnego eventu": "No active event",
    "ustaw szybki event lub plan": "set a quick event or a schedule",
    "SZYBKI START": "QUICK START",
    "Aktywuj teraz": "Activate now",
    "Tymczasowy event działa niezależnie od harmonogramu i kończy się automatycznie.":
        "A temporary event runs independently of the schedule and ends automatically.",
    "Eventy na różnych mapach trwają jednocześnie; uruchomienie na mapie, na której event już trwa, zaczyna go tam od nowa.":
        "Events on different maps run simultaneously; starting one on a map where an event is already running restarts it there.",
    "Zatrzymaj": "Stop",
    "Uruchom jednorazowo": "Run once",
    "Bonus": "Bonus",
    "% ponad ratę serwera": "% above the server rate",
    "EVENTY ŚWIATOWE": "WORLD EVENTS",
    "Udział botów": "Bot participation",
    "Procent kwalifikujących się botów, które dołączą do eventów Tanaka i Zuo.":
        "Percentage of eligible bots that join the Tanaka and Zuo events.",
    "Zapisz udział": "Save participation",
    "TYDZIEŃ POWTARZALNY": "RECURRING WEEK",
    "Harmonogram eventów": "Event schedule",
    "Kliknij wolną godzinę, aby dodać event. Kliknij istniejący blok, aby go edytować. Kalendarz zapisuje te same reguły Playerbots co dotychczas; okno 22:00–02:00 przechodzi przez północ.":
        "Click a free hour to add an event. Click an existing block to edit it. The calendar saves the same Playerbots rules as before; the 22:00–02:00 window crosses midnight.",
    "aktywny": "active",
    "zaplanowany": "scheduled",
    "◉ Teraz": "◉ Now",
    "＋ Dodaj event": "＋ Add event",
    "Tygodniowy harmonogram eventów": "Weekly event schedule",
    "Bloki są powtarzane co tydzień. Możesz zaznaczyć wiele dni w edytorze eventu.":
        "Blocks repeat every week. You can select multiple days in the event editor.",
    "Zapisz harmonogram": "Save schedule",
    "NOWY EVENT": "NEW EVENT",
    "Dodaj event": "Add event",
    "Zamknij": "Close",
    "Event": "Event",
    "Dni tygodnia": "Days of the week",
    "Od": "From",
    "Do": "To",
    "Włączony": "Enabled",
    "Anuluj": "Cancel",
    "Zapisz event": "Save event",
    "HISTORIA": "HISTORY",
    "📜 Ostatnie zakończone eventy": "📜 Latest finished events",
    "Statystyki liczone ze zdarzeń w logu (zdobycie szkatułki / realnie zdobyty yang), nie ze stanu ekwipunku — dokładne niezależnie od tego co boty zrobiły z łupem.":
        "Statistics are counted from log events (chest obtained / actually earned yang), not from equipment state — accurate regardless of what bots did with the loot.",
    "Wynik": "Score",
    "Żaden event jeszcze się nie zakończył od kiedy to śledzimy.": "No event has finished yet since we started tracking this.",
    "brak statystyk": "no statistics",
    "połączony": "connected",
    "czeka na status": "waiting for status",
    # EVENT_MAPS's 0: Tanaka or Zuo picks its map itself
    "Wybiera event": "Event's choice",
    "Piraci naraz": "Pirates at once",
    "Metiny w fali": "Metins per wave",
    # the weekly calendar, which events.html's script draws
    "Poniedziałek": "Monday", "Wtorek": "Tuesday", "Środa": "Wednesday", "Czwartek": "Thursday",
    "Piątek": "Friday", "Sobota": "Saturday", "Niedziela": "Sunday",
    "Pn": "Mon", "Wt": "Tue", "Śr": "Wed", "Cz": "Thu", "Pt": "Fri", "Sb": "Sat", "Nd": "Sun",
    "EDYCJA EVENTU": "EDIT EVENT",
    "Edytuj event": "Edit event",
    "liczba jednostek eventu": "number of event units",
    "Wybierz co najmniej jeden dzień.": "Select at least one day.",
    "Ustaw godzinę rozpoczęcia i zakończenia.": "Set the start and end time.",
    "Można zapisać maksymalnie 16 eventów.": "At most 16 events can be saved.",
})

# --- gm_commands.html ---
EXACT.update({
    "NARZĘDZIA ADMINISTRATORA": "ADMINISTRATOR TOOLS",
    "Komendy GM": "GM commands",
    "Parametry w nawiasach ostrokątnych zastępuj własną wartością.": "Replace parameters in angle brackets with your own value.",
    "⚠ Informacja o zgodności": "⚠ Compatibility notice",
    "Niektóre komendy mogą nie działać w tej paczce plików. Część listy pochodzi z ogólnych poradników Metin2 dostępnych w internecie, a dostępność komendy zależy od wersji i kompilacji rdzenia serwera.":
        "Some commands may not work in this file package. Part of the list comes from general Metin2 guides available online, and command availability depends on the server core's version and build.",
})

# --- guild.html / guilds.html ---
EXACT.update({
    "← Powrót do gildii": "← Back to guilds",
    "GILDIA": "GUILD",
    "Lider": "Leader",
    "Członkowie": "Members",
    "aktualny skład": "current roster",
    "Punkty rangi": "Rank points",
    "ranking gildii": "guild ranking",
    "Wojny": "Wars",
    "wygrane / remisy / porażki": "wins / draws / losses",
    "Członkowie gildii": "Guild members",
    "Postać": "Character",
    "Rola": "Role",
    "Darowizna": "Donation",
    "Brak zapisanych członków.": "No members recorded.",
    "PLAYERBOTS · GILDIE I WOJNY": "PLAYERBOTS · GUILDS & WARS",
    "Gildie botów": "Bot guilds",
    "Klasa wynika z siły mistrza i percentyla królestwa. Lista jest sortowana: Elitarne, Silne, Średnie, Zwykłe.":
        "Class is derived from the master's power and the kingdom percentile. The list is sorted: Elite, Strong, Average, Common.",
    "Boty online w gildiach": "Bots online in guilds",
    "Toczące się wojny": "Ongoing wars",
    "Exp ofiarowany od startu": "Exp donated since start",
    "⚔ Następna wojna gildii botów": "⚔ Next bot guild war",
    "Nazwa gildii lub nick mistrza": "Guild name or master's nickname",
    "Gildia": "Guild",
    "Online": "Online",
    "Mistrz": "Master",
    "Śr. siła": "Avg. power",
    "Z / R / P": "W / D / L",
    "Exp gildii": "Guild exp",
    "Wojna": "War",
    "Rdzenie nie zgłosiły jeszcze gildii botów. Po restarcie pierwszy spis siły odbywa się po około 10 minutach.":
        "The cores haven't reported bot guilds yet. After a restart, the first power census happens after about 10 minutes.",
    "System gildii przygotowuje pierwszy raport": "The guild system is preparing its first report",
    "Rdzeń po starcie wykonuje spis siły botów po około 10 minutach. Wtedy przypisze klasy istniejącym gildiom i zacznie publikować ich status.":
        "After starting, the core runs a bot power census after about 10 minutes. It then assigns classes to existing guilds and starts publishing their status.",
    "Gildie graczy": "Player guilds",
    "Gildie, których mistrzem jest człowiek, prosto z bazy danych: bez klasy (to percentyl botów) i bez liczby osób online.":
        "Guilds whose master is a human, straight from the database: no class (that's a bot percentile) and no online headcount.",
    "Żadnej gildii nie prowadzi jeszcze człowiek.": "No guild is led by a human yet.",
})

# --- item_grants.html ---
EXACT.update({
    "← Zarządzanie": "← Management",
    "MASOWE NADAWANIE": "BULK GRANTING",
    "Przedmioty dla postaci i botów": "Items for characters & bots",
    "Wybierz VNUM, ilość i dowolne warunki. Wszystkie wypełnione warunki obowiązują jednocześnie.":
        "Choose a VNUM, quantity and any conditions. All filled-in conditions apply at once.",
    "Warunki odbiorców": "Recipient conditions",
    "VNUM przedmiotu": "Item VNUM",
    "Ilość na postać": "Quantity per character",
    "Minimalny poziom": "Minimum level",
    "Maksymalny poziom": "Maximum level",
    "Min. poziom konia": "Min. horse level",
    "Min. czas gry": "Min. playtime",
    "godzin": "hours",
    "Min. jeździectwo (skill 130)": "Min. riding (skill 130)",
    "Tylko postacie, które nie mają tego VNUM": "Only characters that don't have this VNUM",
    "Pokaż odbiorców": "Show recipients",
    "VNUM 50051 to „Zdjęcie Konia”. Opcja „nie mają” sprawdza ekwipunek, wyposażenie oraz magazyny konta.":
        "VNUM 50051 is the \"Horse Photo\". The \"don't have\" option checks equipment, inventory and account storage.",
    "Aktywne boty odbierają przedmiot przez grę w kolejnych tickach. System przekazuje naraz do 10 odbiorców, więc duże grupy są obsługiwane seriami. Postacie offline czekają na logowanie. Nie wymaga restartu serwera.":
        "Active bots receive the item in-game over successive ticks. The system delivers to up to 10 recipients at a time, so large groups are handled in batches. Offline characters wait until they log in. No server restart needed.",
    "Lv": "Lv",
    "Koń": "Horse",
    "Jeździectwo": "Riding",
    "Stan nadawania": "Granting status",
    "⚠️ Worker nadawania jeszcze nigdy się nie odezwał. Kontener": "⚠️ The granting worker has never reported in. The container",
    "seban-item-grants": "seban-item-grants",
    "nie działa albo nie ma dostępu do bazy — bez niego zlecenia zostaną w stanie „Czeka na wysłanie”. Uruchom go:":
        "isn't running or has no database access — without it, orders will stay \"Waiting to send\". Start it with:",
    "docker compose up -d seban-item-grants": "docker compose up -d seban-item-grants",
    "stanął — zlecenia zostaną w stanie „Czeka na wysłanie”, dopóki nie wróci:":
        "has stopped — orders will stay \"Waiting to send\" until it comes back:",
    "Ostatni błąd workera:": "Latest worker error:",
    "web_admin": "web_admin",
    ") budzi się przy pierwszym logowaniu po starcie serwera — zaloguj się dowolną postacią, a jeśli to nie pomoże, quest w obrazie gry jest nieaktualny.":
        ") wakes up on the first login after server start — log in with any character, and if that doesn't help, the quest in the game image is out of date.",
    "Czeka na wysłanie:": "Waiting to send:",
    "·\nDo sprawdzenia:": "·\nTo check:",
    "·\nNadano:": "·\nGranted:",
    "Postać offline wraca do kolejki co dwie minuty, aż się zaloguje; „Czeka na wysłanie” przy działającym workerze i pustej kolejce gry oznacza właśnie to.":
        "An offline character returns to the queue every two minutes until it logs in; \"Waiting to send\" with a running worker and an empty in-game queue means exactly this.",
    "Ostatnie nadania": "Latest grants",
    "Odśwież wyniki": "Refresh results",
    "Warunki": "Conditions",
    "Aktualizacja": "Update",
    "Anuluj partię": "Cancel batch",
    "Nie zlecono jeszcze nadawania.": "No grants have been ordered yet.",
})

# --- items.html / items_catalog.html ---
EXACT.update({
    "KATALOG GRY": "GAME CATALOG",
    "Baza ID przedmiotów": "Item ID database",
    "Komplet danych z aktualnej bazy serwera: polskie nazwy, VNUM-y oraz ikony klienta.":
        "Full data from the current server database: the official English names (Polish where the game has none), VNUMs and client icons.",
    "Wszystkie przedmioty": "All items",
    "Szukaj po nazwie lub VNUM": "Search by name or VNUM",
    "Brak przedmiotów pasujących do wyszukiwania.": "No items match the search.",
})

# --- live_chat.html / live_chat_messages.html ---
EXACT.update({
    "Wiadomości": "Messages",
    "Podkategorie wiadomości": "Message subcategories",
    "✦ Wiadomości ze świata": "✦ World messages",
    "▤ Czat na żywo": "▤ Live chat",
    "Protokół wiadomości": "Message log",
    "LIVE · odświeżanie co 4 s": "LIVE · refreshes every 4s",
    "Wołaj i Handel": "Call and Trade",
    "nick prowadzi do karty postaci": "nickname links to the character card",
    "ostatnie 100 wiadomości, zapisane trwale — wejdź o dowolnej porze": "last 100 messages, stored permanently — visit any time",
    "tylko wiadomości zapisane przez rdzeń gry": "only messages recorded by the game core",
    "Podgląd tylko do odczytu · nie wysyła wiadomości do gry": "Read-only preview · doesn't send messages into the game",
    "↻ Odśwież": "↻ Refresh",
    "OGŁOSZENIE": "ANNOUNCEMENT",
    # each line's channel, as the English client calls the two chats
    # (CHAT_SHOUT "Call", CHAT_TRADE "Trade")
    "WOŁAJ": "CALL",
    "HANDEL": "TRADE",
    "Brak przechwyconych wiadomości.": "No captured messages.",
    "Gdy ktoś napisze na Wołaj lub Handel, pojawi się tutaj automatycznie.":
        "When someone writes on Call or Trade, it'll appear here automatically.",
})

# --- login.html (a couple already in base EXACT above) ---

# --- maps.html ---
EXACT.update({
    "AKTYWNOŚĆ ŚWIATA": "WORLD ACTIVITY",
    "Mapy w czasie": "Maps over time",
    "Natężenie graczy z ostatnich 24 godzin oraz zdarzenia odnotowane w logach serwera.":
        "Player density from the last 24 hours and events recorded in the server logs.",
    "Wszystkie kanały": "All channels",
    "Natężenie na mapach": "Map density",
    "Kliknij wiersz aktualnego natężenia lub zaznacz mapy poniżej, aby odfiltrować wykres.":
        "Click a row in the current density table or select maps below to filter the chart.",
    "Wszystkie mapy": "All maps",
    "Mapy na wykresie": "Maps on the chart",
    "Aktualne natężenie": "Current density",
    "Postacie": "Characters",
    "Pokaż tylko tę mapę na wykresie": "Show only this map on the chart",
    "Czekam na dane.": "Waiting for data.",
    "🔥 Mapa cieplna zdarzeń": "🔥 Event heatmap",
    "Śmierci botów, rozbite Metiny i zabite bossy z dostępnej historii gry. Pozycje są grupowane w siatce mapy, a większa plama oznacza większą liczbę zdarzeń w danym obszarze.":
        "Bot deaths, broken Metins and killed bosses from the available game history. Positions are grouped into a map grid, and a larger blob means more events in that area.",
    "Zgony botów": "Bot deaths",
    "Rozbite Metiny": "Broken Metins",
    "Zabite bossy": "Bosses killed",
    "Chunjo M1": "Chunjo M1",
    "📊 Boty wg przedziału poziomu": "📊 Bots by level bracket",
    "Ile obecnie jest botów w każdym przedziale poziomu (co 10) i jak ta liczba zmieniała się w ostatnich dniach — pomaga ocenić, czy czas dodać kolejną pulę świeżych botów.":
        "How many bots are currently in each level bracket (every 10 levels), and how that count has changed over the last few days — helps judge whether it's time to add another batch of fresh bots.",
    "Historia przedziałów poziomu dopiero się zbiera (migawka co 5 minut) — wykres napełni się w ciągu najbliższych godzin.":
        "Level-bracket history is just starting to accumulate (a snapshot every 5 minutes) — the chart will fill in over the next few hours.",
    # the two charts' tooltips (the canvas asks these through its own tr())
    "Godzina": "Time",
    "postaci": "characters",
})

# --- panel_logs.html ---
EXACT.update({
    "DIAGNOSTYKA": "DIAGNOSTICS",
    "Błędy działania samego webpanelu (nie gry) — z pełnym śladem (traceback), która strona/akcja to wywołała i kiedy. Jeśli coś Ci się zepsuło w panelu, pobierz plik poniżej i załącz go do zgłoszenia — będzie od razu jasne, skąd się wziął błąd, zamiast zgadywać po samym opisie.":
        "Errors from the web panel itself (not the game) — with a full traceback, which page/action triggered it, and when. If something in the panel breaks, download the file below and attach it to your report — it'll be immediately clear where the error came from, instead of guessing from a description alone.",
    "📥 Pobierz pełny plik logów": "📥 Download full log file",
    "Ostatnie wpisy (do 500 linii)": "Latest entries (up to 500 lines)",
    "Brak zapisanych błędów — panel nie zarejestrował jeszcze żadnego wyjątku od czasu wdrożenia tej funkcji.":
        "No errors recorded — the panel hasn't logged any exception since this feature was deployed.",
})

# --- world_feed.html / world_feed_events.html ---
EXACT.update({
    "✦ Ogłoszenie": "✦ Announcement",
    "✦ Mistrzostwo": "✦ Mastery",
    "🐚 Rzadkość": "🐚 Rarity",
    "🎁 Skrzynia Ripera": "🎁 Reaper's Chest",
    "Nagroda": "Reward",
    "Nagroda ze szkatułki": "Chest reward",
    "u kowala": "at the blacksmith",
    "Brak wydarzeń.": "No events.",
    "Gdy ktoś ulepszy coś na +7 i wyżej, zdobędzie mistrzostwo umiejętności, złowi Małż albo otworzy Szkatułkę Umarłego Rozpruwacza, pojawi się tutaj.":
        "When someone refines something to +7 or higher, earns a skill mastery, catches a Clam, or opens a Reaper's Chest, it'll appear here.",
    "PLAYERBOTS · KRONIKA ŚWIATA": "PLAYERBOTS · WORLD CHRONICLE",
    "Oś czasu najważniejszych osiągnięć: ulepszenia +7 i wyżej, zdobyte mistrzostwa umiejętności i rzadkie znaleziska — dokładnie to, co widać w tickerze na dashboardzie, tylko z pełną historią.":
        "A timeline of the most important achievements: +7 and higher refines, earned skill masteries and rare finds — exactly what's shown in the dashboard ticker, just with the full history.",
    "Załaduj starsze wydarzenia": "Load older events",
    "To już wszystkie wydarzenia z ostatnich 14 dni.": "That's all the events from the last 14 days.",
    "Dziś": "Today",
    "Wczoraj": "Yesterday",
})

# --- players.html ---
EXACT.update({
    "BAZA GRACZY": "PLAYER DATABASE",
    "Gracze i boty": "Players & bots",
    "Nick lub ID postaci": "Nickname or character ID",
    "Stały towarzysz gracza": "Player's permanent companion",
    "· na żywo": "· live",
    "· ostatni zapis": "· last save",
})

# --- rankings.html ---
EXACT.update({
    "RYWALIZACJA": "COMPETITION",
    "Rankingi": "Rankings",
    "Sortuj według:": "Sort by:",
    "Średnie obrażenia": "Average damage",
    "Obrażenia umiejętności": "Skill damage",
    "Poziom ulepszenia": "Refine level",
    "Pokaż:": "Show:",
    "Wszyscy": "Everyone",
    "Same postacie ludzi, bez botów, ponumerowane między sobą": "Only human characters, no bots, numbered among themselves",
    "👤 Tylko gracze": "👤 Players only",
    "👤 tylko gracze": "👤 players only",
    "Wyników na stronę:": "Results per page:",
    "← Poprzednia": "← Previous",
    "Następna →": "Next →",
    "Idź do strony": "Go to page",
    "Idź": "Go",
    "Sprzedaże na sklepie Offline": "Offline shop sales",
    "CZAT": "CHAT",
    "Tydzień": "Week",
    "Wszechczasów": "All time",
    "OSTATNIE 7 DNI": "LAST 7 DAYS",
    "WSZECHCZASÓW": "ALL TIME",
    "🏆 Sezon i rekordy świata": "🏆 Season and world records",
    "Punkty: Metin 150 · boss 500 · ulepszenie +7 lub wyżej 200. Dane z ostatnich 7 dni.": "Points: Metin 150 · boss 500 · refine +7 or higher 200. Data from the last 7 days.",
    "Punkty: Metin 150 · boss 500. Liczniki całego życia postaci z silnika gry.": "Points: Metin 150 · boss 500. Lifetime character counters from the game engine.",
    "Ulepszenia": "Refines",
    "Metiny — rekord świata": "Metins — world record",
    "Bossy — rekord świata": "Bosses — world record",
    "tydzień": "week",
    "wszechczasów": "all time",
    "👤 to postać gracza; postaci GM-ów nie są liczone.": "👤 this is a player character; GM characters are not counted.",
    "Zainstalowana wersja": "Installed version",
    "Rodzaj broni:": "Weapon type:",
    "Miecz": "Sword",
    "Sztylet": "Dagger",
    "Łuk": "Bow",
    "Broń dwuręczna": "Two-handed weapon",
    "Dzwon": "Bell",
    "Wachlarz": "Fan",
    "Wojownik Ciało": "Warrior Body",
    "Wojownik Umysł": "Warrior Mind",
    "Ninja Ostrze": "Ninja Blade",
    "Ninja Łuk": "Ninja Bow",
    "Sura Broń": "Sura Weapon",
    "Sura Czarna Magia": "Sura Dark Magic",
    "Szaman Smok": "Shaman Dragon",
    "Szaman Leczenie": "Shaman Healing",
})

# --- respawns.html ---
EXACT.update({
    "KONTROLA ŚWIATA": "WORLD CONTROL",
    "Dostosuj tempo i liczebność świata bez wyłączania serwera. Zmiany globalne trafiają do rdzenia przez kolejkę MT2009 i zostają zapisane po restarcie.":
        "Adjust the world's pace and population without shutting down the server. Global changes reach the core through the MT2009 queue and are kept after a restart.",
    "LIVE": "LIVE",
    "kolejny cykl respawnu": "next respawn cycle",
    "CZAS ODRODZENIA": "RESPAWN TIME",
    "Tempo świata": "World pace",
    "100% zachowuje czasy z plików Tieru. Niższa wartość skraca oczekiwanie, przy czym rdzeń nigdy nie zejdzie poniżej 3 sekund.":
        "100% keeps the times from Tieru's files. A lower value shortens the wait, though the core will never go below 3 seconds.",
    "🗿 Metiny i bossy": "🗿 Metins & bosses",
    "🗿 Metiny": "🗿 Metins",
    "👹 Bossowie": "👹 Bosses",
    "🗿 Metiny · 👹 Bossowie": "🗿 Metins · 👹 Bosses",
    "Osobno dla Metinów, bossów i zwykłych potworów. Metin to kamień Metin, boss to potwór o randze bossa.":
        "Metins, bosses and regular monsters each have their own. A Metin is a Metin stone, a boss a monster of the boss rank.",
    "⚔ Zwykłe potwory": "⚔ Regular monsters",
    "Zastosuj tempo na żywo": "Apply pace live",
    "LICZEBNOŚĆ": "POPULATION",
    "Ile stoi na mapie": "How many stand on the map",
    "Mnożnik uzupełnia każdą linię respawnu przy kolejnym cyklu. NPC, teleporty, rudy i instancje pozostają bez zmian.":
        "The multiplier tops up every respawn line on the next cycle. NPCs, teleports, ore and instances stay unchanged.",
    "Zastosuj liczebność na żywo": "Apply population live",
    "🔒 Dokładne czasy jednej mapy wymagają helpera": "🔒 Exact per-map times require the helper",
    "m2-map-regens": "m2-map-regens",
    "DOKŁADNA MAPA": "EXACT MAP",
    "Własny czas respawnu": "Custom respawn time",
    "↻ wymaga krótkiego restartu rdzeni": "↻ requires a short core restart",
    "To precyzyjne ustawienie nadpisuje czas w pliku wybranej mapy. Puste pole przywraca wartość dostarczoną z wydaniem Tieru.":
        "This precise setting overrides the time in the selected map's file. An empty field restores the value shipped with Tieru's release.",
    "Rodzaj": "Type",
    "Potwory": "Monsters",
    "Metiny": "Metins",
    "domyślny": "default",
    "sekundy": "seconds",
    "Zapisz dla mapy": "Save for map",
    "Silnik MT2009 łączy je w jedną grupę. Ustawienie dotyczy obu naraz.": "The MT2009 engine merges them into one group. The setting applies to both at once.",
    "⚡ Zmiany live": "⚡ Live changes",
    "Wpływają na następny respawn, nie tworzą dodatkowych jednostek natychmiast.":
        "They affect the next respawn, they don't create extra units immediately.",
    "↻ Mapa": "↻ Map",
    "Indywidualne sekundy są plikową zmianą mapy, dlatego rdzenie odtwarzają się po zapisaniu.":
        "Individual seconds are a file-level map change, so the cores restart after saving.",
})

# --- season.html ---
EXACT.update({
    "OSTATNIE 7 DNI": "LAST 7 DAYS",
    "🏆 Sezon i rekordy świata": "🏆 Season & world records",
    "Punkty: Metin 150 · boss 500 · ulepszenie +7 lub wyżej 200. Dane są liczone z ostatnich 7 dni.":
        "Points: Metin 150 · boss 500 · +7 or higher refine 200. Data is counted from the last 7 days.",
    "Metiny — rekord świata": "Metins — world record",
    "Bossy — rekord świata": "Bosses — world record",
    "Ulepszenia +7": "+7 refines",
    "Ranking tygodnia": "Weekly ranking",
    "👤 to postać gracza; postaci GM-ów nie są liczone.": "👤 is a player character; GM characters aren't counted.",
    "Bossy": "Bosses",
    "Punkty": "Points",
    "Brak zdarzeń z ostatnich 7 dni.": "No events in the last 7 days.",
})

# --- setup.html ---
EXACT.update({
    "PIERWSZE URUCHOMIENIE": "FIRST RUN",
    "Skonfiguruj panel": "Configure the panel",
    "Te ustawienia można później zmienić w Zarządzaniu.": "These settings can be changed later in Management.",
    "opcjonalnie": "optional",
    "Hasło panelu": "Panel password",
    "Zapisz i otwórz panel": "Save and open the panel",
})

# --- economy.html / economy_shops.html: conditional static branches ---
EXACT.update({
    "Wyniki wyszukiwania": "Search results",
    "Najczęstsze przedmioty": "Most common items",
    "⭐ Wyniki wyszukiwania": "⭐ Search results",
    "⭐ Najpopularniejsze przedmioty w sklepach": "⭐ Most popular items in shops",
    "Brak wyników.": "No results.",
    "Brak aktywnych ofert w sklepach.": "No active shop listings.",
})

# --- dashboard.html theme mottos: Jinja {% set %} literals, not text nodes,
# so they render via {{hero_eyebrow}}/{{hero_sub}} rather than appearing as
# translatable template text -- need the literal values themselves here. ---
EXACT.update({
    "帝國 · CESARSTWO WOJOWNIKÓW": "帝國 · EMPIRE OF WARRIORS",
    "Trzy imperia. Jedno pole bitwy. Kroniki cesarstwa czuwają nad każdym wojownikiem.":
        "Three empires. One battlefield. The empire's chronicles watch over every warrior.",
    "EMBER · CENTRUM DOWODZENIA": "EMBER · COMMAND CENTER",
    "Żar bitew nie gaśnie. Panel czuwa nad każdym wojownikiem i botem.":
        "The embers of battle never fade. The panel watches over every warrior and bot.",
    "FOREST · CENTRUM DOWODZENIA": "FOREST · COMMAND CENTER",
    "Spokojna kontrola świata Playerbots, ukryta pośród zielonych krain.":
        "Calm control of the Playerbots world, hidden among green lands.",
    "OCEAN · CENTRUM DOWODZENIA": "OCEAN · COMMAND CENTER",
    "Nadzór nad światem Playerbots — mapy, ekonomia i wojownicy w jednym miejscu.":
        "Oversight of the Playerbots world — maps, economy and warriors in one place.",
})

# --- rate labels: Jinja tuple literals in manage.html/events.html, not text
# nodes -- render via {{label}} so need the literal values here too. ---
EXACT.update({
    "Doświadczenie": "Experience",
    "Drop przedmiotów": "Item drop",
    "Drop Yang": "Yang drop",
})

# --- app.py GUILD_TIERS / BOT_PERSONALITIES / BOT_ACTIONS: finite Python
# dict vocabularies rendered as plain text, not template literals -- same
# treatment as any other exact phrase since they end up as text nodes. ---
EXACT.update({
    "Elitarna": "Elite",
    "Silna": "Strong",
    "Średnia": "Average",
    "Zwykła": "Common",
    "Wytrwały poszukiwacz": "Persistent seeker",
    "Pogromca Metinów": "Metin slayer",
    "Towarzysz drużyny": "Party companion",
    "Mistrz ekwipunku": "Gear master",
    "Rozważny zbieracz": "Careful gatherer",
    "Handlarz": "Merchant",
    "Wędrowiec": "Wanderer",
    "Dropek Metinów": "Metin dropper",
    "Dropek z M3": "M3 dropper",
    "Dropek z M2": "M2 dropper",
    "Dropek medali": "Medal dropper",
    "Planuje następny ruch": "Planning next move",
    "Podróżuje": "Traveling",
    "Walczy": "Fighting",
    "Podnosi łup": "Picking up loot",
    "Regeneruje się": "Regenerating",
    "Wybiera profesję": "Choosing a profession",
    "Handluje": "Trading",
    "Ulepsza EQ": "Refining gear",
    "Czyta KU": "Reading a skill book",
    "Wkłada KD": "Equipping a mount item",
    "Organizuje PT": "Organizing a party",
    "Robi Biologa": "Doing the Biologist",
    "Odwiedza Stajennego": "Visiting the Stableman",
    "Prowadzi stragan": "Running a stall",
    "Łowi ryby": "Fishing",
    "Przegląda stragany": "Browsing stalls",
    "Wabi potwory": "Luring monsters",
    "Odpoczywa w mieście": "Resting in town",
    "Kopie rudę": "Mining ore",
})

# --- rankings() route's `kinds` dict: Python dict literal, ends up as
# plain <option> text, not template source -- same treatment. ---
EXACT.update({
    "Zbroja": "Armor",
    "Broń": "Weapon",
    "Broń 30 Lv": "Weapon Lv 30",
    "Przedmioty": "Items",
    "Umiejętności": "Skills",
    "Koń": "Horse",
    "Biolog": "Biologist",
    "Otwarte stragany": "Open stalls",
    "Przedmiot +9": "+9 item",
    "Kategoria:": "Category:",
    "Wszystkie": "All",
    "Zbroje": "Armor",
    "Hełmy": "Helmets",
    "Tarcze": "Shields",
    "Bransolety": "Bracelets",
    "Buty": "Boots",
    "Naszyjniki": "Necklaces",
    "Kolczyki": "Earrings",
    "Sortuj według:": "Sort by:",
    "Poziom przedmiotu": "Item level",
    "Poziom postaci": "Character level",
    "Bossy": "Bosses",
    "Pomyślne ulepszenia": "Successful refines",
    "Skuteczność ulepszeń": "Refine success rate",
    "Wyłowione ryby": "Fish caught",
    "Rekord obrażeń (zwykłe)": "Damage record (normal)",
    "Rekord obrażeń (konno)": "Damage record (mounted)",
    "Rekord obrażeń (umiejętność)": "Damage record (skill)",
    "Zabite potwory (łącznie)": "Monsters killed (total)",
    "Pokonane minibossy": "Minibosses defeated",
    "Pokonani gracze (PVP)": "Players defeated (PVP)",
    "Wygrane pojedynki": "Duels won",
    "Wykopane rudy": "Ore mined",
})

# --- manage_panel.html PANEL_FEATURES dict (compatibility gating info) ---
EXACT.update({
    "Wymaga akcji": "Needs action",
    "Docelowa liczba botów": "Target bot count",
    "Hostowy watcher obsługujący botcount.request i odtworzenie kontenera game.":
        "Host watcher handling botcount.request and recreating the game container.",
    "Uruchom updater/install-seban-updater.sh dla katalogu stosu. Watcher zapisze PLAYERBOT_AUTOSPAWN_COUNT w .env i odtworzy usługę game.":
        "Run updater/install-seban-updater.sh for the stack directory. The watcher writes PLAYERBOT_AUTOSPAWN_COUNT in .env and recreates the game service.",
    "Hostowy watcher obsługujący spawn-plan.request.": "Host watcher handling spawn-plan.request.",
    "Zainstaluj updater/install-seban-updater.sh. Integracja zapisuje okno wejścia w .env i bezpiecznie odtwarza game.":
        "Install updater/install-seban-updater.sh. The integration writes the entry window in .env and safely recreates game.",
    "Dokładne respawny map": "Exact map respawns",
    "Helper m2-map-regens w obrazie gry oraz wolumen rates-spool.": "The m2-map-regens helper in the game image, plus the rates-spool volume.",
    "Wdróż integration/m2-map-regens do obrazu game, przebuduj usługę game i pozostaw podłączony wolumen rates-spool.":
        "Deploy integration/m2-map-regens into the game image, rebuild the game service, and keep the rates-spool volume attached.",
    "Skrzynia startowa na żywo": "Live starter chest",
    "Zmodyfikowany starter_chest.quest i tabela common.m2_switches.": "A modified starter_chest.quest and the common.m2_switches table.",
    "Zastosuj patch questa skrzyni startowej, skompiluj questy i ustaw M2_PLAYERBOT_DISABLE_STUDENT_CHEST zgodnie z wyborem dla botów.":
        "Apply the starter chest quest patch, compile the quests, and set M2_PLAYERBOT_DISABLE_STUDENT_CHEST to match the choice for bots.",
    "Komenda NOTICE w web_admin.quest oraz działający seban-collector.": "The NOTICE command in web_admin.quest, plus a running seban-collector.",
    "Wdróż do web_admin.quest obsługę NOTICE, skompiluj quest i uruchom usługę seban-collector.":
        "Deploy NOTICE support into web_admin.quest, compile the quest, and start the seban-collector service.",
    "Usługa systemowa seban-updater i wspólny wolumen update-spool.": "The seban-updater system service and the shared update-spool volume.",
    "Uruchom: sudo updater/install-seban-updater.sh /pełna/ścieżka/do/serwera [projekt-compose]. Następnie włącz funkcję tutaj.":
        "Run: sudo updater/install-seban-updater.sh /full/path/to/server [compose-project]. Then enable the feature here.",
})

# --- bot_names.html: inline Jinja ternary literals ---
EXACT.update({
    "Własny": "Custom",
    "Baza silnika": "Engine pool",
})

# --- app.py RATE_PRESETS tuple: literal Python strings, not template text ---
EXACT.update({
    "🎯 Normalnie — dokładnie jak w oryginalnej grze": "🎯 Normal — exactly like the original game",
    "🌿 Spokojne zadania — doświadczenie 300%, przedmioty 200%, yang 200%": "🌿 Relaxed pace — experience 300%, items 200%, yang 200%",
    "🚀 Szybko — doświadczenie 1000%, przedmioty 500%, yang 500%": "🚀 Fast — experience 1000%, items 500%, yang 500%",
})

# --- app.py server_settings_status() messages ---
EXACT.update({
    "Helper ustawień serwera jest gotowy.": "The server settings helper is ready.",
    "Zlecenie nie jest odbierane przez helper gry. Sprawdź instalację integracji; po 10 minutach można usunąć wyłącznie zaległe zlecenie.":
        "The order isn't being picked up by the game helper. Check the integration install; after 10 minutes you can clear only the pending order.",
    "Ten silnik (mt2009) nie korzysta ze wspólnego helpera ustawień: raty, docelowa liczba botów i respawny na mapach są obsługiwane bezpośrednio przez m2-rates / m2-botcount / m2-map-regens w kontenerze gry, każdy własnym restartem rdzeni.":
        "This engine (mt2009) doesn't use the shared settings helper: rates, target bot count and map respawns are each handled directly by m2-rates / m2-botcount / m2-map-regens in the game container, each with its own core restart.",
    "Ta wersja serwera nie zawiera silnikowej integracji Sebana, więc zmiana respawnów map jest niedostępna. Restart serwera i zmiana rat działają normalnie i niczego nie wymagają.":
        "This server version doesn't include Seban's engine integration, so changing map respawns isn't available. Server restart and rate changes work normally and need nothing extra.",
})

# --- feminine adjective forms ("funkcja"/"cecha" agreement) missing from
# the earlier generic włączone/wyłączone block ---
EXACT.update({
    "włączona": "enabled",
    "wyłączona": "disabled",
})

# --- manage_panel.html PANEL_FEATURES capability cards: bare (no-emoji)
# titles, distinct text nodes from the emoji versions used elsewhere ---
EXACT.update({
    "Aktualizator Seban": "Seban Updater",
    "Plan wejścia botów": "Bot entry plan",
    "Ogłoszenia ulepszeń +9": "+9 refine announcements",
    "Aktywna": "Active",
})

# --- manage_panel.html PANEL_FEATURES "scope" field: shown standalone in
# the capability card, distinct text node from the <title>-tag variant
# ("Zarządzanie grą · X") handled by the generic pattern above. ---
EXACT.update({
    "Zarządzanie grą · liczba botów": "Game management · bot count",
    "Zarządzanie grą · plan wejścia": "Game management · entry plan",
    "Respawny · własny czas mapy": "Respawns · custom map timing",
    "Zarządzanie grą · skrzynia ucznia": "Game management · apprentice chest",
    "Zarządzanie grą · rankingi": "Game management · rankings",
    "Zarządzanie grą · aktualizacje": "Game management · updates",
})

# --- app.py AI_WEIGHT_KEYS: (key, label, icon) tuples, rendered as
# "{{icon}} {{label}}" -- one combined text node with the emoji, so needs
# its own entries distinct from any bare "Koń"/"Wędkowanie" translation
# used elsewhere. ---
EXACT.update({
    "🧪 Mikstury": "🧪 Potions",
    "🔨 Kowal": "🔨 Blacksmith",
    "📖 Księgi umiejętności": "📖 Skill books",
    "🐎 Koń": "🐎 Horse",
    "🧬 Biolog": "🧬 Biologist",
    "🗿 Metiny": "🗿 Metins",
    "👥 Grupy": "👥 Parties",
    "🏹 Misje polowania": "🏹 Hunting missions",
    "⚔️ Bicie potworów": "⚔️ Fighting monsters",
    "🎣 Wędkowanie": "🎣 Fishing",
    "🏪 Stragany": "🏪 Stalls",
})

# --- app.py AI_WEIGHT_HINTS: behaviour slider tooltips (title attribute) ---
EXACT.update({
    "Kiedy bot wraca po mikstury: przy 100 poniżej 300 czerwonych / 200 niebieskich; 25 czeka do ćwiartki, 250 idzie przy 2,5× (najwyżej 480/360). Od razu.":
        "When a bot restocks potions: at 100, below 300 red / 200 blue; 25 waits until a quarter left, 250 goes at 2.5× (capped at 480/360). Immediate.",
    "Wyprawy do kowala po ulepszenie. 100 = każda okazja; poniżej część botów pomija kowala po pół godziny (przy 50 co drugie pół godziny). Od razu.":
        "Trips to the blacksmith to refine. 100 = every opportunity; below that, some bots skip the blacksmith every half hour (at 50, every other half hour). Immediate.",
    "Czytanie ksiąg umiejętności. 100 = każda okazja; poniżej część botów zostawia księgi w plecaku po pół godziny. Od razu.":
        "Reading skill books. 100 = every opportunity; below that, some bots leave books in their bag every half hour. Immediate.",
    "Wyprawy do Lochu Małp po medale konne (stajnia i dropperzy medali nie słuchają). Przy następnym sprawdzeniu podróży.":
        "Trips to the Monkey Dungeon for horse medals (the stable and medal droppers don't listen to this). Takes effect at the next travel check.",
    "Polowanie na okazy dla Biologa. 100 = każdy bot z misją; poniżej część botów po pół godziny bije to, co jest na mapie. To, co niesie, i tak oddaje. Od razu.":
        "Hunting specimens for the Biologist. 100 = every bot with a mission; below that, some bots fight whatever's on the map every half hour instead. What they're carrying still gets handed in either way. Immediate.",
    "Raz na godzinę bot od 15 lv losuje pół godziny na metinach: 25% przy 100 (koń bojowy ×2), razy suwak. Łowcy z roli zawsze. Do godziny.":
        "Once an hour, a bot at level 15+ rolls for half an hour on Metins: 25% at 100 (×2 with a battle horse), times the slider. Role hunters always do. Up to an hour.",
    "Udział botów w grupach: w wioskach 20% przy 100 (5% przy 25, 50% przy 250); na froncie przy 100 już każdy, więc tam działa tylko w dół. 1–3 min.":
        "Bot participation in parties: in villages 20% at 100 (5% at 25, 50% at 250); on the frontier everyone already parties at 100, so the slider there only works downward. 1–3 min.",
    "Misja polowania na awans (tylko r40250). 100 = każdy bot z misją; poniżej część botów po pół godziny bije to, co jest na mapie.":
        "The promotion hunting mission (r40250 only). 100 = every bot with a mission; below that, some bots fight whatever's on the map every half hour instead.",
    "Zwykłe bicie potworów. Podniesione: cel „poziom” wygrywa w statusie, grinderzy biją po kilka potworów naraz i piją mikstury szybkości. Obniżenie nic nie zmienia.":
        "Regular monster fighting. Raised: the \"level\" goal wins in status, grinders fight several monsters at once and drink speed potions. Lowering it changes nothing.",
    "Ilu botów łowi: przy osobowościach bot od 30 lv bez grupy losuje co pół godziny wg nastroju. Podniesienie w sekundy, obniżenie po końcu sesji (do godziny).":
        "How many bots fish: with personalities enabled, a bot at level 30+ without a party rolls every half hour based on mood. Raising it takes effect in seconds, lowering it after the current session ends (up to an hour).",
    "Ilu botów trzyma stragan (bez Handlarza, biednych, pełnego plecaka, droppera pod presją i cennych zapasów). Na 2.x stojący sklep offline tylko nie jest odnawiany po 8 h.":
        "How many bots run a stall (excluding the Merchant, poor bots, a full bag, a dropper under pressure, and valuable stock). On 2.x, a standing offline shop simply isn't refreshed after 8h.",
})

# --- class names (JOB_NAMES / GM_JOB_OPTIONS / item_grants.JOBS / CLASS_PROFILES) ---
EXACT.update({
    "Szaman": "Shaman",
    "Każda klasa": "Any class",
})

# --- app.py GM_RANK_OPTIONS ---
EXACT.update({
    "Gracz (brak rangi)": "Player (no rank)",
    "Pomocnik": "Helper",
    "Wyższy GM": "Senior GM",
    "Właściciel": "Owner",
})

# restart_progress() stage labels render combined with a percentage
# ("100% · Serwer działa"), so they're PATTERNS entries, not EXACT --
# see PATTERNS_RAW below.

# --- item_grants.html criteria_text() ---
EXACT.update({
    "Bez warunków": "No conditions",
})


# --- manage.html behaviour panel reset button ---
EXACT.update({
    "Przywróć 100%": "Restore 100%",
})

# --- app.py APPLY_LABELS: the item stat/bonus name vocabulary used in
# every item tooltip across the whole panel (rankings, player pages, item
# database, economy) -- highest-leverage single block here since it's
# reused on virtually every item shown anywhere. Standard Metin2 stat
# names, matched to the official international client's terminology.
# Kept as its own dict (not folded into EXACT until below) because
# apply_text() renders these combined with a value ("Szybkość ataku
# +5%"), not as a bare label -- PATTERNS entries for that combined form
# are generated from this dict automatically, near the bottom of this
# file, instead of hand-writing ~120 near-identical regexes. ---
_ITEM_STAT_LABELS = {
    "Maks. PŻ": "Max HP", "Maks. PM": "Max SP", "Witalność": "Vitality", "Inteligencja": "Intelligence",
    "Siła": "Strength", "Zręczność": "Dexterity", "Szybkość ataku": "Attack Speed", "Szybkość ruchu": "Movement Speed",
    "Szybkość zaklęcia": "Cast Speed", "Regeneracja PŻ": "HP Regen", "Regeneracja PM": "SP Regen",
    "Szansa na otrucie": "Poison Chance", "Szansa na omdlenie": "Stun Chance", "Szansa na spowolnienie": "Slow Chance",
    "Szansa na cios krytyczny": "Critical Chance", "Szansa na przeszywający": "Penetration Chance",
    "Silny przeciw ludziom": "Strong vs Human", "Silny przeciw zwierzętom": "Strong vs Animal",
    "Silny przeciw orkom": "Strong vs Orc", "Silny przeciw mistykom": "Strong vs Mystic",
    "Silny przeciw nieumarłym": "Strong vs Undead", "Silny przeciw diabłom": "Strong vs Devil",
    "Kradzież PŻ": "HP Steal", "Kradzież PM": "SP Steal", "Szansa na kradzież PM": "SP Steal Chance",
    "Odzyskanie PM po obrażeniach": "SP Recovery on Hit", "Szansa na blok": "Block Chance",
    "Szansa na unik strzał": "Dodge Chance", "Odporność na miecze": "Sword Resist",
    "Odporność na broń dwuręczną": "Two-Handed Resist", "Odporność na sztylety": "Dagger Resist",
    "Odporność na dzwony": "Bell Resist", "Odporność na wachlarze": "Fan Resist",
    "Odporność na strzały": "Bow Resist", "Odporność na ogień": "Fire Resist",
    "Odporność na błyskawice": "Lightning Resist", "Odporność na magię": "Magic Resist",
    "Odporność na wiatr": "Wind Resist", "Odbicie obrażeń fizycznych": "Reflect Physical Damage",
    "Odbicie klątwy": "Reflect Curse", "Odporność na trucizny": "Poison Resist",
    "Odzyskanie PM po zabiciu": "SP Recovery on Kill", "Bonus doświadczenia": "Exp Bonus",
    "Bonus Yang": "Yang Bonus", "Bonus dropu przedmiotów": "Item Drop Bonus", "Bonus mikstur": "Potion Bonus",
    "Odzyskanie PŻ po zabiciu": "HP Recovery on Kill", "Odporność na omdlenie": "Stun Resist",
    "Odporność na spowolnienie": "Slow Resist", "Odporność na przewrócenie": "Knockback Resist",
    "Zasięg łuku": "Bow Range", "Wartość ataku": "Attack Value", "Wartość obrony": "Defense Value",
    "Wartość magicznego ataku": "Magic Attack Value", "Magiczna wartość obrony": "Magic Defense Value", "Magiczna Obrona": "Magic Defense",
    "Maks. wytrzymałość": "Max Stamina", "Silny przeciw wojownikom": "Strong vs Warrior",
    "Silny przeciw ninja": "Strong vs Ninja", "Silny przeciw surom": "Strong vs Sura",
    "Silny przeciw szamanom": "Strong vs Shaman", "Silny przeciw potworom": "Strong vs Monster",
    "Szansa na zdobycie przedmiotów": "Item Acquisition Chance", "Szansa na zdobycie Yang": "Yang Acquisition Chance",
    "Obrażenia umiejętności": "Skill Damage", "Średnie obrażenia": "Average Damage",
    "Odporność na obrażenia umiejętności": "Skill Damage Resist", "Odporność na średnie obrażenia": "Average Damage Resist",
    "Bonus doświadczenia (iCafe)": "Exp Bonus (iCafe)", "Bonus dropu przedmiotów (iCafe)": "Item Drop Bonus (iCafe)",
    "Odporność na wojowników": "Warrior Resist", "Odporność na ninja": "Ninja Resist",
    "Odporność na sury": "Sura Resist", "Odporność na szamanów": "Shaman Resist", "Energia": "Energy",
    "Bonus kostiumu": "Costume Bonus", "Magiczny atak": "Magic Attack", "Magiczny/fizyczny atak": "Magic/Physical Attack",
    "Odporność na lód": "Ice Resist", "Odporność na ziemię": "Earth Resist", "Odporność na mrok": "Dark Resist",
    "Odporność na cios krytyczny": "Critical Resist", "Odporność na przeszywający": "Penetration Resist",
    "Terror": "Terror", "Regeneracja wytrzymałości": "Stamina Regen",
    "Atak sztyletem przeciw potworom": "Dagger Attack vs Monster", "Wartość ataku przeciw potworom": "Attack Value vs Monster",
    "Odporność na potwory": "Monster Resist", "Pochłanianie obrażeń": "Damage Absorption",
    "Pochłanianie obrażeń od potworów": "Monster Damage Absorption", "Przełamanie odporności na ogłuszenie": "Stun Resist Piercing",
    "Przełamanie klątwy świątyni": "Temple Curse Piercing", "Czas trwania umiejętności": "Skill Duration",
    "Silny przeciw potworom z Doliny Orków": "Strong vs Orc Valley Monsters", "Silny przeciw Metinom": "Strong vs Metins",
    "Silny przeciw bossom": "Strong vs Bosses", "Magiczny atak przeciw potworom": "Magic Attack vs Monster",
    "Przełamanie odporności na miecz": "Sword Resist Piercing", "Przełamanie odporności na broń dwuręczną": "Two-Handed Resist Piercing",
    "Przełamanie odporności na sztylet": "Dagger Resist Piercing", "Przełamanie odporności na dzwonek": "Bell Resist Piercing",
    "Przełamanie odporności na wachlarz": "Fan Resist Piercing", "Przełamanie odporności na łuk": "Bow Resist Piercing",
    "Szansa na zbieranie": "Gathering Chance", "Szansa na naukę": "Learning Chance",
    "Odporność na ludzi": "Human Resist", "Szansa na podpalenie": "Ignite Chance",
    "Zamiana obrażeń na PE": "Damage to SP Conversion", "Szansa na rzadki łup": "Rare Drop Chance",
    "Magiczna wartość ataku przeciw potworom": "Magic Attack Value vs Monster", "Szansa na unieruchomienie": "Immobilize Chance",
    "Atak specjalny": "Special Attack", "Kara za śmierć": "Death Penalty",
}
EXACT.update(_ITEM_STAT_LABELS)

# --- system.html ---
EXACT.update({
    "TELEMETRIA VPS": "VPS TELEMETRY",
    "CPU, pamięć i dysk": "CPU, memory & disk",
    "CPU teraz": "CPU now",
    "RAM teraz": "RAM now",
    "Dysk teraz": "Disk now",
})

# --- manage.html: the big "Game & server" management page ---
EXACT.update({
    "Sekcja zarządzania": "Management section",
    "⚔ Gra i serwer": "⚔ Game & server",
    "⚙ Panel webowy": "⚙ Web panel",
    "ADMINISTRACJA GRY": "GAME ADMINISTRATION",
    "Zarządzanie grą i serwerem": "Game & server management",
    "Playerbots, zachowanie świata, raty i operacje serwera w jednym miejscu.":
        "Playerbots, world behaviour, rates and server operations in one place.",
    "⚠ Integracja gry nie zgłasza gotowości": "⚠ Game integration isn't reporting ready",
    "Pliki z katalogu": "Files from the",
    "integration/": "integration/",
    "muszą zostać zainstalowane w kontenerze gry i wymagają przebudowania tylko usługi":
        "directory must be installed in the game container and only require rebuilding the",
    "game": "game",
    "Usuń zaległe zlecenie": "Clear pending order",
    "⚡ Ustawienia wymagające restartu": "⚡ Settings requiring a restart",
    "Mnożniki serwera": "Server multipliers",
    "Presety mnożników": "Multiplier presets",
    "Jedno kliknięcie wypełnia trzy pola — zapisz je przyciskiem poniżej.":
        "One click fills in all three fields — save them with the button below.",
    "🔒 Ta instalacja nie ma zadeklarowanej obsługi zmiany liczby botów.":
        "🔒 This installation hasn't declared support for changing the bot count.",
    "Wymaga akcji": "Needs action",
    "Liczba botów": "Bot count",
    "Ile postaci Playerbots serwer próbuje utrzymać przy życiu. Rejestr botów ogranicza to do tego, co faktycznie zasiane — wpisanie liczby większej niż zasiana pula nic ponad to nie doda. Zmiana restartuje rdzenie osobno od rat/respawnu, więc może to być drugi, krótki restart chwilę po pierwszym.":
        "How many Playerbots characters the server tries to keep alive. The bot registry caps this at what's actually been seeded — entering a number higher than the seeded pool won't add anything beyond that. The change restarts the cores separately from rates/respawn, so this may be a second, short restart shortly after the first.",
    "Docelowa liczba botów": "Target bot count",
    "botów": "bots",
    "↻ Zastosowanie zmian i restart": "↻ Applying changes & restart",
    "Zastosuj zmiany i zleć restart": "Apply changes and order a restart",
    "Zleć restart": "Order a restart",
    "„Zleć restart” uruchamia serwer ponownie z zapisanymi ustawieniami, pomijając zmiany w powyższych polach.":
        "\"Order a restart\" restarts the server with the saved settings, ignoring changes in the fields above.",
    "Postęp restartu": "Restart progress",
    "Ostatni ukończony restart:": "Last completed restart:",
    "brak zarejestrowanych danych": "no data recorded",
    "🔒 Plan wejścia wymaga hostowego watchera.": "🔒 The entry plan requires the host watcher.",
    "PLAYERBOTS · WEJŚCIE DO ŚWIATA": "PLAYERBOTS · WORLD ENTRY",
    "🌅 Plan wejścia botów": "🌅 Bot entry plan",
    "Kohorta wejdzie równomiernie po starcie. Późni boty są dodatkowe względem kohorty i dołączają pojedynczo w wybranym okresie.":
        "The cohort enters evenly after startup. Late bots are additional to the cohort and join one by one over the chosen period.",
    "Okno wejścia": "Entry window",
    "min · 1–180": "min · 1–180",
    "Dodatkowi boty": "Extra bots",
    "Okres późnego wejścia": "Late entry period",
    "h · 1–168": "h · 1–168",
    "Zapisz plan wejścia": "Save entry plan",
    "Stan:": "Status:",
    "🔒 Aktualizator wymaga usługi hostowej.": "🔒 The updater requires the host service.",
    "PLAYERBOTS · AKTUALIZACJE": "PLAYERBOTS · UPDATES",
    "⬆ Aktualizator Seban": "⬆ Seban Updater",
    "Bezpiecznie instaluje najnowszą paczkę MT2009 Playerbots od Tieru. Przed aktualizacją tworzy kopię świata, zachowuje wolumeny z postaciami i bazą oraz stosuje wybrane override’y Seban.":
        "Safely installs the latest MT2009 Playerbots package from Tieru. Before updating it backs up the world, preserves the character and database volumes, and applies the chosen Seban overrides.",
    "Instalacja i działanie aktualizatora": "Installation & how the updater works",
    "Aktualizator jest aktywny jako usługa": "The updater is active as the",
    "seban-updater": "seban-updater",
    ". Włącz ochronę hasłem panelu, zaloguj się ponownie i użyj przycisku poniżej.":
        "service. Enable panel password protection, log in again, and use the button below.",
    "Przed aktualizacją tworzona jest kopia baz świata. Następnie instalowana jest paczka MT2009 Tieru i stosowane są poniższe reguły override.":
        "A backup of the world databases is taken before updating. Then Tieru's MT2009 package is installed and the override rules below are applied.",
    "Aktualizator nie jest jeszcze zainstalowany na tym VPS-ie. W katalogu paczki panelu uruchom:":
        "The updater isn't installed on this VPS yet. In the panel package directory, run:",
    "Przykład:": "Example:",
    "Instalator sprawdzi katalog MT2009, odnajdzie wolumen": "The installer checks the MT2009 directory, finds the",
    "update-spool": "update-spool",
    ", zainstaluje usługę systemową i nie otrzyma żadnych poleceń z przeglądarki poza stałym zleceniem aktualizacji.":
        "volume, installs the system service, and never receives any command from the browser beyond the fixed update order.",
    "🛡️ Reguły po aktualizacji": "🛡️ Rules after an update",
    "Ustawienia są stosowane automatycznie przy każdej kolejnej aktualizacji Playerbots. Aktualizacja Seban Panel pozostaje domyślnie wyłączona.":
        "Settings are applied automatically on every subsequent Playerbots update. Updating Seban Panel itself stays off by default.",
    "🎁 Dawaj Skrzynię Ucznia nowym postaciom": "🎁 Give the Apprentice Chest to new characters",
    "🌙 Włącz Skrzynie Blasku Księżyca w dropie": "🌙 Enable Moonlight Treasure Chests in the drop table",
    "👤 Zachowaj postacie demonstracyjne Tieru": "👤 Keep Tieru's demo characters",
    "🔄 Aktualizuj także Seban Panel do wersji dołączonej przez Tieru": "🔄 Also update Seban Panel to the version bundled by Tieru",
    "zainstaluje tylko nowszą wersję; lokalne zmiany w plikach panelu zostaną nadpisane":
        "only installs a newer version; local changes to panel files will be overwritten",
    "Zapisz ustawienia aktualizatora": "Save updater settings",
    "Stan": "Status",
    "Postęp": "Progress",
    "Usługa": "Service",
    "Postęp aktualizacji": "Update progress",
    "Zaktualizuj Playerbots": "Update Playerbots",
    "Aby zlecać aktualizacje, włącz ochronę hasłem panelu w ustawieniach poniżej i zaloguj się ponownie.":
        "To order updates, enable panel password protection in the settings below and log in again.",
    "Ostatnie wpisy aktualizatora": "Latest updater entries",
    "Panel nie ma dostępu do socketu Dockera. Tylko osobny updater otrzymuje zlecenie o stałej, ograniczonej treści; nie przyjmuje komend, adresów ani ścieżek z przeglądarki.":
        "The panel has no access to the Docker socket. Only a separate updater receives a fixed, limited-content order; it doesn't accept commands, addresses or paths from the browser.",
    "🚪 Boty przy drzwiach": "🚪 Bots at the gate",
    "Świeży świat może trzymać boty przy drzwiach, żeby dało się poustawiać raty/zachowanie zanim ktokolwiek wejdzie. Rdzeń czyta to na tym samym 5-sekundowym zegarze co wagi AI — bez restartu, bez rozłączania.":
        "A fresh world can hold bots at the gate so rates/behaviour can be set up before anyone enters. The core reads this on the same 5-second clock as the AI weights — no restart, no disconnecting.",
    "🔒 boty trzymane": "🔒 bots held",
    "🔓 boty wpuszczone": "🔓 bots let in",
    "🚪 Wpuść boty do świata": "🚪 Let bots into the world",
    "🔒 Zatrzymaj boty przy drzwiach": "🔒 Hold bots at the gate",
    "🗼 Wieża Demonów teraz": "🗼 Demon Tower now",
    "💀 Rajd na Azraela teraz": "💀 Azrael raid now",
    "ŚWIAT · NA ŻYWO": "WORLD · LIVE",
    "⏳ Poziom trudności": "⏳ Difficulty level",
    "Steruje oczekiwaniem u Biologa i Stajennego oraz przerwami między księgami umiejętności. Zmiana działa od razu i zostaje po restarcie.":
        "Controls the wait at the Biologist and Stableman, and the gaps between skill books. The change applies immediately and survives a restart.",
    "Łatwy — bez czekania": "Easy — no waiting",
    "Średni — Biolog 8 h, koń 4–7 h, księgi 7 h": "Medium — Biologist 8h, horse 4–7h, books 7h",
    "Trudny — Biolog 24 h, koń 12–21 h, księgi 21 h": "Hard — Biologist 24h, horse 12–21h, books 21h",
    "Własny — godziny poniżej": "Custom — hours below",
    "Biolog — godziny": "Biologist — hours",
    "Stajenny — każde czekanie": "Stableman — each wait",
    "Księgi — gracze": "Books — players",
    "Księgi — boty": "Books — bots",
    "⏳ Zapisz poziom trudności": "⏳ Save difficulty level",
    "ŚWIAT · DOSTĘP": "WORLD · ACCESS",
    "🏹 Autołowy i kanały CH2–CH4": "🏹 Auto-hunts & CH2–CH4 channels",
    "Panel autołowów wymaga przedmiotu": "The auto-hunt panel requires an item",
    "Zapisz autołowy": "Save auto-hunts",
    "Uruchom CH2 przy następnym restarcie": "Enable CH2 on next restart",
    "Udział botów na CH2": "Bot share on CH2",
    "Świeże boty na CH3/CH4 (Playerbots 2.2.36+): nowa pula botów od 1. poziomu, bez sklepów, bez ruchu między kanałami.":
        "Fresh bots on CH3/CH4 (Playerbots 2.2.36+): a new pool of bots starting at level 1, no shops, no movement between channels.",
    "Świeże kanały": "Fresh channels",
    "Wyłączone": "Disabled",
    "Tylko CH3": "CH3 only",
    "CH3 i CH4": "CH3 and CH4",
    "Liczba świeżych botów": "Number of fresh bots",
    "Zapisz kanały": "Save channels",
    "PLAYERBOTS 2.2.21+ · NA ŻYWO": "PLAYERBOTS 2.2.21+ · LIVE",
    "💀 Rajdy na Azraela": "💀 Azrael raids",
    "Co około dwie godziny 4–8 botów jednego królestwa może przejść Diabelskie Katakumby. Bot musi mieć co najmniej 80 poziom, ukończone 9. piętro Wieży Demonów i Zasuszoną Głowę. Zmiana działa bez restartu.":
        "About every two hours, 4–8 bots from one kingdom may run the Devil's Catacombs. A bot needs at least level 80, a cleared 9th floor of the Demon Tower, and a Withered Head. The change applies without a restart.",
    "Włącz rajdy botów na Azraela": "Enable bot Azrael raids",
    "Zapisz ustawienie": "Save setting",
    "🧠 Zachowanie botów": "🧠 Bot behaviour",
    "100% oznacza domyślne zachowanie autora. Rdzeń stosuje zapis do 5 sekund — bez restartu i bez rozłączania graczy; część suwaków dociera do bota przy jego następnej decyzji (opis po najechaniu).":
        "100% means the author's default behaviour. The core applies a saved value within 5 seconds — no restart, no disconnecting players; some sliders reach a bot on its next decision (see the hover text).",
    "💬 Czynność nad głową bota": "💬 Activity above the bot's head",
    "pokaż": "show",
    "📖 Szybkie czytanie ksiąg": "📖 Fast book reading",
    "czyta od razu, gdy ma księgę (bez dobowej przerwy gry)": "reads immediately once it has a book (no daily in-game cooldown)",
    "🌙 Noc na serwerze": "🌙 Night on the server",
    "22:00–05:59 czasu serwera (flaga xmas_snow: noc i śnieg)": "22:00–05:59 server time (xmas_snow flag: night & snow)",
    "Boty grają jak żywi ludzie": "Bots play like real people",
    "eksperymentalne": "experimental",
    "sesje 3–6 h, odpoczynek 3–9 h": "3–6h sessions, 3–9h rest",
    "Godziny gry na dobę": "Hours of play per day",
    "domyślnie": "default",
    "0 = domyślne sesje": "0 = default sessions",
    "Działa przy włączonych sesjach. 0 zachowuje standardowe sesje 3–6 h i odpoczynek 3–9 h; 1–24 ustawia docelową liczbę godzin gry bota na dobę.": "Works while sessions are enabled. 0 keeps the standard 3–6h sessions and 3–9h rests; 1–24 sets the bot's target daily playtime.",
    "Wojny gildii botów": "Bot guild wars",
    "losowane wojny gildii tego samego królestwa": "randomised wars between guilds of the same kingdom",
    "🗼 Wieża Demonów gildii botów": "🗼 Bot guild Demon Tower",
    "losowe najazdy; przycisk \"teraz\" niżej wymusza od razu": "random raids; the \"now\" button below forces one immediately",
    "Boty kupują w ItemShopie": "Bots buy in the ItemShop",
    "wykorzystują Kupony SM według własnych zasad": "use SM coupons by their own rules",
    "🏪 Boty kupują także w M2": "🏪 Bots also buy in M2",
    "rozszerza zakupy poza pierwsze miasta": "extends purchases beyond the first towns",
    "🎭 System pérsona/nastrój (Iwakura)": "🎭 Persona/mood system (Iwakura)",
    "zastępuje wylosowaną osobowość tą, którą dyktuje sytuacja bota, i dodaje nastrój – widoczne na karcie bota":
        "replaces the randomly rolled personality with one the bot's situation dictates, and adds a mood — visible on the bot's card",
    "♻️ Boty złomiarze": "♻️ Bot scrap dealers",
    "% straganiarzy": "% of stall keepers",
    "🛋️ Odpoczynek w mieście": "🛋️ Resting in town",
    "% botów po sprawach w mieście; 0 = nikt nie odpoczywa (poniżej 18 lv nigdy, bez straganów nigdy); przy osobowościach tylko boty w słabym nastroju":
        "% of bots with business in town; 0 = nobody rests (never below level 18, never without stalls); with personalities enabled, only bots in a low mood",
    "⚔️ PvP między królestwami": "⚔️ PvP between kingdoms",
    "% botów wrogich wobec innych królestw; 0 = pokój; działa tylko przy układzie świata unified":
        "% of bots hostile towards other kingdoms; 0 = peace; only works with the unified world layout",
    "📜 Zwój Błogosławieństwa/Boga Smoka od": "📜 Blessing/Dragon God Scroll from",
    "najniższy + na jaki może spaść ulepszenie zwojem; 1 = brak dna (własne zasady rdzenia)":
        "the lowest + a scroll refine can drop to; 1 = no floor (the core's own rules)",
    "⚔️ Czas wojny gildii": "⚔️ Guild war duration",
    "minut": "minutes",
    "🕐 Odstęp między wojnami": "🕐 Interval between wars",
    "🚫 Wyłącz drop Szkatułek Blasku Księżyca": "🚫 Disable Moonlight Treasure Chest drops",
    "🎁 Szkatułki Blasku": "🎁 Moonlight Treasure Chests",
    "promile szansy, tylko w trakcie eventu szkatułek": "per-mille chance, only during the chest event",
    "z potwora": "from a monster",
    "z Metina": "from a Metin",
    "Najedź na suwak, żeby zobaczyć, co dokładnie zmienia i jak szybko. Kowal, Księgi, Biolog i Misje polowania kończą się na 100, bo przy 100 boty już robią to przy każdej okazji — suwak może je tylko zrobić rzadszymi. Stragany: Handlarz, bot bez yang na mikstury, pełny plecak, dropper pod presją plecaka i cenne zapasy otwierają zawsze — suwak rusza resztę; na r40250 stojące stragany sprawdzają się do 5 min po zmianie, na 2.x stojący sklep offline po prostu nie jest odnawiany po 8 h. Status bota mówi, dlaczego stoi. Szybkie KU i szkatułki pochodzą z aktualizacji Tieru. Szkatułki: domyślnie 10‰ z potwora oraz 300‰ z Metina. Złomiarze wystawiają ulepszenia +0–+3 za 2× cenę NPC.":
        "Hover over a slider to see exactly what it changes and how fast. Blacksmith, Books, Biologist and Hunting Missions cap at 100, because at 100 bots already do it at every opportunity — the slider can only make them rarer. Stalls: the Merchant, a bot with no yang for potions, a full bag, a dropper under bag pressure, and valuable stock always open up — the slider moves the rest; on r40250 standing stalls are checked up to 5 min after a change, on 2.x a standing offline shop simply isn't refreshed after 8h. The bot's status says why it's standing. Fast KU and chests come from Tieru's update. Chests: 10‰ from a monster and 300‰ from a Metin by default. Scrap dealers list +0–+3 refines at 2× the NPC price.",
    "Zapisz zachowanie na żywo": "Save live behaviour",
    "📦 Polityka przedmiotów": "📦 Item policy",
    "Jedna reguła na linię:": "One rule per line:",
    "albo": "or",
    "zawsze zatrzymaj,": "always keep,",
    "wystaw na stragan,": "list on a stall,",
    "sprzedaj handlarzowi,": "sell to the merchant,",
    "wyrzuć. Linie zaczynające się od": "drop. Lines starting with",
    "to komentarz. Rdzeń odczytuje plik na żywo, bez restartu.": "are a comment. The core reads the file live, no restart needed.",
    "Zapisz politykę przedmiotów": "Save item policy",
    "💎 Nadaj VIP wszystkim botom": "💎 Grant VIP to all bots",
    "Ta sama funkcja co \"Nadaj VIP\" na stronie postaci, tylko w jednym zapytaniu na wszystkie konta":
        "The same feature as \"Grant VIP\" on the character page, just in a single query across all",
    "playerbot_*": "playerbot_*",
    ". Jeśli bot ma już aktywny VIP, dni doliczają się do jego obecnego wygaśnięcia (nie licząc od dziś).":
        "accounts. If a bot already has active VIP, the days are added to its current expiry (not counted from today).",
    "Dni": "Days",
    "Nadaj VIP wszystkim botom": "Grant VIP to all bots",
    "🎁 Masowe nadawanie przedmiotów": "🎁 Bulk item granting",
    "Wybierz VNUM, ilość i warunki: poziom, koń, czas gry, jeździectwo oraz klasa. Podgląd odbiorców i historia wyników działają bez restartu gry.":
        "Choose a VNUM, quantity and conditions: level, horse, playtime, riding and class. Recipient preview and result history work without restarting the game.",
    "Otwórz narzędzie nadawania przedmiotów →": "Open the item granting tool →",
    "🔒 Sterowanie skrzynią wymaga zmodyfikowanego questa.": "🔒 Controlling the chest requires a modified quest.",
    "🎒 Skrzynia startowa dla nowych postaci": "🎒 Starter chest for new characters",
    "Jeden przełącznik dla całego świata, graczy i botów: łańcuch Skrzyń Ucznia (warrior/sura 50187, assassin 50212, szaman 50213 i kolejne skrzynie aż po Skrzynię Arcymistrza). Wyłączona: nowa postać gracza jej nie dostaje, nowe boty rodzą się bez niej, a boty tracą nieotwarte skrzynie z łańcucha — skrzyń graczy nic nie rusza. Działa od razu i zostaje po restarcie, dopóki nie zmienisz jej w launcherze (POZIOM TRUDNOŚCI,":
        "One switch for the whole world, players and bots: the Apprentice Chest chain (warrior/sura 50187, assassin 50212, shaman 50213, and further chests up to the Grandmaster Chest). Disabled: a new player character doesn't get it, new bots are born without it, and bots lose unopened chests from the chain — players' chests are left untouched. Applies immediately and survives a restart, until you change it in the launcher (DIFFICULTY LEVEL,",
    "M2_STARTER_CHEST": "M2_STARTER_CHEST",
    "w": "in",
    ".env": ".env",
    "Obejmuje każdą klasę jednakowo: warrior/sura (50187), assassin (50212) i szaman (50213). Działa od razu na kolejnym logowaniu nowej postaci gracza, bez restartu. Nowo zasiane boty nadal biorą ustawienie z":
        "Covers every class equally: warrior/sura (50187), assassin (50212) and shaman (50213). Applies immediately on a new player character's next login, no restart. Newly seeded bots still take the setting from",
    "M2_PLAYERBOT_DISABLE_STUDENT_CHEST": "M2_PLAYERBOT_DISABLE_STUDENT_CHEST",
    "przy starcie": "at the start of",
    "playerbot-migrate": "playerbot-migrate",
    "— jeśli ten wybór ma przetrwać kolejny restart/wdrożenie, ustaw tam to samo.":
        "— if this choice should survive the next restart/deploy, set the same value there.",
    "wyłącz": "disable",
    "Zapisz": "Save",
    "RANKINGI": "RANKINGS",
    "🏆 Prawdziwi gracze w rankingach": "🏆 Real players in rankings",
    "Rankingi, karuzela na dashboardzie i sezon — tu i w panelu klasycznym — liczą boty i postacie graczy, Twoją też, jeśli grasz razem z botami; 👤 oznacza gracza. Postaci GM-ów (z rangą w common.gmlist, np. Admin, AdminNinja, AdminSura i AdminSzaman z konta admin) nie są liczone nigdy. Odznacz, żeby rankingi w obu panelach liczyły znowu tylko boty. Działa od razu, bez restartu.":
        "Rankings, the dashboard carousel and the season — here and in the classic panel — count both bots and player characters, yours too if you play alongside the bots; 👤 marks a player. GM characters (ranked in common.gmlist, e.g. Admin, AdminNinja, AdminSura and AdminSzaman from the admin account) are never counted. Uncheck to make rankings in both panels count only bots again. Applies immediately, no restart.",
    "🏆 Uwzględniaj prawdziwych graczy w rankingach": "🏆 Include real players in rankings",
    "uwzględniaj": "include",
    "🔒 Ogłoszenia +9 wymagają komendy NOTICE w queście.": "🔒 +9 announcements require the NOTICE command in the quest.",
    "📢 Ogłoszenia ulepszeń +9": "📢 +9 refine announcements",
    "Kiedy gracz (nie bot) pomyślnie ulepszy coś na +9, wyśle się wiadomość na złoto do wszystkich na serwerze — tak samo jak przy komendzie GM":
        "When a player (not a bot) successfully refines something to +9, a gold message is sent to everyone on the server — the same as with the GM command",
    "/b": "/b",
    ". Sprawdzane co kilka sekund/minut przez kolektor, więc ogłoszenie może spóźnić się o chwilę względem samego ulepszenia.":
        "Checked every few seconds/minutes by the collector, so the announcement may lag a moment behind the refine itself.",
    "📢 Ogłaszaj ulepszenia graczy na +9": "📢 Announce player +9 refines",
    "ogłaszaj": "announce",
    "🤖 Boty na mapach": "🤖 Bots on maps",
    "Aktywne boty": "Active bots",
})

# --- manage_panel.html: rest (appearance form basics already in main EXACT) ---
EXACT.update({
    "ADMINISTRACJA PANELU": "PANEL ADMINISTRATION",
    "Ustawienia panelu": "Panel settings",
    "Wygląd, monitoring i dostęp do Seban Control Center.": "Appearance, monitoring and access to Seban Control Center.",
    "RANKINGI · WYGLĄD": "RANKINGS · APPEARANCE",
    "🔥 Gradientowa odznaka poziomu": "🔥 Gradient level badge",
    "Wyróżnia poziom postaci zajmujących wybrane miejsca w światowym rankingu. Ustawienie obejmuje wszystkie widoki panelu i działa od razu, bez restartu.":
        "Highlights the level of characters holding selected spots in the world ranking. The setting applies across every panel view and works immediately, no restart.",
    "Pokazuj gradientową odznakę poziomu": "Show the gradient level badge",
    "włączona": "enabled",
    "Lokaty otrzymujące odznakę": "Places receiving the badge",
    "Podgląd": "Preview",
    "Lv 42": "Lv 42",
    "Zapisz odznaki": "Save badges",
    "GRACZE · WYGLĄD": "PLAYERS · APPEARANCE",
    "Odznaka pełnego ekwipunku +9": "Full +9 equipment badge",
    "Pokazuje złoty młotek przy nicku postaci ubranej w pełny zestaw +9: broń, zbroję, hełm, buty, bransoletę, naszyjnik, kolczyki i tarczę.":
        "Shows a golden hammer next to the nickname of a character wearing a full +9 set: weapon, armor, helmet, boots, bracelet, necklace, earrings and shield.",
    "Pokazuj odznakę pełnego ekwipunku +9": "Show the full +9 equipment badge",
    "Pełny ekwipunek +9": "Full +9 equipment",
    "Zapisz odznakę +9": "Save +9 badge",
    "🔎 Wyjaśnienia decyzji sklepów botów": "🔎 Bot shop decision explanations",
    "Pokazuje w tooltipie przedmiotu na straganie bota, dlaczego trafił na ladę i jak krok po kroku silnik wyliczył jego cenę (Playerbots 2.2.39+). Dotyczy tylko przedmiotów dotkniętych przez bota po aktualizacji — silnik nie ma tych danych wstecznie.":
        "Shows in a bot's stall item tooltip why it landed on the counter and how the engine worked out its price step by step (Playerbots 2.2.39+). Only covers items the bot has touched since the update — the engine has no data for older listings.",
    "Pokazuj wyjaśnienia decyzji w tooltipach sklepów": "Show decision explanations in shop tooltips",
    "Ustawienie wyjaśnień decyzji sklepów botów zostało zapisane — działa od razu.": "The bot shop decision explanations setting has been saved — it takes effect immediately.",
    "WIADOMOŚCI · WYDARZENIA": "MESSAGES · EVENTS",
    "✦ Legendarne ogłoszenia botów": "✦ Legendary bot announcements",
    "Wybierz niezależnie, gdzie panel pokazuje złote komunikaty o pokonanych bossach, ukończonych rajdach i lochach. Możesz zaznaczyć jedno miejsce, wszystkie albo nie zaznaczać żadnego.":
        "Choose independently where the panel shows gold messages about defeated bosses, completed raids and dungeons. You can select one place, all of them, or none.",
    "/live-chat": "/live-chat",
    "Wieści ze świata": "World news",
    "/world-feed": "/world-feed",
    "Pasek wiadomości na dole": "Message bar at the bottom",
    "cały panel": "whole panel",
    "Zapisz miejsca ogłoszeń": "Save announcement locations",
    "✦ Ścieżka magii w kolumnie klasy": "✦ Skill path in the class column",
    "Pokazuje w rankingach konkretną ścieżkę umiejętności zamiast samej klasy: Wojownik Ciało/Umysł, Ninja Ostrze/Łuk, Sura Broń/Czarna Magia, Szaman Smok/Leczenie. Postacie, które jeszcze nie wybrały ścieżki, nadal pokazują samą klasę.":
        "Shows the specific skill path in rankings instead of just the class: Warrior Body/Mind, Ninja Blade/Bow, Sura Weapon/Dark Magic, Shaman Dragon/Healing. Characters who haven't picked a path yet still show just the class.",
    "Pokazuj ścieżkę magii zamiast samej klasy": "Show the skill path instead of just the class",
    "/rankings": "/rankings",
    "WIADOMOŚCI · SKRZYNIE": "MESSAGES · CHESTS",
    "💀 Szkatułki Umarłego Rozpruwacza": "💀 Reaper's Chests",
    "Włącz lub ukryj w Wieściach ze świata informacje o otwarciu skrzyni i zdobytej nagrodzie. Licznik w podsumowaniu dnia pozostaje dostępny.":
        "Enable or hide chest-opening and reward information in World News. The counter in the daily summary stays available either way.",
    "Pokazuj otwarcia skrzyń": "Show chest openings",
    "Zapisz ustawienie skrzyń": "Save chest setting",
    "PLAYERBOTS 2.2.29 · ZGODNOŚĆ": "PLAYERBOTS 2.2.29 · COMPATIBILITY",
    "🧩 Funkcje wymagające integracji": "🧩 Features requiring integration",
    "Czysta instalacja Playerbots nie zawiera wszystkich helperów i modyfikacji używanych na serwerze Sebana. Wyłączona funkcja pozostaje widoczna w panelu, ale jest szara i nie przyjmie zlecenia. Włącz ją dopiero po wdrożeniu wymagania z instrukcji.":
        "A clean Playerbots install doesn't include all the helpers and mods used on Seban's server. A disabled feature stays visible in the panel, but greyed out and won't accept an order. Only enable it once you've deployed the requirement from the instructions.",
    "Wymaganie:": "Requirement:",
    "Instrukcja wdrożenia": "Deployment instructions",
    "Udostępnij funkcję w panelu": "Make the feature available in the panel",
    "Zapisz dostępność funkcji": "Save feature availability",
    "Funkcje natywne w Playerbots 2.2.29 — raty, globalne tempo i liczebność respawnu, zachowanie AI, ItemShop, rajdy, polityka przedmiotów, kolejka przedmiotów i monitoring — pozostają dostępne bez dodatkowych przełączników.":
        "Features native to Playerbots 2.2.29 — rates, global respawn pace and population, AI behaviour, ItemShop, raids, item policy, the item queue and monitoring — stay available without extra switches.",
})

# --- player.html: the big character profile page ---
EXACT.update({
    "← Powrót do graczy": "← Back to players",
    "PODGLĄD POSTACI": "CHARACTER OVERVIEW",
    "GM": "GM",
    "🏪 Zobacz sklepik": "🏪 View shop",
    "⚡ Teleportuj moją postać w grze (1 klik)": "⚡ Teleport my in-game character (1 click)",
    "Stan postaci": "Character status",
    "❤ PŻ": "❤ HP",
    "✦ PM": "✦ SP",
    "⚡ EXP": "⚡ EXP",
    "Pozycja": "Position",
    "Ranga": "Rank",
    "Persona": "Persona",
    "Nastrój": "Mood",
    "Ambicja": "Ambition",
    "Aktualny cel": "Current goal",
    "Akcja": "Action",
    "📋 Kartoteka misji": "📋 Quest file",
    "📊 Statystyki": "📊 Stats",
    "STR": "STR",
    "VIT": "VIT",
    "DEX": "DEX",
    "INT": "INT",
    "✨ Umiejętności": "✨ Skills",
    "Postać nie wybrała jeszcze profesji.": "The character hasn't chosen a profession yet.",
    "Premium": "Premium",
    "Wygasł": "Expired",
    "Czas sklepu wygasł — oferta nie jest już aktywna.": "The shop's time has expired — the listing is no longer active.",
    "⚡ Teleportuj moją postać do sklepu": "⚡ Teleport my character to the shop",
    "Zawartość sklepu offline": "Offline shop contents",
    "Stragan jest otwarty, ale nic nie ma wystawione.": "The stall is open, but nothing is listed.",
    "📜 Historia ekwipunku": "📜 Equipment history",
    "Filtr historii ekwipunku": "Equipment history filter",
    "Handel": "Trade",
    "Bonusy": "Bonuses",
    "Ulepszanie": "Refining",
    "Inne": "Other",
    "Wszystko": "Everything",
    "Brak zapisanych zdarzeń ekwipunku.": "No equipment events recorded.",
    "📟 Dziennik zdarzeń bota (logi na żywo)": "📟 Bot event log (live logs)",
    "Linie z logu rdzenia gry wspominające tę postać — zbierane od otwarcia tej strony, nie znikają między odświeżeniami.":
        "Lines from the game core log mentioning this character — collected since this page was opened, they don't disappear between refreshes.",
    "⏸ Zatrzymaj śledzenie": "⏸ Stop tracking",
    "📋 Kopiuj logi": "📋 Copy logs",
    "Wczytywanie logów…": "Loading logs…",
    "🏆 Statystyki postaci (panel Y)": "🏆 Character stats (Y panel)",
    "Zabite potwory (ogółem)": "Monsters killed (total)",
    "Pokonane bossy": "Bosses defeated",
    "Pokonane minibossy": "Minibosses defeated",
    "Zniszczone kamienie Metin": "Metin stones destroyed",
    "Pokonani gracze (przeciwne królestwo)": "Players defeated (enemy kingdom)",
    "Wygrane pojedynki": "Duels won",
    "Wykopane rudy": "Ore mined",
    "Złowione ryby": "Fish caught",
    "Śmierci (łącznie)": "Deaths (total)",
    "Śmierci od potworów": "Deaths from monsters",
    "Śmierci od graczy": "Deaths from players",
    "Największe obrażenia (zwykłe)": "Highest damage (normal)",
    "Największe obrażenia (konno)": "Highest damage (mounted)",
    "Największe obrażenia (umiejętność)": "Highest damage (skill)",
    "Pomyślne ulepszenia": "Successful refines",
    "Spalone przedmioty u Kowala": "Items burned at the Blacksmith",
    "Zdobyty Yang (łącznie)": "Yang earned (total)",
    "Yang ze sprzedaży u NPC": "Yang from NPC sales",
    "Źródło: tabela silnika": "Source: engine table",
    "player_special_flag": "player_special_flag",
    "(system PLAYER_STATS_*), zapisywana po stronie serwera przy każdej zmianie — dokładnie ten sam licznik, który wypełnia okno \"Statystyki\" pod klawiszem Y w grze. Cztery pola z panelu Y — ukończone lochy, zebrane kwiaty, otwarte skrzynie, ukończone księgi misji — są zdefiniowane w silniku, ale nigdy nie są zwiększane przez żaden kod gry na tej wersji serwera, więc nie mają tu żadnej wartości do pokazania.":
        "(the PLAYER_STATS_* system), saved server-side on every change — exactly the same counter that fills the \"Stats\" window under the Y key in-game. Four fields from the Y panel — dungeons cleared, flowers collected, chests opened, quest books completed — are defined in the engine but never incremented by any game code on this server version, so there's no value to show for them here.",
    "⚙ Akcje administracyjne": "⚙ Administrative actions",
    "🎁 Daj przedmiot": "🎁 Give item",
    "Kategoria": "Category",
    "Bronie": "Weapons",
    "Zbroje": "Armor",
    "Mikstury / użytkowe": "Potions / usable",
    "Smocze Kamienie": "Dragon Stones",
    "Kamienie Metin": "Metin Stones",
    "Specjalne": "Special",
    "Nazwa albo VNUM": "Name or VNUM",
    "Wyszukaj przedmiot…": "Search item…",
    "Ilość": "Quantity",
    "🎁 Wyślij przedmiot": "🎁 Send item",
    "💰 Daj Yang": "💰 Give Yang",
    "1 Million": "1 Million",
    "10 Million": "10 Million",
    "100 Million": "100 Million",
    "1 Billion": "1 Billion",
    "Kwota": "Amount",
    "💰 Wyślij Yang": "💰 Send Yang",
    "⭐ Ustaw poziom": "⭐ Set level",
    "⭐ Zmień poziom": "⭐ Change level",
    "🗺️ Teleportuj": "🗺️ Teleport",
    "Miejsce": "Location",
    "Działa, gdy postać jest w grze.": "Works while the character is in-game.",
    "🏃 Szybkość biegu": "🏃 Run speed",
    "Premia na 1 godzinę": "Bonus for 1 hour",
    "Normalna": "Normal",
    "🏃 Ustaw szybkość": "🏃 Set speed",
    "Nadaj VIP": "Grant VIP",
    "Nadaj Smocze Monety": "Grant Dragon Coins",
    "Ilość (account.cash)": "Amount (account.cash)",
    "Dodaj monety": "Add coins",
    "Zmień nick": "Change nickname",
    "Nowy nick": "New nickname",
    "Jeśli to żywy bot, silnik nie powinien cofnąć zmiany przy zapisie — ale w razie czego krótko zrestartuj kanał gry.":
        "If this is a live bot, the engine shouldn't revert the change on save — but if it does, briefly restart the game channel.",
    "Resetuj pozycję": "Reset position",
    "Przenosi do stolicy własnego królestwa (jak żywy bot — może zostać nadpisane przy zapisie z pamięci).":
        "Moves to the capital of its own kingdom (like a live bot — may get overwritten by a save from memory).",
    "Ranga GM": "GM rank",
    "Silnik czyta listę GM-ów z common.gmlist przy starcie i przy /reload a (wymaga zalogowanego Właściciela) — bez tego zmiana zadziała od następnego logowania tej postaci.":
        "The engine reads the GM list from common.gmlist at startup and on /reload a (requires a logged-in Owner) — without that, the change takes effect on this character's next login.",
    "Zapisz rangę": "Save rank",
    "⚠ Usuń postać (nieodwracalne)": "⚠ Delete character (irreversible)",
    "Wpisz dokładną nazwę postaci, żeby potwierdzić:": "Type the character's exact name to confirm:",
    ". Kopia wiersza trafi do web_seban_deleted_players przed usunięciem.": ". A copy of the row is saved to web_seban_deleted_players before deletion.",
    "Usuń postać": "Delete character",
    "Bardzo dobry": "Very good",
    "Polowanie na Metiny": "Hunting Metins",
    "Ząb Orka": "Orc Tooth",
    "Zarażony Pies": "Plagued Dog",  # mob_proto 902, the game's English name
    "⚔ Zawartość ekwipunku": "⚔ Equipment contents",
    "Ekwipunek": "Equipment",
    "Ta postać nie ma odblokowanych juków konnych": "This character hasn't unlocked saddlebags",
    "Juki konne": "Saddlebags",
})

# ---------------------------------------------------------------------------
# PATTERNS_RAW: (regex_source, replacement) pairs for text assembled with
# live data. Every entry is tried (translate_string cascades, it doesn't
# stop at the first hit) -- composed strings like "42 szt. · 12 pokonanych"
# are covered by several smaller patterns each translating their own
# fragment, rather than needing one full-sentence regex per shape.
# ---------------------------------------------------------------------------
PATTERNS_RAW = [
    (r'^Lv (\d+)$', 'Lv $1'),
    (r'^(\d+)% doświadczenia$', '$1% experience'),

    # --- item_base_stats() (app.py): the client-side base stat lines
    # shown above the socket bonuses in every item tooltip ---
    (r'^Wymagany poziom: (\d+)$', 'Required level: $1'),
    (r'^Wartość ataku: (\d+)–(\d+)$', 'Attack Value: $1–$2'),
    (r'^Wartość ataku: (\d+)$', 'Attack Value: $1'),
    (r'^Wartość magicznego ataku: (\d+)–(\d+)$', 'Magic Attack Value: $1–$2'),
    (r'^Wartość magicznego ataku: (\d+)$', 'Magic Attack Value: $1'),
    (r'^Wartość obrony: (\d+)$', 'Defense Value: $1'),

    # --- player.html character header ("Mężczyzna · portret z klienta gry") ---
    (r'^Mężczyzna · ', 'Male · '),
    (r'^Kobieta · ', 'Female · '),
    (r'portret z klienta gry$', 'portrait from the game client'),

    # --- _macros.html: item tooltip (used everywhere an item is shown) ---
    (r'^Ilość: (\d+)$', 'Quantity: $1'),
    (r'^Przemienia w: (.+)$', 'Transforms into: $1'),
    (r'^Pozostały czas: (.+)$', 'Remaining time: $1'),
    (r'^Jakość: Matowy$', 'Quality: Matt'),
    (r'^Jakość: Przejrzysty$', 'Quality: Clear'),
    (r'^Jakość: Bez skazy$', 'Quality: Flawless'),
    (r'^Jakość: Znakomity$', 'Quality: Brilliant'),
    (r'^Jakość: Wyborny$', 'Quality: Excellent'),
    (r'^Jakość: (.+)$', 'Quality: $1'),
    (r'^Poziom: \+(\d+)$', 'Level: +$1'),
    (r'^Matowy$', 'Matt'),
    (r'^Przejrzysty$', 'Clear'),
    (r'^Bez skazy$', 'Flawless'),
    (r'^Znakomity$', 'Brilliant'),
    (r'^Wyborny$', 'Excellent'),
    (r'^Puste kieszenie: (\d+)$', 'Empty slots: $1'),
    (r'^Cena: ([\d\s]+) Yang za (\d+) szt\.$', 'Price: $1 Yang for $2 pcs.'),
    (r'^Cena: ([\d\s]+) Yang$', 'Price: $1 Yang'),

    # --- account_detail.html ---
    (r'^💎 ([\d\s]+) Smoczych Monet$', '💎 $1 Dragon Coins'),
    (r'^🗓 Utworzono: (.+)$', '🗓 Created: $1'),
    (r'^🕐 Ostatnia gra: (.+)$', '🕐 Last played: $1'),
    (r'^Postacie \((\d+)/4\)$', 'Characters ($1/4)'),

    # --- bot_names.html ---
    (r'^Obecnie 0 botów bez nicku — wszystkie już mają swój na stałe\. Przycisk zadziała dopiero po tym, jak przybędzie nowych, jeszcze nienazwanych botów \(pełny wipe/reseed z większą pulą\)\.$',
     'Currently 0 bots without a nickname — they all already have theirs for good. The button only does something once new, still-unnamed bots arrive (a full wipe/reseed with a bigger pool).'),
    (r'^Jest (\d+) bot\(ów\) bez żadnego nicku — kliknięcie nada im nazwy według aktualnych priorytetów/blokad poniżej\.$',
     'There are $1 bot(s) with no nickname yet — clicking assigns them names using the current priorities/blocks below.'),
    (r'^Nadaj nicki oczekującym botom \((\d+)\)$', 'Assign names to waiting bots ($1)'),
    (r'^\(teraz: (.+)\)$', '(now: $1)'),

    # --- bot_personalities.html ---
    (r'^(\d+) bota z tą osobowością · pokazano do 200$', '$1 bot with this personality · showing up to 200'),
    (r'^(\d+) botów z tą osobowością · pokazano do 200$', '$1 bots with this personality · showing up to 200'),
    (r'^(\d+) bota · pokazano do 200$', '$1 bot · showing up to 200'),
    (r'^(\d+) botów · pokazano do 200$', '$1 bots · showing up to 200'),

    # --- changelog.html ---
    (r'^— najnowsze (\d+) wydań silnika\. Pobierane raz na godzinę\.$', '— the latest $1 engine releases. Fetched once an hour.'),
    (r'^Nie udało się pobrać changelogu Tieru: (.+)$', "Failed to fetch Tieru's changelog: $1"),

    # --- daily_summary.html ---
    (r'^DZIEŃ (\d+) · (.+)$', 'DAY $1 · $2'),

    # --- dashboard.html ---
    (r'Dostępna ([\d.]+)$', '$1 available'),
    (r'^Zaktualizowano (.+)$', 'Updated $1'),

    # --- economy.html / economy_shops.html: collector-read banner ---
    (r'^kolektor jeszcze nie wykonał odczytu$', "the collector hasn't read yet"),
    (r'^Ostatni pełny odczyt kolektora \(co 5 minut\): (.+)\. Kliknij przedmiot, aby zobaczyć historię\.$',
     'Last full collector read (every 5 minutes): $1. Click an item to see its history.'),
    (r'^Ostatni odczyt kolektora \(co 5 minut\): (.+)\. Stragany graczy i botów \(IkarusShop\) — stan i wartość rynku per królestwo\.$',
     'Last collector read (every 5 minutes): $1. Player and bot stalls (IkarusShop) — stock and market value per kingdom.'),
    (r'^ostatnie 24h: (\d+)$', 'last 24h: $1'),
    (r'^ostatnio (.+)$', 'last seen $1'),

    # --- events.html ---
    (r'^Trwa na 1 mapie$', 'Running on 1 map'),
    (r'^Trwa na (\d+) mapach$', 'Running on $1 maps'),
    (r'^(\d+) na mapie$', '$1 on the map'),
    (r'(\d+) pokonanych\b', '$1 defeated'),
    (r'(\d+) botów\b', '$1 bots'),
    (r'· spadają Metiny', '· Metins dropping'),
    (r'· bossowie', '· bosses'),
    (r'^Trwa · ', 'Running · '),
    (r'^Trwa$', 'Running'),
    (r'\bjednostek\b', 'units'),
    (r'^Zaplanowany', 'Scheduled'),
    (r'^następny: (.+)$', 'next: $1'),
    (r'^(\d+) min$', '$1 min'),
    (r'^Aktywny do (.+)$', 'Active until $1'),
    (r'^końca odliczania$', 'end of the countdown'),
    (r'^(\d+) szt\.$', '$1 pcs.'),
    # A running Tanaka's or Zuo's line ("Wybiera event: Dolina Orków · 8 szt.
    # · do 20:30 · 6 na mapie · ...") and a finished one's name in the
    # history and in its notification ("Pirat Tanaka · Pyongmoo"): the
    # event's name and its map are separate pieces of the text, translated by
    # the event and map patterns at the bottom.
    (r'^Event zakończony: ', 'Event ended: '),
    (r'^Edytuj: ', 'Edit: '),
    (r'Wybiera event(?=$|:)', "Event's choice"),
    (r' · (\d+) szt\.', ' · $1 pcs.'),
    (r'(^|· )do (\d{2}\.\d{2} )?(\d{1,2}:\d{2})(?= ·|$)', '$1until $2$3'),
    (r' · (\d+) na mapie', ' · $1 on the map'),
    (r'^(\d+) szkatułek$', '$1 chests'),
    (r'^Wydropiono (\d+) szkatułek\.$', '$1 chests dropped.'),
    (r'^Gracze wydropili o ([\d\s]+) więcej yang\.$', 'Players looted $1 more yang.'),

    # --- guild.html / guilds.html ---
    (r'^· poziom (\d+)$', '· level $1'),
    (r'^usunięta postać #(\d+)$', 'deleted character #$1'),
    (r'^Lider$', 'Leader'),
    (r'^Generał$', 'General'),
    (r'^Członek$', 'Member'),
    (r'^Dane z rdzeni Playerbots · raport co minutę', 'Data from the Playerbots cores · reported every minute'),
    (r' · ostatni zapis: (.+)$', ' · last save: $1'),

    # --- item_grants.html ---
    (r'^(.+) · VNUM (\d+)$', '$1 · VNUM $2'),
    # criteria_text()'s own output lands in this capture group already
    # rendered, so it isn't retranslated by this pattern alone -- the
    # "no filter" case (by far the most common) is called out explicitly;
    # an active Lv/Koń/class filter stays partly Polish, a known gap.
    (r'odbiorców · (\d+)× na postać · Bez warunków$', 'recipients · $1× per character · No conditions'),
    (r'odbiorców · (\d+)× na postać · (.+)$', 'recipients · $1× per character · $2'),
    (r'^Nadaj (\d+)× każdemu odbiorcy$', 'Grant $1× to each recipient'),
    (r'^Podgląd odbiorców \((\d+)\)$', 'Recipient preview ($1)'),
    (r'^✅ Worker nadawania działa \(ostatni tick (\d+) s temu\)\.$', '✅ The granting worker is running (last tick $1s ago).'),
    (r'^⚠️ Worker nadawania milczy od (\d+) s\. Kontener$', "⚠️ The granting worker has been silent for $1s. Container"),
    (r'^⚠️ W kolejce gry leży zlecenie sprzed (\d+) s, którego nikt w grze nie odebrał\. Pomocnik w grze \(quest$',
     "⚠️ An order from $1s ago is sitting in the in-game queue, unclaimed by anyone. The in-game helper (quest"),
    (r'^\(najstarsze (\d+) s\) ·\nPrzekazano do gry:$', '(oldest $1s) ·\nDelivered in-game:'),
    (r'^\(najstarsze (\d+) s\) ·\nW kolejce gry:$', '(oldest $1s) ·\nIn the in-game queue:'),

    # --- items.html ---
    (r'^(\d+) przedmiotów w wybranej kategorii · pełna lista bez stron$', '$1 items in the selected category · full list, no pages'),
    # The count line /api/items writes in its place while the search types.
    (r'^(\d+) przedmiotów w wybranej kategorii', '$1 items in the selected category'),
    (r'^(\d+) przedmiotów pasuje do wyszukiwania', '$1 items match the search'),
    (r'^(\d+) przedmiotów · pełna lista bez stron', '$1 items · full list, no pages'),
    (r' \(pokazano pierwsze 500 — zawęź wyszukiwanie\)$', ' (showing the first 500 — narrow the search)'),
    (r'^VNUM (\d+) · typ (\d+)/(\d+)$', 'VNUM $1 · type $2/$3'),
    (r'^VNUM (\d+) · typ (\d+)$', 'VNUM $1 · type $2'),
    (r'^Cena: ([\d\s]+) Yang$', 'Price: $1 Yang'),

    # --- manage.html: restart_progress() stage labels ("100% · X") ---
    (r'· Serwer działa$', '· Server running'),
    (r'· Oczekiwanie na usługi$', '· Waiting for services'),
    (r'Plan wejścia jest gotowy\.$', 'The entry plan is ready.'),
    (r'Plan wejścia zapisany; oczekiwanie na restart gry\.$', 'Entry plan saved; waiting for the game to restart.'),

    # --- manage.html ---
    (r'^Stan działający teraz: CH2 włączony\.$', 'Currently running: CH2 enabled.'),
    (r'^Stan działający teraz: CH2 wyłączony\.$', 'Currently running: CH2 disabled.'),
    (r'^Stan działający teraz: świeże kanały wyłączone\.$', 'Currently running: fresh channels disabled.'),
    (r'^Stan działający teraz: świeże kanały CH3\.$', 'Currently running: fresh channels CH3.'),
    (r'^Stan działający teraz: świeże kanały CH3 i CH4\.$', 'Currently running: fresh channels CH3 and CH4.'),
    (r'^🎒 Wyłącz Skrzynię Ucznia \(gracze i boty\)$', '🎒 Disable the Apprentice Chest (players and bots)'),
    (r'^aktywnych botów', 'active bots'),
    (r'^gotowa$', 'ready'),
    (r'^nie uruchomiona$', 'not running'),

    # --- maps.html ---
    (r'^Kanał (\d+)$', 'Channel $1'),
    # map_name()'s answer for a map the panel does not name
    (r'^Poza aktywnym światem \(mapa #(\d+)\)$', 'Outside the active world (map #$1)'),
    (r'^co (\d+)% zwykłego czasu$', 'at $1% of the normal time'),

    # --- panel_logs.html ---
    (r'^Rozmiar aktywnego pliku: ([\d.]+) KB$', 'Active file size: $1 KB'),
    (r'— pusty, jeszcze żaden błąd nie został zapisany$', "— empty, no error has been recorded yet"),

    # --- player.html ---
    (r'^· (.+) · poziom (.+)$', '· $1 · level $2'),
    # where a bot's offline shop stands (its map is translated after this)
    (r'^(.+), współrzędne (\d+), (\d+)\.$', '$1, coordinates $2, $3.'),
    (r'^Yang ([\d\s]+)$', 'Yang $1'),
    (r'^⏱ (\d+) h (\d+) min$', '⏱ $1 h $2 min'),
    (r'^🕐 Ostatnio: (.+)$', '🕐 Last seen: $1'),
    (r'^💍 Poślubiony/a z (.+)$', '💍 Married to $1'),
    (r'Wojownik', 'Warrior'),

    # --- rankings() route: every ranking kind's "detail" column, a single
    # SQL CONCAT() string per row (operator, 2026-10-03: "właściwie wszystko
    # w rankingach jest do przetłumaczenia" -- reviewed every kind in
    # bot_ranking(), not just the ones reported). Where a row combines an
    # item's own name with trailing stat text in one string (weapon/armor),
    # {N: "item"}-style group tagging looks the name up in ITEM_NAMES --
    # EXACT alone only translates a *whole* text node, and "Krwawy Miecz+9
    # (wymagany poziom 45)" as one string never is one. Must come before the
    # generic "poziom (\d+)" below, or that rule eats "poziom 45" out of the
    # weapon/armor string on its own first and this one no longer matches
    # (same bug as the first, narrower "wymagany poziom" fix, 2026-10-03).
    (r'^Średnie obrażenia: (-?\d+)% · Obrażenia umiejętności: (-?\d+)% · (.+)$',
     'Average damage: $1% · Skill damage: $2% · $3', {3: "item"}),
    (r'^(.+) \(wymagany poziom (\d+)\)$', '$1 (required level $2)', {1: "item"}),
    (r'^(.+) \((\d+) obrony\)$', '$1 ($2 defense)', {1: "item"}),
    (r'^(\d[\d,\s]*) złowionych ryb$', '$1 fish caught'),
    (r'^(\d+) zabitych bossów · 7 dni$', '$1 bosses killed · 7 days'),
    (r'^(\d+) pomyślnych ulepszeń$', '$1 successful upgrades'),
    (r'^([\d.]+)% \((\d+)/(\d+) ulepszeń\)$', '$1% ($2/$3 upgrades)'),
    (r'^(\d+) przedmiotów$', '$1 items'),
    (r'^Koń Lv (\d+)$', 'Horse Lv $1'),
    (r'^(\d+) / (\d+) misji$', '$1 / $2 missions'),
    (r'^([\d,\s]+) Yang ze sprzedaży$', '$1 Yang from sales'),
    (r'^Brak rozwiniętych umiejętności$', 'No developed skills'),
    (r'^(\d[\d,\s]*) obrażeń \(zwykłe, rekord\)$', '$1 damage (normal, record)'),
    (r'^(\d[\d,\s]*) obrażeń \(konno, rekord\)$', '$1 damage (mounted, record)'),
    (r'^(\d[\d,\s]*) obrażeń \(umiejętność, rekord\)$', '$1 damage (skill, record)'),
    (r'^(\d[\d,\s]*) Yang zdobytych łącznie$', '$1 Yang earned total'),
    (r'^(\d[\d,\s]*) zabitych potworów łącznie$', '$1 monsters killed total'),
    # Not "pokonanych minibossów"/"pokonanych graczy" -- the earlier, more
    # general (\d+) pokonanych\b rule below (line ~1786, applied first since
    # it comes first in this list) already turns "pokonanych" into
    # "defeated" on its own by the time these run, same ordering quirk as
    # above.
    (r'^(\d[\d,\s]*) defeated minibossów$', '$1 minibosses defeated'),
    (r'^(\d[\d,\s]*) defeated graczy \(wrogie królestwo\)$', '$1 players defeated (enemy kingdom)'),
    (r'^(\d[\d,\s]*) wygranych pojedynków$', '$1 duels won'),
    (r'^(\d[\d,\s]*) wykopanych rud$', '$1 ore mined'),

    (r'^zwojem \((.+)\)$', 'by scroll ($1)', {1: "item"}),
    (r'poziom (\d+)', 'level $1'),
    (r'Premium \(ogólne, VIP\)', 'Premium (general, VIP)'),
    (r' do (\d{2}\.\d{2}\.\d{4})$', ' until $1'),
    (r'^Walczę z (.+)$', 'Fighting $1'),
    (r'^Zbieram: ', 'Collecting: '),
    (r'Ząb Orka', 'Orc Tooth'),
    (r'Zarażony Pies', 'Diseased Dog'),
    (r'^· ([\d\s]+) pkt$', '· $1 pts'),
    (r'^Nierozdane: (\d+) pkt statystyk · (\d+) pkt umiejętności$', 'Unspent: $1 stat pts · $2 skill pts'),
    (r'^Ranga: (.+) · poziom (\d+)$', 'Rank: $1 · level $2'),
    (r'^Ranga: (.+)$', 'Rank: $1'),
    (r'^(.+), współrzędne (\d+), (\d+)\.$', '$1, coordinates $2, $3.'),
    (r'^💰 Potencjalny zarobek: ([\d\s]+) Yang$', '💰 Potential earnings: $1 Yang'),
    (r'^Magazyn \(pusty\)$', 'Storage (empty)'),
    (r'^Magazyn$', 'Storage'),

    # --- rankings.html ---
    (r'^Boty i gracze razem: 👤 oznacza postać gracza, a postaci GM-ów \(z rangą w common\.gmlist\) nie są liczone\. ',
     'Bots and players together: 👤 marks a player character, and GM characters (ranked in common.gmlist) aren\'t counted. '),
    (r'^Liczone są tylko boty \(przełącznik „Prawdziwi gracze w rankingach” w Zarządzaniu\)\. ',
     'Only bots are counted (the "Real players in rankings" switch in Management). '),
    (r'Dane pochodzą bezpośrednio z postaci, wyposażenia i questów\.$', "Data comes straight from characters, equipment and quests."),

    # --- world_feed_events.html message verbs (app.py builds "{name}
    # ulepszył {item}" / "{name} rozwinął {skill} na {rank}" server-side;
    # item/skill/rank names are raw game data, out of scope, but the verb
    # itself is worth catching wherever it lands in the sentence) ---
    (r'ulepszył', 'refined'),
    (r'rozwinął', 'mastered'),

    # --- respawns.html ---
    (r'^co (\d+)% zwykłego czasu$', 'at $1% of the normal time'),
    (r'^(\d+)%$', '$1%'),
    (r' · domyślnie$', ' · default'),

    # --- <title> tags (browser tab text) across templates ---
    (r'^Konto (.+) · (.+)$', 'Account $1 · $2'),
    (r'^Konta · (.+)$', 'Accounts · $1'),
    (r'^Nazwy postaci botów · (.+)$', 'Bot character names · $1'),
    (r'^Osobowości botów · (.+)$', 'Bot personalities · $1'),
    (r'^Kreator postaci · (.+)$', 'Character creator · $1'),
    (r'^Podsumowanie dnia (\d+) · (.+)$', 'Daily summary $1 · $2'),
    (r'^Diagnostyka · (.+)$', 'Diagnostics · $1'),
    (r'· Gospodarka$', '· Economy'),
    (r'^Sklepy offline · (.+)$', 'Offline shops · $1'),
    (r'^Eventy · (.+)$', 'Events · $1'),
    (r'^Komendy GM · (.+)$', 'GM commands · $1'),
    (r'· Gildie$', '· Guilds'),
    (r'^Gildie botów · (.+)$', 'Bot guilds · $1'),
    (r'^Masowe nadawanie · (.+)$', 'Bulk granting · $1'),
    (r'^Baza przedmiotów · (.+)$', 'Item database · $1'),
    (r'^Czat na żywo · (.+)$', 'Live chat · $1'),
    (r'^Zarządzanie grą · (.+)$', 'Game management · $1'),
    (r'^Ustawienia panelu · (.+)$', 'Panel settings · $1'),
    (r'^Logi panelu · (.+)$', 'Panel logs · $1'),
    (r'^Rankingi · Seban Panel$', 'Rankings · Seban Panel'),
    (r'^Respawny · (.+)$', 'Respawns · $1'),
    (r'^Sezon · (.+)$', 'Season · $1'),
    (r'^Pierwsza konfiguracja · (.+)$', 'Initial setup · $1'),
    (r'^Wiadomości ze świata · (.+)$', 'World messages · $1'),
]

# --- player.html: quest/mission-file labels (character_mission_progress) ---
EXACT.update({
    "oddanych": "handed in", "ukończonych misji": "missions completed", "pokonanych": "defeated",
    "Koń bojowy: próba na pustyni": "Battle horse: desert trial",
})
PATTERNS_RAW += [
    (r'^Biolog (\d+)/14: (.+)$', 'Biologist $1/14: $2'),
    (r'^Biolog: misja wstępna (\d+) z (\d+)$', 'Biologist: preliminary mission $1 of $2'),
    (r'^Aktualnie szuka: (.+)$', 'Currently looking for: $1'),
    (r'^Zbiera: (.+)$', 'Collecting: $1'),
    (r' · w ekwipunku: (\d+)$', ' · in inventory: $1'),
    (r'^Polowanie nr (\d+): (.+)$', 'Hunt #$1: $2'),
]

# --- player.html: "Wpisz {name}" delete-confirm placeholder + flash messages ---
EXACT.update({
    "Wpisz poprawne liczby godzin (0–720).": "Enter valid hour numbers (0-720).",
    "Wpisz całkowite wartości liczbowe.": "Enter whole numeric values.",
    "To jest NIEODWRACALNE i skasuje wszystkie przedmioty tej postaci. Kontynuować?":
        "This is IRREVERSIBLE and will delete all of this character's items. Continue?",
})
PATTERNS_RAW.append((r'^Wpisz (.+)$', 'Type $1'))

# --- app.py GEAR_HISTORY_HOWS: equipment history entry labels ---
EXACT.update({
    "Ulepszenie udane": "Refine succeeded", "Ulepszenie nieudane": "Refine failed",
    "Spalone przy ulepszaniu": "Burned while refining", "Wędka ulepszona": "Rod refined",
    "Wędka nieulepszona": "Rod refine failed", "Założone": "Equipped", "Podarowane": "Gifted",
    "Dostane w prezencie": "Received as a gift", "Sprzedane na straganie": "Sold at a stall",
    "Kupione na straganie": "Bought at a stall", "Sprzedane handlarzowi": "Sold to merchant",
    "Zużyte na przemianę bonusów": "Used to change bonuses", "Dodano bonus (Wzmocnienie)": "Bonus added (Enhancement)",
    "Zmieniono bonusy (Zmiana)": "Bonuses changed (Change)", "Dodano 5. bonus (Marmur)": "5th bonus added (Marble)",
    "Kupione u handlarza": "Bought from merchant", "Marmur z Magicznego Pyłu": "Marble from Magic Dust",
    "Do magazynu": "To storage", "Z magazynu": "From storage", "Ze Szkatułki Blasku": "From a Moonlight Treasure Chest",
    "Z wymiany": "From an exchange", "Oddane w wymianie": "Given in an exchange",
})

# --- app.py EVENT_LABELS ---
EXACT.update({
    "Szkatułki Blasku Księżyca": "Moonlight Treasure Chests",
    "Pirat Tanaka": "Pirate Tanaka",
    "Zuo: deszcz Metinów": "Zuo: Metin rain",
})

# --- app.py REFINE_METHOD_LABELS + _classify_news_events()/world_feed
# message templates -- these feed both /world-feed and the dashboard's
# live news ticker (static/news-feed.js), so the same phrasing needs
# covering in both places (PATTERNS since names/items/scrolls are
# embedded live data). ---
EXACT.update({
    "u kowala": "at the blacksmith",
    "w kuźni gildii": "at the guild forge",
    "Wieżą Diabła": "with the Devil's Tower",
    "zwojem": "by scroll",
    "innym sposobem": "by another method",
})
PATTERNS_RAW += [
    (r'^zwojem \((.+)\)$', 'by scroll ($1)'),
    (r'^(.+) znalazł Małż podczas połowu$', '$1 found a Clam while fishing'),
    (r'^(.+) otworzył Szkatułkę Umarłego Rozpruwacza i zdobył (.+)$', '$1 opened a Reaper\'s Chest and got $2'),
    # Same method labels, but reachable as a " — {method}" suffix glued
    # onto a refine message in the news ticker (news_feed_events()),
    # rather than their own isolated text node.
    (r' — u kowala$', ' — at the blacksmith'),
    (r' — w kuźni gildii$', ' — at the guild forge'),
    (r' — Wieżą Diabła$', " — with the Devil's Tower"),
    (r' — zwojem \((.+)\)$', ' — by scroll ($1)'),
    (r' — zwojem$', ' — by scroll'),
    (r' — innym sposobem$', ' — by another method'),
]

# --- app.py legendary_announcement_from_syslog(): the raids' gold notices in
# the live chat, the world feed and the ticker. The game's own English names:
# Azrael and the Death Reaper (mob_proto 2598 and 1093), the Devil's
# Catacomb (the client's MAP_DEVILCATACOMB); the world boss is whichever
# boss the core named, put into English by MOB_NAMES. ---
EXACT.update({
    "Rajd na Azraela": "Azrael raid",
    "Pokonany boss": "Boss defeated",
    "Legendarne wydarzenie": "Legendary event",
})
PATTERNS_RAW += [
    (r'^Drużyna (.+) \((.+)\) pokonała Azraela w Katakumbach Diabła!$',
     "$1's party ($2) defeated Azrael in the Devil's Catacomb!"),
    (r'^(.+) pokonał Umarłego Rozpruwacza na dziewiątym piętrze Wieży Demonów!',
     '$1 defeated the Death Reaper on the ninth floor of the Demon Tower!'),
    (r' Ostatni cios: (.+)\.$', ' Last blow: $1.'),
    (r'^Boty z królestwa (.+?) pokonały: (.+) \((\d+) min\)\.$', 'Bots of the $1 kingdom defeated: $2 ($3 min).',
     {2: "mob"}),
    # EMPIRES' answer for an empire it does not know, and the notice's own
    # for a raid that came without a name
    (r'^Bots of the nieznanego królestwa kingdom ', 'Bots of an unknown kingdom '),
    (r'\(nieznanego królestwa\)', '(unknown kingdom)'),
    (r"^Nieznana drużyna's party ", 'An unknown party '),
    (r'^Nieznana drużyna(?= defeated )', 'An unknown party'),
]

# --- static/ajax-forms.js ---
EXACT.update({
    "Błąd sieci — spróbuj ponownie.": "Network error — try again.",
})
PATTERNS_RAW.append((r'^Coś poszło nie tak \(', 'Something went wrong ('))

# --- static/character-creator-page.js ---
EXACT.update({
    "Stwórz nową postać": "Create new character",
    "Nieprawidłowa nazwa.": "Invalid name.",
    "Ta nazwa jest już zajęta.": "This name is already taken.",
    "To konto ma już 4 postacie — brak wolnego slotu.": "This account already has 4 characters — no free slot.",
})
PATTERNS_RAW.append((r'^To konto ma już postać w królestwie ', 'This account already has a character in the '))

# --- static/dashboard-charts.js ---
EXACT.update({
    "Sklepy według map": "Shops by map",
    "Sklepy według map (offline)": "Shops by map (offline)",
})

# --- static/dashboard-deferred.js: JS-side fallback defaults ---
EXACT.update({
    "Obciążenie VPS": "VPS load",
    "Ładowanie botów wg kanału": "Loading bots by channel",
    "Ładowanie danych": "Loading data",
    "Ładowanie zalogowanych botów": "Loading logged-in bots",
    "Ładowanie": "Loading",
    "Aktualna": "Up to date",
    "Pobieranie danych": "Fetching data",
    "Nie udało się doładować danych.": "Failed to load data.",
})

# --- static/heatmap.js ---
PATTERNS_RAW.append((r' zdarzeń$', ' events'))

# --- static/live-widget.js ---
EXACT.update({
    "Pozostałe aktywności": "Other activities",
    "Aktywności w świecie": "World-wide activities",
    "Boty wg poziomu": "Bots by level",
    "Brak botów w tym królestwie.": "No bots in this kingdom.",
    "Brak botów online.": "No bots online.",
    "Automatycznie zmieniaj mapy po bezczynności": "Automatically switch maps when idle",
    "Pozycje botów na żywo": "Live bot positions",
    "Mapa cieplna: zgony botów": "Heatmap: bot deaths",
    "Mapa cieplna: rozbite Metiny": "Heatmap: broken Metins",
    "Mapa cieplna: zabite bossy": "Heatmap: bosses killed",
    "Brak aktywnych botów na tej mapie.": "No active bots on this map.",
    "Brak zdarzeń na tej mapie.": "No events on this map.",
    "W trybie mapy cieplnej aktywności nie są wyświetlane.": "Activities aren't shown in heatmap mode.",
    "Inna aktywność": "Other activity",
    "Wieża Demonów": "Demon Tower",
    "Zakłada kostium": "Putting on a costume",
    "Zbiera łup": "Picking up loot",
    "rozbitych Metinów": "broken Metins",
    "zabitych bossów": "bosses killed",
    "zdarzeń": "events",
    "zgonów botów": "bot deaths",
    "← Ranking i aktywności": "← Ranking & activities",
    "Możliwie zawieszony": "Possibly stuck",
    # live-widget.js's own action/goal dicts -- slightly different wording
    # from app.py's BOT_ACTIONS, used only in the live map's JS.
    "Planuje ruch": "Planning a move",
    "Przemieszcza się": "Traveling",
    "Expi / walczy": "Grinding / fighting",
    "Wabi potwory": "Luring monsters",
    "Rozwija umiejętności": "Improving skills",
    "Zdobywa ekwipunek": "Getting gear",
    "Uzupełnia zapasy": "Restocking",
    "Poluje na Metiny": "Hunting Metins",
    "Misje polowania": "Hunting missions",
    "Rozwija konia": "Training the horse",
    "Ulepsza ekwipunek": "Upgrading gear",
    "Gra w grupie": "Playing in a party",
    "Kupione w sklepie offline": "Bought from an offline shop",
})
PATTERNS_RAW += [
    (r'^x(\d+) za ([\d ]+) yang · od (.+)$', 'x$1 for $2 Yang · from $3'),
    (r'^za ([\d ]+) yang · od (.+)$', 'for $1 Yang · from $2'),
    (r'^x(\d+) za ([\d ]+) yang$', 'x$1 for $2 Yang'),
    (r'^za ([\d ]+) yang$', 'for $1 Yang'),
    (r'^zamiast (.+)$', 'instead of $1'),
    (r'poziom (\d+)', 'level $1'),
    (r'możliwie zablokowany', 'possibly stuck'),
    (r'walczy z Metinem', 'fighting a Metin'),
    (r'^Własny czas mapy · (\d+) s$', 'Custom map timing · $1s'),
    (r'^Globalnie · (\d+)% czasu podstawowego$', 'Global · $1% of base time'),
    (r'Potwory (\d+)%', 'Monsters $1%'),
    (r'Metiny/bossy (\d+)%', 'Metins/bosses $1%'),
    (r'Metiny (\d+)%', 'Metins $1%'),
    (r'Bossowie (\d+)%', 'Bosses $1%'),
]

# --- static/news-feed.js ---
EXACT.update({
    "Feed wydarzeń jest chwilowo niedostępny.": "The event feed is temporarily unavailable.",
    "Oczekiwanie na nowe ważne wydarzenia ze świata…": "Waiting for major new world events…",
    "Nie udało się pobrać wiadomości.": "Failed to fetch messages.",
    "Nieprawidłowa odpowiedź feedu.": "Invalid feed response.",
})

# --- static/notifications-bell.js ---
EXACT.update({
    "Brak powiadomień.": "No notifications.",
    "Kliknij, żeby zobaczyć.": "Click to see.",
})

# --- player.html: a bot's EXP lock card and its flash messages
# (bot_exp_lock_view / player_action_exp_lock in app.py, Playerbots 2.x) ---
EXACT.update({
    "⚡ Doświadczenie (EXP)": "⚡ Experience (EXP)",
    "Towarzysz gracza: jego exp zależy od Pierścienia Anty-Exp właściciela i jego własnego limitu, nie od panelu.":
        "A player's companion: its EXP follows its owner's Anti-Exp Ring and its own cap, not the panel.",
    "🔒 Exp zablokowany: bot nie zdobywa doświadczenia": "🔒 EXP blocked: the bot gains no experience",
    "✅ Exp leci: bot zdobywa doświadczenie": "✅ EXP flows: the bot gains experience",
    "Bota nie ma w grze, stan z ostatniego zapisu postaci.": "The bot is not in the game; as its character was last saved.",
    "🔓 Operator odblokował exp: osobowość nie blokuje tego bota.":
        "🔓 Unlocked by the operator: its personality does not block this bot.",
    "Bez zmiany operatora: o blokadzie decyduje osobowość.": "No operator override: its personality decides the lock.",
    "Przywróć blokadę": "Restore the lock",
    "🔓 Odblokuj exp": "🔓 Unlock EXP",
    "„Odblokuj exp” pozwala botowi zdobywać doświadczenie, choć jego osobowość by go zatrzymała (Grinder na progu swojego tieru, dropper w swoim paśmie). „Przywróć blokadę” oddaje decyzję osobowości. Zmianę wykonuje rdzeń, na którym bot gra; bot poza grą dostanie ją, gdy wejdzie.":
        "\"Unlock EXP\" lets the bot gain experience although its personality would hold it (a Grinder at its tier's lock, "
        "a dropper in its band). \"Restore the lock\" hands the decision back to its personality. The core the bot plays on "
        "makes the change; a bot out of the game gets it when it comes in.",
    "Blokadę exp botów ma tylko linia Playerbots 2.x (mt2009).": "Only the Playerbots 2.x line (mt2009) has the bots' EXP lock.",
    "Nieobsługiwana akcja.": "Unsupported action.",
    "Panel nie zmienia blokady exp tej postaci: to nie jest bot z rejestru albo to towarzysz gracza.":
        "The panel does not change this character's EXP lock: it is not a registered bot, or it is a player's companion.",
})
PATTERNS_RAW += [
    (r'^Osobowość trzyma go na poziomie (\d+)\.$', 'Its personality holds it at level $1.'),
    (r'^⏳ Odblokowanie czeka na wejście bota do gry \(zlecone (.+)\)\.$',
     '⏳ The unlock waits for the bot to come into the game (asked $1).'),
    (r'^⏳ Przywrócenie blokady czeka na wejście bota do gry \(zlecone (.+)\)\.$',
     '⏳ Restoring the lock waits for the bot to come into the game (asked $1).'),
    (r'^⏳ Rdzeń bota właśnie wykonuje zmianę \(zlecone (.+)\)\.$',
     "⏳ The bot's core is making the change right now (asked $1)."),
    (r'^(.+): exp odblokowany, bot zdobywa doświadczenie\.$', '$1: EXP unlocked, the bot gains experience.'),
    (r'^(.+): blokada przywrócona, o blokadzie decyduje osobowość\.$', '$1: the lock is restored, its personality decides.'),
    (r'^(.+) nie jest teraz w grze albo jego rdzeń jeszcze nie odpowiedział\. Zmiana czeka i wykona ją rdzeń bota, '
     r'gdy bot będzie w grze\.$',
     "$1 is not in the game now, or its core has not answered yet. The change waits, and the bot's core makes it "
     "once the bot is in the game."),
    (r'^Rdzeń bota (.+) właśnie wykonuje zmianę\. Odśwież stronę za chwilę\.$',
     'The core of $1 is making the change right now. Reload the page in a moment.'),
    (r'^Nie udało się zmienić blokady exp \((.+)\)\.$', 'Could not change the EXP lock ($1).'),
    # The mood line's tail ("Normalny · blokada expa na 30 lvl").
    (r'blokada expa na (\d+) lvl', 'EXP locked at level $1'),
    (r'exp odblokowany przez operatora', 'EXP unlocked by the operator'),
]


def _compile_pattern(entry):
    """A PATTERNS_RAW entry, (source, replacement[, names]), as re.subn wants
    it. names maps a group to the kind of game name it holds ("mob"): that
    group's text is put back under the monster's official English name where
    it has one (MOB_NAMES, below), so a pattern can translate a sentence that
    names a boss without guessing at the boss. static/i18n-watch.js reads the
    first two fields only and keeps such a name in Polish -- the names are
    server-side, which is why app.py translates the live chat's fragment
    before sending it."""
    replacement = _dollar_to_backslash(entry[1])
    names = entry[2] if len(entry) > 2 else None
    if not names:
        return re.compile(entry[0]), replacement

    def substitute(match):
        def group(token):
            number = int(token.group(1))
            text = match.group(number) or ""
            table = {"mob": MOB_NAMES, "item": ITEM_NAMES}.get(names.get(number))
            return table.get(text, text) if table is not None else text
        return re.sub(r'\\g<(\d+)>', group, replacement)
    return re.compile(entry[0]), substitute


PATTERNS = [_compile_pattern(entry) for entry in PATTERNS_RAW]

# apply_text() (app.py) renders each item stat/bonus as "{label} {value:+d}
# {suffix}" e.g. "Szybkość ataku +5%" or "Maks. PŻ +80" -- one pattern per
# _ITEM_STAT_LABELS entry, generated instead of hand-written, matching the
# label followed by a signed number and whatever suffix follows. Added to
# PATTERNS_RAW too (JS-style $-refs) so i18n_payload() ships them to
# static/i18n-watch.js for client-rendered tooltips as well.
for _pl_label, _en_label in _ITEM_STAT_LABELS.items():
    _raw_pattern = r'^' + re.escape(_pl_label) + r' ([+-]\d+)(.*)$'
    _raw_repl = f'{_en_label} $1$2'
    PATTERNS_RAW.append((_raw_pattern, _raw_repl))
    PATTERNS.append((re.compile(_raw_pattern), _dollar_to_backslash(_raw_repl)))


# A map's name inside a longer text ("Zuo: deszcz Metinów · Dolina Orków",
# "Dolina Orków, współrzędne 512, 300.") -- EXACT only catches one that is a
# whole text node. One pattern a map, generated like the stat labels above
# and appended after every other pattern, so a sentence pattern that keeps a
# map in its (.+) has had its turn first. A map is bounded by the text's
# start or a space/bracket before it and by the end, a space or punctuation
# after it (no \b: JS's knows only ASCII letters, and "Świątynia" begins
# with one it does not); longest first, so "Czerwony Las" is never read as
# some other "Las". The bare "Las" (the Ghost Wood's short name on the live
# map) is an ordinary word too, so it is left to EXACT, and a village is
# called the same in English.
_MAP_NAMES_IN_TEXT = (
    "Loch Małp Shinsoo", "Loch Małp Chunjo", "Loch Małp Jinno", "Loch Małp Normalny", "Loch Małp Trudny",
    "Loch Pająków V1", "Loch Pająków V2", "Grota Wygnańców V1", "Grota Wygnańców V2",
    "Dolina Orków", "Pustynia Yongbi", "Góra Sohan", "Ognista Ziemia", "Świątynia Hwang",
    "Las Duchów", "Czerwony Las", "Wieża Demonów",
)
for _pl_map in sorted(_MAP_NAMES_IN_TEXT, key=len, reverse=True):
    _raw_pattern = r'(^|[\s(])' + re.escape(_pl_map) + r'(?=$|[\s),.!?:;])'
    _raw_repl = '$1' + EXACT[_pl_map]
    PATTERNS_RAW.append((_raw_pattern, _raw_repl))
    PATTERNS.append((re.compile(_raw_pattern), _dollar_to_backslash(_raw_repl)))

# An event's name (app.py's EVENT_LABELS) inside a longer text: a finished
# Tanaka's or Zuo's "Pirat Tanaka · Pyongmoo" in the history, the same in
# its notification after "Event zakończony: ", a calendar block's
# "Edytuj: Doświadczenie (20:00–21:00)". Yang is Yang in English.
for _pl_event in ("Szkatułki Blasku Księżyca", "Doświadczenie", "Drop przedmiotów", "Pirat Tanaka", "Zuo: deszcz Metinów"):
    _raw_pattern = r'(^|: )' + re.escape(_pl_event) + r'(?= · | \(|$)'
    _raw_repl = '$1' + EXACT[_pl_event]
    PATTERNS_RAW.append((_raw_pattern, _raw_repl))
    PATTERNS.append((re.compile(_raw_pattern), _dollar_to_backslash(_raw_repl)))


# ---------------------------------------------------------------------------
# ITEM_NAMES: an item's Polish proto name -> its official English name, for a
# text node that is exactly the name the panel printed from item_proto
# (the item database, inventories, rankings, shops). The names are the ones
# the Playerbots core says to a player who reads English: static/
# item_names_en.json, rendered by tools/generate_game_names_en.py from
# Playerbots' playerbot_names_en.tsv (Gameforge's English, and the world's
# own items by hand where Gameforge never named them). A Polish name that two
# vnums share under two different English names cannot say which item it is,
# so it stays Polish, as the core leaves it; so does an item with no official
# English name at all.
# ---------------------------------------------------------------------------
def _load_game_names(filename):
    """vnum -> [Polish proto name, English name], or {} without the file."""
    try:
        with open(Path(__file__).parent / "static" / filename, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def _names_by_polish(table):
    names, shared = {}, set()
    for polish, english in table.values():
        if names.setdefault(polish, english) != english:
            shared.add(polish)
    for polish in shared:
        del names[polish]
    return names


_ITEM_NAMES_BY_VNUM = _load_game_names("item_names_en.json")
ITEM_NAMES = _names_by_polish(_ITEM_NAMES_BY_VNUM)


def item_vnums_named(text):
    """The vnums whose official English name contains text, in any case --
    for the item database's search on an English panel, which shows these
    names while the database knows only the Polish ones."""
    needle = (text or "").strip().casefold()
    if not needle:
        return []
    return [int(vnum) for vnum, (_polish, english) in _ITEM_NAMES_BY_VNUM.items()
            if needle in english.casefold()]


# The monsters and NPCs the same way (static/mob_names_en.json), but only for
# a pattern's group marked as a monster's name -- the boss in a raid's notice
# -- and never for a whole text node: bots and guilds are called "Wilk" or
# "Kowal" too, and a name is somebody's, not a word to translate.
MOB_NAMES = _names_by_polish(_load_game_names("mob_names_en.json"))

_SCRIPT_STYLE_RE = re.compile(r'(<(script|style|textarea|pre)\b[^>]*>.*?</\2>)', re.I | re.S)
# An element marked translate="no" -- the HTML attribute browsers' own
# translators honour -- holds somebody's own words, a chat line and the nick
# that wrote it, and is left exactly as it is, like a script. Its content
# must not hold another element of the same tag: the match ends at the first
# closing one.
_NO_TRANSLATE_RE = re.compile(r'(<([a-zA-Z][\w-]*)\b[^>]*\btranslate="no"[^>]*>.*?</\2>)', re.I | re.S)
_PLACEHOLDER_RE = re.compile(r"<!--\x00SS(\d+)\x00-->")
# Quote-aware: a naive <[^>]+> stops at the FIRST > anywhere, including one
# inside a quoted attribute value -- an inline onclick="...e=>{...}..."
# arrow function's own > was enough to split a tag in half and corrupt the
# text segment right after it (found via manage.html's "Restore 100%"
# button, the one onclick handler in the templates with a bare > in it).
_TAG_RE = re.compile(r'''(<(?:[^>"']|"[^"]*"|'[^']*')*>)''')
_ATTR_TRANSLATE_RE = re.compile(r'\b(title|alt|placeholder|aria-label)="([^"]*)"')
_TYPE_SUBMIT_RE = re.compile(r'\btype="(submit|button)"', re.I)
_VALUE_ATTR_RE = re.compile(r'\bvalue="([^"]*)"')
_WS_RE = re.compile(r'^(\s*)(.*?)(\s*)$', re.S)


def translate_string(raw):
    """Translate one already-HTML-escaped fragment (a trimmed text node or
    an attribute value). Returns the original unchanged if nothing matches.

    A whole-phrase EXACT hit wins outright, then an item's whole name
    (ITEM_NAMES -- after EXACT, so a panel phrase that happens to be some
    item's name keeps the panel's own translation). Otherwise every PATTERNS
    entry is applied in turn (not just the first match) -- many dynamic strings
    are composed from more than one translatable fragment (e.g. "42 szt. ·
    12 pokonanych"), so a single anchored pattern can't always cover the
    whole thing; letting several smaller patterns each fire on the parts
    they recognise covers far more of these without an explosion of
    one-off full-sentence regexes."""
    if not raw or not raw.strip():
        return raw
    core = html.unescape(raw)
    if core in EXACT:
        return html.escape(EXACT[core])
    if core in ITEM_NAMES:
        return html.escape(ITEM_NAMES[core])
    result, changed = core, False
    for pattern, repl in PATTERNS:
        new_result, count = pattern.subn(repl, result)
        if count:
            result = new_result
            changed = True
    if not changed:
        return raw
    return html.escape(result)


def _translate_text_segment(text):
    if not text or not text.strip():
        return text
    m = _WS_RE.match(text)
    lead, core, trail = m.group(1), m.group(2), m.group(3)
    return lead + translate_string(core) + trail


def _translate_tag(tag):
    tag = _ATTR_TRANSLATE_RE.sub(lambda m: f'{m.group(1)}="{translate_string(m.group(2))}"', tag)
    if tag[:6].lower() == '<input' and _TYPE_SUBMIT_RE.search(tag):
        tag = _VALUE_ATTR_RE.sub(lambda m: f'value="{translate_string(m.group(1))}"', tag, count=1)
    return tag


def translate_html(body, lang):
    """Translate a full rendered HTML response. No-op for anything but
    "en" -- Polish output is returned byte-identical to what Jinja made."""
    if lang != "en" or not body:
        return body
    placeholders = []

    def stash(m):
        placeholders.append(m.group(1))
        # Wrapped as a fake tag (matches _TAG_RE's <[^>]+>) so it always
        # lands in its own split token -- a bare \x00SS0\x00 marker glued
        # directly onto neighbouring text with no intervening whitespace
        # (e.g. "<label>Text<textarea>...") used to merge into that text's
        # segment and break its EXACT-dict lookup.
        return f"<!--\x00SS{len(placeholders) - 1}\x00-->"

    stashed = _SCRIPT_STYLE_RE.sub(stash, body)
    stashed = _NO_TRANSLATE_RE.sub(stash, stashed)
    parts = _TAG_RE.split(stashed)
    out = []
    for part in parts:
        if not part:
            continue
        out.append(_translate_tag(part) if part[0] == "<" else _translate_text_segment(part))
    translated = "".join(out)
    # A stashed translate="no" element can hold a stashed script of its own,
    # so the placeholders are put back until none is left.
    restored = None
    while restored != translated:
        restored = translated
        translated = _PLACEHOLDER_RE.sub(lambda m: placeholders[int(m.group(1))], translated)
    return translated


def i18n_payload():
    """EXACT + PATTERNS_RAW as JSON for static/i18n-watch.js, so the browser
    can apply the identical table to content the JS dashboard/live-map/
    rankings-carousel code renders client-side after the initial page load."""
    return json.dumps({"exact": EXACT, "patterns": PATTERNS_RAW}, ensure_ascii=False)

# --- configurable shop ranking feedback ---
EXACT.update({
    "Wybierz obsługiwany limit rankingu: 15, 25, 50 albo 100.": "Choose a supported ranking limit: 15, 25, 50, or 100.",
})
EXACT.update({
    "Ranking najszybciej sprzedających się przedmiotów pokazuje teraz 15 pozycji.": "The fastest-moving items ranking now displays 15 entries.",
    "Ranking najszybciej sprzedających się przedmiotów pokazuje teraz 25 pozycji.": "The fastest-moving items ranking now displays 25 entries.",
    "Ranking najszybciej sprzedających się przedmiotów pokazuje teraz 50 pozycji.": "The fastest-moving items ranking now displays 50 entries.",
    "Ranking najszybciej sprzedających się przedmiotów pokazuje teraz 100 pozycji.": "The fastest-moving items ranking now displays 100 entries.",
})
EXACT.update({
    # templates/_macros.html: the offline shop's price explanation (panel on the player card)
    "Dlaczego na ladzie": "Why it is on the counter",
    "Jak powstała cena": "How the price was set",
    "Krok": "Step",
    "Zmiana": "Change",
})
