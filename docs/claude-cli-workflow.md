# Praca nad Seban Panelem z Claude CLI

Repozytorium: `C:\Users\Sebastian\Projekty\seban-panel` (lub inny klon `krajevsky/metin2-playerbots-advanced-webpanel`). Produkcja: `/opt/seban-panel-custom` na VPS. Źródłem prawdy jest `origin/main`; panel Tieru na porcie 7788 pozostaje tylko do odczytu.

## Przed rozpoczęciem sesji

1. Otwórz Claude CLI **w katalogu klonu**, a nie w `C:\WINDOWS\system32`. Poproś go o przeczytanie całego `AGENTS.md` i wskazanej części `docs/audit-tieru-7788.md`.
2. Sprawdź `git status --short --branch`. Jeśli są niezapisane zmiany, nie wykonuj `pull` ani resetu w ciemno; najpierw ustal ich autora i cel.
3. Przy czystym drzewie uruchom `git fetch origin`, `git pull --ff-only origin main`, ponownie `git status --short --branch`. Nie pracuj na starym commicie ani równolegle z drugim agentem w tym samym katalogu.
4. Daj Claude jedną funkcję lub poprawkę na raz. Każda powinna mieć osobny mały commit; zmiana widoczna dla użytkownika wymaga patch bump w `VERSION`, wpisu w `CHANGELOG.md`, badge'a `via Claude by Seban` i pasującego tagu.

## Gotowy prompt dla Claude CLI

> Pracujesz w repo Seban Panelu. Najpierw przeczytaj AGENTS.md i zsynchronizuj czyste drzewo z origin/main przez fetch oraz pull --ff-only. Zrób wyłącznie tę zmianę: [tu opisz konkretny ekran i zachowanie]. Zachowaj motyw Laka i Złoto, szczególnie istniejące reguły laka.css, laka-shell.js, mapy i tooltipy /player/. Nie kopiuj HTML/CSS panelu Tieru; jego kod czytaj tylko do ustalenia logiki. Dodaj PL/EN, sprawdź desktop 1440×900 i telefon 375×812 w motywach laka oraz ocean, uruchom testy z AGENTS.md. Przed pushem sprawdź, czy origin/main nie przesunął się. Zrób osobny commit, patch bump i tag, wypchnij na main. Wdróż dokładnie ten commit na VPS zgodnie z AGENTS.md i potwierdź /login 200 oraz brak nowych błędów w logach. Nie restartuj ani nie modyfikuj panelu Tieru lub gry; nie usuwaj baz, botów ani nadpisań. Podaj link do commita, wyniki testów i ryzyka.

## Testy i wdrożenie

W PowerShell testy wymagają zmiennych środowiskowych: `DB_USER=x`, `DB_PASSWORD=x`, `SEBAN_SESSION_SECRET=x`. Uruchom `python -m pytest -q --ignore=test_manage_settings.py`. Nie uznawaj samego poprawnego kodu za wdrożenie.

Po wypchnięciu commita Claude ma wdrożyć **ten sam hash**: `git -C /opt/seban-panel-custom fetch origin main`, `git -C /opt/seban-panel-custom merge --ff-only FETCH_HEAD`, następnie w katalogu `/opt/metin2-mt2009/mt2009-r41023-base/linux-port/docker` wykonać `sudo -n docker compose up -d --build --no-deps seban-panel seban-collector seban-item-grants`. Na końcu: `curl -i http://127.0.0.1:7790/login`, `git -C /opt/seban-panel-custom rev-parse HEAD` i świeże logi `metin2-seban-panel`. Wysokie obciążenie VPS może wydłużyć budowę; sprawdź zakończenie polecenia, nie zakładaj sukcesu po samym `git pull`.

Nigdy nie podawaj hasła VPS w promptach, plikach repo, komendach ani logach. Korzystaj z aliasu SSH `seban-vps` i klucza skonfigurowanego lokalnie.

## Gdy pracują dwaj agenci

Nie zlecaj obu agentom edycji tych samych plików jednocześnie. Przed każdym pushem pobierz `origin/main`. Jeśli przesunął się od rozpoczęcia pracy, Claude ma zatrzymać push i wdrożenie, włączyć swoje zmiany na nowym stanie, uruchomić testy ponownie i dopiero wtedy wypchnąć. Produkcja ma zawsze odpowiadać wypchniętemu commitowi, nie lokalnym zmianom na VPS.
