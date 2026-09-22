# Metin2 Playerbots — Advanced Web Panel (Seban Panel)

Alternatywny, rozbudowany panel administracyjny dla serwerów **Metin2 z
[Playerbots by Tieru](https://github.com/TieruYT/metin2-playerbots)** (linia
mt2009). Działa obok klasycznego Panelu Tieru — nie zastępuje go i nie
wymaga migracji danych, tylko dokłada drugi, nowocześniejszy widok świata i
własne narzędzia.

To repozytorium jest **fanowskim dodatkiem do Playerbots by Tieru** — jeśli
nie prowadzisz serwera na tym silniku, ten projekt Ci się nie przyda.

## Jak to jest zbudowane

Ten panel **nie jest samodzielnym projektem z własnym `docker-compose.yml`**.
Jest podkatalogiem wpiętym w istniejący stack Playerbots — Tieru's
`docker-compose.yml` buduje go stąd (`context: /opt/seban-panel-custom`) jako
trzy dodatkowe usługi obok gry i bazy:

- `seban-panel` — sama aplikacja webowa (Flask + gunicorn), port `7790` na
  zewnątrz;
- `seban-collector` — proces w tle zbierający migawki (mapy, ekonomia,
  telemetria hosta) co kilka minut do własnych tabel `player.web_seban_*`;
- `seban-item-grants` — obsługa masowych nadań przedmiotów dla aktywnych
  postaci.

Panel czyta tę samą bazę MariaDB, te same pliki statusu Playerbots
(`playerbot_status.tsv`) i tę samą kolejkę administracyjną co reszta stacku —
nic nie trzeba migrować ani duplikować.

## Instalacja (jako część istniejącego serwera Playerbots)

1. W katalogu serwera (obok `linux-port/docker/docker-compose.yml`) sklonuj
   to repozytorium jako `seban-panel-custom`:

   ```bash
   git clone https://github.com/krajevsky/metin2-playerbots-advanced-webpanel.git seban-panel-custom
   ```

2. Podepnij go do stacku — najprościej przez `docker-compose.override.yml` w
   `linux-port/docker/`, żeby nie ruszać pliku Tieru bezpośrednio (przeżywa
   wtedy każdą aktualizację silnika):

   ```yaml
   services:
     seban-panel:
       build:
         context: /ścieżka/do/seban-panel-custom
   ```

3. Zbuduj i uruchom:

   ```bash
   docker compose build seban-panel seban-collector seban-item-grants
   docker compose up -d seban-panel seban-collector seban-item-grants
   ```

4. Wejdź na `http://adres-serwera:7790/setup` — kreator zapyta o nazwę
   panelu, motyw i opcjonalne hasło.

Zmienne środowiskowe, jakich panel oczekuje (ustawiane zwykle przez
`docker-compose.yml` Tieru, nie ręcznie — patrz `environment: &seban-env` w
tamtym pliku):

| Zmienna | Znaczenie |
| --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` | Połączenie z bazą MariaDB. |
| `PLAYERBOTS_GAME_HOST` | Nazwa kontenera gry w sieci Compose. |
| `PLAYERBOTS_LOGIN_PORT`, `PLAYERBOTS_WORLD_PORT` | Porty rdzenia gry — kontrola etapu restartu. |
| `PLAYERBOTS_STATUS_GLOB` | Ścieżka do plików `playerbot_status.tsv`. |
| `PLAYERBOTS_VERSION` | Wersja Playerbots wyświetlana na dashboardzie. |
| `TIERU_PANEL_URL` | Publiczny adres klasycznego Panelu Tieru (link w menu). |
| `SEBAN_SESSION_SECRET` | Sekret sesji Flask. Nigdy nie publikuj wartości. |
| `SEBAN_COLLECTOR_INTERVAL` | Interwał kolektora w sekundach (domyślnie `300`). |
| `SEBAN_M2_ROOT` | Ścieżka do katalogu serwera na hoście — używana przez `seban-collector` do jednorazowego wczytania puli nicków botów. |

## Aktualizacja (jak sklonować najnowszą wersję)

```bash
cd /ścieżka/do/seban-panel-custom
git pull
docker compose build seban-panel seban-collector seban-item-grants
docker compose up -d seban-panel seban-collector seban-item-grants
```

Tabele historii i ustawienia panelu zostają w bazie — `git pull` dotyka tylko
kodu aplikacji, nic nie kasuje.

## Co panel oferuje

Pełna lista funkcji — zobacz [CHANGELOG.md](CHANGELOG.md), aktualizowany na
bieżąco z każdą zmianą. W skrócie:

- mapa świata botów na żywo (pozycje, grupy, walki z Metinami, boty możliwie
  zawieszone), z filtrami poziomu i wyszukiwarką;
- pełne profile postaci: ekwipunek/magazyn w stylu gry z tooltipami,
  statystyki, HP/MP/EXP, koń, ranga, historia zdarzeń;
- rankingi botów (poziom, Yang, broń, pancerz, koń, bronie 30 poziomu);
- ekonomia: historia cen, sklepy offline, ItemShop, obieg Yang;
- dashboard z telemetrią hosta (CPU/RAM/dysk), wersją Playerbots, ratami
  serwerowymi z licznikiem aktywnych eventów bonusowych;
- system powiadomień (koniec eventu, nowa wersja Playerbots, podsumowanie
  dnia) z dzwoneczkiem i powiadomieniami na żywo;
- zarządzanie: raty, liczba botów, zachowania AI, respawny map, restart;
- kreator postaci, baza przedmiotów, komendy GM, konta i GM (w tym
  przeglądanie/edycja puli nicków botów);
- logi panelu (Diagnostyka → Logi panelu) — do załączania przy zgłaszaniu
  błędów.

## Bezpieczeństwo

- Włącz hasło w kreatorze pierwszego uruchomienia, jeśli panel ma być
  dostępny spoza zaufanej sieci.
- Nie wystawiaj portu MariaDB publicznie.
- `SEBAN_SESSION_SECRET` nigdy nie powinien trafić do repozytorium ani do
  publicznego zgłoszenia błędu.

## Rozwój

Ten panel jest rozwijany na bieżąco pod konkretny serwer — zmiany trafiają
tu razem z wdrożeniem, nie osobno. Issues/PR mile widziane, ale to nie jest
projekt myślany jako uniwersalne, wspierane narzędzie dla każdego —
korzystasz na własną odpowiedzialność.
