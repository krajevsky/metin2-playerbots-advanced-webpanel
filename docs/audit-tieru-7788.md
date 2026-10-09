# Audyt porównawczy: Tieru 7788 → Seban Panel 7790

Stan źródeł: 9 października 2026. Panel Tieru sprawdzono **wyłącznie odczytem**: `/opt/panel/admin_panel.py` (27 394 linie) oraz pakiety `/opt/panel/editsql` i `/opt/panel/market_preview` z kontenera `metin2-panel`. Jego szablony i skrypty są w większości osadzone w `admin_panel.py`; nie istnieje osobny `/opt/panel/templates`. Odczytano też HTML działających tras `/admin`, `/map`, `/rates`, `/ai`, `/market`, `/events`, `/guilds`, `/player/2005`; `/season` nie odpowiedział w limicie 15 sekund, więc tę stronę oceniono z kodu. `/editsql` zwracał 401, a `/drops` i `/client-data` przekierowywały do logowania edytora; tych formularzy nie uruchamiano. Odnośniki `admin_panel.py:linia` dotyczą tej kopii. Odpowiedniki podano dla Seban Panelu 1.114.5 i aktualizowano wraz z patchami (`app.py`, `templates/`, `static/`). „Częściowo” oznacza także funkcję dostępną wyłącznie przez link do Tieru, a nie natywnie u nas. Ten dokument jest listą kontrolną wdrożenia.

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
| HP mobów | `admin_panel.py:20224` `/rates/mob_hp` | `app.py` `/manage/mob-hp`, `templates/manage.html` | jest | średnia | Zakres 10–300% zgodny. |
| Dodatkowy bonus dropu | `admin_panel.py:20263` `/rates/drop_bonus` | `app.py` `/manage/drop-bonus`, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.10, zakres 10–1000%, flaga i komenda źródłowa. |
| Szybkość ruchu postaci | `admin_panel.py:20302` `/rates/move_speed` | `app.py` `/manage/move-speed`, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.11, zakres 50–200%, flaga i komenda źródłowa. |
| Dodatki świata | `admin_panel.py:20341` `/rates/world_extras` | `app.py` `/manage/world-extras`, `templates/manage.html` | jest | średnia | Cor Draconis, drop kamieni i szkatułek zgodny. |
| Smocza Alchemia | `admin_panel.py:20383` `/rates/dragon_soul` | `app.py` `/manage/dragon-soul`, `/player` | jest | średnia | Nie naruszać okna alchemii. |
| Bonus unikatowych przedmiotów poziomu 70 | `admin_panel.py:20423` | `app.py` `/manage/unique70-bonus`, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.7 z flagą i komendą silnika Tieru. |
| Yang z potworów: ekwipunek lub ziemia | `admin_panel.py:20457` `/rates/yang_ground` | `app.py` `/manage/yang-ground`, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.8, flaga `m2_yang_ground`. |
| Obrona przed botami innych królestw | `admin_panel.py:20491` `/rates/owner_defence` | `app.py` `/manage/owner-defence`, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.9 z flagą i komendą silnika Tieru. |
| Kanały i rozdział botów | `admin_panel.py:20622` `/rates/channels` | `app.py:8111`, `templates/manage.html` | jest | wysoka | Bez zmian. |
| Wagi AI, decyzje i aktualne akcje | `admin_panel.py:1745–2000,20883,21120` `/ai`, `/decisions` | `app.py:7780,8051`, `templates/decisions.html` | częściowo | wysoka | Porównać wszystkie suwaki, limity i etykiety. |
| Polityka przedmiotów AI | `admin_panel.py:1603–1627,21344` `/ai/items` | `app.py:8067`, `templates/manage.html` | jest | wysoka | Zachować plik TSV odczytywany przez silnik. |
| Natychmiastowy start Wieży Demonów/Katakumb | `admin_panel.py:21292,21309` | `app.py` `/manage/tower-now`, `/manage/catacomb-now` | jest | średnia | Zachować istniejący tor plików silnika. |
| Zwolnienie zatrzymanych botów | `admin_panel.py:21326` | `app.py` `/manage/release-bots` | jest | wysoka | Zachować istniejący przełącznik hold. |
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

## Szczegółowa lista kontrolek, kolumn i API

Każdy wiersz poniżej jest osobną pozycją kontrolną. Linie odpowiadają źródłom Tieru odczytanym z kontenera, a nie kopii wyglądu. Przy ustawieniach AI stan „częściowo” znaczy, że nasz odczyt/zapis pliku wag zna klucz, lecz nie daje operatorowi tej samej kontrolki albo zakresu. Zmiany w pliku wag zachowują nieznane klucze, co chroni nowe opcje Tieru przed skasowaniem.

