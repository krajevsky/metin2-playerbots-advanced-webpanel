> Odznaka `via` na dole każdego wpisu pokazuje, kto/co stoi za daną zmianą. Praca z asystą AI (Claude albo Codex) dostaje formę `![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)` albo `![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)` — w panelu "Seban" dostaje animowany, przelewający się kolor + gwiazdkę. Kod wniesiony wprost przez Tieru (bez asysty AI, np. przy łączeniu funkcji z jego panelu) dostaje samo `![via Tieru](https://img.shields.io/badge/via-Tieru-f2c34d)`, bez "by".

## 2026-09-26 · 1.88.0 · Kartoteka misji na karcie postaci

- **Nowa sekcja "📋 Kartoteka misji" na `/player/`**, w stylu pasków PŻ/PM/EXP: pokazuje aktualny postęp w konkretnych, śledzonych misjach bota — Biolog ("Zęby Orka: X/10 oddanych", albo "misja N z 7" dla wcześniejszych etapów), Koń bojowy ("X/100 pokonanych" na pustynnej próbie) i Polowanie ("Polowanie nr N: X/Y {nazwa potwora} pokonanych").
- Progi zweryfikowane wprost w skryptach questów i silniku (`collect_quest_lv30.quest`, `playerbot_battle_horse.h`, `hunting_data.lua`), nie zgadywane — łącznie z pełną tabelą 79 etapów polowania przepisaną z silnika, żeby liczyć realny cel dla każdej misji.
- Sekcja pokazuje się tylko wtedy, gdy dana misja jest faktycznie w toku (nie zaczęta lub ukończona = nic do pokazania) — bez zmyślania zerowego postępu tam, gdzie danych po prostu nie ma.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-26 · 1.87.0 · Nowa strona: Osobowości botów

- **Gracze i boty → Osobowości botów** — nowa lista wszystkich aktualnie zalogowanych botów, filtrowalna po osobowości (kafelki z licznikami, jak na Bazie przedmiotów) i przeszukiwalna po nicku, ucięta do 200 wyników (posortowana jak ranking: poziom, potem EXP).
- Każdy wiersz: flaga królestwa, portret klasy, nick, poziom, pasek EXP, **kolorowana nazwa osobowości**, aktualna czynność bota i mapa, na której teraz jest — cały wiersz klikalny, prowadzi prosto do karty postaci.
- Osobowość/czynność/mapa są odczytywane z live'owego statusu rdzenia, więc lista pokazuje tylko boty aktualnie online (offline nie mają tych danych do pokazania — nigdy nie trafiają do bazy).

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-26 · 1.86.0 · Dashboard mapy świata z diagramami i stanem respawnów

- **Mapa świata botów na szerokich ekranach otrzymała trzy niezależne karty danych dla aktualnie wybranej mapy:** rozkład botów na kanałach, konfigurację respawnów oraz dominację królestw. Nie zmieniają wielkości mapy, rankingu ani listy aktywności; na węższych ekranach cały zestaw nadal jest dostępny pod jednym przyciskiem.
- **Kanały i królestwa są pokazane jako wykresy kołowe** z procentem dominującej grupy oraz legendą liczbową. Karty dostosowują kolory do motywu panelu i korzystają z tego samego ciemnobrązowego tła co ranking oraz aktywności mapy.
- **Karta respawnów opisuje faktyczny stan konfiguracji:** globalny procent czasu podstawowego albo własny czas mapy w sekundach. Techniczny zapis `reset s` nie jest już widoczny.
- **Usprawniono sterowanie liczbą botów w Zarządzaniu:** suwak i pole liczbowe pozostają zsynchronizowane, a stara, zdublowana sekcja respawnów została usunięta, ponieważ ma już własną stronę `/respawns`.
- **Czat na żywo otrzymał prostsze, działające filtry widoku**, bez nieaktywnych kart, które sugerowały funkcję niedostępną w danych gry.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-26 · 1.85.0 · Ranking Broń/Zbroja liczy realną moc, nie tylko "+N"

- **Rankingi "Broń" i "Zbroja" wystawiały na górę cokolwiek miało wyższy "+N", niezależnie od tego, na jaki poziom w ogóle jest ten przedmiot** — +9 na przedmiocie z niskiego poziomu potrafiło wyprzedzić +7 na dużo lepszej bazie. Sprawdzone bezpośrednio w bazie: same wartości ataku/obrony w tabeli przedmiotów okazały się niespójne między rodzinami (część zbroi ma zapisane rosnące obrażenia/obronę per "+", większość ma płaskie liczby identyczne od +0 do +9), więc nie dało się na nich polegać jako mierniku mocy.
- Znaleziono spójny, wiarygodny wskaźnik: **wymagany poziom postaci przedmiotu** rośnie razem z jego prawdziwą jakością bazową w każdej sprawdzonej rodzinie. Ranking liczy teraz `poziom_wymagany × 10 + poziom_ulepszenia`, więc zbroja na 34 poziom +7 wyprzedza zbroję na 18 poziom +9, dokładnie jak powinno być. Wynik w tabeli pokazuje wprost, jaki poziom wymaga dany przedmiot, żeby kolejność była zrozumiała na pierwszy rzut oka.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-26 · 1.84.0 · Aktualizacja do 2.2.19, naprawa suwaka botów, audyt vs panel Tieru

- **Playerbots zaktualizowane do 2.2.19** (z 2.2.9), przez oficjalny, odizolowany aktualizator panelu — pełny backup bazy (>1,2 GB) zrobiony automatycznie przed czymkolwiek. Panel webowy (ten) pozostał nietknięty, zgodnie z ustawieniem.
- **Naprawiony realnie zepsuty suwak "Docelowa liczba botów" w Zarządzaniu.** Nigdy nie działał — odwoływał się do mechanizmu (`m2-botcount`) który nie istnieje i nigdy nie istniał w obrazie gry. Naprawione tak, jak realnie robi to silnik: zmiana `PLAYERBOT_AUTOSPAWN_COUNT` w `.env` i pełne odtworzenie kontenera gry (silnik czyta tę liczbę tylko raz, przy starcie od zera — potwierdzone w kodzie C++ i własnym changelogu Tieru: "Zmiana suwaka działa dopiero po restarcie serwera"). Ten sam, już sprawdzony mechanizm co plan wejścia spóźnionych botów.
- **Pełny audyt panelu Tieru (port 7788) w wersji dołączonej do 2.2.19** vs nasz panel — wynik: nasz panel już pokrywa niemal wszystko po stronie admina (mapa na żywo, ranking botów, wagi zachowań, teleport do bota, historia ekwipunku, sklepy offline, magazyn, sezon, restart z planem wejścia, aktualizator) — Tieru ma dodatkowo strony rejestracji/konta/pobierania klienta, które nie mają zastosowania w tym single-operatorskim wdrożeniu.
- **Dodana jedna realnie brakująca funkcja: "📦 Polityka przedmiotów"** w Zarządzaniu — reguły keep/stall/merchant/drop per VNUM albo typ przedmiotu, edytowane jako zwykły tekst, odczytywane przez rdzeń na żywo (bez restartu). Ta sama ścieżka co wagi zachowań (`/opt/m2spool`), potwierdzona w kodzie silnika (`playerbot_config.h`).

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-26 · 1.83.0 · Własny kursor panelu + wybór w Zarządzaniu

- **Panel ma teraz własny, niestandardowy kursor** (dostarczony przez operatora) zamiast domyślnego kursora systemowego — widoczny na każdej stronie, linki i przyciski dalej pokazują zwykłą "łapkę" przy najechaniu.
- **Nowa opcja w Zarządzanie → Wygląd, monitoring i dostęp: "Kursor"** — "Nasz (domyślny)" albo "Systemowy". Domyślnie włączony jest nasz kursor; zmiana widoczna po odświeżeniu strony (tak samo jak zmiana kolorystyki).

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-26 · 1.82.0 · Ikony ulepszeń + naprawa lagów w bazie przedmiotów

- **Wiadomości ze świata: ikonka zamiast podpisu przy ulepszeniach.** Zamiast tekstu "zwojem (Zwój Błogosławieństwa)" pokazuje się teraz ikona faktycznie użytego przedmiotu (zwój błogosławieństwa, zwój boga smoków, podręcznik kowala — cokolwiek trafi do `refinelog.setType` jako `SCROLL:<vnum>`, rozpoznawane automatycznie), a przy zwykłym ulepszeniu u kowala — własna ikonka operatora.
- **Naprawiony realny problem z laggami przy wpisywaniu w "Bazie przedmiotów".** Stara wersja renderowała od razu wszystkie 6001 przedmiotów do strony i przy każdym naciśnięciu klawisza przeszukiwała wszystkie te węzły w przeglądarce od nowa, bez żadnego opóźnienia — przy szybkim pisaniu przeglądarka częściowo to znosiła, ale wolne, pojedyncze naciśnięcia klawiszy płaciły pełny koszt za każdym razem (stąd spowolnienie całego komputera). Wyszukiwanie pyta teraz serwer (z opóźnieniem 300 ms), zwracając tylko pasujące przedmioty zamiast przeglądać wszystko lokalnie.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-25 · 1.81.0 · Sposób ulepszenia w wiadomościach ze świata

