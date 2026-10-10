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
| Usuwanie przedmiotu bezpośrednio ze sklepu offline | `admin_panel.py:23099–23107` (tylko INVENTORY/EQUIPMENT); silnik `ikarus_shop_manager.cpp:3651–3712` | brak bezpiecznej komendy kolejki | brak u obu | wysoka | IkarusShop usuwa ofertę własnym pakietem DB po sprawdzeniu właściciela, trybu edycji, odległości i miejsca na przedmiot; wymaga osobnej komendy silnika, nie `DELITEM` ani bezpośredniego SQL. |
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
| Eventy: harmonogramy, status, wywołanie | `admin_panel.py:7909,20995` `/events` | `app.py`, `templates/events.html`, `_laka_events.html` | u nas lepiej | wysoka | Oba panele mają te same sześć typów; nasz dodatkowo udostępnia kalendarz tygodniowy, status map i historię. Zachować istniejący planer. |
| Changelog/patchlog i sprawdzanie aktualizacji | `admin_panel.py:21540,21684,21712` | `app.py:7459`, `templates/changelog.html` | jest | średnia | Zachować wersjonowanie naszego panelu. |
| Aktualizator Tieru i pliki Playerbots | `admin_panel.py:21611,21742–21779` | `app.py:8051`, `templates/manage.html` | częściowo | średnia | Zachować istniejący updater i bezpieczny tor wdrożenia. |
| Pobieranie klienta, uruchamianie gry przez przeglądarkę | `admin_panel.py:21945,22049–22064` | brak | brak | niska | Osobna integracja; odłożyć do potwierdzenia dostępności klienta. |
| Raport awarii klienta i lista awarii | `admin_panel.py:22115,22172` `/crash-report`, `/admin/crashes` | diagnostyka serwera; brak klienta przeglądarkowego Tieru | brak | niska | Raporty pochodzą z klienta uruchamianego przez `/play`; bez takiego klienta nie powstają u nas. Nie wystawiać anonimowego zapisu plików bez źródła raportów. |
| Rejestracja konta, logowanie konta gracza, zmiana hasła/reset | `admin_panel.py:21899–21943,22191–22296` | `app.py:6875,7340` | częściowo | niska | Administracja kont już istnieje; oddzielny portal gracza wymaga przeglądu uprawnień. |
| Akcje GM i kody administracyjne | `admin_panel.py:23339,23442,23476,23559` | `app.py:6868,5681–6046` | częściowo | wysoka | Porównać każdą komendę i zachować kontrolę uprawnień. |
| Eksport Iwakura | `admin_panel.py:25802` | brak | brak | niska | Przenieść tylko gdy jest odbiorca danych. |
| Edytor dropów: lista plików, wyszukiwanie, grupa, dodanie, podgląd, zapis | `admin_panel.py:26513–26878` `/drops/*` | brak | brak | średnia | Zweryfikować ścieżki serwera i atomowość zapisu; nie kopiować HTML Tieru. |
| Dane klienta i pobieranie | `admin_panel.py:27175,27214` `/client-data` | brak | brak | niska | Zostawić po funkcjach administracji botami. |
| Podgląd rynku: oferty, szukanie i filtry | `market_preview/__init__.py:282,312,513–518` `/market`, `/market/api/offers` | `app.py` `/economy/offers`, `templates/economy_offers.html` | częściowo | wysoka | Działają kategorie, sprzedawca, cena, do trzech konkretnych bonusów, kamienie, właściciel sklepu, sortowanie bonusów i porównanie 2–3 ofert. Pozostają referencyjne okazje, filtry maksymalnych wartości i zakończonych ofert. |
| Podgląd rynku: teleport, status kolejki i historia | `market_preview/__init__.py:366–470` `/market/api/tp*` | `app.py:5040`, `templates/player.html` | częściowo | średnia | Porównać koszt i historię; zachować ochronę API. |
| Ustawienia rynku: koszt teleportacji | `market_preview/__init__.py:470–494` `/market/settings` | brak opłaty w `/api/admin/teleport-me` | brak | średnia | Tieru zapisuje wyłącznie `tp_cost`; nie pobierać opłaty w panelu, dopóki własna ścieżka teleportacji nie ma atomowego rozliczenia w silniku. |
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
| Panel AI: przechowywanie wyjaśnień `EXPLAIN` | `admin_panel.py:8372–8386` | `app.py` `/manage/explain-retention`, `templates/manage.html` | jest | średnia | W 1.114.33 dodano 0–30 dni z domyślnym brakiem klucza = 7 dni; zapis innych wag zachowuje `EXPLAIN`. |
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
| Rynek: szukanie po nazwie/VNUM i odświeżanie migawki | `market_preview/page.py:188–200,415–430`; `__init__.py:312` | `app.py:6720` `/economy/offers` i `templates/economy_offers.html` | u nas lepiej | wysoka | Wyszukiwanie po nazwie/VNUM działa od 1.114.22. Nasz widok czyta bieżące wiersze IkarusShop przy każdym żądaniu, więc ponowne otwarcie lub odświeżenie strony pobiera aktualny stan; osobna kolejka odbudowy migawki Tieru nie ma zastosowania. |
| Rynek: sortowanie (najnowsze, ceny, ulepszenie, poziom, bonusy, okazje) | `market_preview/rules.py:256–270`; `page.py:194–196` | `/economy/offers`: ceny, najnowsze, ulepszenie, poziom i liczba bonusów | częściowo | wysoka | W 1.114.32 dodano sortowania po ID, ulepszeniu i poziomie; w 1.114.43 po liczbie zwykłych bonusów, z pominięciem punktów średnich i umiejętności jak u Tieru. Sortowanie po okazjach wymaga ceny referencyjnej. |
| Rynek: cena min/max, cena za sztukę | `market_preview/page.py:205–212`; `rules.py:221–244,313–350` | `app.py` /economy/offers, `templates/economy_offers.html` | jest | wysoka | Wdrożone w 1.114.23 z parserem `k/kk/kkk` i filtrem jednostkowym. |
| Rynek: kategoria/podkategoria, ulepszenie +min/+max | `market_preview/page.py:213–218`; `rules.py:29–67` | `market_categories.py` i `/economy/offers`: kategorie, podkategorie i zakres ulepszeń | jest | wysoka | W 1.114.29 domknięto zakres `+0`–`+19`, odczytywany z nazwy proto jak u Tieru. |
| Rynek: wymagany poziom od/do | `market_preview/page.py:211–213`; `snapshot.py:407–416` | `market_categories.py` i `/economy/offers` | jest | średnia | W 1.114.31 dodano zakres 0–255 z pól limitu proto, zachowując pierwszeństwo drugiego limitu Tieru. |
| Rynek: klasa postaci i tylko pasujące do mojej postaci | `market_preview/page.py:219–223`; `rules.py:162–180,364` | `/economy/offers` filtr klasy z `antiflag` i umiejętności księgi | częściowo | średnia | W 1.114.30 dodano wybór klasy; „tylko pasujące do mojej postaci” wymaga ustalenia aktywnej postaci konta. |
| Rynek: bonusy (do trzech), minimum bonusów, maksymalne wartości | `market_preview/page.py:224–232`; `rules.py:370–380` | `/economy/offers` minimum zwykłych linii i trzy konkretne bonusy | częściowo | średnia | W 1.114.35 dodano minimum 1–5 linii; w 1.114.39 trzy punkty z minimalną wartością. Liczenie maksymalnych wartości pozostaje. |
| Rynek: średnie obrażenia, obrażenia umiejętności, kamienie | `market_preview/page.py:233–238`; `rules.py:313–350` | `/economy/offers` zakresy SR/UM i kamienie | jest | średnia | W 1.114.36 dodano zakresy 0–200 według punktów 122/121; w 1.114.37 filtr kamieni 28000–28999 dla broni i zbroi. |
| Rynek: królestwo, bot/osoba, nick sprzedawcy i nazwa sklepu | `market_preview/page.py:239–245`; `rules.py:393–400` | `app.py` /economy/offers, `templates/economy_offers.html` | jest | wysoka | Królestwo i bot/gracz od 1.114.22, nick oraz nazwa sklepu od 1.114.24. |
| Rynek: okazje, ukrycie pomyłek cenowych, zakończone oferty | `market_preview/page.py:246–249`; `rules.py:505–656` | brak | brak | średnia | Portować wzór ceny referencyjnej z arkusza Tieru. |
| Rynek: strony 25/50/100, liczba wyników, chipy aktywnych filtrów | `market_preview/page.py:270,527–531` | `app.py` /economy/offers: 25/50/100, licznik ofert i chipy | jest | średnia | W 1.114.34 dodano usuwanie pojedynczego filtra oraz czyszczenie wszystkich; zmiana filtra wraca na pierwszą stronę. |
| Rynek: karta oferty (ikona, nazwa, sprzedawca, CH/mapa, cena, sztuki, bonusy, kamienie) | `market_preview/page.py:480–510`; `__init__.py:211–241` | `app.py` `/economy/offers`, `templates/economy_offers.html` | jest | wysoka | W 1.114.21 dodano sprzedawcę, sklep, mapę/CH, ilość i ceny; w 1.114.44 dodano atrybuty przedmiotu i osadzone kamienie. Porównanie ofert jest osobną pozycją niżej. |
| Rynek: wykres historii cen wybranego przedmiotu | `market_preview/page.py:535–552`; `__init__.py:341–350` | `templates/economy_item.html` częściowo | częściowo | średnia | Porównać źródła punktów i zakres czasu. |
| Rynek: porównanie zaznaczonych ofert | `market_preview/page.py:270–275,580–600` | `templates/economy_offers.html` | jest | średnia | W 1.114.46 dodano porównanie 2–3 ofert widocznych na bieżącej stronie: ceny, ceny jednostkowej, ilości, sprzedawcy, bonusów i kamieni. Wybór jest lokalny dla aktualnej listy, aby nie pokazywać nieaktualnych cen z innych stron. |
| Rynek: teleport do sklepu, koszt, status, historia teleportów | `market_preview/__init__.py:366–468` | `/api/admin/teleport-me` bez historii | częściowo | średnia | Nie przenosić opłaty bez weryfikacji wymagań serwera. |
| Mapa: filtry poziomów, map, auto-logów, heatmapa | `admin_panel.py:10050–12465` `/map` | `templates/maps.html`, dashboard | częściowo | średnia | Porównać każdą nakładkę z aktualnym podglądem; proporcje map są chronione. |
| Gildie: kolumny gildia/królestwo/klasa/poziom/członkowie/online/mistrz/siła/ranking/Z-R-P/EXP/wojna | `admin_panel.py:8012–8226` `/guilds` | `templates/guilds.html`, `guild.html` | częściowo | średnia | Rozbić statystyki członków i wojen na szczegóły profilu gildii. |
| Sezon: 9 kolumn i sortowanie tabeli | `admin_panel.py:7841–7908,21401–21477` `/season` | `app.py` `/season`, `templates/season.html` | u nas lepiej | średnia | W 1.114.47 dodano zgony `DEAD_BY_NPC` i poziom konia, a w 1.114.48 rekordy konia oraz Yang wraz z właścicielem. Nasz sezon ma dodatkową kolumnę potworów, filtry kategorii i osobny widok wszechczasów. Tabela przewija się w swoim kontenerze na telefonie. |
| Eventy: wiersze harmonogramu, dni tygodnia, start/koniec, mapa, wartość, usunięcie | `admin_panel.py:7909–8011` `/events` | `templates/events.html`, `_laka_events.html` | u nas lepiej | wysoka | Te same pola edytuje tygodniowy kalendarz w obu motywach; brak funkcji do przeniesienia. |
| Dropy: przegląd grup, edycja wierszy, podgląd zmiany, potwierdzenie | `admin_panel.py:26513–26878` `/drops/*` | brak | brak | średnia | Dopiero po sprawdzeniu fizycznych plików i atomowego zapisu. |
| Edytor SQL: struktura, historia, etykiety, formularz, dodanie/usunięcie wiersza | `editsql/__init__.py:53–110,269–1050` `/editsql/*` | link do Tieru | częściowo | niska | Wymaga osobnego audytu autoryzacji; nie kopiować ogólnego zapisu SQL. |