| Funkcja | Gdzie u Tieru (plik:linia / URL) | Gdzie u nas | Status | Przydatność | Plan |
|---|---|---|---|---|---|
| Panel AI: gęstość czatu Global `LIVE_CHAT` 0–200% | `admin_panel.py:8257–8262` `/ai` | `app.py` /manage/behavior, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.13, niezależnie od `CHAT`. |
| Panel AI: przełącznik napisów `CHAT` | `admin_panel.py:8253–8256` `/ai` | `templates/manage.html` zachowanie botów | jest | średnia | Bez zmian. |
| Panel AI: udział rzemieślników `CRAFTSMAN` 0–100% | `admin_panel.py:8274–8279` `/ai` | `app.py` /manage/behavior, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.14 z domyślną wartością 30. |
| Panel AI: szybkie księgi `BOOKS` | `admin_panel.py:8280–8295` `/ai` | `templates/manage.html` (tylko r40250) | jest | niska | Na mt2009 Tieru przeniósł to do rat; nie dublować. |
| Panel AI: noc `NIGHT` | `admin_panel.py:8297–8300` | `templates/manage.html` | jest | niska | Bez zmian. |
| Panel AI: cykl sesji `LIFE` | `admin_panel.py:8302–8308` | `templates/manage.html` | jest | wysoka | Bez zmian. |
| Panel AI: godziny na dobę `LIFE_HOURS` 0–24 | `admin_panel.py:8309–8312` | `templates/manage.html` | jest | wysoka | Zachować 0 = rytm domyślny. |
| Panel AI: realizm sesji `SESSION_REALISM` 0–100% | `admin_panel.py:8313–8318` | `app.py` /manage/behavior, `templates/manage.html` | jest | wysoka | Wdrożone w 1.114.12; 0 usuwa klucz z TSV. |
| Panel AI: wojny gildii `WARS`, długość `WAR_MINUTES`, odstęp `WAR_HOURS` | `admin_panel.py:8320–8345` | `templates/manage.html` | jest | średnia | W 1.114.15 skorygowano zakresy do 15/30 minut i 1–4 godzin. |
| Panel AI: limit zabójstw wojny `WAR_KILLS` | `admin_panel.py:8346–8353` | `app.py` /manage/behavior, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.15, zakres 0–1000. |
| Panel AI: Wieża Demonów `TOWER` i przycisk „teraz” | `admin_panel.py:8354–8359` | `templates/manage.html` | jest | średnia | Bez zmian. |
| Panel AI: Katakumby `CATACOMB` i przycisk „teraz” | `admin_panel.py:8360–8363` | `templates/manage.html` | jest | średnia | Bez zmian. |
| Panel AI: zakupy ItemShop `ISHOP` | `admin_panel.py:8364–8366` | `templates/manage.html` | jest | średnia | Bez zmian. |
| Panel AI: targowanie `HAGGLE` | `admin_panel.py:8362–8364` | `app.py` /manage/behavior, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.16, domyślnie włączone. |
| Panel AI: sprzedaż w sklepiku w mieście `SHOP_ROOM_SELL` | `admin_panel.py:8366–8371` | `app.py` /manage/behavior, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.17, domyślnie włączone. |
| Panel AI: przechowywanie wyjaśnień `EXPLAIN` | `admin_panel.py:8372–8386` | `app.py` ustawienie retencji decyzji | częściowo | średnia | Porównać zakres i lokalizację, nie utracić historii decyzji. |
| Panel AI: zakupy także w M2 `SHOP_M2` | `admin_panel.py:8387–8390` | `templates/manage.html` | jest | średnia | Bez zmian. |
| Panel AI: pasma podaży `SUPPLY_BANDS` | `admin_panel.py:8391–8397` | `app.py` /manage/behavior, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.18, domyślnie włączone. |
| Panel AI: skalowanie podaży `SUPPLY_SCALE` | `admin_panel.py:8397–8403` | `app.py` /manage/behavior, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.19, domyślnie wyłączone. |
| Panel AI: referencyjna liczba botów `SUPPLY_REF_BOTS` | `admin_panel.py:8400–8408` | `app.py` /manage/behavior, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.19, zakres 50–50 000, domyślnie 1000. |
| Panel AI: złomiarze `SCRAP`, odpoczynek `REST`, PvP między królestwami `KINGDOMPVP` | `admin_panel.py:8410–8430` | `templates/manage.html` | jest | średnia | Bez zmian. |
| Panel AI: minimalny poziom zwoju `SCROLL_FROM` | `admin_panel.py:8431–8440` | `app.py` czyta/zapisuje, brak suwaka | częściowo | niska | Silnik 2.2.83 (Patch 14) usunął tę opcję; nie przywracać martwej kontrolki. |
| Panel AI: Szkatułki Blasku `CHEST_OFF`, `CHEST`, `CHEST_STONE` | `admin_panel.py:8441–8460` | `templates/manage.html` | jest | średnia | Nie nadpisywać niestandardowych ustawień skrzynek. |
| Panel AI: zestawy PvP `PVP_SET` | `admin_panel.py:8461–8475` | `app.py` /manage/behavior, `templates/manage.html` | jest | średnia | Wdrożone w 1.114.20, domyślnie wyłączone. |
| Panel AI: udział zestawów `PVP_SET_SHARE` | `admin_panel.py:8476–8478` | `app.py`, `templates/manage.html` | jest | średnia | Zakres 0–100%, domyślnie 25. |
| Panel AI: minimalny poziom `PVP_SET_MIN_LEVEL` | `admin_panel.py:8479–8482` | `app.py`, `templates/manage.html` | jest | średnia | Zakres 1–120, domyślnie 30. |
| Panel AI: siła `PVP_SET_STRENGTH` | `admin_panel.py:8483–8491` | `app.py`, `templates/manage.html` | jest | średnia | Enum 0 niska, 1 normalna, 2 wysoka. |
| Panel AI: budżet `PVP_SET_BUDGET` | `admin_panel.py:8492–8498` | `app.py`, `templates/manage.html` | jest | średnia | Zakres 0–100%, domyślnie 20. |
| Panel AI: zestawy przeciw graczom `PVP_SET_VS_HUMAN` | `admin_panel.py:8499–8503` | `app.py`, `templates/manage.html` | jest | średnia | Domyślnie włączone tylko gdy zestawy PvP są aktywne. |
| Panel AI: wagi celów, reset do 100%, podpowiedzi | `admin_panel.py:8503–8534` | `app.py` `AI_WEIGHT_KEYS`, `templates/manage.html` | jest | wysoka | Zachować limity poszczególnych wag. |
| Panel AI: polityka przedmiotów TSV | `admin_panel.py:8535–8560` `/ai/items` | `templates/manage.html` | jest | wysoka | Zachować składnię i odczyt silnika. |
| Rynek: szukanie po nazwie/VNUM i odświeżanie migawki | `market_preview/page.py:188–200,415–430`; `__init__.py:312` | `templates/economy_shops.html` | częściowo | wysoka | Rozszerzyć wyszukiwanie na pojedyncze oferty, zachować limit zapytań. |
| Rynek: sortowanie (najnowsze, ceny, ulepszenie, poziom, bonusy, okazje) | `market_preview/rules.py:256–270`; `page.py:194–196` | brak | brak | wysoka | Zbudować sortowanie w naszej stronie rynku. |
| Rynek: cena min/max, cena za sztukę | `market_preview/page.py:205–212`; `rules.py:313–350` | brak | brak | wysoka | Portować parser `k/kk/kkk` i filtr jednostkowy. |
| Rynek: kategoria/podkategoria, ulepszenie +min/+max | `market_preview/page.py:213–218`; `rules.py:29–67` | brak | brak | wysoka | Portować klasyfikację z `item_proto`, nie z VNUM. |
| Rynek: klasa postaci i tylko pasujące do mojej postaci | `market_preview/page.py:219–223`; `rules.py:162–180,364` | brak | brak | średnia | Użyć `antiflag` i klasy, bez zgadywania. |
| Rynek: bonusy (do trzech), minimum bonusów, maksymalne wartości | `market_preview/page.py:224–232`; `rules.py:370–380` | brak | brak | średnia | Portować identyfikatory bonusów z migawki. |
| Rynek: średnie obrażenia, obrażenia umiejętności, kamienie | `market_preview/page.py:233–238`; `rules.py:313–350` | brak | brak | średnia | Portować dokładne pola przedmiotu. |
| Rynek: królestwo, bot/osoba, nick sprzedawcy i nazwa sklepu | `market_preview/page.py:239–245`; `rules.py:393–400` | `templates/economy_shops.html` częściowo | częściowo | wysoka | Dodać filtry bez naruszania listy popularności. |
| Rynek: okazje, ukrycie pomyłek cenowych, zakończone oferty | `market_preview/page.py:246–249`; `rules.py:505–656` | brak | brak | średnia | Portować wzór ceny referencyjnej z arkusza Tieru. |
| Rynek: strony 25/50/100, liczba wyników, chipy aktywnych filtrów | `market_preview/page.py:270,527–531` | brak | brak | średnia | Dodać paginację serwerową i reset filtrów. |
| Rynek: karta oferty (ikona, nazwa, sprzedawca, CH/mapa, cena, sztuki, bonusy, kamienie) | `market_preview/page.py:480–510`; `__init__.py:211–241` | `templates/economy_shops.html` tylko agregaty | częściowo | wysoka | Zbudować natywną listę ofert z naszej migawki. |
| Rynek: wykres historii cen wybranego przedmiotu | `market_preview/page.py:535–552`; `__init__.py:341–350` | `templates/economy_item.html` częściowo | częściowo | średnia | Porównać źródła punktów i zakres czasu. |
| Rynek: porównanie zaznaczonych ofert | `market_preview/page.py:270–275,580–600` | brak | brak | średnia | Dodać po kartach ofert. |
| Rynek: teleport do sklepu, koszt, status, historia teleportów | `market_preview/__init__.py:366–468` | `/api/admin/teleport-me` bez historii | częściowo | średnia | Nie przenosić opłaty bez weryfikacji wymagań serwera. |
| Mapa: filtry poziomów, map, auto-logów, heatmapa | `admin_panel.py:10050–12465` `/map` | `templates/maps.html`, dashboard | częściowo | średnia | Porównać każdą nakładkę z aktualnym podglądem; proporcje map są chronione. |
| Gildie: kolumny gildia/królestwo/klasa/poziom/członkowie/online/mistrz/siła/ranking/Z-R-P/EXP/wojna | `admin_panel.py:8012–8226` `/guilds` | `templates/guilds.html`, `guild.html` | częściowo | średnia | Rozbić statystyki członków i wojen na szczegóły profilu gildii. |
| Sezon: 9 kolumn i sortowanie tabeli | `admin_panel.py:7841–7908` `/season` | `templates/season.html` | częściowo | średnia | Zweryfikować realne dane sezonu; live GET przekroczył 15 s. |
| Eventy: wiersze harmonogramu, dni tygodnia, start/koniec, mapa, wartość, usunięcie | `admin_panel.py:7909–8011` `/events` | `templates/events.html` | częściowo | wysoka | Porównać zapisane typy eventów i walidacje zakresu. |
| Dropy: przegląd grup, edycja wierszy, podgląd zmiany, potwierdzenie | `admin_panel.py:26513–26878` `/drops/*` | brak | brak | średnia | Dopiero po sprawdzeniu fizycznych plików i atomowego zapisu. |
| Edytor SQL: struktura, historia, etykiety, formularz, dodanie/usunięcie wiersza | `editsql/__init__.py:53–110,269–1050` `/editsql/*` | link do Tieru | częściowo | niska | Wymaga osobnego audytu autoryzacji; nie kopiować ogólnego zapisu SQL. |

