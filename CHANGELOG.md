## 2026-10-10 · 1.114.32 · Sortowanie aktywnych ofert

- Przeglądarka rynku sortuje teraz także po najnowszych ofertach, najwyższym ulepszeniu oraz wymaganym poziomie rosnąco lub malejąco. Reguły ulepszenia i poziomu korzystają z tych samych pól `item_proto` co filtry, zgodnie z panelem Tieru.
- Każdy porządek jest na zamkniętej liście SQL; dodano nazwy PL/EN i testy wszystkich nowych wariantów.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)
## 2026-10-10 · 1.114.31 · Wymagany poziom w ofertach rynku

- Przeglądarka ofert filtruje przedmioty po wymaganym poziomie od 0 do 255. Odczyt z dwóch pól limitu `item_proto` zachowuje regułę Tieru: drugi limit poziomu ma pierwszeństwo, jeśli obydwa są ustawione.
- Granice działają razem z innymi filtrami i pozostają przy zmianie strony. Dodano teksty PL/EN i testy błędnego zakresu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)
## 2026-10-09 · 1.114.30 · Filtr klasy na rynku

- Aktywne oferty można ograniczyć do przedmiotów używanych przez Wojownika, Ninjy, Surę albo Szamana. Zgodność sprzętu wynika z `item_proto.antiflag`, a ksiąg z numeru umiejętności, tak jak w klasyfikacji Tieru.
- Filtr działa wraz z pozostałymi i pozostaje przy zmianie strony. Dodano etykiety PL/EN oraz test zapytania.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)
## 2026-10-09 · 1.114.29 · Zakres ulepszenia na rynku

- Przeglądarka aktywnych ofert filtruje przedmioty po ulepszeniu od `+0` do `+19`, osobno z dolną i górną granicą. Wartość jest odczytywana z końcówki nazwy `item_proto` zgodnie z parserem Tieru, a nie zgadywana z VNUM.
- Zakres zachowuje się przy zmianie strony, błędne i odwrócone wartości są odrzucane. Dodano teksty PL/EN i testy obu przypadków.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)
## 2026-10-09 · 1.114.28 · Podkategorie ofert rynku

- Filtr rynku rozróżnia typ broni, tarcze i hełmy, biżuterię, klasy ksiąg, poziom kamieni duszy oraz rodzaje materiałów zgodnie z regułami Tieru.
- Lista podkategorii zależy od wybranej kategorii, a wybór pozostaje przy zmianie strony. Zachowano nazwy PL/EN i dodano testy zgodności oraz odrzucania niepasujących podkategorii.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)
## 2026-10-09 · 1.114.27 · Kategorie aktywnych ofert

- Oferty rynku można filtrować według 11 kategorii Tieru. Klasyfikacja używa typu i podtypu przedmiotu z `item_proto` oraz dokładnej listy wyjątków dla ulepszaczy, ksiąg, ziół i rud z jego reguł.
- Filtr działa razem z pozostałymi i pozostaje przy zmianie strony. Opcje mają nazwy PL/EN, a zapytania są parametryzowane.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)
## 2026-10-09 · 1.114.26 · Liczba ofert dla filtrów rynku

- Przeglądarka rynku pokazuje łączną liczbę aktywnych ofert odpowiadających bieżącym filtrom, niezależnie od rozmiaru strony. Liczy ją z tego samego źródła IkarusShop co listę pozycji.
- Dodano tłumaczenie PL/EN i test zgodności parametrów zapytań listy oraz licznika.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.25 · Liczba ofert na stronie rynku

- Przeglądarka aktywnych ofert pozwala wybrać 25, 50 albo 100 pozycji na stronę. Wybór pozostaje aktywny przy przechodzeniu między stronami i działa razem z filtrami.
- Parametr ma zamkniętą listę dozwolonych wartości; dodano tłumaczenie PL/EN oraz test granic i przesunięcia wyników.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.24 · Sprzedawca i nazwa sklepu w filtrach rynku

- Aktywne oferty można filtrować po nicku sprzedawcy oraz nazwie straganu. Oba filtry działają razem z dotychczasowymi filtrami i pozostają przy zmianie strony wyników.
- Zapytania są parametryzowane, a teksty formularza mają wersję PL/EN. Dodano testy złożonych filtrów.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.23 · Zakres cen na rynku

- Przeglądarka ofert przyjmuje minimalną i maksymalną cenę Yang oraz opcjonalnie filtruje cenę za sztukę w stosie. Obsługuje wpisy `500k`, `1.5kk`, `2kkk` i grupowane kwoty tak samo jak parser Tieru.
- Niepoprawne wartości są oznaczane bez przerwania strony. Filtry pozostają przy zmianie strony wyników; dodano teksty PL/EN i testy parsera oraz zapytania.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.22 · Przeglądarka ofert rynku

- W Gospodarce dodano stronę aktywnych ofert IkarusShop z wyszukiwaniem po nazwie lub VNUM, filtrem królestwa i typu sprzedawcy oraz sortowaniem po cenie całkowitej albo za sztukę. Wyniki są stronicowane po 50 i prowadzą do przedmiotu lub sprzedawcy.
- Odczyt używa źródłowych tabel sklepu i ceny JSON, ogranicza zapytania oraz nie dotyka wystawionych przedmiotów. Nowa strona jest w nawigacji Laka i klasycznej, z tekstami PL/EN oraz testami filtrów.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.21 · Aktywne oferty przedmiotu na rynku

- Strona historii przedmiotu pokazuje do 100 aktywnych ofert IkarusShop z ceną całkowitą i za sztukę, ilością, sprzedawcą, nazwą sklepu, królestwem, mapą i kanałem. Można sortować po cenie rosnąco lub malejąco.
- Dane pochodzą z tych samych tabel i pola JSON ceny, których używa rynek Tieru. Widok ma teksty PL/EN, zapytanie ograniczone limitem oraz testy sortowania i przeliczania ceny.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.20 · Zestawy PvP botów

- Dodano eksperymentalny przełącznik zestawów PvP botów wraz z udziałem, minimalnym poziomem, siłą zestawu, budżetem i użyciem przeciw graczom. Domyślnie funkcja jest wyłączona.
- Wszystkie sześć kluczy `PVP_SET*` ma zakresy i wartości domyślne z reguł silnika Tieru. Formularz ma polskie i angielskie teksty; testy chronią odczyt, granice i zapis.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.19 · Skalowanie progów podaży

- Dodano opcjonalne skalowanie progów podaży do liczby żywych botów oraz referencyjną liczbę 50–50 000 (domyślnie 1000). Przy wyłączonym przełączniku silnik zachowuje oryginalne progi Iwakury.
- Panel zapisuje dokładnie `SUPPLY_SCALE` i `SUPPLY_REF_BOTS`, z tekstami PL/EN i testami granic.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.18 · Wycena opasek i Kamienia Duchowego według podaży

- Dodano przełącznik `SUPPLY_BANDS`: Opaski Zapomnienia i Kamień Duchowy mogą korzystać z progów podaży ksiąg umiejętności. Stan domyślny jest zgodny z silnikiem Tieru: włączony.
- Ustawienie działa przez plik wag AI, ma teksty PL/EN i test odczytu/zapisu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.17 · Miejsce w sklepach offline botów

- Dodano przełącznik `SHOP_ROOM_SELL`, zgodny z panelem Tieru. Gdy sklep bota jest pełny, silnik może sprzedać u handlarki ćwierć najtańszego stosu materiałów lub ksiąg, aby zwolnić komórkę. Wyposażenie pozostaje poza tą regułą.
- Opcja jest domyślnie włączona. Dodano teksty PL/EN i test odczytu/zapisu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.16 · Targowanie botów w sklepach graczy

- W zachowaniu botów można włączyć lub wyłączyć targowanie o zbyt drogie przedmioty +6 i wyższe w sklepach offline graczy. Opcja jest domyślnie włączona i zapisuje klucz `HAGGLE` zgodny z panelem Tieru.
- Dodano teksty PL/EN i testy odczytu oraz zapisu. Zwykły zakup przedmiotów nie zależy od tej opcji.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.15 · Koniec wojny gildii po zabójstwach

- Dodano limit 0–1000 zabójstw kończących wojnę gildii botów; 0 oznacza zakończenie wyłącznie po czasie. `WAR_KILLS` zapisuje się w pliku wag dokładnie jak u Tieru.
- Dopasowano dotychczasowe suwaki wojny do zakresów silnika: 15 lub 30 minut oraz 1–4 godziny odstępu. Dodano polskie i angielskie teksty oraz testy.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.14 · Rzemieślnicy botów

- Dodano suwak udziału botów od 35 poziomu kujących przedmioty na sprzedaż. Wartość domyślna 30%, zakres 0–100%; 0 wyłącza tę cechę.
- Kontrolka używa klucza `CRAFTSMAN` jak panel Tieru, ma teksty PL/EN oraz testy odczytu i zapisu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.13 · Gęstość czatu botów

- Dodano suwak Global chat 0–200% niezależny od przełącznika komunikatów nad głową bota. 100% oznacza normalne natężenie, 0 przywraca dawny czat i wołanie w obrębie królestwa.
- Odczyt i zapis `LIVE_CHAT` jest zgodny z panelem Tieru. Teksty dostępne po polsku i angielsku; testy chronią domyślną wartość, zakres i niezależność ustawień.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.12 · Realistyczne sesje botów

- W ustawieniach zachowania botów dodano suwak „Realizm sesji” 0–100%. Wskazuje odsetek botów objętych rytmem dnia i tygodnia Iwakury; działa niezależnie od starszego przełącznika sesji.
- Zapis jest zgodny z `SESSION_REALISM` panelu Tieru. Przy 0 klucz znika z pliku wag, więc silnik zachowuje dotychczasowy tryb. Dodano teksty PL/EN i testy odczytu oraz zapisu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.11 · Szybkość ruchu graczy i botów

- W dodatkach świata można ustawić 50–200% szybkości ruchu graczy, botów i Towarzysza pieszo oraz na wierzchowcu. 100% oznacza normalne tempo gry; potwory nie są objęte zmianą.
- Panel zapisuje `m2_move_speed_pct` i wysyła komendę `MOVE_SPEED` jak Tieru. Po potwierdzeniu silnika ustawienie działa na żywo i zostaje po restarcie. Dodano PL/EN oraz testy zakresu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.10 · Bonusy w przedmiotach wypadających z potworów

- W dodatkach świata można ustawić 10–1000% szansy na bonusy nowych broni i zbroi z potworów; 100% oznacza normalną szansę gry. Dotyczy najwyżej trzech bonusów i nie zmienia nagród, skrzyń ani sklepów.
- Panel zapisuje `m2_drop_bonus_pct` i wysyła komendę `DROP_BONUS` zgodnie z kodem Tieru. Po odpowiedzi silnika zmiana działa od następnego dropu i pozostaje po restarcie. Dodano PL/EN i testy zakresu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.9 · Obrona przed botami innych królestw

- W dodatkach świata można teraz włączyć lub wyłączyć reakcję Towarzysza w trybie Atak/Obrona oraz pomocy gildii i grupy na celowe ataki obcych botów na gracza. Pasywny Towarzysz nie odpowiada atakiem.
- Panel zapisuje flagę `m2_owner_defence_off` i wysyła komendę `OWNER_DEFENCE`, tak jak panel Tieru. Ustawienie działa na żywo po odpowiedzi silnika, przetrwa restart i ma teksty PL/EN.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.8 · Yang z potworów: do ekwipunku lub na ziemię

- W dodatkach świata dodano wybór, czy Yang z potworów zabitych przez gracza trafia od razu do ekwipunku, czy spada na ziemię jak w oryginalnej grze. Boty i Towarzysz nadal dostają Yang bezpośrednio.
- Panel używa flagi `m2_yang_ground` i komendy `YANG_GROUND` z panelu Tieru. Ustawienie działa na żywo po potwierdzeniu silnika i przetrwa restart. Formularz jest dostępny po polsku i angielsku.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.7 · Szósty bonus nowych broni 70 poziomu

- W zarządzaniu dodatkami świata można teraz włączać lub wyłączać losowy szósty bonus nowo tworzonych broni poziomu 70. Istniejące bronie nie zmieniają się.
- Panel zapisuje tę samą flagę `m2_unique70_bonus_off` i wysyła tę samą komendę `UNIQUE70_BONUS` co panel Tieru. Zmiana działa na żywo po odpowiedzi silnika i przetrwa restart. Dodano tłumaczenie angielskie oraz testy kontraktu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.6 · Usuwanie przedmiotów bota przez silnik gry

- Na karcie bota, pod ekwipunkiem, dodano zwijaną listę przedmiotów z torby i wyposażenia. Administrator może wskazać konkretny egzemplarz do usunięcia; panel potwierdza nazwę, a operację wykonuje silnik Playerbots przez kolejkę `DELITEM`.
- Offline bot zastosuje żądanie po wejściu do gry. Do tego czasu można je anulować; gdy silnik już zaczął usuwać przedmiot, panel nie obiecuje anulowania. Stan po wykonaniu oraz odmowa silnika pojawiają się obok listy.
- Serwer sprawdza sesję administratora, token żądania, tożsamość bota, właściciela, okno przedmiotu, VNUM i liczbę sztuk. Przedmioty graczy, magazynu i sklepu offline są poza tą akcją. Dodano teksty polskie i angielskie oraz testy endpointu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-09 · 1.114.5 · Tooltip przy powiększonym ekranie

