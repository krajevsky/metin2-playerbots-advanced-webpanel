# Audyt porównawczy: Tieru 7788 → Seban Panel 7790

Stan źródeł: 9 października 2026. Panel Tieru sprawdzono **wyłącznie odczytem**: `/opt/panel/admin_panel.py` (27 394 linie) oraz pakiety `/opt/panel/editsql` i `/opt/panel/market_preview` z kontenera `metin2-panel`. Jego szablony i skrypty są w większości osadzone w `admin_panel.py`; nie istnieje osobny `/opt/panel/templates`. Odnośniki `admin_panel.py:linia` dotyczą tej kopii. Odpowiedniki podano dla Seban Panelu 1.114.5 (`app.py`, `templates/`, `static/`). „Częściowo” oznacza także funkcję dostępną wyłącznie przez link do Tieru, a nie natywnie u nas. Ten dokument jest listą kontrolną wdrożenia: statusy należy aktualizować wraz z kolejnymi commitami.

| Funkcja | Gdzie u Tieru (plik:linia / URL) | Gdzie u nas | Status | Przydatność | Plan |
|---|---|---|---|---|---|
| Logowanie administratora, wylogowanie i ochrona tras | `admin_panel.py:21790,22301,6648` `/login` | `app.py:4237,4253`, `templates/login.html` | jest | wysoka | Zachować istniejący mechanizm. |
| Wybór języka interfejsu | `admin_panel.py:5755` `/lang/<code>` | `app.py`, `translations.py` | jest | wysoka | Nowe funkcje tłumaczyć PL/EN. |
| Strona główna, karty botów i filtry listy | `admin_panel.py:7197,22306` `/admin` | `app.py:4282,4542`, `templates/dashboard.html`, `players.html` | u nas lepiej | wysoka | Zachować układ laka, sprawdzić pojedyncze pola danych. |
| Status serwera i liczba graczy | `admin_panel.py:1337,6535` `/api/status` | `app.py:7504,7523`, dashboard | jest | wysoka | Bez zmian. |
| Sprawdzanie nazwy postaci | `admin_panel.py:6544` `/api/checkname` | `app.py:7171` | jest | średnia | Bez zmian. |
| Wyszukiwarka przedmiotów i definicje ikon | `admin_panel.py:6430,6562` `/api/items`, `/static/item_defs.json` | `app.py:6487,6512`, `templates/items.html` | jest | wysoka | Zachować indeks i ikony. |
| Karta gracza: pozycja, zdrowie, EXP, ranga, sesje | `admin_panel.py:7402,23133` `/player/<pid>` | `app.py:5504`, `templates/player.html` | u nas lepiej | wysoka | Nie naruszać natywnych okien ani tooltipów. |
| Ekwipunek bota i wyposażenie | `admin_panel.py:19159` `/api/bot_inventory/<pid>` | `app.py:5504,5764`, `_inventory_fragment.html` | u nas lepiej | wysoka | Zachować mapowanie slotów. |
| Magazyn bota | `admin_panel.py:19328` `/api/bot_safebox/<pid>` | `app.py:5504`, `templates/player.html` | jest | wysoka | Bez zmian wizualnych. |
| Sklep bota i oferty | `admin_panel.py:19378` `/api/bot_shop/<pid>` | `app.py:5504`, `templates/player.html` | u nas lepiej | wysoka | Zachować okno sklepu i warstwę tooltipów body. |
| Usunięcie konkretnego przedmiotu z torby lub wyposażenia przez `DELITEM` | `admin_panel.py:22995–23131` `/api/bot_item_delete` | `app.py` `/api/bot-item-delete`, `templates/player.html` | jest | wysoka | Wdrożone w 1.114.6: kolejka, walidacja właściciela/vnum/liczby/window i testy. |
| Anulowanie oczekującego `DELITEM` | `admin_panel.py:23069–23102` `/api/bot_item_delete` | `app.py` `/api/bot-item-delete` | jest | wysoka | Wdrożone w 1.114.6; bez anulowania stanu wykonywania `w*`. |
| Usuwanie przedmiotu bezpośrednio ze sklepu offline | `admin_panel.py:23099–23107` (tylko INVENTORY/EQUIPMENT) | brak | brak u obu | wysoka | Najpierw sprawdzić komendę silnika i własność pozycji sklepu; nie pisać bezpośrednio do DB. |
| Blokada/odblokowanie EXP bota | `admin_panel.py:22827` `/player/<pid>/exp_lock` | `app.py:5419–5503,5726` | jest | wysoka | Bez zmian. |
| Teleport administratora do gracza/sklepu | `admin_panel.py:12634` `/api/admin/warp_me`; `market_preview/__init__.py:366` | `app.py:5040`, `templates/player.html` | jest | wysoka | Porównać statusy kolejki przy wdrożeniu rynku. |
| Historia decyzji sprzętowych bota | `admin_panel.py:14637` `/api/bot_gear_history/<pid>` | `app.py:4909`, `templates/decisions.html` | częściowo | średnia | Porównać filtry i objaśnienia, portować brakujące kody z tablic źródłowych. |
| Logi konkretnego bota | `admin_panel.py:14784` `/api/bot_logs/<name>` | `app.py:5031` `/api/bot-logs/<pid>` | jest | średnia | Zachować filtrowanie i limit rozmiaru. |
| Mapa na żywo, kafelki, heatmapa, pozycje | `admin_panel.py:10050,12466,18998–19069` `/map`, `/api/map_tile`, `/api/bot_heatmap`, `/api/bot_positions` | `app.py:4282,7416`, `templates/maps.html`, `player.html` | u nas lepiej | wysoka | Nie zmieniać proporcji M1 4:5/max 416 px i pozostałych 1:1/max 520 px. |
| Rankingi botów i graczy, filtry | `admin_panel.py:19478` `/api/bot_rankings` | `app.py:7542`, `templates/rankings.html` | u nas lepiej | średnia | Utrzymać istniejące kategorie +9 i języki. |
| Gildie i ich statystyki | `admin_panel.py:20683` `/guilds` | `app.py:4597,4622` | u nas lepiej | średnia | Zachować profil gildii. |
| Sezon i sortowanie | `admin_panel.py:21503` `/season` | `app.py:7707`, `templates/season.html` | jest | średnia | Zweryfikować kolumny sezonu w dalszym audycie. |
| Ustawienia EXP/drop/Yang | `admin_panel.py:19860` `/rates` | `app.py:8051`, `templates/manage.html` | jest | wysoka | Zachować źródła danych silnika. |
| Czas odrodzenia metinów, bossów i mobów | `admin_panel.py:20021` `/rates/regen` | `app.py:7863` | jest | wysoka | Zachować oddzielenie metinów od bossów. |
| Liczba odrodzeń | `admin_panel.py:20063` `/rates/regen_count` | `app.py:7886` | jest | średnia | Bez zmian. |
| Trudność i tempo gry | `admin_panel.py:20104` `/rates/difficulty` | `app.py:8070` | jest | wysoka | Bez zmian. |
| Automatyczne polowanie | `admin_panel.py:20153` `/rates/autohunt` | `app.py:8099` | jest | średnia | Bez zmian. |
| Skrzynia startowa | `admin_panel.py:20188` `/rates/starter_chest` | `app.py:8051` | jest | średnia | Nie nadpisywać Skrzyni Ucznia. |
| HP mobów i bonus dropu | `admin_panel.py:20224,20263` | `app.py:8051`, `templates/manage.html` | jest | średnia | Zweryfikować zakresy formularzy. |
| Szybkość ruchu botów | `admin_panel.py:20302` | `app.py:8051`, `templates/manage.html` | jest | średnia | Zweryfikować zakres. |
| Dodatki świata | `admin_panel.py:20341` `/rates/world_extras` | `app.py:8051`, `templates/manage.html` | częściowo | średnia | Porównać każdą flagę z formularzem; brakujące dodać osobno. |
| Smocza Alchemia | `admin_panel.py:20383` `/rates/dragon_soul` | `app.py:8051`, `/player` | częściowo | średnia | Porównać ustawienia, bez naruszania okna alchemii. |
| Bonus unikatowych przedmiotów poziomu 70 | `admin_panel.py:20423` | `app.py` `/manage/unique70-bonus`, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.7 z flagą i komendą silnika Tieru. |
| Yang z potworów: ekwipunek lub ziemia | `admin_panel.py:20457` `/rates/yang_ground` | `app.py` `/manage/yang-ground`, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.8, flaga `m2_yang_ground`. |
| Obrona przed botami innych królestw | `admin_panel.py:20491` `/rates/owner_defence` | `app.py` `/manage/owner-defence`, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.9 z flagą i komendą silnika Tieru. |
| Kanały i rozdział botów | `admin_panel.py:20622` `/rates/channels` | `app.py:8111`, `templates/manage.html` | jest | wysoka | Bez zmian. |
| Wagi AI, decyzje i aktualne akcje | `admin_panel.py:1745–2000,20883,21120` `/ai`, `/decisions` | `app.py:7780,8051`, `templates/decisions.html` | częściowo | wysoka | Porównać wszystkie suwaki, limity i etykiety. |
| Polityka przedmiotów AI | `admin_panel.py:1603–1627,21344` `/ai/items` | `app.py:8067`, `templates/manage.html` | jest | wysoka | Zachować plik TSV odczytywany przez silnik. |
| Natychmiastowy start Wieży Demonów/Katakumb | `admin_panel.py:21292,21309` | `app.py:8051` | częściowo | średnia | Sprawdzić kolejkę i dodać akcje, jeśli brak. |
| Zwolnienie zatrzymanych botów | `admin_panel.py:21326` | `app.py:8051` | częściowo | wysoka | Sprawdzić istniejący przełącznik hold. |
| Eventy: harmonogramy, status, wywołanie | `admin_panel.py:7909,20995` `/events` | `app.py:7934`, `templates/events.html` | częściowo | wysoka | Porównać rodzaje eventów i formularze. |
| Changelog/patchlog i sprawdzanie aktualizacji | `admin_panel.py:21540,21684,21712` | `app.py:7459`, `templates/changelog.html` | jest | średnia | Zachować wersjonowanie naszego panelu. |
| Aktualizator Tieru i pliki Playerbots | `admin_panel.py:21611,21742–21779` | `app.py:8051`, `templates/manage.html` | częściowo | średnia | Zachować istniejący updater i bezpieczny tor wdrożenia. |
| Pobieranie klienta, uruchamianie gry przez przeglądarkę | `admin_panel.py:21945,22049–22064` | brak | brak | niska | Osobna integracja; odłożyć do potwierdzenia dostępności klienta. |
| Raport awarii klienta i lista awarii | `admin_panel.py:22115,22172` | `app.py:7835`, `templates/diagnostics.html` | częściowo | średnia | Dodać widok logów awarii, jeśli źródło jest dostępne. |
| Rejestracja konta, logowanie konta gracza, zmiana hasła/reset | `admin_panel.py:21899–21943,22191–22296` | `app.py:6875,7340` | częściowo | niska | Administracja kont już istnieje; oddzielny portal gracza wymaga przeglądu uprawnień. |
| Akcje GM i kody administracyjne | `admin_panel.py:23339,23442,23476,23559` | `app.py:6868,5681–6046` | częściowo | wysoka | Porównać każdą komendę i zachować kontrolę uprawnień. |
| Eksport Iwakura | `admin_panel.py:25802` | brak | brak | niska | Przenieść tylko gdy jest odbiorca danych. |
| Edytor dropów: lista plików, wyszukiwanie, grupa, dodanie, podgląd, zapis | `admin_panel.py:26513–26878` `/drops/*` | brak | brak | średnia | Zweryfikować ścieżki serwera i atomowość zapisu; nie kopiować HTML Tieru. |
| Dane klienta i pobieranie | `admin_panel.py:27175,27214` `/client-data` | brak | brak | niska | Zostawić po funkcjach administracji botami. |
| Podgląd rynku: oferty, szukanie i filtry | `market_preview/__init__.py:282,312,513–518` `/market`, `/market/api/offers` | `app.py:6348,6465`, `templates/economy_shops.html` | częściowo | wysoka | Dodać brakujące filtry i kolumny, używając kart/tabel laka. |
| Podgląd rynku: teleport, status kolejki i historia | `market_preview/__init__.py:366–470` `/market/api/tp*` | `app.py:5040`, `templates/player.html` | częściowo | średnia | Porównać koszt i historię; zachować ochronę API. |
| Ustawienia rynku | `market_preview/__init__.py:470` `/market/settings` | `app.py:8051` | brak | średnia | Dodać tylko ustawienia aktywne w naszym silniku. |
| Edytor SQL: przegląd struktury i nazwy | `editsql/__init__.py:53–125,1264–1275` `/editsql`, `/editsql/structure`, `/editsql/api/name` | `templates/_laka_nav.html:40`, `base.html:59` (link do Tieru) | częściowo | średnia | Rozważyć natywny widok tylko z osobnym modelem uprawnień. |
| Edytor SQL: historia, plan zmian, etykiety, formularze, dodanie i usunięcie wiersza | `editsql/__init__.py:69–110,269–1050,1264–1282` | tylko link do Tieru | częściowo | niska | Pozostawić po audycie bezpieczeństwa i uprawnień. |