## Trasy pakietów poza głównym `admin_panel.py`

Te trasy rejestrują się przez `add_url_rule`, więc nie pojawiają się w wyszukiwaniu dekoratorów `@app.route`. Poniższy spis uzupełnia tabelę funkcji; status dotyczy zachowania, nie identyczności adresu URL.

| Funkcja | Gdzie u Tieru (plik:linia / URL) | Gdzie u nas | Status | Przydatność | Plan |
|---|---|---|---|---|---|
| Strona rynku | `market_preview/__init__.py:513` `/market` | `/economy/offers`, `/economy/shops` | częściowo | wysoka | Oferty na żywo, filtry i porównanie są dostępne; pozostała cena referencyjna oraz okazje. |
| API ofert rynku | `market_preview/__init__.py:514` `/market/api/offers` | serwerowo renderowane `/economy/offers` | częściowo | wysoka | Porównanie działa na bieżącej liście; osobnego API nie trzeba dublować. Pozostałe obliczenia okazji wymagają potwierdzonej ceny referencyjnej. |
| Zlecenie teleportu | `market_preview/__init__.py:515` `/market/api/tp` | `/api/admin/teleport-me` | częściowo | średnia | Zweryfikować parametry, uprawnienia i wyniki kolejki. |
| Stan teleportu | `market_preview/__init__.py:516` `/market/api/tp/<qid>` | stan komendy administracyjnej | częściowo | średnia | Powiązać z identyfikatorem zlecenia przed wdrożeniem. |
| Historia teleportów | `market_preview/__init__.py:517` `/market/api/tp_history` | brak widoku historii | brak | średnia | Portować po weryfikacji źródła kolejki. |
| Koszt teleportu | `market_preview/__init__.py:518` `/market/settings` | brak | brak | średnia | Zachować wyłączenie do atomowego pobrania Yang w silniku. |
| Logowanie edytora SQL | `editsql/__init__.py:1264` `/editsql/login`, `/editsql/logout` | link do Tieru | częściowo | niska | Nie wprowadzać drugiego modelu sesji bez projektu uprawnień. |
| Strona edytora SQL i nazwa | `editsql/__init__.py:1266–1269` `/editsql`, `/editsql/`, `/editsql/api/name` | link do Tieru | częściowo | niska | Pozostawić po przeglądzie uprawnień. |
| Struktura baz i tabel | `editsql/__init__.py:1270–1272` `/editsql/structure[/<db>/<table>]` | brak natywnego widoku | brak | średnia | Rozważyć osobny, tylko odczytowy podgląd. |
| Historia, plan, etykiety | `editsql/__init__.py:1273–1275` `/editsql/history`, `/editsql/apply`, `/editsql/labels` | brak | brak | niska | Wymaga audytu zapisów i uprawnień. |
| Formularze rekordów | `editsql/__init__.py:1276–1282` `/editsql/<module_id>[/new|/delete|/<db>/<pk>]` | brak | brak | niska | Nie kopiować ogólnej mutacji SQL do panelu administracji botów. |