- Po mocnym przybliżeniu ekranu palcami na telefonie tooltip przedmiotu w sklepie i w ekwipunku na karcie postaci pojawiał się gdzieś wysoko, daleko od ikony. Teraz wyskakuje tuż przy stukniętym przedmiocie, w widocznej części ekranu, i ma czytelną wielkość zamiast rosnąć razem z przybliżeniem.
- Arkusz z wyjaśnieniem ceny przy przybliżeniu też mieści się w tym, co widać, i trzyma się dołu ekranu. Przesunięcie lub zmiana przybliżenia chowa tooltip i dopasowuje otwarty arkusz.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-09 · 1.114.4 · Telefon: sklep da się klikać, przycisk „Dlaczego ta cena?”

- Na telefonie dało się stuknąć tylko pierwsze kolumny sklepu na karcie postaci. Pusty pojemnik na wyskakujące powiadomienia rozciągał się w motywie Laka i Złoto na niemal cały ekran i przechwytywał dotknięcia. Teraz ma tylko wysokość powiadomień i nigdy nie zabiera dotknięć stronie pod spodem, także w pozostałych motywach.
- Na telefonie tooltip przedmiotu w sklepie ma przycisk „Dlaczego ta cena?”, który otwiera wyjaśnienie. Nie trzeba już trafiać drugi raz w mały slot. Ponowne stuknięcie w ten sam przedmiot chowa tooltip.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-09 · 1.114.3 · Wyjaśnienie ceny wczytywane po kliknięciu

- Wyjaśnienie ceny w sklepie na karcie postaci znów działa. Od przebudowy okna sklepu (natywne UI) żadna oferta go nie dostawała, także w 1.114.2.
- Wyjaśnienie wczytuje się dopiero po kliknięciu w przedmiot (na telefonie po drugim stuknięciu). Panel otwiera się od razu z animacją ładowania, a ponowne otwarcie tego samego przedmiotu nie pyta serwera drugi raz. Strona gracza nie ładuje wyjaśnień, których nikt nie otworzy.
- Gdy bot nie zapisał wyjaśnienia danej oferty, panel mówi to wprost.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-09 · 1.114.2 · Sklep na karcie postaci: tooltipy na telefonie i wyjaśnienie ceny

- Tooltipy przedmiotów w sklepie offline działają na telefonie w każdej kolumnie. Wcześniej okno sklepu, szersze od ekranu, ucinało je od mniej więcej szóstej kolumny.
- Najechanie pokazuje zwykły tooltip przedmiotu, a kliknięcie przypina obok panel z wyjaśnieniem ceny. Na telefonie pierwsze stuknięcie pokazuje tooltip, a drugie otwiera wyjaśnienie jako arkusz od dołu.
- Wyjaśnienie mówi tyle co panel Tieru: wynik towaru, który był kandydatem i ilu wyżej odrzuciła lada, jak ucięto stos i ile zostało w plecaku, kiedy i za ile wystawiono, flagi lady, cenę krok po kroku (z „=” dla kroków bez zmiany) i cenę za sztukę wobec arkusza.
- Słownik decyzji botów odświeżony z panelu Tieru (Playerbots 2.2.82): nowe kroki ceny, np. „Ludzkie zaokrąglenie” zamiast „kod 47”, nazwy umiejętności i potworów oraz poprawne polskie nazwy przedmiotów. Generator `tools/generate_decision_tables.py` odświeża go po każdej aktualizacji.
- Strona Decyzje botów pokazuje kroki ceny jako tabelę zamiast surowych danych.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-09 · 1.114.1 · Metiny osobno od bossów w respawnach

- Strona Respawny ma osobne ustawienia dla Metinów, bossów i zwykłych potworów, zarówno dla tempa odrodzenia, jak i liczebności (Patch 12 Iwakury, punkt 2). Metin to kamień Metin, boss to potwór o randze bossa.
- Kolejka gry dostaje teraz trzy liczby, „metin,boss,mob”, w REGEN i REGEN_COUNT. Rdzeń czyta je z flag `fastMetinSpawn` i `m2_metin_count` obok dotychczasowych `fastBossSpawn` i `m2_boss_count`. web_admin.quest gry z Patchem 12 nadal rozumie też dawną postać „boss,mob”.
- Świat, w którym migrator Playerbots nie rozdzielił jeszcze ustawień, pokazuje dla Metinów wartość bossów. Podsumowanie respawnów na mapie świata wymienia Metiny i bossów osobno.

![via Tieru](https://img.shields.io/badge/via-Tieru-f2c34d)

## 2026-10-09 · 1.114.0 · Laka i Złoto: nowy panel

- Nowy motyw jest domyślny. Nowe instalacje startują w „Laka i Złoto”, a istniejące przełączają się na niego jeden raz, przy pierwszym starcie tej wersji. Kto potem wybierze w Ustawieniach panelu dawną kolorystykę (Cesarstwo, Ocean, Ember, Forest), ten ją zachowa przy kolejnych aktualizacjach.
- Nawigacja. Własne konturowe ikony sekcji zamiast przedmiotów z gry. Nowy podział: Świat (Przegląd, Planer eventów, Sezon), Postacie, Gospodarka, Kronika, Serwer (m.in. Aktywność map, Respawny), Administracja (m.in. Baza przedmiotów). Wyszukiwarka Ctrl+K, a na telefonie lupa.
- Przegląd świata. Tabela najważniejszych liczb (boty, konta, yang, poziomy, raty z eventem lub najbliższym planowanym eventem, wersje). Obciążenie VPS z wykresem CPU/RAM z 24 godzin, szczytem CPU, średnim RAM i wolnym dyskiem. Boty według map dla wszystkich map z podziałem na królestwa. Lista rankingów, Kronika świata i pasek „Źródła danych” z czasami odpowiedzi endpointów.
- Kronika świata. Ikona przedmiotu, którego dotyczy wpis (ulepszony, znaleziony lub sprzedany), księga dla umiejętności M1–M10, Kamień Duchowy dla G1–P, własne ikony dla bossów. Nowe wpisy: awans lidera rankingu poziomu oraz rekordowa sprzedaż na straganie (najwyższa cena za sztukę danego przedmiotu, od 1 mln Yang).
- Planer eventów. Tygodniowy kalendarz z dzisiejszym dniem, linią „teraz” i kolorowymi blokami eventów (trwające świecą, wyłączone są kreskowane). Do tego statusy z ikonami, karty szybkiego startu i historia jako lista. Formularze i zapis harmonogramu bez zmian.
- Karta postaci. Akcje administracyjne jako równe karty z ikonami i przyciskami na jednej wysokości, usuwanie postaci jako osobny czerwony pasek. Tooltipy ekwipunku znów pojawiają się przy kursorze. Oryginalne okna gry bez zmian.
- Cały panel. Jeden wygląd filtrów i paginacji (złote chipsy), przełączników, suwaków, list rozwijanych, pól wyszukiwania, nagłówków paneli, powiadomień, komunikatów i wykresów. Nowe ekrany logowania i błędu. Animacje przejść między stronami.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)
## 2026-10-08 · 1.113.6 · Motyw „Laka i Złoto”

- Nowa opcja w Ustawieniach panelu → Kolorystyka: „Laka i Złoto (nowy układ)”. Pozostałe motywy wyglądają bez zmian, a powrót to jedno kliknięcie.
- Nowa nawigacja: 6 sekcji z ikonami przedmiotów z gry (Świat, Postacie, Gospodarka, Kronika, Serwer, Administracja), zakładki podstron w górnej belce, wyszukiwarka stron i graczy pod Ctrl+K, licznik botów online, a na telefonie dolny pasek z arkuszem „Więcej”.
- Przegląd świata: liczby w jednym pasku, mapa na żywo w ozdobnej ramce z nakładką HUD (celowniki, linie skanowania, radar). Rozmiary i proporcje map są takie same jak dotąd.
- Wszystkie strony dostały wspólny wygląd tabel, formularzy, przycisków i zakładek. Strony szczegółów pokazują swoją nazwę w górnej belce. Oryginalne okna gry na karcie postaci są nietknięte.
- Animacje wejścia i wyjścia przy przechodzeniu między stronami (wyłączone przy systemowym „ogranicz ruch”).

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)
## 2026-10-08 · 1.113.5 · Tooltipy podglądu sklepu

- Podgląd sklepu wrócił do własnej obsługi tooltipów. Wspólny skrypt ekwipunku nie przechwytuje już slotów sklepu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-08 · 1.113.4 · Przestrzeń na tooltip ekwipunku

- Metinowa siatka ekwipunku w `/player/` została obniżona wewnątrz panelu. Nad nią jest stałe miejsce na tooltipy, więc nie zachodzą już na nagłówek „Zawartość ekwipunku”.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-08 · 1.113.3 · Pewny pomiar tooltipu

- Tooltip ekwipunku jest najpierw niewidocznie renderowany i mierzony, zanim wybierze stronę kursora. Wysokie opisy nie są już błędnie pozycjonowane nad kursorem przy górnej krawędzi ekranu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-08 · 1.113.2 · Tooltipy i obecność 24/7

- Tooltip przedmiotu mierzy teraz własną wysokość przy kursorem: gdy nie mieści się nad nim, otwiera się pod nim i pozostaje w granicach ekranu. Standardowe bonusy są szersze oraz nie łamią się bez potrzeby na dwie linie.
- Po wyłączeniu opcji „Boty grają jak żywi ludzie” wykres obecności na `/player/` pokazuje ciągłe 24/7. Historyczne przerwy z czasu, gdy sesje były włączone, nie zaniżają już bieżącego wskazania.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-08 · 1.113.1 · English: ranking +9

- Filtry kategorii oraz sortowanie rankingu **Przedmiot +9** są przetłumaczone w angielskim interfejsie.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-08 · 1.113.0 · Kategorie rankingu +9

- Ranking **Przedmiot +9** otrzymał filtry: broń, zbroje, hełmy, tarcze, bransolety, buty, naszyjniki i kolczyki.
- Wyniki można sortować według poziomu przedmiotu albo poziomu postaci. Wybrany filtr pozostaje przy przechodzeniu między stronami oraz przy widoku samych graczy.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-08 · 1.112.9 · Świeży stan dashboardu

- Odpowiedź z danymi dashboardu nie jest już zapisywana przez przeglądarkę. Po aktualizacji przez GUI launcher kafelek Playerbots od razu dostaje numer z bieżącego statusu serwera.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-08 · 1.112.8 · Rzeczywista wersja paczki Playerbots

- Dashboard dostaje numer z głównego pliku VERSION paczki Playerbots — dokładnie tego samego źródła, którego używa panel Tieru. Kolektor publikuje go do statusu panelu, więc aktualizacja przez GUI launcher odświeża numer niezależnie od nadpisywanego pliku Compose.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-07 · 1.112.7 · Wersja Playerbots z launchera

- Plik .env aktualizowany przez launcher jest nadrzędnym źródłem wersji Playerbots. Dashboard nie może już wybrać starszej lub wyższej wartości zapamiętanej w środowisku kontenera.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-07 · 1.112.6 · Synchronizacja Playerbots i regulator sesji

- Dashboard odczytuje wersję Playerbots także bezpośrednio z pliku .env aktualizowanego przez launcher. Numer przestaje zależeć od zmiennej środowiskowej zapamiętanej podczas tworzenia kontenera.
- Zarządzanie botami otrzymało regulator **Godziny gry na dobę** dla eksperymentalnego trybu „Boty grają jak żywi ludzie”. Wartość 0 zachowuje standardowe sesje 3–6 godzin i odpoczynek 3–9 godzin; zakres 1–24 ustawia docelowy czas gry na dobę.
- Nawigacja Seban Panelu zawiera odnośnik **Edytor bazy danych**, prowadzący do zabezpieczonego edytora /editsql panelu Tieru.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-07 · 1.112.5 · Synchronizacja aktualizacji operatora

- Zsynchronizowano najnowsze aktualizacje z gałęzi głównej panelu: boty na piętrach instancji Wieży Demonów są widoczne na mapie świata, a karta gracza otrzymała akcje operatora do odblokowania i przywrócenia blokady EXP.
- Zlecenia EXPUNLOCK i EXPLOCK działają przez kolejkę silnika, uwzględniają stan not_allowed oraz nie zmieniają danych postaci bez odpowiedzi rdzenia.
- Zachowano nowsze funkcje wdrożonej gałęzi: wyszukiwanie posiadaczy przedmiotów, wykres sesji botów i statystyki odpoczynku.
- Poprawiono format wcześniejszego wpisu changelogu, w którym znaki nowej linii były zapisane dosłownie.

### Zmiany Tieru włączone do 1.112.5

- **Boty na piętrach Wieży Demonów:** instancje 660000, 660001 i kolejne są teraz liczone jako mapa bazowa 66. Boty w środku lochu są widoczne na obrazku Wieży, uwzględniane w natężeniu map i mapie cieplnej, przy zachowaniu współrzędnych mapy bazowej.
- **Sterowanie EXP przez operatora:** karta bota na Playerbots 2.x ma akcję odblokowania EXP oraz przywrócenia blokady osobowości. Polecenia EXPUNLOCK i EXPLOCK trafiają do web_admin_queue, zastępują starsze zlecenie tego samego bota i czekają do ośmiu sekund na odpowiedź silnika.
- Akcja nie jest dostępna dla towarzyszy gracza oraz nie pojawia się na r40250. Status botów nadal działa ze starszym plikiem playerbot_status.tsv, w którym nie ma jeszcze kolumn exp_block i exp_unlock.
- Kolejka rozpoznaje dodatkowy końcowy stan **not_allowed**, a stan nastroju rozróżnia zwykłą blokadę poziomu od odblokowania wymuszonego przez operatora.