## Elementy świadomie nieprzenoszone

- HTML, CSS i JS klasycznego panelu Tieru: przenosimy zachowanie do komponentów `laka` i drugiego motywu, aby zachować skalowanie na telefonach.
- Alternatywne mechanizmy logowania i sesji konta gracza z `/account`: nasz panel jest administracyjny i nie powinien bez analizy otwierać drugiego portalu gracza.
- Bezpośrednie usuwanie danych SQL w celu skasowania przedmiotu bota: silnik musi wykonać `DELITEM` i ponownie sprawdzić przedmiot; modyfikacja DB pod aktywnym botem może rozjechać stan gry.
- Przycisk usuwania przedmiotu już wystawionego w sklepie offline: kontrakt `DELITEM` Tieru ogranicza się do `INVENTORY` i `EQUIPMENT`, a usuwanie aktywnej oferty bez osobnej komendy silnika mogłoby rozjechać sklep i stan bota.
- Automatyczne kopiowanie updatera i binariów klienta Tieru: to oddzielny tor dystrybucji, który mógłby nadpisać lokalne poprawki i zasoby serwera.
- Zastępowanie naszych map, natywnych okien `/player` i warstwy tooltipów wariantami Tieru: obecny układ spełnia wymagania proporcji, slotów i zoomu mobilnego.

## Kolejność dalszych prac

1. `DELITEM` z ekwipunku/wyposażenia, ze stanem kolejki i anulowaniem: wykonane w 1.114.6. Usuwanie ze sklepu wymaga nowej, potwierdzonej komendy silnika.
2. Brakujące ustawienia świata: szósty bonus, Yang i obrona wykonane w 1.114.7–1.114.9; bonus dropu, prędkość ruchu i `SESSION_REALISM` wykonane do 1.114.12. Następne są pozostałe kontrolki AI.
3. Filtry rynku, statusy kolejek, historie, potem edytor dropów i diagnostyka awarii.
4. Funkcje o niskiej przydatności tylko po potwierdzeniu ich źródeł danych i uprawnień.

Każda pozycja wymaga odrębnego commita, testów, sprawdzenia `laka` i drugiego motywu na desktopie i 375×812, patch bumpu z badge’em Codex przy zmianie widocznej dla użytkownika, tagu oraz wdrożenia dokładnie wypchniętego commita.