- **"Wiadomości ze świata" i ticker na dashboardzie pokazują teraz, jak dane ulepszenie powstało** — u kowala czy zwojem (z nazwą zwoju, np. "Zwój Błogosławieństwa"). Log gry (`log.log`) nigdy tego nie zapisywał w treści zdarzenia, ale silnik ma osobną tabelę `log.refinelog` z dokładnie tą informacją (`setType`: POWER/GUILD/DEVILTOWER/SCROLL:vnum) — znaleziona w kodzie silnika (`LogManager::RefineLog`, `char_item.cpp`) i podłączona.
- Przy okazji rzadkie ulepszenia (+7/+8/+9) są teraz czytane z tej mniejszej, szybszej tabeli (280 tys. wierszy) zamiast z ogromnego `log.log` (6,4 mln) — trochę mniej pracy dla synchronizacji w tle.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-25 · 1.80.0 · Prawdziwa przyczyna wolnego dashboardu

- **Znaleziono i naprawiono właściwe źródło długiego ładowania dashboardu** (poprzednia poprawka tickera pomogła, ale to nie było główne opóźnienie). Sprofilowałem stronę zapytanie po zapytaniu: trzy rankingi w karuzeli — "Pomyślne ulepszenia", "Skuteczność ulepszeń" i "Ryby" — liczyły pełną agregację po 200-300 tysiącach wierszy logu przy KAŻDYM wejściu na dashboard (1,3 s + 1,8 s + 1,0 s = większość z tych 5-6 sekund).
- Te trzy rankingi w karuzeli dostały teraz własny, mały cache (odświeżany co najwyżej raz na 5 minut, tak jak wiadomości ze świata) — reszta panelu (w tym pełny `/rankings`) dalej liczy je na żywo, bez zmian. Efekt: pierwsze wejście po restarcie panelu nadal płaci pełną cenę raz, każde kolejne to ~0,6-0,7 s zamiast ~5-6 s.
- Po drodze złapany i naprawiony realny bug w cache'u z 1.79.0: `web_seban_settings.value` jest celowo małe (VARCHAR 255, na proste ustawienia), więc zapis JSON-a z rankingiem się ucinał po cichu i cache nigdy faktycznie nie działał — nowy cache ma własną, poprawnie rozmiarowaną tabelę.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-25 · 1.79.0 · "Czat na żywo" → "Wiadomości", nowa oś czasu świata

- **"Czat na żywo" w nawigacji przerobione na sekcję "Wiadomości"** z dwiema podkategoriami: dotychczasowy **Czat na żywo** oraz nowe **Wiadomości ze świata** (`/world-feed`) — oś czasu w stylu starych statusów z IP.Board / kart Twittera-X: awatar klasy, flaga królestwa, nick, plakietka rangi ulepszenia (+7/+8/+9, złota poświata dla +9) albo mistrzostwa/rzadkiego znaleziska, ikonka przedmiotu przy ulepszeniach, dzielone na "Dziś"/"Wczoraj"/datę, z przyciskiem "Załaduj starsze wydarzenia" (pełna historia z 14 dni, nie tylko to co mieści się w tickerze na dashboardzie).
- **Po drodze naprawiony realny problem z wydajnością**, który dotykał też starego tickera: `log.log` (6,4 mln wierszy) nie ma indeksu po czasie, więc każde pytanie "co się wydarzyło od X" kosztowało 5-7 sekund, niezależnie od okna czasowego (sprawdzone przez EXPLAIN: silnik i tak skanuje ~1,7 mln wierszy). Zamiast ruszać tabelę silnika (MyISAM, ryzykowna przebudowa na żywo) panel dostał własną, małą, zaindeksowaną kopię (`web_seban_news_event`), dociąganą przyrostowo co najwyżej raz na 5 minut — dashboard i `/world-feed` zawsze czytają tylko z niej, więc są szybkie.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-25 · 1.78.0 · Wycofano ekran ładowania

- Wycofano pierwsze-wejście ekranu ładowania z 1.77.0 (art klienta + pasek postępu) — nie skracał realnego czasu ładowania dashboardu, a wizualnie nie spełnił oczekiwań operatora. Usunięte pliki graficzne i cały kod, zero pozostałości.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-25 · 1.76.0 · Trwały odczyt czatu botów na /live-chat

- **Naprawiono efekt "wiadomość pojawia się i zaraz znika" na `/live-chat`.** Przyczyna: wiadomości Playerbotów (Wołaj/ulepszenia) były czytane z ostatnich 384 KB rosnącego na żywo pliku syslog rdzenia — przy ~1200 zalogowanych botach jeden rdzeń dopisuje do tego pliku ok. 45 KB/s, więc wiadomość wypadała z tego okna w mniej niż 10 sekund (żadnej rotacji logów, która mogłaby to ograniczyć, też nie ma).
- Teraz panel pamięta pozycję bajtową w każdym pliku syslog (`web_seban_chat_offset`) i przy każdym odświeżeniu (co 4 s) czyta wyłącznie dopisane od ostatniego razu bajty, zapisując dopasowane wiadomości trwale w `web_seban_bot_chat_log` (przycinane do najnowszych 2000). Wiadomość zostaje widoczna tak długo, jak długo ma być, niezależnie od tego, ile danych rdzeń dopisał do logu w międzyczasie — bez restartu silnika, bez skanowania całych, wielogigabajtowych plików.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-25 · 1.75.0 · Czat na żywo

- **Nowa sekcja `/live-chat`** pokazuje na bieżąco wiadomości Wołaj oraz globalny kanał Handel, korzystając z natywnego dziennika `log.chat_log` MT2009 — bez zmiany silnika i bez restartu serwera.
- Każdy wpis ma dokładny czas, flagę królestwa, portret klasy, nick prowadzący do karty postaci oraz oczyszczoną treść bez technicznych znaczników formatu klienta.
- Widok ma metinową ramę, filtry kanałów i automatyczne odświeżanie co cztery sekundy; pozostaje wyłącznie podglądem, więc nie wysyła treści do gry.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)
## 2026-09-25 · 1.74.0 · Respawny MT2009 na żywo

- **Nowa sekcja `/respawns`** daje osobne, czytelne sterowanie tempem i liczebnością świata: Metiny z bossami oraz zwykłe potwory mają własne ustawienia.
- **Globalne ustawienia działają na żywo przez natywną kolejkę `web_admin.quest` MT2009:** panel czeka na potwierdzenie rdzenia i pokazuje eleganckie powiadomienie AJAX bez przeładowania strony. Wartości są też zapisywane, więc przetrwają następny restart.
- **Dokładny czas dla pojedynczej mapy** pozostał dostępny jako osobne ustawienie plikowe. Interfejs uczciwie oznacza, że po jego zapisaniu rdzenie są krótko odtwarzane; puste pole przywraca czas dostarczony z wydaniem Tieru.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-24 22:30 CEST · 1.73.0 · Tygodniowy kalendarz eventów i baner wszystkich motywów

- **Harmonogram eventów na `/events` jest teraz interaktywnym kalendarzem tygodniowym:** siedem dni, format 24-godzinny, kliknięcie wolnej godziny dodaje wydarzenie, a kliknięcie bloku otwiera jego edycję. Kalendarz przewija się od razu w okolice najbliższego zaplanowanego wydarzenia.
- **Bloki wydarzeń są zwarte i czytelne:** pokazują dużą ikonę, godziny oraz wartość bonusu; używają kolorów zależnych od rodzaju eventu. Ujednolicono też wysokość przycisków edytora i wygląd paska przewijania zgodny z aktywnym motywem.
- **Karuzela rankingów na dashboardzie nie przełącza się samoczynnie bez zgody:** przełącznik `Auto` pozwala włączyć automatyczną rotację na życzenie.
- **Animowany baner Szamanki działa dla każdego motywu:** Empire, Ember, Forest i Ocean otrzymują własne kolory tła oraz dopasowany efekt tytułu. Szamanka przebiega przez baner, a następnie pozostaje w jego prawej części; naprawiono też jej pozycjonowanie i tor biegu.
- **Akcje AJAX zachowują działanie formularzy eventów i wyszukiwarek**, więc przyciski „Aktywuj teraz” oraz zapytania do sklepów przekazują właściwe dane po zmianie panelu na odświeżanie w tle.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-23 19:34 CEST · 1.72.0 · Baner Empire i pełny indeks komend MT2009

- **Baner Empire dostał krótkie, ogniste wejście nazwy serwera:** po odsłonięciu przez przebiegającą Szamankę tytuł przez kilka sekund żarzy się płomieniem, a następnie płynnie wraca do zwykłej formy.
- **Stojąca Szamanka jest większa:** wypełnia więcej wysokości banera, wykorzystując wolną przestrzeń nad głową i pod nogami.
- **`/gm-commands` zawiera teraz indeks 296 komend z faktycznego `cmd_info[]` MT2009 r41023 / Playerbots 2.x**, pogrupowany według uprawnień GM i z nazwami procedur silnika. Zachowano dawną listę poradnikową; usunięto wyłącznie błędne `/setsk 130`, zastąpione potwierdzonym `/horse_level <nick> <poziom>`.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-23 18:50 CEST · 1.71.0 · Animowany baner Szamanki w motywie Empire