## Elementy świadomie nieprzenoszone

- HTML, CSS i JS klasycznego panelu Tieru: przenosimy zachowanie do komponentów `laka` i drugiego motywu, aby zachować skalowanie na telefonach.
- Alternatywne mechanizmy logowania i sesji konta gracza z `/account`: nasz panel jest administracyjny i nie powinien bez analizy otwierać drugiego portalu gracza.
- Bezpośrednie usuwanie danych SQL w celu skasowania przedmiotu bota: silnik musi wykonać `DELITEM` i ponownie sprawdzić przedmiot; modyfikacja DB pod aktywnym botem może rozjechać stan gry.
- Przycisk usuwania przedmiotu już wystawionego w sklepie offline: `DELITEM` Tieru ogranicza się do `INVENTORY` i `EQUIPMENT`, a `RecvShopRemoveItemClientPacket` w silniku wymaga trybu edycji sklepu, bliskości właściciela i synchronizacji przez pakiet IkarusShop; bez osobnej komendy kolejki panel nie może bezpiecznie wykonać tej operacji.
- Automatyczne kopiowanie updatera i binariów klienta Tieru: to oddzielny tor dystrybucji, który mógłby nadpisać lokalne poprawki i zasoby serwera.
- Anonimowy `/crash-report` i JSON z `/admin/crashes` z klienta Tieru: nasz panel nie udostępnia jego `/play`, więc raporty nie miałyby źródła; publiczny zapis plików bez odbiorcy byłby zbędny.
- Opłata `tp_cost` w `/market/settings`: nasza komenda teleportacji nie ma potwierdzonego, atomowego pobrania Yang w silniku, więc samo pole ustawienia obiecywałoby działanie, którego nie można zagwarantować.
- Zastępowanie naszych map, natywnych okien `/player` i warstwy tooltipów wariantami Tieru: obecny układ spełnia wymagania proporcji, slotów i zoomu mobilnego.

## Kolejność dalszych prac

1. `DELITEM` z ekwipunku/wyposażenia, ze stanem kolejki i anulowaniem: wykonane w 1.114.6. Usuwanie ze sklepu wymaga nowej, potwierdzonej komendy silnika.
2. Brakujące ustawienia świata: szósty bonus, Yang i obrona wykonane w 1.114.7–1.114.9; bonus dropu, prędkość ruchu i `SESSION_REALISM` wykonane do 1.114.12. Następne są pozostałe kontrolki AI.
3. Filtry rynku, statusy kolejek, historie, potem edytor dropów i diagnostyka awarii.
4. Funkcje o niskiej przydatności tylko po potwierdzeniu ich źródeł danych i uprawnień.

Każda pozycja wymaga odrębnego commita, testów, sprawdzenia `laka` i drugiego motywu na desktopie i 375×812, patch bumpu z badge’em Codex przy zmianie widocznej dla użytkownika, tagu oraz wdrożenia dokładnie wypchniętego commita.