![via Codex, Claude & Tieru](https://img.shields.io/badge/via-Codex%2C%20Claude%20%26%20Tieru-8B5CF6)

## 2026-10-07 · 1.112.4 · Wycofanie powiadomienia o nieudanym ulepszeniu

- Usunięto eksperymentalne okno porażki ulepszania wraz z losowymi komunikatami i dźwiękiem z klienta gry.
- Zdarzenia `REMOVE (REFINE FAIL)` nie tworzą już globalnych powiadomień panelu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)
## 2026-10-07 · 1.112.2 · Ekran diagnostyczny błędów

- Każdy błąd HTTP panelu korzysta teraz ze spójnego ekranu diagnostycznego zamiast domyślnej strony Flask.
- Nieobsłużony wyjątek otrzymuje identyfikator zdarzenia, traceback na ekranie i wpis PANEL_INCIDENT w logu panelu.
- Widok błędu działa bez normalnego layoutu oraz bez odczytu ustawień z MariaDB.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-07 · 1.112.1 · Poprawka skrytek w wyszukiwaniu „kto ma najwięcej”

- Skrytki (`SAFEBOX`) w `player.item` mają ID konta w kolumnie właściciela, a nie ID postaci. Wyszukiwanie przypisywało je więc błędnym graczom (np. pid bez postaci). Teraz skrytka trafia do postaci o najwyższym poziomie na tym koncie.
- Konto bez postaci pokazuje się po loginie, bez linku do profilu.