- **Wejście na Dashboard w motywie Empire zaczyna się od krótkiej sceny:** Szamanka przebiega przez baner od lewej do prawej w 2,2 s, a cofająca się maska odsłania nazwę serwera i opis bez naruszania ich personalizacji.
- **Po biegu Szamanka zostaje przy prawej krawędzi:** animacja `general_wait` zapętla się jako spokojny, dekoracyjny element banera.
- Oba GIF-y są częścią panelu (`static/shaman_run.gif`, `static/shaman_idle.gif`); przy systemowym ograniczeniu ruchu baner od razu pokazuje stojącą postać.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-23 12:05 CEST · 1.70.0 · Królestwo na /players + boty online per królestwo

- **Kolumna "Królestwo" na `/players`** — flaga i nazwa (Shinsoo/Chunjo/Jinno) przy każdej postaci.
- **Dashboard, "Stan serwera":** usunięte "Jeździectwo · śr." i "Jeździectwo · max" (mało kto na nie patrzył), w ich miejsce "Zalogowane boty" z podziałem na trzy królestwa — trzy flagi z liczbą botów online przy każdej, żeby od razu było widać proporcje.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-23 11:20 CEST · 1.69.0 · Ryby, ruda i bossy w podsumowaniu dnia

- **"Podsumowanie dnia" liczy teraz też wyłowione ryby, wykopaną rudę i pokonanych bossów** (obok istniejących +9/Metinów/eventów). Ryby z `log.fish_log`, bossy z `log.log` (jak Metiny), a ruda z `log.money_log(type='DROP')` odfiltrowanego do 19 vnumów surowej rudy, które faktycznie wydaje `mining.cpp` (50601–50619) — bo `money_log` typu DROP loguje też zwykłe łupy z potworów, więc bez filtra po vnumie liczyłoby wszystko, nie tylko górnictwo.
- Stare wpisy sprzed tej zmiany po prostu nie mają tych trzech liczb (pokazują "—"), nowe naliczają się od najbliższej granicy dnia.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-23 10:02 CEST · 1.68.0 · 10 nowych rankingów z player_special_flag

- Odkrycie z 1.67.0 (tabela `player_special_flag`, źródło panelu Y) posłużyło teraz do przebudowy rankingów: 10 nowych kategorii na `/rankings`, wszystkie all-time i dokładne (nie 7-dniowe okno jak dotychczasowe "Bossy"/"Metiny" z `log.log`) — Rekord obrażeń (zwykłe/konno/umiejętność), Zdobyty Yang łącznie, Yang ze sprzedaży u NPC, Zabite potwory łącznie, Pokonane minibossy, Pokonani gracze PVP (łącznie, nie tylko 7 dni), Wygrane pojedynki, Wykopane rudy.
- Dwie z nich — Rekord obrażeń i Zdobyty Yang łącznie — trafiły też do karuzeli na dashboardzie, obok istniejących.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-23 09:15 CEST · 1.67.0 · Prawdziwy panel "Statystyki" (Y) na /player/

- **Znaleziono realne, serwerowe źródło całego okna "Statystyki" (klawisz Y w grze) i podłączono je w pełni na `/player/`.** Wcześniejszy audyt tego panelu (na `log.log`) uznał większość pól za niezapisywane server-side — operator słusznie się z tym nie zgodził ("gra nie ma prawa brać tego znikąd, to działa niezależnie od tego gdzie się zalogujesz"). Właściwym źródłem okazała się osobna tabela silnika `player.player_special_flag` (pid, flag, value), zapisywana przy każdej zmianie przez `CHARACTER::AddPlayerStat`/`SetSpecialFlagSave` (game/src/char.cpp, char_battle.cpp, char_item.cpp, mining.cpp, shop_manager.cpp) — kompletnie pominięta przez wcześniejszy audyt, bo ten patrzył tylko na `log.log`.
- Panel pokazuje teraz naprawdę wszystko, co silnik faktycznie liczy: zabite potwory (ogółem), pokonane bossy i minibossy osobno, zniszczone kamienie Metin, pokonanych graczy wrogiego królestwa, wygrane pojedynki, wykopane rudy, złowione ryby, śmierci (łącznie/od potworów/od graczy), trzy rekordy obrażeń (zwykłe/konno/umiejętność), udane i spalone ulepszenia, zdobyty Yang łącznie oraz Yang ze sprzedaży u NPC.
- Cztery pola z panelu Y — ukończone lochy, zebrane kwiaty, otwarte skrzynie, ukończone księgi misji — mają zdefiniowaną w silniku "szufladkę" na wartość (`PLAYER_STATS_DUNGEON/HERBALISM/CHEST/QUESTBOOK_FLAG`), ale żaden kod gry nigdy jej nie zwiększa na tej wersji serwera — potwierdzone przeszukaniem całego `game/src`, nie zgadywane. Panel jasno to teraz opisuje, zamiast milczeć.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-23 07:28 CEST · 1.66.0 · Ranking "Wyłowione ryby"

- **Nowy ranking na `/rankings` i w karuzeli na dashboardzie: "Wyłowione ryby".** Wcześniejszy audyt uznał, że silnik nigdzie nie zapisuje złowienia ryby — to była prawda tylko dla `log.log` (tam faktycznie nie ma takiego zdarzenia), ale silnik ma osobną, dedykowaną tabelę `log.fish_log`, zapisywaną przy każdym złowieniu (`LogManager::FishLog`, wywoływane wprost z questa rybackiego). Znaleziona i podłączona po zgłoszeniu operatora — 5557 realnych połowów na start.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-22 21:47 CEST · 1.65.0 · Nowa odznaka "via" w changelogu + dołączenie Tieru

- Operator i Tieru rozwijają teraz jeden wspólny panel zamiast dwóch osobnych — odznaka `via` na dole każdego wpisu dostała nową formę: praca z asystą AI to teraz `via Claude by Seban` / `via Codex by Seban` (imię operatora w panelu ma animowany, przelewający się kolor + migającą gwiazdkę obok), a kod wniesiony wprost przez Tieru (bez asysty AI) dostaje samo `via Tieru`, własnym, bursztynowym kolorem.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-22 20:37 CEST · 1.64.0 · Punkty wędek w tooltipie

- **Tooltip wędki na `/player/` pokazuje teraz Poziom, Punkty X/Y oraz Bonus puli rybołówstwa** — dokładnie jak w kliencie gry. Odczytane wprost z mechaniki rybołówstwa silnika (`fishing.lua`): punkty i przynęta leżą w gniazdach przedmiotu (to samo miejsce, które chwilę wcześniej było źródłem błędu z fałszywymi "kamieniami" — teraz odczytywane poprawnie), poziom wynika wprost z numeru VNUM wędki, a próg punktów i bonus puli z danych przedmiotu w bazie.

