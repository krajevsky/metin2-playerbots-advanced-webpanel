# Audyt zgodności: Playerbots 2.2.29 i Seban Advanced Webpanel 1.95

Audyt wykonano względem oficjalnego archiwum serwera `playerbots-2.2.29-server-update.zip`, tagu `v2.2.29`, dołączonego `docker-compose.yml`, obrazu gry, questów oraz panelu klasycznego i wersji Seban Panel dołączonej przez Tieru.

## Funkcje dostępne w czystej instalacji 2.2.29

| Obszar | Mechanizm w 2.2.29 | Wniosek dla panelu |
|---|---|---|
| Raty EXP/drop/Yang | `web_admin.quest`, `m2-rates`, `rates-spool` | dostępne bez przełącznika |
| Globalne tempo i liczebność respawnu | komendy `REGEN` i `REGEN_COUNT` w rdzeniu/queście | dostępne na żywo |
| Zachowanie botów, ItemShop, persona, wojny, rajdy | pliki wag w `m2spool`, obsługa w rdzeniu 2.2.29 | dostępne na żywo |
| Trzymanie botów przy wejściu | `PLAYERBOT_HOLD_PATH` w rdzeniu | dostępne na żywo |
| Wieża Demonów i Katakumby „teraz” | natywne pliki sygnałowe w rdzeniu | dostępne na żywo |
| Polityka przedmiotów | parser polityki w rdzeniu | dostępna na żywo |
| Kolektor, historia, nadawanie przedmiotów | usługi `seban-collector` i `seban-item-grants` w oficjalnym compose | dostępne w oficjalnym stosie |
| Monitoring VPS | oficjalny compose montuje wymagane źródła hosta | dostępny w oficjalnym stosie |

## Funkcje opcjonalne, wymagające integracji

| Funkcja | Czego brakuje w czystej instalacji | Skutek bez integracji |
|---|---|---|
| Docelowa liczba botów z Advanced Panel | watcher `botcount.request`, który zmienia `.env` i odtwarza `game` | żądanie pozostaje nieodebrane |
| Plan wejścia botów | watcher `spawn-plan.request` | zapis nie trafia do parametrów kontenera |
| Dokładny czas respawnu jednej mapy | helper `m2-map-regens` | plik mapy nie jest przepisywany |
| Skrzynia startowa przełączana na żywo | zmieniony `starter_chest.quest` i `common.m2_switches` | wpis w bazie nie steruje questem |
| Ogłoszenia ulepszeń +9 | komenda `NOTICE` w `web_admin.quest` i kolektor | kolejka NOTICE nie zostaje wykonana |
| Aktualizator Seban | hostowa usługa `seban-updater` i `update-spool` | panel nie może bezpiecznie sterować Dockerem hosta |

## Zasada publikacji

Na nowej instalacji wszystkie powyższe funkcje opcjonalne są wyłączone. Nadal są widoczne na szaro z odnośnikiem **Wymaga akcji**. Operator włącza każdą osobno w `/manage/panel` po wykonaniu pokazanej instrukcji. Backend odrzuca bezpośrednie żądania do wyłączonej funkcji, więc samo wywołanie endpointu nie utworzy martwego zlecenia.

Istniejące instalacje Sebana z `M2_PANEL_CUSTOM_PATCHES=1` zachowują dotychczasową dostępność do chwili zapisania własnych ustawień. Dzięki temu aktualizacja panelu nie wyłącza działających integracji na serwerze autora, a czyste instalacje nie pokazują aktywnych funkcji-widm.