![via Claude](https://img.shields.io/badge/via-Claude-D97757)

## 2026-10-07 · 1.112.0 · Gospodarka sięga do graczy, sesje botów na wykresie

Ta wersja łączy trzy rzeczy: operator może zobaczyć, kto trzyma dany przedmiot, karta gracza pokazuje, kiedy bot grał, a dashboard zaczyna liczyć boty odpoczywające w ramach harmonogramu „boty grają jak ludzie”.

### /economy/item — kto ma najwięcej przedmiotu

- Przycisk „Wyświetl graczy z największą ilością” uruchamia wyszukiwanie tylko na żądanie. Nic nie liczy się w tle. Wynik to top 10 graczy z ilością sztuk.
- Pasek postępu pokazuje etapy: przeszukiwanie ekwipunków, magazynów i sklepów, a potem zestawianie wyników. Każdy wiersz ma czas wykonania.
- Dla każdego gracza widać poziom, portret klasy, flagę królestwa i znacznik „bot”. Nick prowadzi do karty `/player/`.
- Ilość rozbija się na trzy miejsca: ekwipunek (także pas smoków), magazyn i sklep offline. Pokazują się tylko miejsca, w których przedmiot faktycznie leży.
- Wyniki wygasają po 10 minutach. Ponowne kliknięcie w trakcie trwającego wyszukiwania dołącza do niego zamiast uruchamiać drugie.
- Interfejs działa w polskim i angielskim, zgodnie z językiem panelu. Kolory pochodzą z motywu.

### /economy/item — księgi umiejętności

- Księgi (vnum 50300) rozróżniane są po `socket0`, czyli po konkretnej umiejętności. Wynik wyszukiwania prowadzi do statystyk tej jednej księgi, np. „Aura Miecza”, a nie do sumy wszystkich ksiąg.
- Strona przedmiotu pokazuje ilość w obiegu z godziną odczytu oraz historię z ostatnich 14 dni dla tej księgi.

### /player — wykres sesji bota

- Obok pasków PŻ, PM i EXP pojawił się wykres online/offline z ostatnich 24 godzin, w kwadransach co 5 minut.
- Znaczniki co 3 godziny i legenda ułatwiają odczyt. Kolor pochodzi z motywu.
- Wykres pokazuje się tylko przy botach z zapisanymi migawkami. Włącznik „Wykres sesji bota” jest w zarządzaniu panelem funkcjami.

### /dashboard — odpoczywające boty

- Karta „Botów w grze” ma nową komórkę „Odpoczywa (offline)”. Liczba pochodzi z pliku `playerbot_life.tsv`, który zapisuje rdzeń co 10 minut.
- Dopóki rdzeń nie zapisuje pliku, komórka pokazuje „—”. Wartość nie jest odświeżana w tle, więc po zmianie trzeba przeładować stronę.

### Wersja Playerbots

- Konfiguracja Compose (`M2_PLAYERBOTS_VERSION`) została ustawiona na 2.2.74, zgodnie z zainstalowanym serwerem. Dashboard pokazuje tę samą wersję, którą działa gra.

![via Claude](https://img.shields.io/badge/via-Claude-D97757)

## 2026-10-04 · 1.111.1 · UI z gry przejmuje webpanel!

To największa dotychczasowa przebudowa karty postaci oraz kolejny duży etap rozwoju dashboardu, sezonów i rankingów. Webpanel korzysta teraz z języka wizualnego klienta Metin2, zachowując dane na żywo, responsywność i obsługę języka polskiego oraz angielskiego.

### /player/ — interaktywny interfejs z gry

- Cała karta gracza została złożona z natywnych okien Metin2. Ekwipunek, status postaci, umiejętności, Smocza Alchemia, magazyn, mapa, sklep offline i misje tworzą jeden spójny pulpit z oryginalnymi tłami, ramkami, slotami, belkami i zakładkami klienta.
- Układ reaguje na szerokość ekranu. Na komputerze mapa, karta postaci i sklep stoją obok siebie, a na mniejszych urządzeniach mapa przechodzi nad pozostałe okna.
- Okno postaci pokazuje aktualny stan z momentu wejścia na stronę. Wartości WIT, INT, SIŁ i ZR, PŻ, PM, ataku, obrony, szybkości oraz uników wyrównano do pól klienta.
- Najechanie na nazwę postaci pokazuje rangę i punkty rangi, a nazwa rangi otrzymuje właściwy kolor.
- Okno umiejętności odwzorowuje kolejność klienta. Każda umiejętność zajmuje trzy kolejne pola: poziomy 1–20, M1–M10 oraz G1–P. Poprawiono podpisy umiejętności pasywnych, pozycję cyfr i kontrast nieaktywnych ikon.
- Smocza Alchemia obsługuje sześć rodzin kamieni, jakość, stopień +0–+6, zestaw, pozostały czas i bonusy. Punkty 97 i 98 są prezentowane jako Wartość Magicznego Ataku i Magiczna Obrona. Ulepszone kamienie dziedziczą właściwą nazwę oraz ikonę bazowego prototypu.
- Tooltipy przedmiotów otwierają się pod kursorem lub slotem, gdy nad ikoną brakuje miejsca. Nie są już ucinane przez kartę, belkę, zakładki ani przyciski.
- Ekwipunek zachowuje cztery strony i rzeczywisty rozmiar przedmiotów. Broń oraz inne przedmioty wielopolowe rezerwują wszystkie zajmowane sloty.
- Magazyn korzysta z natywnego tła i trzech przełączanych stron. Otwiera się z przycisku depozytu, zachowuje czytelny rozmiar ikon i wraca do ekwipunku po zamknięciu.
- Sklep offline otwiera się automatycznie wraz z kartą gracza. Siatkę przekształcono do układu 16 × 10, dodano nazwę sklepu, wartość potencjalnego zarobku w polu Yang oraz kompaktowy przycisk „Teleportuj do sklepu”.
- Mapa pokazuje aktualne położenie postaci. Korzysta z tych samych obrazów i granic co dashboard, skaluje mapy o różnych proporcjach, a znacznik obraca się zgodnie z kierunkiem ruchu wyliczonym z kolejnych pozycji.
- Okno misji przejęło Kartotekę biologa. Pokazuje zadanie, zbierany przedmiot, stan ekwipunku i pasek postępu. Numeracja obejmuje pełne 14 etapów: Ząb Orka to 7/14, Księga Klątw 8/14, Pamiątka po Demonie 9/14, Matowy Lód 10/14, a Notatka Przywódcy 14/14.
- Zakładka Emocje pozostaje częścią oryginalnej ramki, lecz nie prowadzi do pustego widoku. Status, Umiejętności i Zadania działają bez opuszczania karty.

### /dashboard/ — mapa świata i wiarygodniejsze dane

- Mapa na żywo wróciła do klasycznych kropek. Nazwa bota przy znaczniku ma kolor jego królestwa, a obok nicku widoczny jest kanał gry.
- Ranking i aktywności mapy działają jako zakładki. Diagramy można rozwinąć, a rozkład kanałów, respawny, królestwa, aktywności świata i poziomy botów mają czytelny układ.
- Widget „Boty na mapach” ponownie pokazuje kompletną listę. Naprawiono położenie obok wykresu, przewijanie i wyrównanie kart.
- Dolne widgety korzystają ze wspólnej pamięci podręcznej i ładują ostatni kompletny zestaw natychmiast. Mapa nadal odświeża pozycje niezależnie co 1,5 sekundy.
- Tracker wersji panelu nie porównuje już lokalnej wersji z wydaniem na GitHubie.
- Wykrywanie wersji Playerbots uwzględnia ręczne aktualizacje. Panel wybiera najnowszy poprawny numer z konfiguracji Compose i statusu aktualizatora; ujednolicono raportowanie zainstalowanej wersji.
- Ulepszenia +9 wróciły do Wiadomości ze świata i /world-feed/. Panel scala log.log z log.refinelog, dzięki czemu pokazuje +9 oraz rzeczywistą metodę: kowal, gildia albo zwój wraz z ikoną.

### /season/ — rankingi według osiągnięcia

- Sezon można sortować według punktów, zniszczonych Metinów, pokonanych bossów i udanych ulepszeń.
- Dodano przełącznik Tydzień / Wszechczasów. Widok całego życia korzysta z liczników player.player_special_flag, a tygodniowy z wydarzeń okresu sezonu.
- Zakładki, nagłówki, opisy punktów i przełączniki otrzymały kompletne wersje angielskie.

### /rankings/ — prawdziwe wyniki zamiast martwych liczników

- „Wystawione Stragany” zastąpił ranking „Sprzedaże na sklepie Offline”. Wynik oznacza łączny Yang faktycznie uzyskany ze sprzedaży.
- Usunięto „Yang ze sprzedaży u NPC”, ponieważ silnik zapisał tę statystykę tylko raz w całej historii świata.
- Kolumna klasy może pokazywać ścieżkę magii: Ciało/Umysł, Ostrze/Łuk, Broń/Czarną Magię oraz Smok/Leczenie, także po angielsku.
- Ranking broni porównuje rzeczywiste parametry mieczy, sztyletów, łuków, broni dwuręcznej, dzwonów i wachlarzy z item_proto. Amunicja jest wykluczona.

### Język angielski i spójność

- Natywne okna gracza otrzymały osobne angielskie warianty grafik. Przetłumaczono tytuły, zakładki i przyciski, w tym „Teleport to shop”, bez nakładania tekstu na polskie napisy.
- Rozszerzono tłumaczenia dynamiczne biologa, umiejętności, map, aktywności, historii ekwipunku, sprzedaży offline, sezonów i rankingów.
- Nicki, wypowiedzi graczy i botów oraz surowe dane pozostają w oryginalnej postaci.

### Zaplecze i zgodność

- Panel został sprawdzony przez zespół Playerbots na świecie testowym z wersją 2.2.70: zweryfikowano 57 stron bez wykrytych regresji.
- Kolejka wydawania przedmiotów rozpoznaje wszystkie stany końcowe Playerbots 2.2.70: full, qty_too_big, player_offline, no_skill, has_item i partial. Panel kończy oczekiwanie także przy odmowie lub częściowej realizacji, zamiast pozostawiać operację jako oczekującą.
- Panel korzysta z danych Playerbots 2.2.70: playerbot_status.tsv, player.item, player.item_proto, player.ikashop_offlineshop, log.ikarusshop_log, log.refinelog, log.log i player.player_special_flag.
- Okna przedmiotów pozostają tylko do odczytu poza istniejącymi, jawnie opisanymi akcjami, takimi jak teleport do sklepu.
- Zachowano zgodność z polską i angielską wersją panelu oraz aktualizacją Playerbots wykonywaną automatycznie lub ręcznie.

![Via Codex & Claude](https://img.shields.io/badge/Via-Codex%20%26%20Claude-8B5CF6)

## 2026-10-03 · 1.109.13 · Tooltipy equipmentu i inventory ponad ikonami

- Tooltip aktywnego przedmiotu z wyposażenia oraz dolnej siatki inventory jest renderowany ponad ikonami Alchemii, juków, depozytu i sklepu.
- Podnoszony jest tylko aktywny slot z tooltipem, dzięki czemu tło equipmentu nie zasłania już przycisków interfejsu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.12 · Tooltipy nad przyciskami ekwipunku

- Podczas wskazywania założonego przedmiotu cała warstwa wyposażenia przechodzi nad przyciski Alchemii, juków, depozytu i sklepu.
- Tooltip wraz z nazwą i parametrami nie jest już przecinany ikonami interfejsu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.11 · Ikony +0–+6 dla wszystkich Smoczych Kamieni

- Wspólna reguła ikon obejmuje jawnie wszystkie sześć rodzin: Diament, Rubin, Jadeit, Szafir, Granat i Onyks.
- Rozpoznawanie ulepszonego kamienia nie zależy już od obecności jego dokładnego prototypu w lokalnym zestawie danych.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.10 · Nazwy bonusów ulepszonych Smoczych Kamieni

- Punkty 97 i 98 z silnika są rozpoznawane jako Wartość Magicznego Ataku i Magiczna Obrona, zgodnie z definicjami klienta.
- Ulepszony Smoczy Kamień dziedziczy nazwę i typ bazowego prototypu, więc tooltip nie pokazuje już zastępczej nazwy VNUM.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.9 · Pełne tooltipy górnych kamieni Alchemii

- Tooltipy diamentu oraz dwóch górnych bocznych kamieni otwierają się pod slotem, dzięki czemu nazwa i początek opisu nie są ucinane nad oknem Alchemii.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.8 · Tooltipy sklepów i ulepszone Smocze Kamienie

- Tooltipy przedmiotów w pierwszych czterech rzędach sklepu otwierają się w dół, dzięki czemu panel nie ucina wyliczeń ceny.
- Ulepszone Smocze Kamienie +0–+6 używają ikony bazowego kamienia, więc są widoczne również po założeniu w kole Alchemii.
- Tooltip Smoczego Kamienia pokazuje jakość, poziom ulepszenia i pozostały czas w języku polskim oraz angielskim.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.7 · Tooltipy ponad Alchemią i przezroczysty przycisk

- Tooltipy wyposażenia mogą zasłaniać przycisk Smoczej Alchemii i nie chowają się już pod jego warstwą.
- Przycisk Alchemii nie dodaje tła, obramowania ani efektu motywu do przezroczystego PNG.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.6 · Oryginalna ikona Smoczej Alchemii

- Przycięty fragment screenshota w przycisku Smoczej Alchemii zastąpiono czystą ikoną 32 × 32 px z przezroczystością.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.5 · Większe przyciski i czytelne tooltipy wyposażenia

- Przyciski juków, depozytu i sklepu są odrobinę większe oraz dosunięte do prawej krawędzi wyposażenia.
- Tooltipy górnych slotów otwierają się pod przedmiotem, dzięki czemu karta panelu nie ucina ich górnej części.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.4 · Ikony bezpośrednio nad zakładkami ekwipunku

- Reguły położenia ikon Alchemii, juków, depozytu i sklepu mają teraz właściwą szczegółowość CSS, dzięki czemu przeglądarka umieszcza je przy dolnej krawędzi wyposażenia, tuż nad przyciskami I–IV.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.3 · Wyrównanie przycisków ekwipunku

- Ikony okien znajdują się bezpośrednio nad zakładkami I–IV i pozostają widoczne podczas najechania na wyposażenie.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.2 · Przyciski okien w natywnym ekwipunku

- Przycisk Smoczej Alchemii ma duży rozmiar i znajduje się po lewej stronie wyposażenia, zgodnie z klientem gry.
- Juki konne, depozyt i sklep mieszczą się w prawym dolnym rogu wyposażenia; po otwarciu innego okna przyciski znikają.
- Krzyżyk w Smoczej Alchemii, depozycie i jukach wraca do ekwipunku.
- Ikony założonych przedmiotów wyrównano względem pól klienta, a ich tooltipy wyświetlają się nad belką okna.
- Tytuł okna ekwipunku zmienia się na „Inventory” po wybraniu języka angielskiego.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.1 · Korekta układu natywnego ekwipunku

- Pole wyposażenia zaczyna się 33 px pod belką tytułową, więc hełm i górne sloty nie są już zasłonięte.
- Usunięto pustą przestrzeń między wyposażeniem i zakładkami I–IV.
- Ikony Alchemii, juków, depozytu i sklepu przeniesiono do prawego dolnego rogu wyposażenia.
- Przedmioty w depozycie mają ten sam natywny rozmiar 32 px co przedmioty w ekwipunku.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.109.0 · Oryginalne okno ekwipunku z klienta gry

- Ekwipunek w karcie postaci ma ponownie natywny rozmiar 176 × 565 px.
- Pole wyposażenia, sloty, zakładki I–IV i pasek Yang wykorzystują sprite’y wycięte bezpośrednio z atlasów klienta Metin2.
- Przełączniki Alchemii, juków konnych, depozytu i sklepu otrzymały ikonki zgodne z klientem.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.108.2 · Ikony dopasowane do powiększonego ekwipunku

- Ikony wyposażenia, plecaka i magazynu skalują się teraz razem ze slotami w poszerzonej kolumnie profilu. Zachowano rozmiar potrzebny dla okna Smoczej Alchemii.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.108.1 · Spójne ikony zwojów, tłumaczenie sezonu, koniec trackera wersji

- **Ulepszenia +9 pokazują ikonę zwoju tak samo jak +7/+8** (brakowało powiązania z przedmiotem zwoju), a metoda jest po angielsku: "by scroll (Blessing Scroll)".
- **/season** w całości po angielsku: przełącznik Tydzień/Wszechczasów, kategorie, nagłówki i opisy punktów.
- **Usunięto tracker najnowszej wersji panelu** z dashboardu. Panel aktualizuje się tylko razem z wydaniami Tieru, więc informacja "Dostępna …" była tylko irytująca. Zostaje zainstalowana wersja.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-03 · 1.108.0 · Sezon: zakładki kategorii i ranking wszechczasów; poprawna metoda ulepszeń +9

- **/season: przełącznik Tydzień / Wszechczasów oraz zakładki Punkty, Metiny, Bossy, Potwory, Ulepszenia +7.** Widok wszechczasów czyta liczniki całego życia postaci z silnika (`player_special_flag`), więc jest dokładny i szybki. W widoku tygodniowym potwory nie są liczone (brak zdarzenia w logu), więc ta zakładka tam się nie pojawia.
- **Ulepszenia +9 w wiadomościach ze świata podają teraz prawdziwą metodę** (kowal, zwój, gildia) zamiast zawsze "u kowala". Metodę bierzemy z zapisu `refinelog` z tej samej sekundy i tego samego gracza; poprzednio ~22% takich ulepszeń (zwojem) było źle oznaczonych. Zaktualizowano już zapisane wpisy.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-03 · 1.107.2 · Smocza Alchemia i branding projektu

- Przywrócono tooltipy, filtrowanie klas i zachowanie wybranej strony Smoczej Alchemii po automatycznym odświeżeniu.
- Tooltipy kamieni ponownie pomijają ogólny wymagany poziom, a okno ma podpis viaSeban.
- Ekran logowania otrzymał oficjalny baner Seban WEBPANEL dopasowany do ciemnobrązowo-złotego motywu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

> Odznaka `via` na dole każdego wpisu pokazuje, kto/co stoi za daną zmianą. Praca z asystą AI (Claude albo Codex) dostaje formę `![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)` albo `![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)` — w panelu "Seban" dostaje animowany, przelewający się kolor + gwiazdkę. Kod wniesiony wprost przez Tieru (bez asysty AI, np. przy łączeniu funkcji z jego panelu) dostaje samo `![via Tieru](https://img.shields.io/badge/via-Tieru-f2c34d)`, bez "by".


## 2026-10-03 · 1.107.1 · Brakujące tłumaczenia: Wachlarz i Sprzedaże na sklepie Offline

- Dwa przeoczone w poprzedniej wersji: etykiety filtra broni (Miecz/Sztylet/Łuk/Broń dwuręczna/Dzwon/Wachlarz) i nazwa rankingu "Sprzedaże na sklepie Offline" nie miały wpisów w słowniku angielskim.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-03 · 1.107.0 · Filtr rodzaju broni, pełne tłumaczenie rankingów, nowy ranking sklepów

- **Nowy filtr rodzaju broni w rankingu "Broń"**: Miecz, Sztylet, Łuk, Broń dwuręczna, Dzwon, Wachlarz — każdy liczony osobno, więc sztylet Ninja i miecz Wojownika nie rywalizują już bezpośrednio na tej samej liście (łuki mają z natury wyższe wartości ataku niż sztylety, więc sztylet nigdy nie wygrywał).
- **Kompleksowy przegląd tłumaczeń we wszystkich 25 rodzajach rankingów** — nie tylko to, co zostało zgłoszone. Naprawione m.in.: "40/41 ulepszeń", "3606 złowionych ryb", obrażenia (zwykłe/konno/umiejętność, rekord), Yang zdobyty/ze sprzedaży, zabici/pokonani przeciwnicy, wykopane rudy, misje biologa, oraz nazwy przedmiotów wewnątrz dłuższych opisów (np. "Krwawy Miecz+9 (wymagany poziom 45)" i "Ubranie Czarn. Wiatru+6 (126 obrony)" — wcześniej tłumaczyła się tylko reszta zdania, nazwa przedmiotu zostawała po polsku, bo te dwie rzeczy są jednym połączonym tekstem w bazie). Jedna rzecz zostaje po polsku: nazwy umiejętności w rankingu "Umiejętności" (np. "Strach") — nie ma dla nich osobnej tabeli angielskich nazw, to osobny temat na przyszłość.
- **"Wystawione Stragany" zastąpione realnym rankingiem "Sprzedaże na sklepie Offline"** — poprzednia wersja pokazywała tylko kto ma akurat otwarty stragan live (status, nie osiągnięcie, z czasów sprzed sklepów offline). Nowa liczy całkowity Yang zarobiony ze sprzedaży na sklepie offline, tym samym sprawdzonym mechanizmem co Podsumowanie dnia.
- **Usunięty ranking "Yang ze sprzedaży u NPC"** — silnik prawie nigdy nie zapisuje tej statystyki (1 wiersz w całej bazie), więc ranking był pusty/bezużyteczny. Ten sam powód, dla którego wcześniej usunięto "Polowanie".

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-03 · 1.106.1 · Ranking broni: naprawione dla wszystkich typów + tłumaczenie

- **Ranking "Broń" uwzględniał realne obrażenia tylko dla mieczy** — sztylety, łuki, wachlarze wciąż liczone starym wzorem `wymagany_poziom×10+refine`, więc np. sztylet Ninja +2 na 55 poziom nadal wygrywał z lepiej wyposażonymi postaciami. Znaleziono: `item_proto.value4` (maks. obrażenia) + `value5` (bonus z ulepszenia) to w rzeczywistości uniwersalna para kolumn obecna w **każdym** typie broni — sprawdzone na wszystkich 7 podtypach (miecze, sztylety, łuki, włócznie, dzwonki, wachlarze). Ranking liczy teraz to samo dla wszystkich, bez wyjątków i bez wzorów zapasowych — amunicja (strzały) jawnie wykluczona, żeby nie wskakiwała na szczyt rankingu (miała zawyżone wartości z innego powodu).
- **Panel po angielsku pokazywał "(wymagany level 45)"** zamiast "(required level 45)" w szczegółach rankingu broni/zbroi — ogólna reguła tłumacząca samo słowo "poziom" → "level" działała wcześniej niż reguła dla całej frazy, zostawiając "wymagany" nieprzetłumaczone. Dodano regułę dla całej frazy przed ogólną.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-03 · 1.106.0 · Brakujące ulepszenia +9 w wiadomościach ze świata + poprawiony ranking broni

- **Naprawiono brak ulepszeń +9 w "Wiadomościach ze świata" i tickerze dashboardu.** Przyczyna: silnik gry przy udanym ulepszeniu +8→+9 zapisuje do `log.refinelog` nazwę i poziom przedmiotu *sprzed* ulepszenia (czyli "+8"), więc ta tabela nigdy nie miała ani jednego wiersza z poziomem 9 — zweryfikowane bezpośrednio w bazie (0 z ~900 tys. wierszy). To błąd po stronie silnika C++ (`NotifyRefineSuccess()` w `char_item.cpp` przekazuje stary obiekt przedmiotu zamiast nowego); operator zdecydował na razie o obejściu w panelu zamiast przebudowy silnika. Panel doczytuje teraz brakujące +9 bezpośrednio z `log.log` (ten sam niezawodny mechanizm co w Podsumowaniu dnia, gdzie nazwa przedmiotu jest zapisywana poprawnie) i scala je z istniejącymi +7/+8. Metoda ulepszenia (kowal/zwój) nie jest tam dostępna, więc domyślnie pokazuje "u kowala" — w danych to zdecydowanie najczęstszy przypadek.
- **Naprawiono kolejność w rankingu "Broń".** Wzór liczył moc jako `wymagany_poziom×10 + poziom_ulepszenia`, więc różnica wymaganego poziomu (×10) całkowicie przytłaczała różnicę w ulepszeniu (maks. 9) — przykład zgłoszony przez operatora: Krwawy Miecz+9 (realne obrażenia 130-152) był niżej niż Miecz Lat. Maga+4 (94-120), bo wyższy wymagany poziom tego drugiego dawał więcej punktów niż 5 dodatkowych poziomów ulepszenia. Ranking liczy teraz prawdziwe obrażenia z `item_proto` (baza + bonus z ulepszenia) dla mieczy i podobnych typów broni, które tę wartość posiadają; dla sztyletów/łuków/wachlarzy (bez tych danych w bazie) został stary wzór jako zabezpieczenie, żeby nic się nie pogorszyło.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-03 · 1.105.0 · Ścieżka magii w kolumnie klasy rankingów

- **Nowe, opcjonalne ustawienie w Zarządzanie → Panel webowy: „Ścieżka magii w kolumnie klasy”.** Po włączeniu rankingi pokazują konkretną ścieżkę umiejętności zamiast samej klasy: Wojownik Ciało/Umysł, Ninja Ostrze/Łuk, Sura Broń/Czarna Magia, Szaman Smok/Leczenie — zarówno po polsku, jak i po angielsku. Domyślnie wyłączone; postacie, które jeszcze nie wybrały ścieżki, nadal pokazują samą klasę.
- Zażądane przez operatora (3 października) — zapytanie o 8 nazw ścieżek zmapowane 1:1 na istniejący podział umiejętności (`job`+`skill_group` w `player.player`), bez nowej infrastruktury.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-03 · 1.104.0 · Smocza Alchemia na karcie postaci

- **Karta `/player/` otrzymała okno Alchemii Smoczych Kamieni odtworzone z oryginalnego klienta gry.** Panel korzysta z właściwego tła, zakładek, przycisków klas i obu zestawów alchemii wyciągniętych bezpośrednio z paczki klienta.
- **Okno pokazuje prawdziwe dane postaci.** Wyposażone Smocze Kamienie są odczytywane z obu zestawów, a magazyn alchemii obsługuje sześć rodzajów kamieni, sześć klas i 32 pola na każdej stronie. Ikony mają te same rozbudowane tooltipy co pozostały ekwipunek.
- **Podgląd odświeża się razem z ekwipunkiem co pięć sekund.** Okno w panelu jest świadomie tylko do odczytu, żeby przypadkowe kliknięcie w przeglądarce nie przeniosło ani nie aktywowało kamienia na żywej postaci.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.103.9 · Pełne tłumaczenie aktywności i historii ekwipunku

- **Widget „Aktywności w świecie” tłumaczy teraz także „Ulepsza ekwipunek” i „Gra w grupie”.** Lista nie miesza już polskich nazw z angielskimi.
- **Historia ekwipunku tłumaczy zakupy ze sklepów offline oraz ich szczegóły.** Komunikaty z ceną, liczbą sztuk i sprzedawcą używają teraz po angielsku form „for … Yang” oraz „from …”; poprawka obejmuje również analogiczne wpisy sprzedaży na straganie i zamiany wyposażenia.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-03 · 1.103.8 · Natychmiastowe ładowanie widgetów dashboardu

- **Obciążenie VPS, Boty według map i karuzela rankingów korzystają teraz ze wspólnej pamięci podręcznej.** Dashboard od razu otrzymuje ostatni kompletny zestaw danych, a starszy niż minutę zestaw jest odświeżany w tle bez zatrzymywania strony.
- **Mapa na żywo zachowuje niezależne odświeżanie co 1,5 sekundy.** Przyspieszenie nie opóźnia pozycji botów ani danych mapy live.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-02 · 1.103.7 · Druga poprawka "schodka": limit wysokości listy przywrócony

- Poprzednia wersja (1.103.5) usunęła limit wysokości listy w karcie "Aktywności w świecie / Boty wg poziomu" (`max-height:none`), żeby mogła rozciągać się do pełnej wysokości kolumny na szerokich ekranach. To działało tylko tam, gdzie JS wymusza wysokość kolumny (≥1700px) — w pozostałych układach (węższe ekrany, tryb przełącznika) nic nie ograniczało listy i przy filtrze "Wszystkie" (więcej wierszy) wyjeżdżała poza swoje pudełko.
- Przywrócony skończony limit (`max-height:280px`) jako siatka bezpieczeństwa niezależna od kontekstu — karta nadal rozciąga się, żeby wyrównać dół z panelem Ranking/Aktywności, ale lista wewnątrz zawsze przewija się we własnym, ograniczonym obszarze zamiast ryzykować przelanie.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-02 · 1.103.6 · Panel po angielsku: przedmioty, mapy, eventy i czat na żywo

- **Baza przedmiotów na panelu angielskim pokazuje oficjalne angielskie nazwy przedmiotów** — „Sword+0”, „Long Sword+1”, „Crescent Sword+2” zamiast „Miecz+0”, „Długi Miecz+1”, „Sejmitar+2” (zgłoszenie Edi, 2 października). To nazwy, którymi rdzeń Playerbots mówi do gracza czytającego po angielsku: pliki `static/item_names_en.json` i `static/mob_names_en.json` generuje `tools/generate_game_names_en.py` z pliku `playerbot_names_en.tsv` Playerbots (angielskie nazwy Gameforge i ręczne nazwy przedmiotów tego świata), panel niczego nie tłumaczy sam. Działa wszędzie, gdzie nazwa przedmiotu stoi sama (baza przedmiotów, ekwipunek, rankingi, sklepy), także w wynikach wyszukiwania. Po polsku zostają przedmioty, które w grze nie mają angielskiej nazwy (139 z 6001), i 30 polskich nazw noszonych przez kilka przedmiotów o różnych nazwach angielskich (np. Zwój Powrotu Do Miasta, część fryzur).
- **Wyszukiwarka bazy przedmiotów na panelu angielskim znajduje przedmiot także po angielskiej nazwie** („Sword”, „Town Scroll”); panel polski szuka jak dotąd.
- **Mapy noszą angielskie nazwy, których używa gra**: Mount Sohan, Doyyumhwaji, Ghost Wood, Red Wood, Spider Dungeon i Spider Dungeon 2, Monkey Dungeon II i III zamiast roboczych Sohan Mountain, Fireland, Forest, Red Forest, Monkey Dungeon (Normal)/(Hard) — także wewnątrz dłuższych tekstów (event z mapą, położenie sklepu offline), w podpowiedziach wykresu „Mapy w czasie” i na wykresach słupkowych dashboardu.
- **Historia eventów i trwające eventy po angielsku**: kolumny Event i Score („Zuo: Metin rain · Orc Valley”, „Pirate Tanaka · Event's choice”, „no statistics”, „12 chests”), linie trwającego Tanaki i Zuo, powiadomienie o końcu eventu, status rdzenia oraz dni tygodnia i edytor kalendarza.
- **Czat na żywo po angielsku**: kanały nazywają się jak w angielskim kliencie (CALL, TRADE), złote ogłoszenia rajdów (Azrael, Umarły Rozpruwacz, bossowie świata, z angielską nazwą bossa) są przetłumaczone, a fragment odświeżany co 4 sekundy przychodzi z serwera już przetłumaczony. **Wypowiedzi graczy i botów oraz nicki zostają dokładnie takie, jak je napisano** — dotąd słowniki tłumaczyły ich kawałki („poziom 40” stawało się „level 40”, a gracz o nicku „Las” wyświetlał się jako „Forest”); teraz oznacza je atrybut `translate="no"`, którego pilnuje tłumaczenie po stronie serwera i w przeglądarce. Okrzyki botów są po polsku, bo rdzeń zapisuje w logu tylko polską wersję okrzyku.

![via Tieru](https://img.shields.io/badge/via-Tieru-f2c34d)

## 2026-10-02 · 1.103.5 · Wyrównanie wysokości karty insightów + naprawa "Podsumowania dnia"

- **Naprawiono "schodek"** między nową kartą "Aktywności w świecie / Boty wg poziomu" a panelem Ranking/Aktywności na dashboardzie (powyżej 1700px, gdzie panel insightów pływa obok mapy jako osobna kolumna). Jego wysokość jest teraz dopasowywana do mapy tym samym mechanizmem co panel boczny, a ostatnia karta rozciąga się, żeby wypełnić dokładnie tyle miejsca ile trzeba — oba dolne brzegi równe.
- **Naprawiono "Podsumowanie dnia"** (`/daily-summary/`) — ładowało się 30-40+ sekund albo w ogóle nie działało (timeout). Przyczyna: tabela `log.log` (29 mln wierszy) nie miała żadnego indeksu na kolumnie czasu ani na kombinacji przedmiot+typ zdarzenia, więc każde z kilku zapytań dnia robiło pełne skanowanie. Dodano dwa indeksy (`how+time`, `what+how`) na żywej tabeli (MyISAM, więc krótka blokada zapisu podczas przebudowy, ok. 7-9 minut każdy, zaakceptowana przez operatora) plus jeden indeks na `ikarusshop_log` (InnoDB, bez blokady). Czas ładowania strony spadł z ~39s do ~8s.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-02 · 1.103.4 · Ładne scrollbary w "Aktywności w świecie" / "Boty wg poziomu"

- Listy w obu zakładkach karty insightów na dashboardzie dostały cienkie, kolorowe scrollbary (Chrome/Edge i Firefox) zamiast domyślnych systemowych — kolor dopasowuje się automatycznie do aktywnego motywu (złoty w Cesarstwie).

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-02 · 1.103.3 · Płynna skala typografii/odstępów (telefon → 4K/ultrawide)

- Nagłówki (`h1`/`h2`) i odstępy kart/paneli skalują się teraz płynnie (`clamp()`) zamiast skakać na sztywnych progach pikselowych — dotyczy całego panelu, nie tylko dashboardu.
- Subtelny złoty poblask na kartach i panelach przy najechaniu w motywie Cesarstwo.
- Zbadano pełne przeprojektowanie panelu od zera (makiety w Claude Design) — odrzucone na rzecz tej iteracji, bo obecny dashboard ma już sporo zbudowanej, sprawdzonej roboty (prawdziwe grafiki map per-lokacja, osobno tuningowane proporcje, przełącznik insightów na 1351/1700/2199px), której wyrzucenie byłoby cofnięciem jakości, nie poprawą. Dalszy polish idzie przyrostowo, zakładka po zakładce.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-02 · 1.103.2 · Aktywności w świecie i Boty wg poziomu: jedna karta, dwie zakładki

- **Naprawiono widgety "Aktywności w świecie" i "Boty wg poziomu" wyglądające tragicznie na komputerze** — jako dwie osobne, zawsze widoczne karty wystawały poza pudełko sidebar'a na szerszych ekranach (zgłoszenie ze zrzutem ekranu).
- Teraz to jedna karta z przyciskami-zakładkami do przełączania między widokami, identyczny wzorzec jak istniejące zakładki Ranking/Aktywności na tej samej stronie. Filtr królestwa (Wszystkie/Shinsoo/Chunjo/Jinno) działa wspólnie dla obu zakładek.
- Przy okazji sprawdzono zgłoszenie o bardzo wolnym ładowaniu dolnych widgetów (obciążenie VPS, boty/sklepy wg map, karuzela rankingów): przyczyną było wyczerpanie RAM-u/swap na VPS przy 2000 botach (swap w 100%, zapytanie dashboardu 12 s zamiast <1 s), nie kod panelu. Liczba botów zmniejszona do 1600 — swap spadł do ~62%, zapytanie przyspieszyło do ~6 s.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-01 · 1.103.1 · Dashboard na telefonie: 1,2 MB → 56 KB na jedno odświeżenie

- **Naprawiono niepełne ładowanie dashboardu na telefonie na wolniejszym internecie.** `/api/live-bots` — odpytywane co 1,5 sekundy przez mapę na żywo — przy obecnych ~2000 botach online ważyło 1,19 MB nieskompresowane. Dwie zmiany naraz: (1) endpoint wysyła teraz tylko 15 pól na bota zamiast 34 (reszta — pełne etykiety osobowości, nastroju itd. — i tak nie jest używana przez mapę, tylko przez inne strony), co samo w sobie zeszło do ~430 KB; (2) panel kompresuje teraz gzipem duże odpowiedzi JSON/HTML, co dla tak powtarzalnego tekstu jak JSON zbija to dalej do **~56 KB** — prawie 95% mniej niż na starcie.
- Działa automatycznie dla każdej przeglądarki, która deklaruje obsługę gzip (czyli praktycznie każdej); nic nie trzeba włączać.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-01 · 1.103.0 · Aktywności w świecie i przedziały poziomów (feedback graczy)

- **Nowy widget "Aktywności w świecie" na dashboardzie** — pokazuje, ile botów łowi/robi Biologa/expi/stoi itd. na WSZYSTKICH mapach naraz, z przełącznikiem Wszystkie/Shinsoo/Chunjo/Jinno. Wcześniej dało się to zobaczyć tylko dla jednej wybranej mapy.
- **Nowy widget "Boty wg poziomu"** — ten sam filtr królestwa, pokazuje ile botów jest w każdym przedziale poziomu (1-10, 11-20...), na żywo.
- **Na stronie "Mapy w czasie" doszła sekcja "Boty wg przedziału poziomu"**: aktualne liczby plus wykres historii z ostatnich 7 dni, żeby ocenić tempo przechodzenia botów przez przedziały poziomowe. Kolektor zapisuje teraz migawkę co 5 minut — wykres zacznie się wypełniać od razu, a sensowny trend będzie widoczny po kilku godzinach/dniach.
- Zgłoszone przez gracza Kordyl13 na feedbacku (1 października); oba widgety z dashboardu i wykres trendu korzystają z już istniejących danych na żywo/migawek, bez nowej infrastruktury poza jedną dodatkową migawką w kolektorze.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-10-01 · 1.102.7 · Rozszerzone statystyki sklepów

- **Rozmiar rankingu najszybciej sprzedających się przedmiotów można ustawić w Zarządzanie → Panel webowy.** Dostępne bezpieczne limity to 15, 25, 50 i 100 pozycji.
- **Najpopularniejsze przedmioty w sklepach pokazują również sprzedaż z ostatnich 24 godzin oraz tempo sprzedaży na godzinę.** Dane pochodzą z tych samych rzeczywistych transakcji co ranking sprzedaży.
- **Wyszukiwarka rynku pokazuje stan wyszukiwania**, aby dłuższe zapytanie nie wyglądało jak niedziałający przycisk. Wszystkie nowe elementy mają polską i angielską wersję.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-01 · 1.102.6 · Brakujące komunikaty dashboardu po angielsku

- **Status wersji panelu, komunikat ładowania karuzeli i znacznik odświeżenia mapy reagują teraz na język angielski.** „Aktualna”, „Pobieranie danych” i „Zaktualizowano HH:MM:SS” nie pozostają już po polsku.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-10-01 · 1.102.5 · Pełniejsze angielskie tłumaczenia dashboardu i karty postaci

- **Angielski język obejmuje teraz dynamiczne informacje o respawnach, podpis rankingu, nazwy map na wykresie, komunikaty paska świata oraz dane statusu postaci.** Poprawiono między innymi liczebność i globalne czasy respawnu, polskie nazwy map w canvasie, klasę i poziom postaci, Premium, nastrój, cel, akcję oraz kartotekę Biologa.
- **Tłumaczenie czasowników w pasku wiadomości działa również w JavaScript.** Usunięto granice słów niezgodne z polskimi znakami, przez które „ulepszył” i „rozwinął” pozostawały po polsku.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-30 · 1.102.4 · Puste mapy i botowie walczący z "Człowiekiem"

- **Wykres "Królestwa na mapie" na pustej mapie pokazuje teraz "— 0%" zamiast fałszywie ogłaszać Shinsoo dominującym w 0%.** Wybór "lidera" domyślnie wskazywał pierwsze królestwo z listy, gdy wszystkie liczniki wynosiły zero.
- **Boty walczące z potworami z "Człowiek" w nazwie (Zarażony Człowiek, Zły Człowiek...) mogły nigdy nie dostać etykiety "Możliwie zawieszony", nawet gdy realnie utknęły.** Wykrywanie wędkowania po tekście statusu porównywało proste dopasowanie podciągu, a "lowi" pasowało też do środka słowa "Czlowiek"/"Człowiek" — więc każdy bot walczący z takim potworem wyglądał dla panelu jak wędkarz. Teraz dopasowanie działa na granicach słów.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-30 · 1.102.3 · Wyłącznik wyjaśnień sklepów i poprawka fałszywego "Yang" w gniazdach

- **Zarządzanie → Panel webowy ma teraz przełącznik dla wyjaśnień decyzji sklepów botów** (dodanych wczoraj) — domyślnie włączony, wyłączenie chowa sekcję z tooltipów natychmiast.
- **Naprawiono fałszywe "Yang" w tooltipach broni i zbroi z pustymi gniazdami na kamienie duszy.** Puste gniazdo silnik zapisuje jako VNUM 1 (czyli item_proto "Yang"), nie 0 — panel traktował to jak prawdziwy osadzony kamyk, więc np. Krwawy Miecz+4 z trzema pustymi gniazdami pokazywał "Yang" trzykrotnie. Zgłoszone przez [GA]Seban.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-30 · 1.102.2 · Równa siatka ekwipunku

- **Usunięto przypadkowe kwadraty przy pierwszym i 26. slocie ekwipunku na karcie postaci.** Tło SVG miało 71 współrzędnych zapisanych z przecinkiem dziesiętnym, których przeglądarka nie interpretowała prawidłowo; wszystkie współrzędne mają teraz poprawny zapis z kropką.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-30 · 1.102.1 · Niższe wiersze rankingu Broń 30 Lv na telefonie

- **Kolumna "Wynik" w rankingach (najbardziej widoczne na Broń 30 Lv, z długim opisem i ikonką sklepu) już nie zawija tekstu na kilka linii na wąskim ekranie** — poniżej 650px jest przycięta do jednej linii z wielokropkiem, pełny tekst dalej dostępny po przytrzymaniu/najechaniu. Pozostałe kolumny tabeli już wcześniej nie zawijały się, więc tylko ta jedna winduje wysokość wiersza.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-30 · 1.102.0 · Panel wyjaśnia decyzje sklepów botów

- **Tooltip przedmiotu na straganie bota pokazuje teraz, dlaczego bot go wystawił i jak krok po kroku wyliczył cenę** — dokładnie funkcja opisana w changelogu Tieru dla Playerbots 2.2.39 ("panel klasyczny wyjaśnia decyzje botów"). Silnik od tej aktualizacji zapisuje to do dwóch nowych tabel (`log.playerbot_listing`, `log.playerbot_equip`), a Seban Panel czyta pierwszą z nich.
- Słowniki kodów (dlaczego coś jest towarem, kolejne kroki wyceny, powód zdjęcia z lady...) są wyciągnięte wprost z kodu panelu klasycznego Tieru (referencyjna implementacja), nie zgadywane — więc znaczenie każdego kodu jest identyczne jak tam, tylko po polsku/angielsku zamiast czterech języków.
- **Celowo węższy zakres na start**: tylko wyjaśnienie sklepu (najbardziej widoczna część z changeloga). Powód zmiany założonego ekwipunku i osobna strona "Decyzje" ze światowym filtrem anomalii to naturalny kolejny krok, ta sama para tabel już to obsłuży.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-30 · 1.101.6 · Prawidłowa szybkość ataku broni dwuręcznych

- **Tooltip odejmuje stałą karę 10 punktów szybkości od wbudowanego bonusu broni dwuręcznych, dokładnie jak klient Metin2.** Ostrze z Czerwonej Stali (VNUM 3210–3219) pokazuje teraz 15% zamiast surowych 25% z item_proto; reguła obejmuje wszystkie bronie dwuręczne i nie zmienia bonusów dodanych do przedmiotu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-30 · 1.101.5 · Zielone warianty bonusów w tooltipach

- **Bonusy wbudowane ponownie są zielone, a bonusy dodane mają jaśniejszy odcień zieleni.** Zachowują czytelne rozróżnienie bez skojarzenia z kolorem wartości negatywnych; ujemne bonusy nadal korzystają z osobnego koloru ostrzegawczego.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-30 · 1.101.4 · Poprawny priorytet kolorów bonusów przedmiotów

- **Kolor bonusów wbudowanych nie jest już nadpisywany przez ogólną regułę bonusów.** Szybkość zaklęcia i witalność pochodzące z definicji przedmiotu mają teraz subtelny, jasny kolor; cztery bonusy dodane pozostają zielone.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-30 · 1.101.3 · Tooltipy przedmiotów zgodne z klientem i motywem

- **Wbudowane bonusy przedmiotu oraz bonusy dodane są wyświetlane osobnymi kolorami**, tak jak w kliencie Metin2. Reguła działa we wspólnym tooltipie wyposażenia, ekwipunku, magazynu, torby konia i sklepów offline.
- **Tło, obramowanie, tekst podstawowy i akcent tooltipu korzystają z kolorów aktywnego motywu panelu.** Usunięto stałe niebieskie tło i obramowanie.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-30 · 1.101.2 · Komendy GM po angielsku i ticker wiadomości ze świata

- **`/gm-commands` ma teraz osobny, w pełni przetłumaczony plik angielski** — treść jest w `<pre>`, którego tłumacz panelu świadomie nie rusza (tak samo jak surowego zrzutu logów czy przykładów shellowych w Zarządzaniu), więc zamiast łatać silnik dorobiłem prawdziwe angielskie źródło i panel wybiera właściwy plik po języku.
- **Ticker "Wiadomości ze świata" na dole dashboardu tłumaczy się teraz w całości** — brakowało komunikatów specyficznych dla tego paska (znalezienie Małża, otwarcie Szkatułki Umarłego Rozpruwacza) oraz etykiet sposobu ulepszenia (u kowala / zwojem / w kuźni gildii) doklejanych do wiadomości o ulepszeniu.
- **Poprawiono nazwę na oficjalną angielską**: "Szkatułka Blasku Księżyca" to teraz wszędzie "Moonlight Treasure Chest", nie robocze "Moonlight Chest".

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-29 · 1.101.1 · Domykanie tłumaczenia panelu

- **Dołożono tłumaczenia, których zabrakło w pierwszej wersji**: aktualnie wykonywana misja (Biolog/koń bojowy/polowanie) na `/player/`, historia ekwipunku, potwierdzenie usunięcia postaci, nazwy eventów (Szkatułki Blasku Księżyca, Zuo: deszcz Metinów), rangi GM, oraz cała treść generowana przez JavaScript na żywo: aktywności na mapie, pozycje botów na mapie, filtr map/kanałów, kreator postaci, powiadomienia i pasek wiadomości.
- Changelog **celowo zostaje po polsku jako zapis historyczny** — to setki gęstych, technicznych wpisów, osobny, dużo większy temat niż tłumaczenie samego panelu.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-29 · 1.101.0 · Panel po angielsku

- **Cały panel webowy można teraz przełączyć na angielski** — nowy wybór języka w Zarządzanie → Panel webowy → Wygląd i działanie. Domyślnie zostaje polski, nic się nie zmienia dopóki ktoś sam nie wybierze English.
- **To prawdziwe tłumaczenie treści, nie automatyczny/dosłowny przekład**: menu, wszystkie strony (dashboard, rankingi, gracze, gildie, gospodarka, mapy, eventy, respawny, diagnostyka, zarządzanie grą i panelem, kreator postaci, baza przedmiotów...), etykiety statystyk przedmiotów w tooltipach (te same co widać na każdym przedmiocie w całym panelu), dynamiczne komunikaty statusu i tytuły stron w przeglądarce.
- **Działa też dla treści doładowywanych przez JavaScript** (dashboard na żywo, mapa botów, karuzela rankingów) — ten sam słownik tłumaczeń jest wysyłany do przeglądarki i stosowany na bieżąco do nowo pojawiających się elementów.
- Świadomie **poza zakresem zostały**: nazwy przedmiotów/potworów/umiejętności z bazy gry (to lokalizacja klienta gry, nie panelu) oraz historyczne wpisy tego changeloga (zostają jako zapis źródłowy po polsku).
- Mechanizm nie dotyka żadnego z tysięcy miejsc w `app.py`/szablonach, gdzie polski tekst jest dziś zaszyty na stałe — tłumaczy już wyrenderowaną stronę, więc ryzyko regresji w istniejącym kodzie jest minimalne.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-29 · 1.100.13 · Przedmioty na sklepie liczą się w rankingach

- **Rankingi Zbroja, Broń, Broń 30 Lv i Przedmiot +9 uwzględniają teraz przedmioty wystawione na własnym straganie gracza/bota** — wcześniej znikały z rankingu w chwili wystawienia na sprzedaż (np. broń z realnie wyższymi obrażeniami stała niżej niż gorsza sztuka, bo lepsza akurat leżała na sklepie). Dla Zbroi/Broni ranking bierze teraz mocniejszy z dwóch: założony egzemplarz lub ten wystawiony na sklepie.
- **Przedmiot na sklepie dostaje w rankingu ikonkę tobołka i fioletową poświatę na opisie**, żeby było widać, że akurat wisi na straganie, a nie jest założony.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-29 · 1.100.12 · Dzienny licznik Szkatułek Umarłego Rozpruwacza

- **Podsumowanie dnia pokazuje liczbę otwartych Szkatułek Umarłego Rozpruwacza jako „tego dnia / ogółem”.** Statystyka obejmuje graczy i boty oraz liczy zdarzenia rdzenia bez analizowania wylosowanych nagród.
- **W Zarządzanie → Panel webowy można wyłączyć komunikaty o otwieraniu skrzyń w Wieściach ze świata.** Przełącznik jest domyślnie włączony i nie wyłącza statystyki dziennej.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-29 · 1.100.11 · Łupy ze Szkatułki Ripera także dla prawdziwych graczy

- **Rdzeń gry zapisuje teraz otwarcie Szkatułki Umarłego Rozpruwacza przez prawdziwego gracza jako dokładne zdarzenie `CHEST_OPEN`.** Wpis zawiera VNUM i nazwę faktycznie zdobytej nagrody, więc Wieści ze świata nie zależą od Historii ekwipunku ani od mechanizmu botów. Dotychczasowy format `USE_ITEM` botów pozostaje obsługiwany.
- **Nowe zdarzenie pojawia się przy najbliższym odświeżeniu `/world-feed`**, bez oczekiwania na pięciominutowy kolektor.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-29 · 1.100.10 · Poprawne wersje dashboardu i łupy ze Szkatułki Ripera

- **Wskaźniki „Wersja panelu” i „Wersja Playerbots” aktualizują własne pola** — numer Playerbots nie trafia już do kafelka panelu, a etykieta Playerbots nie zostaje na „Ładowanie…”. Numer Seban Panel jest zawsze czytany z jego pliku `VERSION`, nawet gdy paczka Playerbots przekaże w zmiennej środowiskowej własny numer wydania.
- **Wieści ze świata pokazują otwarcia Szkatułki Umarłego Rozpruwacza (VNUM 50082)** przez graczy i boty razem z nazwą, liczbą oraz ikoną zdobytej nagrody. Dane pochodzą z rzeczywistych wpisów `USE_ITEM` rdzenia gry; zdarzenia pozostają na `/world-feed` i nie zaśmiecają dolnego paska wiadomości.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-29 · 1.100.9 · Aktualna wersja Seban Panel na dashboardzie

- **Widget „Gildie botów” zastąpił wskaźnik „Wersja panelu”**, zbudowany tak samo jak wskaźnik Playerbots. Przy każdym otwarciu lub odświeżeniu dashboardu panel porównuje lokalny plik `VERSION` z wersją na GitHubie i pokazuje „Aktualna” albo „Dostępna X.Y.Z”. Brak połączenia z GitHubem nie blokuje dashboardu i jest czytelnie sygnalizowany.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-28 · 1.100.8 · Skrzynia Ucznia na Playerbots 2.x to jeden przełącznik dla graczy i botów

- **Na Playerbots 2.x (mt2009) przełącznik „Skrzynia startowa” w Zarządzaniu steruje flagą świata `m2_starter_chest_off`** — tą samą, którą czyta quest skrzyni przy pierwszym logowaniu gracza, seed przy tworzeniu bota i rdzenie dla botów, które już są w świecie. Wyłączona: nowa postać gracza jej nie dostaje, nowe boty rodzą się bez niej, a boty tracą nieotwarte skrzynie z łańcucha (skrzyń graczy nic nie rusza). Zapis działa od razu przez kolejkę `web_admin.quest` (`STARTER_CHEST`, Playerbots 2.2.38) i zostaje po restarcie; gdy gra nie odpowiada, panel mówi, że zadziała przy następnym starcie. Dotąd panel pisał do `common.m2_switches`, którego na mt2009 nic nie czyta, więc skrzynie wracały mimo wyłączenia. Na pozostałych silnikach bez zmian.

![via Tieru](https://img.shields.io/badge/via-Tieru-f2c34d)

## 2026-09-28 · 1.100.7 · Wylogowanie nie nachodzi na rozwijane menu

- **Przycisk „Wyloguj” zachowuje własne miejsce pod całą nawigacją również przy wysokości 1080 px.** Otwarcie sekcji „Zarządzanie” albo „Konta i GM” nie ściska już listy i nie układa przycisku na pozycjach podmenu; przy krótszym ekranie cały pasek przewija się jako jedna kolumna.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-28 · 1.100.6 · Gracze w rankingach, teleport na kanał bota i poprawki z kopii panelu w Playerbots

- **Rankingi, karuzela na dashboardzie i sezon liczą boty razem z postaciami graczy, bez postaci GM-ów** (z rangą w `common.gmlist`, np. Admin, AdminNinja, AdminSura i AdminSzaman z konta admin — dotąd wykluczała je lista imion, która nie widziała GM-a założonego w panelu pod innym imieniem). Gracz ma 👤 i podświetloną linię, a „👤 Tylko gracze” pokazuje samych ludzi, ponumerowanych między sobą i ze stronicowaniem. Przełącznik „Prawdziwi gracze w rankingach” jest teraz domyślnie włączony (wyłącza go zapisane 0), bo panel klasyczny Playerbots czyta ten sam wiersz i oba panele mają liczyć to samo. Ranking „Broń 30 Lv” nie bierze już przedmiotów z magazynu (tam `owner_id` to konto, nie postać), a „Najwyższy poziom” w sezonie nie stoi na zawsze na 90 poziomie GM-ów. Zgłosił blipu.
- **„Teleportuj mnie” przenosi postać na kanał bota**, nie tylko na jego współrzędne na kanale, na którym stała postać (zgłosił prodnathin). Działa z `web_admin.quest` z Playerbots 2.2.37; starszy quest odpowiada `bad_args`, a panel ponawia wtedy zwykły teleport na kanale postaci, jak dotąd.
- **Tanaka i Zuo na wybranej mapie**, tak jak uruchamia je Playerbots od 2.2.28.
- **Etykiety osobowości znają rzadkie osobowości (10–14) i czterech hazardzistów z Community Patch 5 (15–18)**, a karta bota pokazuje blokadę expa przy nastroju.
- **Suwaki celów AI mają opis po najechaniu**: co dokładnie zmienia każdy i jak szybko. Kowal, Księgi, Biolog i Misje polowania kończą się na 100, bo przy 100 boty robią to już przy każdej okazji; „Wszystko na 100” nie rusza wrogości królestw, a zapis nie nadpisuje ustawień, których strona nie pokazuje.
- **Strona gildii pokazuje też gildie prowadzone przez graczy** (zgłosił Derpsonkowy95).
- **Sklep offline bota na karcie postaci ma 16 rzędów, gdy towar stoi też w polach 80–159**, zamiast rysować drugą połowę na pierwszej.
- **Tooltip oferty podaje cenę za cały stos raz**, z liczbą sztuk.
- **Zgodność z Playerbots 2.x trzymana dotąd tylko w kopii panelu w paczce Playerbots:** kolektor czyta `playerbot_status.tsv` po nagłówku (kolumny osobowości Iwakury) i liczy tylko oferty, które da się kupić; raty na mt2009 czytane z flag gry, z bazą eventu; brak tabeli przełączników, zrzutu sklepów czy skrzyni ucznia w bazie nie wywraca strony; Zarządzanie pokazuje liczbę botów na każdym kanale i link do masowego nadawania przedmiotów; obraz buduje się także bez wygenerowanego `VERSION`. Ranking „Polowanie” usunięty, bo `levelup.quest` nie działa na mt2009.

![via Tieru](https://img.shields.io/badge/via-Tieru-f2c34d)

## 2026-09-28 · 1.100.5 · Animacja ładowania dla statystyk "Stan serwera"

- **Widget "Zalogowane boty wg kanału" dostał tę samą animację ładowania (shimmer) co "Zalogowane boty" wg królestw** — wcześniej mignął pusto zanim dane dotarły. Przy okazji ten sam efekt dostały też pozostałe liczby w karcie "Stan serwera" (botów w grze, śr. poziom, w grupach, maks. poziom, gildie botów), które wcześniej krótko pokazywały "0" zamiast animacji ładowania.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-28 · 1.100.4 · Nowy widget: zalogowane boty wg kanału

- **Dashboard "PLAYERBOTS · ŚWIAT" ma teraz drugi widgecik pod rozkładem królestw: "Zalogowane boty wg kanału"** — pokazuje CH1–CH4 z kolorowymi kropkami identycznymi jak obwódki na mapie na żywo. Naprawiono też błąd, przez który widget początkowo pokazywał samą cyfrę zamiast rozbicia na kanały — oba widgety (królestwa i kanały) używały tej samej klasy CSS, więc skrypt dociągający dane na żywo aktualizował tylko pierwszy z nich.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-28 · 1.100.3 · Kolory CH3/CH4 na mapie na żywo

- **Mapa świata botów, legenda i wykres "Rozkład kanałów" rozpoznają teraz kanały CH3 (biała obwódka) i CH4 (czarna obwódka)** — przygotowanie pod Playerbots 2.2.36, który pozwala włączyć dwa dodatkowe kanały. Reszta panelu (filtr kanałów, wybór na mapie, wykres botów wg kanału na mapach) już wcześniej skalowała się automatycznie do dowolnej liczby wykrytych kanałów.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-28 · 1.100.2 · Przetopy (gniazda akcesoriów) w tooltipach

- **Tooltipy bransolet, naszyjników i kolczyków pokazują teraz włożone przetopy**: stopień gniazda (np. "Ebonit 2/2"), realny bonus jaki dają (np. Siła +2, Maks. PŻ +80 — zweryfikowane wprost w kodzie silnika i na żywych postaciach), pozostały czas do degradacji o jeden stopień oraz liczbę pustych, niewykorzystanych kieszeni. Ikona materiału pokazana dla kolczyków (potwierdzone jako "Ebonit"); dla bransolet/naszyjników pokazuje się sam bonus bez nazwy materiału, bo silnik jej nigdzie nie zapisuje.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-28 · 1.100.1 · Wybór miejsc legendarnych ogłoszeń

- **Zarządzanie panelem pozwala niezależnie wybrać trzy miejsca dla ogłoszeń o bossach, rajdach i lochach:** Czat na żywo, Wieści ze świata oraz dolny pasek wiadomości. Można włączyć dowolny zestaw, wszystkie miejsca albo wyłączyć je całkowicie.
- **Nowe i dotychczasowe instalacje domyślnie pokazują ogłoszenia wszędzie.** Wyłączenie dotyczy wyłącznie legendarnych komunikatów i nie ukrywa zwykłego czatu ani pozostałych wydarzeń świata.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-28 · 1.100.0 · Pełna zgodność funkcji administracyjnych z Playerbots 2.2.35

- **Karta postaci otrzymała brakujące akcje z panelu Tieru:** wyszukiwarkę i kategorie przedmiotów, nadawanie Yang z presetami, zmianę poziomu, teleport do 11 lokacji oraz godzinny bonus szybkości biegu. Polecenia korzystają z tego samego interfejsu `web_admin_queue`, który obsługuje rdzeń gry.
- **Zarządzanie grą ma presety rat, poziom trudności świata, konfigurację dostępu do autołowów oraz CH2.** Poziom trudności ustawia czasy Biologa, Stajennego i ksiąg osobno dla graczy i botów; CH2 zachowuje wybrany podział botów i wchodzi przy restarcie.
- **Uzupełniono audyt ustawień AI z Playerbots 2.2.35:** twarde wyłączenie dropu Szkatułek Blasku z pamiętaniem obu szans, zakupy botów w M2 oraz czas i odstęp wojen gildii. Wrogość królestw, próg zwojów i wyprawy na Metiny były już obsługiwane i pozostały dostępne.
- **Kartoteka Biologa rozpoznaje osiem klasycznych badań** od Zębów Orka do Notatek Przywódcy, pokazuje nazwę zbieranego przedmiotu, liczbę sztuk w ekwipunku i przejście do etapu poszukiwania właściwego Kamienia Duchowego.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-28 · 1.99.1 · Naprawiono etykietę wersji Playerbots na dashboardzie

- **Dashboard pokazywał "Brak wersji lokalnej" pod poprawnie wyświetloną wersją Playerbots** (np. "2.2.33") — dashboard pomijał sprawdzenie GitHub dla przyspieszenia pierwszego renderu, co było zbędne odkąd te dane i tak ładują się asynchronicznie w tle (od 1.94.0). Dashboard znowu pokazuje realny stan, np. "Dostępna 2.2.34".

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-28 · 1.99.0 · Pełne dzienne osiągnięcia świata

- **Podsumowanie dnia pokazuje teraz prawdziwe dzienne rekordy:** najwięcej pokonanych graczy, udanych ulepszeń, spalonych przedmiotów oraz największy zarobek netto ze sklepu offline.
- **Dodano trzy najcenniejsze osiągnięcia +9 dnia:** broń poziomu 30/75 z co najmniej 40% średnich obrażeń, nowy rekord zbroi +9 oraz zdobycie odznaki Złotego Młota Kowala za pełny założony zestaw +9.
- **Naprawiono najwyższy poziom dnia:** historyczny wynik pochodzi z logu awansów i pomija całe konta GM oraz stałych towarzyszy graczy. Dotychczasowe Lv 99 pochodziło właśnie z tych wykluczonych postaci.
- **Duże liczniki ryb i rudy są formatowane czytelnie** z odstępami tysięcy; istniejące podsumowania również korzystają z nowych obliczeń po otwarciu.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-27 · 1.98.1 · Numerowane strony i pole "Idź do strony"

- **Paginacja rankingów ma teraz numerowane strony** (1, 2, 3…ostatnia, ze zwijaniem "…" pomiędzy) zamiast samego Poprzednia/Następna, plus pole do wpisania numeru strony i przejścia od razu.
- **Przyciski paginacji dopasowują się do aktywnego motywu** panelu (Ocean/Ember/Forest/Empire) zamiast sztywnego niebieskiego.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.98.0 · Gildia i paginacja w rankingach

- **Rankingi botów pokazują teraz kolumnę "Gildia"** przy każdym graczu/bocie.
- **Dodano stronicowanie** ("Poprzednia"/"Następna") zamiast sztywnych 100 pozycji.
- **Dodano wybór liczby wyników na stronę**: 100 / 200 / 500 / 1000.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.97.1 · Naprawiono ranking zbroi

- **Ranking `/rankings?type=armor` źle porównywał zbroje**: liczył `poziom_wymagany × 10 + stopień_ulepszenia`, więc np. zbroja poziom 42 +7 (realnie 97 obrony) wychodziła wyżej niż zbroja poziom 34 +9 (realnie 101 obrony). Naprawione na dokładny wzór gry: obrona = wartość bazowa zbroi + 6 punktów za każdy stopień ulepszenia — zweryfikowane wprost w bazie na graczach top1/top6 i zgodne z tabelą przysłaną przez operatora. Ranking pokazuje teraz realną wartość obrony zamiast wymaganego poziomu.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.97.0 · Gradientowa odznaka poziomu dla światowej top 10

- **Postacie należące do pierwszej dziesiątki rankingu poziomu otrzymały rozpoznawalną odznakę poziomu:** ciemny gradientowy kafelek, pomarańczowy tekst i świetlista dolna krawędź odtwarzają wygląd przesłanego wzoru.
- **Oznaczenie działa w całym panelu:** w głównym rankingu, karuzeli dashboardu, rankingu i podpisach mapy na żywo, profilu postaci, bazie graczy, kontach, gildiach, osobowościach, diagnostyce, sezonie oraz podglądzie odbiorców przedmiotów.
- **Top 10 korzysta z tego samego źródła i kolejności co ranking poziomu:** poziom malejąco, następnie doświadczenie, z uwzględnieniem ustawienia dotyczącego prawdziwych graczy. Podpowiedź odznaki pokazuje dokładną pozycję od #1 do #10.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-27 · 1.96.0 · Prawdziwa mapa cieplna i porządki w tabelach

- **Mapa cieplna na `/maps` i dashboardzie pokazuje teraz faktyczne zagęszczenie zdarzeń:** pojedyncze punkty zastąpiła płynna warstwa od niebieskiego przez zieleń i żółć do czerwieni. Ten sam renderer obsługuje zgony botów, rozbite Metiny i zabitych bossów.
- **Dodano brakujące mapy Season 2 do wyboru mapy cieplnej:** Ognistą Ziemię, Loch Pająków V2 oraz obie Groty Wygnańców.
- **Naprawiono poziome przepełnienia w `/manage`:** rajdy na Azraela i ustawienie prawdziwych graczy w rankingach mieszczą się w panelu także na węższych ekranach.
- **Uporządkowano kolejkę nicków:** wolne nicki oczekujące na użycie są pierwsze, w kolejności priorytetu; zajęte i zablokowane pozycje trafiają niżej. Pole dodawania respektuje aktywny motyw, a kolumna akcji zachowuje wysokość pozostałych komórek.
- **Wyrównano kolumnę wyniku w rankingach** dla wszystkich zestawień poza poziomem.
- **Dodano informację o zgodności komend GM:** panel jasno zaznacza, że komendy pochodzące z ogólnych poradników mogą być niedostępne w konkretnej kompilacji rdzenia.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-27 · 1.95.0 · Koniec funkcji-widm na czystych instalacjach

- **Pełny audyt zgodności z Playerbots 2.2.29:** sprawdzone zostały oficjalne archiwum serwera, compose, questy, rdzeń, panel Tieru i usługi dołączone do wydania. Wynik wraz z macierzą funkcji znajduje się w `AUDIT_COMPATIBILITY_2.2.29.md`.
- **Nowa konsola zgodności w `/manage/panel`:** operator może osobno udostępnić sześć integracji, których czysta instalacja nie gwarantuje: docelową liczbę botów, plan wejścia, dokładne respawny map, skrzynię startową na żywo, ogłoszenia +9 i Aktualizator Seban. Każda karta podaje wymaganie oraz instrukcję wdrożenia.
- **Funkcje-widma już nie udają działających:** wyłączone integracje pozostają widoczne na szaro z komunikatem „Wymaga akcji”, a backend blokuje również ręczne wywołanie ich endpointów. Czysta instalacja ma je domyślnie wyłączone.
- **Bezpieczna migracja istniejącego serwera:** instalacje z `M2_PANEL_CUSTOM_PATCHES=1` zachowują dotychczasowe działanie. Po pierwszym zapisie konsoli każdą funkcją steruje już jej własny przełącznik.
- **Funkcje natywne 2.2.29 pozostają dostępne:** raty, globalne respawny, zachowanie AI, ItemShop, rajdy, polityka przedmiotów, trzymanie botów przy wejściu, kolejka przedmiotów i monitoring nie dostały zbędnych blokad.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-27 · 1.94.8 · Naprawiono "Brak danych live" i plakietkę mapy

- **Zielona plakietka "X botów na mapie" dublowała się z "Widoczne" obok mapy** — zamieniona na znacznik czasu ostatniej aktualizacji ("Zaktualizowano HH:MM:SS"), żeby potwierdzać że dane faktycznie odświeżają się na żywo.
- **Znaleziono i naprawiono prawdziwą przyczynę "Brak danych live"**: szybka wersja dashboardu (1.94.0) wysyłała danym o czasach respawnu zły kształt, przez co JS rzucał błąd przy każdym odświeżeniu mapy (nie tylko przy realnych problemach z siecią) i przerywał całe renderowanie — obok plakietki gasły też diagramy "Respawny na mapie". Naprawione po stronie Python (poprawny domyślny kształt danych) i JS (dane respawnu wczytywane na bieżąco zamiast raz przy starcie strony, plus zabezpieczenie na przyszłość gdyby kształt znów się nie zgadzał).

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.94.7 · Ikonki botów i lista rankingu na węższych ekranach

- **Ikonki botów na mapie skalują się teraz razem z mapą** zamiast być zawsze 18px — na węższych ekranach (np. 1366×768, gdzie mapa jest mniejsza) były nieproporcjonalnie duże i nakładały się na siebie.
- **Naprawiono nakładanie się powiększonej mapy na diagramy** po kliknięciu "Diagramy mapy" — mapa przestała "wylewać się" poza swoją kolumnę siatki na węższych ekranach.
- **Lista "Ranking na mapie"/"Aktywności na tej mapie" miała ledwie ~15-27px wysokości** na węższych ekranach (mapa, do której dopasowana była wysokość panelu bocznego, sama była bardzo niska) — panel boczny ma teraz minimalną wysokość, więc lista mieści kilka czytelnych pozycji nawet gdy mapa jest niska.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.94.6 · Mapa na 1920×1080 mieści się bez przewijania

- **Poszerzona mapa (492×616px) była wyższa niż zostawało miejsca w jednym ekranie** na 1920×1080 — trzeba było przewijać stronę, żeby zobaczyć ją w całości. Wysokość mapy jest teraz ograniczona do ~520px z zachowaniem proporcji (szerokość dopasowuje się do wysokości, nie na odwrót) — cała mapa mieści się na ekranie bez przewijania w jej obrębie. Dotyczy tylko 1351–2199px, monitor 2K bez zmian.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.94.5 · Poprawki mapy tylko do 2199px, 2K bez zmian

- **Dzisiejsze poprawki mapy (1.94.1–1.94.3) dotyczą teraz wyłącznie ekranów 1351–2199px.** Monitor 2K (2560×1440) wraca do dokładnie oryginalnego układu sprzed tych poprawek — bez zakładek Ranking/Aktywności, ten sam wzór skalowania mapy co wcześniej. Operator poprosił o to wprost: jego monitor nigdy nie miał problemu ze ściśniętą mapą, więc nie powinien dostawać zmian pomyślanych dla mniejszych ekranów (np. 1920×1080).

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.94.4 · Naprawiono cache przeglądarki dla stylów mapy

- **`live-overrides.css` (style mapy świata botów) był ładowany z JS pod stałym adresem, bez numeru wersji w URL-u** — jedyny plik CSS w panelu pomijający mechanizm cache-busting. Przeglądarka mogła latami trzymać starą wersję tego pliku niezależnie od wdrożeń, przez co dzisiejsze poprawki mapy (1.94.1–1.94.3) mogły nie być widoczne bez twardego odświeżenia (Ctrl+Shift+R). Dołączony teraz normalnie w `base.html`, tak jak reszta arkuszy stylów.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.94.3 · Zakładki Ranking/Aktywności przy mapie

- **Sekcja "Aktywności na tej mapie" znikała za rankingiem** na desktopie: ranking miał sztywne 380px, a aktywnościom zostawało ledwie ~30px (sam nagłówek, bez treści) — widoczne jako pusta "dziura" pod rankingiem, szczególnie po powiększeniu mapy. Panel boczny dostał zakładki "Ranking"/"Aktywności" (jak istniejący przycisk "Diagramy mapy") — aktywna zakładka zajmuje całą dostępną wysokość.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.94.2 · Pułap rozmiaru mapy na monitorach 2K+

- **Mapa świata botów miała brak górnego limitu rozmiaru** po poprzedniej poprawce — na monitorze 2K (2560 px) rosła wraz z szerokością ekranu i robiła się zbyt duża. Obszar mapy jest teraz zamrożony na rozmiarze potwierdzonym jako dobry na 1920×1080; szersze ekrany dostają po prostu większy margines z prawej, a nie większą mapę.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.94.1 · Poprawka mapy na szerokich ekranach

- **Naprawiono ściśniętą mapę świata botów na szerokich monitorach** (np. 1920×1080): siatka mapy rezerwowała widmową, niewykorzystywaną kolumnę 300px, a panel "Stan serwera" zabierał sztywno połowę szerokości strony, przez co mapa robiła się wąska i wysoka. Mapa dostaje teraz całą wolną przestrzeń, a diagramy (Rozkład kanałów, Respawny, Królestwa) na bardzo szerokich ekranach (≥1700px) mają własną kolumnę zamiast nachodzić na ranking.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.94.0 · Szybszy dashboard i ładowanie widgetów w tle

- **Dashboard wysyła teraz szybki shell natychmiast po wejściu**, a cięższe rankingi, agregacje logów, snapshoty sklepów i monitoring są pobierane osobno po renderze.
- **Widgety oczekujące na dane pokazują dopasowany do motywu skeleton shimmer**, zamiast blokować całą stronę pustym oczekiwaniem.
- **Dane na żywo, mapy, monitoring i rankingi zachowują dotychczasowe funkcje**, ale pojawiają się stopniowo, gdy ich źródła zakończą pracę.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-27 · 1.93.1 · Poprawka wyceny sklepiku offline

- **Naprawiono "Potencjalny zarobek" na karcie gracza**: cena z `ikashop_data` to cena za cały stos, nie za sztukę — panel mnożył ją jeszcze raz przez ilość, zawyżając sumę dla przedmiotów w stosach (mikstury, księgi, peleryny).
- **Dodano odznakę stałego towarzysza przy nicku** na liście graczy; działa również dla towarzyszy offline i ma opis po najechaniu.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

## 2026-09-27 · 1.93.0 · Responsywność panelu i szybszy dashboard

- **Nawigacja boczna jest przewijalna i responsywna** na mniejszych monitorach; poniżej 1100 px przechodzi w drawer, a długie menu nie jest już ucinane.
- **Poprawiono responsywność stron panelu**: ograniczono poziome wypychanie layoutu, zabezpieczono szerokości paneli i tabel oraz dopasowano odstępy dla mniejszych ekranów.
- **Dashboard ładuje się znacznie szybciej** — z pierwszego renderu usunięto blokujące sprawdzanie GitHub, a czas zimnego renderu spadł z około 9,7 s do około 0,9 s.
- **Naprawiono wykresy gospodarki** na `/economy`, `/economy/shops` i `/economy/itemshop`; dane snapshotów collectora pozostały nienaruszone.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-26 · 1.92.0 · Oryginalne mapy klienta i filtry historii ekwipunku

- **Grota Wygnańców V1 i V2 korzysta teraz z prawdziwych minimap klienta gry**, złożonych z 36 kafli każda z paczki `season2`, zamiast poglądowych grafik generowanych przez AI.
- **Ognista Ziemia została dodana do przeglądarki map i ustawień respawnu** z oficjalnym atlasem oraz granicami z `atlasinfo.txt`. Czerwony Las otrzymał poprawny, pełny atlas bez wcześniejszego błędnego kadrowania.
- **Historia ekwipunku na karcie gracza ma filtry** Handel, Bonusy, Ulepszanie, Inne i Wszystko, zgodne z podziałem zdarzeń panelu Tieru.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-26 · 1.91.0 · Pełna zgodność z Playerbots 2.2.24

- **Dodano eventy świata z 2.2.22:** Pirat Tanaka i Zuo mają szybki start, tygodniowy harmonogram, wybór mapy, liczbę jednostek oraz regulowany udział botów. Status pokazuje także żywe i pokonane jednostki, boty uczestniczące i fazę eventu.
- **Dodano rajdy na Azraela z 2.2.21:** osobny przełącznik zachowania `CATACOMB` oraz przycisk uruchomienia rajdu natychmiast, bez restartu serwera.
- **Mapa na żywo obsługuje Grotę Wygnańców V1 i V2** wraz z prawidłowymi granicami, grafikami i wyborem mapy. Groty dodano też do ustawień czasu respawnu potworów.
- **Karta postaci i gospodarka uwzględniają poprawki 2.2.23–2.2.24:** wygasłe sklepy są oznaczone i wyłączone ze statystyk aktywnego rynku, a historia wyposażenia pokazuje zakupy u NPC, Marmur z Magicznego Pyłu oraz zakupy w sklepach offline z ceną i sprzedawcą.
- Pełna macierz porównawcza znajduje się w `AUDIT_PLAYERBOTS_2.2.24.md`. Rejestrację kont pominięto świadomie zgodnie z konfiguracją tego serwera.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-26 · 1.90.0 · Osobne zarządzanie grą i panelem

- **Zarządzanie zostało rozdzielone na dwie czytelne strony:** `/manage` zawiera wyłącznie sterowanie grą, Playerbots i serwerem, a nowe `/manage/panel` skupia nazwę panelu, motyw, monitoring, kursor oraz ochronę hasłem.
- **Nawigacja ma teraz rozwijaną sekcję Zarządzanie** z bezpośrednimi odnośnikami do obu części. Na górze obu ekranów znajduje się też spójny przełącznik „Gra i serwer / Panel webowy”.
- Zapis ustawień panelu wraca na właściwą stronę panelową również po błędzie walidacji, więc obsługa formularza nie przenosi już operatora do ustawień gry.

![via Codex by Seban](https://img.shields.io/badge/via-Codex%20by%20Seban-10A37F)

## 2026-09-26 · 1.89.0 · Changelog: nasz panel i silnik Tieru osobno

- **`/changelog` ma teraz dwie zakładki na środku góry strony**: "Advanced Seban Webpanel" (jak dotychczas) i "Playerbots by Tieru" — pobierane bezpośrednio z jego repozytorium ([CHANGELOG.md na GitHub](https://github.com/TieruYT/metin2-playerbots/blob/main/CHANGELOG.md)), najnowsze 25 wydań silnika, ładnie sformatowane (nagłówki, listy, pogrubienia). Pobierane raz na godzinę, nie za każdym wejściem.

![via Claude by Seban](https://img.shields.io/badge/via-Claude%20by%20Seban-D97757)

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