![via Claude](https://img.shields.io/badge/via-Claude-D97757)

## 2026-09-22 20:01 CEST · 1.63.0 · Nadawanie GM bez restartu, poprawki tooltipów przedmiotów

**Nowa funkcja:**

- **Nadanie/odebranie rangi GM działa teraz od razu, bez restartu** — dokładnie ten sam trik co w klasycznym panelu Tieru (7788): panel prosi o to postać z rangą IMPLEMENTOR, jeśli akurat jest online (wysyła jej w kolejce polecenie `/reload a`, silnik natychmiast wczytuje `common.gmlist` na nowo). Jeśli żaden IMPLEMENTOR nie jest zalogowany, zmiana i tak zadziała — tylko dopiero przy najbliższym logowaniu tej postaci, zamiast od razu.

**Poprawki tooltipów przedmiotów (`/player/`):**

- **Fałszywe "kamienie duszy" w opisach przedmiotów innych niż broń/pancerz** — wędka, rękawiczka i inne pokazywały przypadkowo trafione, zupełnie niezwiązane miecze (np. "Sejmitar+5") jako rzekomo osadzony kamień. Przyczyna: te typy przedmiotów przechowują w tych samych kolumnach bazy zupełnie inne dane (np. wędka — liczniki niezwiązane z gniazdami), a panel sprawdzał każdą niezerową wartość jako potencjalny VNUM kamienia, trafiając przypadkiem w prawdziwe, istniejące przedmioty. Sprawdzanie kamieni ograniczone teraz tylko do broni i pancerza.
- **Marmur Polimorfii i inne kamienie przemiany teraz pokazują, w jakiego potwora przemieniają** ("Przemienia w: ...") zamiast nic nie mówić.
- **Nieprzetłumaczony "Bonus #94"** na kilku przedmiotach (np. Buty Z Brązu+0) — brakujący wpis w tabeli tłumaczeń silnika, teraz poprawnie pokazuje "Wartość obrony +%".
- **Wszystkie hełmy pokazywały zaniżoną wartość obrony** — mnożnik bonusu z ulepszenia był błędnie ustawiony na pojedynczy zamiast podwójny (tak jak zbroja i tarcza).

![via Claude](https://img.shields.io/badge/via-Claude-D97757)

## 2026-09-22 19:45 CEST · 1.62.0 · Ikony umiejętności i odznaka GM na profilach postaci

**Nowe funkcje i poprawki:**

- **Umiejętności na `/player/`** korzystają teraz z oryginalnych ikon wyciętych z klienta Metin2. Dotyczy to skilli klasowych oraz pasywnych: Dowodzenia, Combo, Wędkarstwa, Górnictwa, Kowalstwa, języków królestw, Polimorfii, Poziomu konia i Przywołania konia.
- Ikony klasycznych umiejętności poprawnie rozróżniają zwykły poziom oraz rangi M, G i P. Brakujące wcześniej Wędkarstwo jest odczytywane z danych postaci.
- **Poziom konia i Przywołanie konia** zachowują własną skalę liczbową, więc np. poziom 21 pokazuje `21`, zamiast błędnego `M2`.
- Karta umiejętności używa kolorów aktualnie wybranego motywu panelu.
- Postacie wpisane do `common.gmlist` otrzymują przy nazwie oryginalną, animowaną **odznakę GM** z klienta gry. Podpowiedź po najechaniu pokazuje zapisaną rangę GM.

![via Codex](https://img.shields.io/badge/via-Codex-10A37F)

## 2026-09-22 19:27 CEST · 1.61.0 · Panel działa na żywo — koniec przeładowań strony

**Nowa funkcja:**

- **Żaden przycisk w panelu już nie przeładowuje całej strony.** Wszystkie formularze (Zarządzanie, Konta i GM, Nazwy postaci botów, Kreator postaci, Gospodarka, Eventy, Gildie, nadania przedmiotów, Baza przedmiotów, profil gracza/bota, lista graczy) wysyłają się teraz w tle — treść strony aktualizuje się na żywo w miejscu, dokładnie tak samo jak po przeładowaniu, tylko bez samego przeładowania. Wyjątek celowy: logowanie i pierwszy kreator uruchomienia, gdzie prawdziwe przekierowanie jest właściwe.
- **Nowy system powiadomień o wykonanej akcji**: zamiast blokującego okienka z przyciskiem "OK", komunikat wjeżdża animacją od góry ekranu i **zostaje, dopóki nie klikniesz X** — nie znika sam. Osobny mechanizm od dzwoneczka powiadomień (ten obsługuje zdarzenia serwera, nie akcje w panelu).
- Usuwanie postaci (i inne akcje przenoszące gdzie indziej niż bieżąca strona) poprawnie robi prawdziwe przekierowanie zamiast podmiany w miejscu — pasek adresu nigdy nie pokazuje niezgodnej treści.
- Formularze wyszukiwania/filtrowania aktualizują adres URL na bieżąco (można kopiować link z aktywnym filtrem, cofać się przyciskiem Wstecz).

**Poprawka przy okazji:** na stronie Eventy fragment skryptu (włącz/wyłącz pole bonusu przy wyborze "szkatułka") od dawna przypadkiem siedział w tytule strony zamiast w treści i nigdy się nie wykonywał — przeniesiony, teraz działa.

![via Claude](https://img.shields.io/badge/via-Claude-D97757)

## 2026-09-22 18:15 CEST · 1.60.0 · Sklep offline, nazwy botów, logi panelu, poprawki dashboardu

**Nowe funkcje:**

- **Sklep offline (`/player/`) przebudowany na prawdziwą siatkę przedmiotów** w stylu klienta gry (10×8 pól) zamiast tabelki tekstowej: ikony, tooltipy z nazwą/statystykami/bonusami/kamieniami duszy (dokładnie ten sam mechanizm co ekwipunek), cena na każdym slocie, przedmioty 2/3-slotowe zajmują odpowiednio więcej pól. Nazwa sklepu jest teraz stylizowanym okienkiem (jak tooltip w grze) i rozwija/zwija zawartość po kliknięciu. Na dole widoczny "Potencjalny zarobek" (suma cena × ilość wszystkich ofert).
- **Konta i GM → Nazwy postaci botów** (nowa podstrona): przegląd całej puli 5400 nicków silnika (1800 na królestwo) z filtrowaniem po królestwie/statusie i wyszukiwarką, dodawanie własnych nicków z priorytetem, blokowanie/usuwanie z kolejki oraz ręczne uruchomienie przydziału dla botów bez nicku. Baza puli wczytywana raz z pliku silnika (`playerbot_names.sql`) do własnej tabeli, żeby nie parsować 5600-linijkowego pliku SQL przy każdym wejściu na stronę. Uwaga udokumentowana wprost na stronie: nick jest przydzielany raz, w momencie powstania konta bota — priorytety/blokady realnie coś zmienią dopiero po pełnym wipe'ie/reseedzie z większą pulą botów, nie na obecnie żyjących botach.
- **Diagnostyka → Logi panelu** (nowa podstrona): błędy działania samego webpanelu (nie gry) trafiają teraz do trwałego, rotującego pliku logów, przeżywającego restarty i aktualizacje. Strona pokazuje ostatnie 500 linii i ma przycisk pobrania pełnego pliku — do załączania przy zgłaszaniu błędów.

**Poprawki:**

- **Tooltipy przedmiotów ucinane/wychodzące poza ekran** — dwie osobne przyczyny, obie naprawione: (1) `.panel{overflow-x:auto}` przycinał dymek wystający poza krawędź sekcji sklepu offline; (2) dymek wyśrodkowany na skrajnych kolumnach siatki (ekwipunek, magazyn, ekwipunek podręczny, sklep) realnie wychodził poza widoczny obszar okna. Skrajne kolumny/sloty kotwiczą teraz dymek do swojej wewnętrznej krawędzi zamiast do środka — naprawione we wszystkich miejscach używających tego mechanizmu, nie tylko w sklepie.
- **Powiadomienia dublowały się** (dwa identyczne wpisy w dzwoneczku) — przyczyna: panel działa na 2 workerach × 4 wątki, a powiadomienia powstają przy okazji zwykłego ruchu na stronie, więc dwa równoległe żądania mogły oba zobaczyć ten sam "właśnie zakończony event/dzień" i wstawić duplikat. Dodany unikalny indeks `(kind, ref_id)` + `INSERT IGNORE` czyni to bezpiecznym pod współbieżnością; powiadomienia o nowej wersji Playerbots dostały deterministyczny `ref_id` (CRC32 numeru wersji), bo wcześniej zawsze miały `NULL`, co omijało tę ochronę.
- **Wyświetlanie rat serwerowych (EXP/Drop/Yang) z aktywnym bonusem eventu** — bonus (`+50% · czas`) był osobnym elementem flex w wierszu z `justify-content:space-between`, co rozpychało go na sam koniec wiersza z ogromną przerwą po wartości procentowej. Wartość i bonus są teraz zgrupowane razem przy prawej krawędzi wiersza; kolorem wyróżnia się tylko sam bonus, nie cała wartość.
- **Widget "Boty CH1/CH2 na mapach" na dashboardzie** — pełne nazwy map/kody `M<n>` pod słupkami były nieczytelne w wąskim kafelku (zwłaszcza dla lochów/stref specjalnych bez `M<n>` w nazwie, gdzie pokazywała się cała, długa nazwa). Zastąpione małą ikonką charakterystycznego dropu z danej mapy (ta sama ikonka dla M1/M2/M3 każdego królestwa, bo tiery dropią to samo) + flagą królestwa obok — obie wycentrowane jedna pod drugą. Mapy bez dobrze dobranej ikony (M3) dostają zamiast tego krótki kod tekstowy + flagę, w tym samym układzie.
- **Podsumowanie dnia**: dodana kategoria "Najwyższe średnie obrażenia w broni" (nazwa, ikona, średnie obrażenia, właściciel) korzystająca z tego samego rankingu co `/rankings`.

![via Claude](https://img.shields.io/badge/via-Claude-D97757)

## 2026-09-19 03:05 CEST · 1.59.5 · Poprawka poszerzania panelu bocznego

- Moja poprzednia poprawka (kolumna paska bocznego `minmax(300px,420px)`) miała efekt odwrotny do zamierzonego — zabierała miejsce mapie zamiast wypełnić pustą przestrzeń obok. Cofnięte.
- Zamiast tego: mapa dostała stały, maksymalny rozmiar (nie rośnie już dalej), a `.live-shell` (całe pudełko z mapą i paskiem bocznym) zostało poszerzone z 66,666% do 74% szerokości, z odpowiednio zmniejszonym udziałem panelu "Stan serwera" (z 50% do 45% tej większej podstawy — jego rozmiar bezwzględny zostaje praktycznie bez zmian). Uwolnione w ten sposób miejsce trafia teraz w całości do paska bocznego (ranking + aktywności), zamiast zostawać pustą szczeliną.

## 2026-09-19 02:55 CEST · 1.59.4 · Baner i kafelek changelogu

- Baner herosa na Dashboardzie miał ujemne marginesy boczne (-6vw), które poszerzały go poza pudełko `<main>` — wjeżdżał wizualnie na stały pasek nawigacji z lewej i wypychał poziomy suwak strony z prawej. Baner mieści się teraz w normalnej szerokości treści, z własną ramką i zaokrągleniem zamiast pełnej szerokości "od krawędzi do krawędzi".
- Kafelek "Najnowsza zmiana" na Dashboardzie pokazywał pełną treść pierwszego punktu najnowszego wpisu changelogu — przy dłuższych wpisach rozciągał cały wiersz siatki (4 kafelki w rzędzie dzielą wysokość najwyższego), więc pozostałe 3 kafelki robiły się nienaturalnie wysokie i puste. Opis jest teraz obcinany do 2 linii, odnośnik "Zobacz changelog →" zostaje zawsze widoczny na dole.

## 2026-09-19 02:50 CEST · 1.59.3 · Naprawa: cofnięta zła diagnoza, prawdziwa przyczyna

- Moja poprzednia "naprawa" (usunięcie starego `@media(min-width:1351px)`) była błędna diagnozą — ten kod wcale nie był martwy, tylko wciąż potrzebny, bo `.world-overview` celowo "wystaje" poza pudełko `.live-shell` (pozycjonowanie absolutne). Usunięcie go zrobiło dwie szkody naraz: mapa na żywo urosła na całą szerokość (bo `.live-shell` stracił ograniczenie do 66,666% szerokości), a sekcja "PLAYERBOTS · ŚWIAT" zniknęła **we wszystkich motywach**, nie tylko w Cesarstwie. Cofnięte.
- **Prawdziwa przyczyna** zniknięcia sekcji tylko w Cesarstwie: mój efekt "ściętego rogu" (`clip-path`) na `.live-shell` obcinał też to, co z niego wystawało — a `.world-overview` wystaje z niego celowo, żeby siedzieć obok mapy. `clip-path` przycina potomków tak samo jak `overflow:hidden`, nawet jeśli są pozycjonowani poza pudełkiem rodzica. Wyłączyłem `.live-shell` z efektu ściętego rogu (tło/ramka i tak są już poprawnie ostylowane przez wcześniej dodane zmienne `--live-*`), reszta paneli zostaje ścięta jak było.

## 2026-09-19 02:45 CEST · 1.59.2 · Motyw Cesarstwo — właściwy audyt

- **Zniknięta sekcja "PLAYERBOTS · ŚWIAT / Stan serwera"**: to nie był błąd motywu — to martwy, sprzeczny kod CSS sprzed obecnego układu Dashboardu (`@media(min-width:1351px)`), który na bardzo szerokich ekranach wypychał tę sekcję poza widoczny obszar strony. Usunięty.
- **Pasek "Wiadomości ze świata" nie dolegał do nawigacji**: mój "ścięty róg" objął też ten pasek, co wizualnie odcinało mu lewy-dolny róg dokładnie tam, gdzie powinien stykać się z sidebarem. Wyłączony z tego efektu.
- **Teksty nawigacji dalej niebieskie + hover bez złota**: dodano brakujący kolor tekstu linków i podświetlenie na hover w barwie złota (wcześniej hover robił się na ciemny brąz, nie złoto).
- **Paski PŻ/PM/EXP bez segmentów**: efekt "przedziałków" (background-image) był po cichu nadpisywany przez `!important` na skrócie `background` w tej samej regule — rozdzielone na `background-color` + `background-image`, oba teraz faktycznie widoczne.
- **Statystyki STR/VIT/DEX/INT**: dodano prawdziwy kształt sześciokąta (clip-path), zamiast tego samego ściętego rogu co reszta paneli.
- **Plakietki profilu bota (Chunjo, HP, MP, Yang, mapa, kanał, VIP...)** na `/player/`: nie miały żadnego wariantu dla Cesarstwa — zostawały na stałym granatowym tle. Dodane.
- **Tło logów na żywo** (`/player/`) dociemnione zgodnie z motywem.
- **Wykres "Yang w obiegu" w `/economy/`**: kolor linii/siatki zależny teraz od aktywnego motywu.
- Znana, jeszcze nieodhaczona reszta: wykresy Chart.js w `/economy/sklepy`, `/economy/itemshop`, `/economy/przedmiot/*`, `/system` i `/maps` (mapa cieplna) nadal mają twardo wpisany niebieski kolor — to nie jest coś co Cesarstwo popsuło, ten sam brak dotyczy też Ember i Forest od zawsze, ale skoro robimy porządny audyt, to uczciwie: jeszcze nie zrobione. Dam znać osobno jak dokończyć.

## 2026-09-19 02:30 CEST · 1.59.1 · Poprawki motywu Cesarstwo

- Mapa świata botów: moja reguła tła dla `.world-map` w motywie Cesarstwo miała wyższą specyficzność CSS niż reguły ustawiające prawdziwe tło każdej mapy (`.world-map[data-map-index="N"]`) — po cichu je nadpisywała, więc mapa była pusta, a boty wyglądały jak rozjechane po przekątnej (bo faktycznie były we właściwych miejscach, tylko bez podkładu mapy widać to było jako chaos). Usunięte.
- Widżet "Mapa świata botów" na Dashboardzie (przyciski poziomu, tło, panel boczny, ranking) ma osobny system zmiennych kolorów (`--live-*`), który Ember i Forest miały już zdefiniowany — motyw Cesarstwo tego wariantu nie miał, więc spadał do domyślnego niebieskiego (Ocean). Dodany brakujący zestaw w barwach bursztynu.
- Poprawiony kontrast tekstu na złotych przyciskach (ciemny tekst zamiast białego).
- Usunięta martwa, sprzeczna reguła `.inv-tabs` w `manage.css` z czasów przed przebudową stron ekwipunku (1.57.0) — kolidowała nazwą klasy z nowym systemem.

## 2026-09-19 02:25 CEST · 1.59.0 · Nowy motyw "Cesarstwo"

- Dodano czwarty motyw kolorystyczny obok Ocean/Ember/Forest — **Cesarstwo** (`data-theme="empire"`), zaprojektowany w Claude Design: ścięte narożniki paneli zamiast zaokrągleń, czcionka Cinzel w nagłówkach, złoto-bursztynowa paleta, unoszące się iskry w tle, baner herosa na Dashboardzie, medaliony na podium rankingów (top 3) i flagi królestw jako proporce.
- Ustawiono jako **domyślny motyw** — zarówno dla nowych instalacji, jak i wymuszone na tej instancji już teraz (`web_seban_settings.theme='empire'`). Zmienialny jak zawsze w Zarządzaniu → Wygląd.
- Wyłącznie warstwa wizualna (CSS + kilka warunkowych fragmentów markupu) — zero zmian w działaniu panelu.

## 2026-09-19 01:45 CEST · 1.58.1 · Poprawka zakładki juków

- `/player/`: zakładka "Juki konne" jest teraz zawsze widoczna u każdej postaci zamiast znikać, ale wyszarzona i nieklikalna, gdy postać ich nie ma — spójniej z "Magazyn (pusty)". Pasek zakładek łamie się do nowego wiersza zamiast wyjeżdżać poza kolumnę ekwipunku na węższych szerokościach.

## 2026-09-19 01:40 CEST · 1.58.0 · Juki konne

- `/player/`: dodano podgląd juków konnych (dostępne po odblokowaniu u stajennego, widoczne w grze tylko przy przywołanym koniu) jako nowa zakładka obok "Ekwipunek" i "Magazyn" — pokazuje się tylko dla postaci, które faktycznie coś w nich trzymają. Zmapowane wprost na koncie [GA]Seban: siatka współdzieli ten sam mechanizm slotów co magazyn (`--col`/`--row`/`--size`), a juki to technicznie dalszy ciąg tej samej tablicy INVENTORY (pozycje od 180 wzwyż) — bez osobnej logiki układu.
- Odświeża się razem z resztą ekwipunku co 5 sekund (patrz 1.57.0).

## 2026-09-19 01:30 CEST · 1.57.0 · Ekwipunek: 4 strony i odświeżanie bez opóźnień

- `/player/`: ekwipunek ma teraz 4 strony (silnik od dawna obsługuje aż tyle — sprawdzone wprost w bazie, sloty sięgają pozycji 144) zamiast dotychczasowych 2. Przyciski przełączania stron przestały być obrazkami wyciętymi z gry — są teraz zwykłymi przyciskami na całą szerokość panelu ekwipunku, z delikatnym połyskiem i "falą" pod kursorem, dziedziczącymi kolory aktywnego motywu (Ocean/Ember/Forest), tak jak reszta interfejsu.
- `/player/`: ekwipunek i magazyn odświeżają się teraz same co 5 sekund, bez przeładowania strony — to samo zawsze-żywe zapytanie SQL co przy pierwszym wejściu na stronę (żadnego cache), więc założenie/zdjęcie przedmiotu na bocie widać tu prawie od razu, tak jak w panelu Tieru.
- Techniczne: logika odczytu ekwipunku/magazynu została wydzielona do jednej funkcji (`load_character_items`) współdzielonej przez pełną stronę gracza i nowy endpoint `/api/player/<pid>/inventory-fragment` — jedno miejsce prawdy zamiast dwóch kopii tego samego zapytania.

## 2026-09-19 01:20 CEST · 1.56.1 · Poprawki po CH2

- Selektor kanału na mapie świata botów miał własną, niedopasowaną ramkę i tło — teraz wygląda jak sąsiednie listy (mapa, tryb) w tym samym pasku filtrów.
- Zakładki kanałów na `/maps` były na stałe niebieskie niezależnie od motywu — teraz nieaktywna zakładka dziedziczy kolory aktywnego motywu (Ocean/Ember/Forest) tak jak reszta interfejsu.
- Dashboard: kafelek "Boty według map" zyskał trzecią klatkę karuzeli — słupkowe zestawienie CH1 obok CH2 (i kolejnych kanałów, jeśli kiedyś dojdą) dla najbardziej obleganych map, obok istniejącego donuta i wykresu sklepów offline. Pojawia się tylko gdy działa więcej niż jeden kanał.

## 2026-09-19 01:10 CEST · 1.56.0 · Obsługa drugiego kanału (CH2)

- Panel przestał zakładać, że boty żyją wyłącznie na `channel1` — status live, gildie, dziennik zdarzeń, logi bota i mapa cieplna wędkarska czytają teraz automatycznie wykryte katalogi `channelN`, więc obsługa skaluje się na 3+ kanały bez kolejnej zmiany kodu, nie tylko na CH1/CH2 jak w panelu Tieru.
- Mapa świata botów: nowy selektor kanału (pojawia się dopiero gdy jest więcej niż jeden kanał) oraz osobne kształty znaczników na mapie na żywo (kółko/kwadrat/trójkąt/...) — kolor nadal oznacza status bota (grupa/zawieszony/Metin), kształt oznacza kanał, więc oba się nie mylą.
- Karta gracza: pokazuje aktualny kanał na żywo (📡) albo ostatni znany kanał zapisany w historii pozycji, gdy bot jest offline (💤).
- `/maps` ("Aktywność map"): zakładki Wszystkie/CH1/CH2/... przełączają wykres i tabelę natężenia bez przeładowania strony.
- `web_seban_map_snapshot` i `web_seban_bot_position_snapshot` (kolektor) zyskały kolumnę `channel`; stara historia (sprzed tej aktualizacji, cała z CH1) jest zachowana, nowe wiersze są już tagowane kanałem.

## 2026-09-17 01:05 CEST · 1.55.0 · Playerbots 2.x i ItemShop

- `/manage`: dodano plan wejścia botów — okno wejścia kohorty, liczbę późno dołączających botów oraz czas ich wejścia. Zapis ustawia parametry Playerbots 2.x i odtwarza wyłącznie kontener gry.
- Gildie: rozbudowano zestawienie o dane mechanizmu doboru, aktywność i czytelniejsze sortowanie zgodne z aktualizacjami Playerbots 2.x.
- Eventy: dodano planer oraz obsługę zdarzeń z panelu Playerbots.
- ItemShop: saldo obejmuje konta botów działające i zablokowane, a Smocze Znaki są liczone z `account.cash_mark`.
- ItemShop: ostatnie zakupy i popularność przedmiotów korzystają z natywnego dziennika `log.itemshop`; w paczce znajduje się bezpieczny generator brakującej tabeli.
- Naprawiono konfigurację referencyjnej instalacji wędkarstwa: karta wędkarska 27620 ma ponownie właściwy typ przedmiotu i może zostać wyposażona przez boty.

## 2026-09-16 14:15 CEST · 1.54.2 · ulepszenia interfejsu

- `/manage`: poprawiono układ aktualizatora — checkbox aktualizacji Seban Panel jest wyrównany z pozostałymi opcjami, a modal nie tworzy poziomego paska przewijania.
- `/rankings`: pierwszy wiersz otrzymał spójne wyróżnienie na całej szerokości tabeli oraz animowany efekt gwiezdnego blasku na nicku, dopasowany do aktywnego motywu.
- Nawigacja „Gospodarka” na desktopie pokazuje pozycje podmenu w czytelnym układzie; na dashboardzie dodano dokładniejsze zakresy poziomów botów i uproszczono informacje o wersjach Playerbots.
- `/guilds`: dodano kolumnę Królestwo z flagą i nazwą Shinsoo, Chunjo lub Jinno, ustalaną na podstawie lidera gildii.
- `/economy/shops`: usunięto mylącą mapę z ostatnich sprzedaży, sprzedawca prowadzi teraz do karty postaci, a wyszukiwanie przedmiotów po odświeżeniu przenosi bezpośrednio do wyników.
## 2026-09-16 02:30 CEST · 1.54.1

- Dodano domyślnie wyłączony checkbox „Aktualizuj także Seban Panel do wersji dołączonej przez Tieru”. Decyzja jest zapisywana trwale i dołączana do konkretnego zlecenia aktualizacji. Po włączeniu aktualizator przebudowuje również `seban-panel`, `seban-collector` i `seban-item-grants`; po wyłączeniu zachowuje aktualny panel oraz lokalne zmiany. Porównanie wersji blokuje przypadkowy downgrade, gdy paczka Tieru zawiera panel starszy od już zainstalowanego.
- Aktualizator obsługuje teraz nazwę projektu Docker Compose podaną instalatorowi, dzięki czemu mechanizm nie jest przywiązany do projektu `metin2`. Ujednolicono publiczną instrukcję i usunięto przestarzałe odwołanie do starego `m2-updater selftest`.

## 2026-09-16 01:35 CEST · 1.54.0

- Przygotowano publiczne wydanie Aktualizatora Seban: przenośny instalator przyjmuje ścieżkę dowolnej instalacji MT2009 i nazwę projektu Compose, wykrywa wspólną kolejkę oraz uruchamia trwałą usługę systemową. Instrukcja w `/manage` zmienia się zależnie od stanu usługi.
- Checkboxy override'ów sterują rzeczywistą aktualizacją: Skrzynią Ucznia, Skrzyniami Blasku Księżyca i zachowaniem postaci demonstracyjnych. Oryginalny quest Tieru jest zachowywany i może zostać przywrócony.
- Reguły override'ów połączono z sekcją Aktualizator Seban. Ukryto skrót do niedziałającego masowego nadawania przedmiotów.

## 2026-09-16 01:10 CEST · 1.53.1

- Domknięto aktualizator: nazewnictwo w /manage jest jednolite (Aktualizator Seban), usunięto przestarzałe odwołania do oficjalnego kontenera updater Tieru i nieistniejącej ścieżki starego serwera. Ostatni restart po aktualizacji pokazuje teraz rzeczywistą datę oraz źródło „Aktualizator Seban”. Blok aktualizatora jest widoczny tylko przy monitoringu VPS/host.

## 2026-09-16 00:40 CEST · 1.53.0

- Przełomowy, niezależny aktualizator MT2009 w /manage: przed każdą aktualizacją tworzy kopię baz account, common, player i log, pobiera wyłącznie paczkę MT2009 Tieru, weryfikuje jej sumę SHA-256, ponownie stosuje nasze override'y (brak Skrzyni Ucznia, brak Skrzyń Blasku Księżyca, usuwanie kont demonstracyjnych) i przebudowuje tylko usługi gry. Seban Panel na porcie 7790 pozostaje nienaruszony. Watcher działa jako trwała usługa systemowa i pokazuje rzeczywistą wersję VERSION, a pasek postępu przechodzi przez kolejne etapy aktualizacji.

## 2026-09-15 14:41 CEST · 1.52.1

- Naprawiono regresję z 1.52.0: CSS nowej szuflady nawigacji celował w każdy element `<aside>` na stronie, nie tylko w pasek boczny — na telefonie w pionie to samo (`transform`, `overflow-y`, `max-width`) trafiało też w moduł "Mapa świata botów" (średni/maks. poziom, liczniki aktywności) i w ekwipunek na `/player/`, spychając oba poza ekran. Pasek nawigacji ma teraz własną klasę (`aside.site-nav`), więc reguły dotyczą wyłącznie niego. Zgłoszone przez [GA]Seban (telefon w pionie).

## 2026-09-15 14:20 CEST · 1.52.0

- Mobilny układ: nawigacja (lewy pasek na desktopie) jest teraz rozwijaną szufladą z przyciskiem ☰ w rogu zamiast wielkiej siatki linków na górze każdej strony. Na `/player/` ekwipunek/magazyn pokazuje się od razu pod paskiem PŻ/PM/EXP zamiast na samym dole strony po przewinięciu wszystkich sekcji. Zgłoszone przez [GA]Seban (widok na iPhone).

## 2026-09-15 12:10 CEST · 1.51.0

- Odblokowano przycisk "Aktualizator Tieru" w `/manage` (był ukryty od 2026-09-13). Izolowany kontener `updater` Tieru — jedyny, który dotyka gniazda Dockera, panel nigdy go nie dostaje — teraz sam odtwarza nasze skrypty `patch_*.py` i zamiata skrzynię ucznia zaraz po pobraniu nowych plików, przed zbudowaniem obrazów. Po drodze naprawiono trzy niezależne usterki blokujące tę usługę: zepsuty entrypoint w mt2009-owym renderze `docker-compose.yml` Tieru (wskazywał na nieistniejący plik), brak widoczności `/opt/seban-panel-custom` w kontenerze updatera (build panelu się tam zatrzymywał) i odmowę gita ("dubious ownership") przy pracy jako root. Wszystko naprawione lokalnie w `docker-compose.override.yml`, przeżyje każdą przyszłą aktualizację Tieru. Zweryfikowane działającym, pełnym przebiegiem na żywo.

## 2026-09-15 07:54 CEST · 1.50.0

- Naprawiono ranking "Przedmiot +9": zapytanie łączyło przedmioty z postacią tylko po `owner_id`, bez sprawdzania `window`. W SAFEBOX `owner_id` to ID konta (magazyn dzielony między postaciami), więc gdy ID czyjegoś konta zbiegło się z ID cudzej postaci, przedmiot leżący w skrytce był pokazywany jako własność tamtej postaci. Ranking teraz liczy tylko przedmioty w EQUIPMENT/INVENTORY. Zgłoszone przez [GA]Seban (kolczyki w skrytce błędnie przypisane postaci Medicusa).

## 2026-09-15 00:43 CEST · 1.49.1

- Ogłoszenia +9 ukryte w wersji publicznej, tym samym mechanizmem co liczba botów/respawn/skrzynia startowa: nowa komenda `NOTICE` istnieje na razie tylko w naszej kopii `web_admin.quest`, nie u Tieru — bez tego, u innego operatora kolejka zalegałaby jako "pending" na zawsze, bez żadnego błędu.

## 2026-09-15 00:39 CEST · 1.49.0

- Nowy przełącznik w `/manage`: rankingi (i karuzela na dashboardzie) mogą teraz liczyć też prawdziwych graczy, nie tylko boty — zgłoszone przez gracza NerrVoVy na Discordzie. Wyłączone domyślnie, jedno kliknięcie żeby włączyć.
- `/economy/shops`: kafelki "Oferty" i "Sztuk towaru" scalone w jeden, zwolnione miejsce na nowy kafelek "Transakcji łącznie" (+ ostatnie 24h).
- Nowy przełącznik w `/manage`: serwerowe ogłoszenie na złoto (jak `/b` GM-a), gdy prawdziwy gracz ulepszy coś na +9 — nigdy dla botów. Wymagało dopisania jednej komendy do `web_admin.quest` (reużywa silnikowej `notice_all()`) i przy okazji naprawiło rozjazd między naszą kopią tego questa a tym co faktycznie działa na serwerze. Wyłączone domyślnie.

## 2026-09-15 00:11 CEST · 1.48.0

- Naprawiono "Internal Server Error" przez pierwsze ~5 minut po restarcie/aktualizacji: panel sam tworzy potrzebne tabele przy starcie zamiast czekać, aż kolektor je stworzy w swoim własnym cyklu; kolektor też ponawia szybko (10s) zamiast czekać pełne 5 minut, gdy pierwsza próba się nie uda (np. baza jeszcze się budzi). Zgłoszone przez graczy (sizowski, 23:16).
- `/manage`: docelowa liczba botów, respawn na mapach i wyłączanie skrzyni startowej — te trzy kontrolki wymagają naszych własnych skryptów questów, których świeży/publiczny install nie ma. Ukryte domyślnie, włączone na tym VPS-ie osobną flagą.
- Poprawiono błędne granice map Las, Czerwony Las i Wieża Demonów (błąd we wszystkich trzech współrzędnych bazowych i/lub rozmiarach) — zweryfikowane wprost z plików `Setting.txt` silnika.
- Zaktualizowano rdzeń Playerbots do wydania Tieru 2.0.48; przełączniki bez skrzyni ucznia i bez szkatułek blasku księżyca przetrwały. Liczba botów podniesiona do 1050 (+150).

## 2026-09-14 23:25 CEST · 1.47.0

- `/player/`: logi na żywo zaczynają się teraz same przy otwarciu strony (bez klikania), zbierają linie zamiast je zamieniać (nie "znikają" między odświeżeniami przy zatłoczonym logu) i kolorują wpisy jak w panelu Tieru.
- `/player/`: przycisk "Teleportuj moją postać do sklepu" przy Sklepie offline — przenosi na dokładne współrzędne straganu, nawet jeśli bot akurat nie odpowiada na status live.

## 2026-09-14 23:16 CEST · 1.46.0

- Naprawiono ranking "Skuteczność ulepszeń": silnik loguje porażkę jako `REMOVE (REFINE FAIL)`, a nie `REFINE FAIL` (który ma zero wpisów w bazie) — stąd wszyscy pokazywali 100%. Teraz zgadza się z wartością widoczną na `/player/`.
- `/player/`: nowa sekcja "Dziennik zdarzeń bota (logi na żywo)" — te same logi rdzenia gry co w panelu Tieru, z przyciskiem odświeżania na żądanie (co 4s) i kopiowania do schowka.

## 2026-09-14 23:05 CEST · 1.45.0

- Karuzela rankingów na dashboardzie sama się teraz przewija co 8s, z animacją wjazdu slajdu; kliknięcie strzałki/punktu resetuje timer.
- Puste rankingi (np. "Bossy" — na tym serwerze jeszcze nikt nie zabił bossa) pokazują teraz w karuzeli "Brak danych", zamiast całkowicie niewidocznego, pustego slajdu.
- Dodano ranking "Skuteczność ulepszeń" (% udanych ulepszeń, minimum 20 prób żeby jednorazowy szczęśliwy strzał nie lądował na #1) — w `/rankings/` i w karuzeli dashboardu.
- Naprawiono wiersze w `/rankings/`, które "rozjeżdżały się" wysokością, gdy niektóre boty nie mają danego przedmiotu (brak ikonki = niższy wiersz).

## 2026-09-14 22:42 CEST · 1.44.1

- Zakładki stron magazynu (Strona I/II/III) i obramówka siatki magazynu mają teraz kolor aktywnego motywu, zamiast sztywnego niebieskiego.

## 2026-09-14 22:26 CEST · 1.44.0

- Tooltipy ekwipunku pokazywały złe wartości bazowe: obrona/atak nie uwzględniały bonusu z ulepszenia, więc np. Różowa Szata+9 pokazywała 29 obrony zamiast rzeczywistych 83. Naprawione dla broni i zbroi (ciało, głowa, tarcza, buty).
- Wiele etykiet bonusów na przedmiotach było przesuniętych o jeden numer w tabeli tłumaczeń (np. "Silny przeciw mistykom" zamiast "Silny przeciw nieumarłym", "Odporność na dzwony" zamiast "na wachlarze") — cała tabela zweryfikowana krzyżowo z panelem Tieru i poprawiona. Znany, niepoprawiony wyjątek: jeden rzadki bonus (odbicie strzał) nadal pokazuje się jako "Odporność na sury" — ten sam brak jest też w źródle Tieru, wymaga dalszego śledztwa.

## 2026-09-14 22:04 CEST · 1.43.0

- `/player/`: magazyn ma teraz strony (I/II/III) jak w grze i uwzględnia rozmiar przedmiotu (2-3 sloty wysokości) — przedmioty nie nakładają się już na siebie.
- `/player/`: nagłówek postaci pokazuje teraz czas gry, ostatnie logowanie, Smocze Monety, małżeństwo i gildię jako osobne znaczniki; usunięto zbędną sekcję "Smocze Monety i VIP" (te wartości są teraz w nagłówku).
- `/player/`: naprawiono ikonki umiejętności — panel próbował je ładować z `127.0.0.1:7788`, adresu, który w przeglądarce operatora wskazuje na jego własny komputer, nie na serwer. Ikony są teraz hostowane lokalnie w naszym panelu.
- `/player/`: umiejętności wyświetlają się teraz jak przedmioty w ekwipunku — ranga nałożona na ikonę, pełna nazwa w tooltipie po najechaniu, bez osobnego tekstu obok. Dodano też listę umiejętności pasywnych bez ikon (Górnictwo, Kowalstwo, Polimorfia, Dowodzenie, Combo, języki, jazda konna).

## 2026-09-14 20:09 CEST · 1.42.0

- Zaktualizowano rdzeń Playerbots do wydania Tieru 2.0.46; przełączniki bez skrzyni ucznia i bez szkatułek blasku księżyca przetrwały bez ingerencji.
- Dashboard i `/economy/`: konta testowe instalatora (Admin, AdminNinja, AdminSura, AdminSzaman — 2 mld sztucznego yang) nie liczą się już do "yang w obiegu".
- Dashboard: liczba w segmencie "Boty na mapach" nie chowa się już za paskiem przewijania; segment rośnie i wypełnia cały wolny sidebar.
- `/player/`: nowa sekcja "Sklep offline" — co bot aktualnie sprzedaje, za ile i gdzie stoi stragan (nazwa, mapa, współrzędne), dociągane bezpośrednio z tabel IkarusShop.
- `/player/`: przycisk "Teleportuj moją postać w grze (1 klik)" — jak w panelu Tieru, przez tę samą kolejkę questa co nadania przedmiotów.
- `/player/`: "Historia ekwipunku" zamiast surowego logu — czytelne zdarzenia (Sprzedane handlarzowi, Założone, Ulepszenie udane, Spalone przy ulepszaniu itd.) z nazwą przedmiotu, jak w panelu Tieru.

## 2026-09-14 18:02 CEST · 1.41.0

- Sklepy offline: tooltip Księgi Umiejętności w profilu bota nie pokazuje już losowych bonusów innego przedmiotu.
- Sklepy offline: ranking najlepiej sprzedających się przedmiotów rozpoznaje teraz konkretną umiejętność Księgi (dociągana z socketu sprzedanego przedmiotu), zamiast jednej generycznej pozycji; dodano osobny panel z top księgami.
- Sklepy offline: nowy live-feed ostatnich sprzedaży ze straganów (ikona, sprzedawca, królestwo, mapa, cena) i wykres tempa sprzedaży z trendem ceny.
- Dashboard: kafelek "Boty według map" przełącza się automatycznie co 8s na wykres słupkowy "Sklepy według map" (jak w Sklepach offline, w mniejszej wersji).
- Dashboard: lista "Boty na mapach" w panelu bocznym jest teraz przewijana i nie wyjeżdża poza swój segment po dodaniu nowych map.
- Dodano trzy nowe mapy botów: Las, Czerwony Las i Wieża Demonów (heatmapa zdarzeń); Wieża Demonów nie pojawia się na mapie na żywo z kropkami botów, bo to prywatne instancje dungeonu.
- Naprawiono nakładające się linki w rozwijanym menu "Gospodarka" (bug Safari/WebKit z display:contents w grid).

## 2026-09-09 18:10 CEST · 1.40.0

- Dodano zwijany poradnik uruchomienia aktualizatora Tieru na VPS bezpośrednio w Zarządzaniu.
- Tabele, przyciski, linki, przedziałki i kafelki wskazanych widoków dziedziczą teraz aktywny motyw.
- Baza przedmiotów pokazuje ikonę rzeczywistego przedmiotu przy każdej kategorii.
- Konta i profil postaci pokazują flagę oraz nazwę królestwa.

## 2026-09-09 17:45 CEST · 1.39.1

- Karta Playerbots · świat na Dashboardzie dziedziczy pełną kolorystykę aktywnego motywu, także dla etykiet, rat i listy map.

## 2026-09-09 17:30 CEST · 1.39.0

- Kreator GM pozwala wybrać kobietę albo mężczyznę; zapisuje właściwy wariant modelu klienta, zachowując klasyczny wariant jako domyślny.
- Oryginalne portrety klas są widoczne w profilu postaci, liście graczy, rankingach, karuzeli Dashboardu i rankingu aktualnej mapy.
- Ranking botów otrzymał kolumnę klasy z portretem i nazwą.
- Mapa na żywo, filtry, paski aktywności oraz karuzela rankingów dziedziczą teraz pełną paletę motywu Ocean, Ember lub Forest.

## 2026-09-09 16:47 CEST · 1.38.6

- Kreator kont GM zapisuje teraz indeks wyboru postaci (`player.player_index`), więc utworzona postać jest widoczna od razu po zalogowaniu.
- Nieudana konfiguracja GM sprząta utworzone przez siebie rekordy, także na tabelach MyISAM bez transakcji.
- Nick GM przyjmuje pojedynczy prefiks w nawiasach, np. `[GM]Seban` lub `[GA]Seban`.
- Dodano osiem oryginalnych portretów klas z ekranu postaci klienta do `static/class-portraits/`.

## 2026-09-08 21:45 CEST · 1.38.5

- Wiadomości świata odzyskują polskie nazwy ulepszanych przedmiotów z VNUM; ulepszenia +8 i +9 są złote.
- Sezon liczy wyłącznie trzy indeksowane typy zdarzeń z ostatnich 7 dni, bez pełnych skanów całej historii logów.

## 2026-09-08 17:35 CEST · 1.38.4

- Sesja panelu ma własną nazwę ciasteczka i trwa 30 dni. Nie koliduje już z klasycznym panelem Tieru działającym na tym samym hoście pod innym portem.
- Dodano poprawkę rdzenia: po załadowaniu danych questa bot uruchamia własne timery. Dzięki temu odbiera także masowe nadania z kolejki panelu.
- Masowe nadania wybierają wyłącznie Playerboty; postacie zwykłych graczy i administracji nie trafią do listy odbiorców nawet wtedy, gdy spełniają warunki poziomu lub konia.

## 2026-09-08 17:15 CEST · 1.38.3

- Uporządkowano wykresy map: trwała paleta kolorów, wybór map przez tabelę i checkboxy oraz tooltip z godziną i liczbą postaci.
- Dashboard i `/manage` sprawdzają najnowsze wydanie Playerbots na GitHubie co 15 minut; lokalna wersja jest zielona, gdy aktualna, i pomarańczowa, gdy zaległa.
- Pasek wiadomości świata można ukryć; na telefonie zachowuje formę pojedynczego paska.
- Konto GM tworzy teraz od razu prawidłową postać wybranej klasy w wybranym królestwie; sama ranga GM nadal wymaga restartu usług gry.

## 2026-09-08 15:00 CEST · 1.38.2

- Dodano brakujące, śledzone tło ekwipunku `inventory-background.svg`; jest kopiowane do każdego obrazu i ZIP-a panelu.
- Helper ustawień serwera publikuje sygnał gotowości. `/manage` nie pozwala już utworzyć zlecenia restartu/respawnu, gdy integracja gry nie działa.
- Dodano bezpieczne usunięcie wyłącznie zaległego zlecenia po 10 minutach bez aktywnego helpera oraz wyjaśnienie instalacji integracji w README.

## 2026-09-08 14:35 CEST · 1.38.1

- Dodano `UPDATER_VPS.md`: komendy dla standardowych i niestandardowych instalacji Tieru na VPS, przygotowanie cache oraz diagnostykę aktualizatora.
- Rozszerzono README o wymagany wolumen `update-spool` i instrukcję włączenia aktualizacji z panelu.

## 2026-09-08 00:00 CEST · 1.38.0

- Dodano most do izolowanego aktualizatora Tieru w `/manage`: stan, postęp, log i przycisk zlecenia aktualizacji.
- Panel zapisuje wyłącznie identyfikator zlecenia do wspólnej kolejki; Docker socket pozostaje wyłącznie w kontenerze aktualizatora.
- Przycisk wymaga aktywnej ochrony hasłem oraz tokenu sesji; wdrożona aktualizacja automatycznie odświeża widoczną wersję Playerbots.

## 2026-09-07 22:55 CEST · 1.37.1

- Poprawiono źródło wersji Playerbots w Dashboardzie: jest ustawiane jawnie w `PLAYERBOTS_VERSION`, a przykładowa konfiguracja wskazuje 1.30.12.

## 2026-09-07 22:35 CEST · 1.37.0

- Zaktualizowano rdzeń Playerbots do wydania Tieru 1.30.12: obsługę szkatułek, wycenę bonusów w sklepach oraz diagnostykę Dockera.
- Dodano Loch Małp Normalny (108) i Loch Małp Trudny (109) do mapy na żywo, historii natężenia, heatmap, wykresów, list map i zarządzania respawnem.
- Z panelu można teraz sterować respawnem potworów we wszystkich trzech Lochach Małp; Metiny są ukryte, ponieważ te mapy nie mają pliku `stone.txt`.

## 2026-09-07 22:00 CEST · 1.36.2

- Dodano ranking zabitych bossów (`BOSS_KILL`) za ostatnie 7 dni do `/rankings` i karuzeli Dashboardu.
- Zweryfikowano produkcyjnie ustawienia respawnu: aktywne wartości są zapisywane do właściwych plików `regen.txt` przed restartem rdzeni.

## 2026-09-07 21:27 CEST · 1.36.1

- `/maps` pokazuje pełną listę obsługiwanych map, także gdy bieżące natężenie wynosi 0.
- Dodano warstwę cieplną zabitych bossów (`BOSS_KILL`) na dashboardzie i w aktywności map.
- Dodano publiczną w panelu sekcję Changelog; kolejne hotfixy będą dopisywane z czasem wdrożenia.
- Połączono kafelki postaci i kont, a wersję panelu przeniesiono do stopki dashboardu.

## 1.36.0

- Dodano Górę Sohan (ID 61) i Loch Pająków V1 (ID 104) do mapy live, historii natężenia, heatmap, wykresów, list botów oraz ustawień respawnu.
- Wsparto osobny respawn potworów dla obu map i Metinów dla Góry Sohan; Loch Pająków V1 nie zawiera pliku `stone.txt`, co panel oznacza wprost.
- Podkłady obu map są renderowane z tych samych danych terenu, z których korzysta nawigacja Playerbots.

## 1.35.0

- Synchronizacja nazw i numerów umiejętności z aktualnym Panelem Tieru: ikona i podpis używają tego samego VNUM; nieużywane pozycje nie są już wyświetlane.
- Zarządzanie zachowaniem obsługuje przełącznik szybkich ksiąg (`BOOKS`) oraz szanse szkatułek (`CHEST`, `CHEST_STONE`).
- Zapis wag zachowuje przyszłe klucze silnika, których panel jeszcze nie zna.

## Wcześniejsze funkcje (przed prowadzeniem changeloga)

- Prawdziwe podkłady map wyciągnięte z folderu `/pack/` klienta gry (nie zastępcze grafiki) wpięte do wszystkich widoków z mapą.
- Prawdziwe ikony przedmiotów z klienta gry w całym panelu: ekwipunek, ekonomia, baza przedmiotów, sklepy.
- Karta postaci: nadawanie VIP oraz Smoczych Monet bez wychodzenia z profilu bota.
- Karta postaci: możliwość usunięcia postaci.
- Karta postaci: zmiana nicku postaci.
- `/manage`: usunięto sekcje, które i tak nie działały.
- `/economy/`: kliknięcie w przedmiot otwiera wykres "Stan w gospodarce · ostatnie 14 dni".
- `/player/`: statystyki postaci — te same, które gracz widzi w grze pod klawiszem Y.
- Wiadomości ze świata poprawnie wyświetlają polskie znaki.

## 1.34.0

- Osobne czasy respawnu potworów i Metinów dla obsługiwanych map.
- Jawne ID map, Joan przypisane do Chunjo M1 (21); poprawiona ścieżka Doliny Orków (64).
- Wspólna kolejka mnożników i respawnu: jeden restart dla całego zestawu, walidacja i cofnięcie ustawień przy błędzie zapisu.
- Równe przyciski, postęp i historia restartu w jednej sekcji zarządzania.
- Data ukończonego restartu, źródło zlecenia oraz osobna informacja o automatycznym podniesieniu rdzenia.
- Przycisk samego restartu pomija niezapisane pola, również gdy zawierają nieprawidłowe wartości.
- Testy regresji formularza i integracji z kontenerem gry.
