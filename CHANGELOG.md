> Wpisy oznaczone `(via Claude)` / `(via Codex)` pokazują, które narzędzie AI wykonało daną zmianę — operator pracuje z oboma. Dopisuj to oznaczenie w nagłówku każdego nowego wpisu.

## 2026-09-22 18:15 CEST · 1.60.0 · Sklep offline, nazwy botów, logi panelu, poprawki dashboardu (via Claude)

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