## Elementy świadomie nieprzenoszone

- HTML, CSS i JS klasycznego panelu Tieru: przenosimy zachowanie do komponentów `laka` i drugiego motywu, aby zachować skalowanie na telefonach.
- Alternatywne mechanizmy logowania i sesji konta gracza z `/account`: nasz panel jest administracyjny i nie powinien bez analizy otwierać drugiego portalu gracza.
- Bezpośrednie usuwanie danych SQL w celu skasowania przedmiotu bota: silnik musi wykonać `DELITEM` i ponownie sprawdzić przedmiot; modyfikacja DB pod aktywnym botem może rozjechać stan gry.
- Automatyczne kopiowanie updatera i binariów klienta Tieru: to oddzielny tor dystrybucji, który mógłby nadpisać lokalne poprawki i zasoby serwera.
- Zastępowanie naszych map, natywnych okien `/player` i warstwy tooltipów wariantami Tieru: obecny układ spełnia wymagania proporcji, slotów i zoomu mobilnego.

## Kolejność dalszych prac

1. `DELITEM` z ekwipunku/wyposażenia, ze stanem kolejki i anulowaniem. Usuwanie ze sklepu wymaga osobnej weryfikacji komendy silnika.
2. Brakujące akcje AI i ustawienia świata wykryte w porównaniu pól formularzy.
3. Filtry rynku, statusy kolejek, historie, potem edytor dropów i diagnostyka awarii.
4. Funkcje o niskiej przydatności tylko po potwierdzeniu ich źródeł danych i uprawnień.

Każda pozycja wymaga odrębnego commita, testów, sprawdzenia `laka` i drugiego motywu na desktopie i 375×812, patch bumpu z badge’em Codex przy zmianie widocznej dla użytkownika, tagu oraz wdrożenia dokładnie wypchniętego commita.
