# Audyt zgodności panelu z Playerbots 2.2.24

Zakres: oficjalne wydania od 2.2.20 do 2.2.24, porównane z panelem Tieru dostarczonym z 2.2.24 oraz Advanced Seban Webpanel. Rejestracja kont została świadomie pominięta zgodnie z decyzją operatora.

Źródła: [oficjalny changelog Playerbots](https://github.com/TieruYT/metin2-playerbots/blob/main/CHANGELOG.md), kod panelu Tieru z instalacji 2.2.24 oraz pliki statusu i konfiguracji rdzenia.

| Wydanie | Funkcja autora | Stan po audycie w panelu 7790 |
|---|---|---|
| 2.2.20 | Grota Wygnańców V1/V2 na mapie na żywo i teleportacja | Dodane nazwy, granice, grafiki map, wybór mapy i obsługa API live. |
| 2.2.21 | Rajdy botów na Azraela | Dodany przełącznik `CATACOMB` odczytywany na żywo i przycisk natychmiastowego rajdu. |
| 2.2.21 | Wieża Demonów od poziomu 55 | Zachowanie leży w rdzeniu; panel steruje jedynie przełącznikiem i nie nadpisuje progu. |
| 2.2.22 | Event Tanaka | Dodany szybki start, harmonogram, liczba piratów, mapa i stan wykonania. |
| 2.2.22 | Event Zuo | Dodany szybki start, harmonogram, liczba Metinów w fali, mapa i stan wykonania. |
| 2.2.22 | Procent botów uczestniczących w eventach świata | Dodany suwak zapisujący linię `bots` do konfiguracji rdzenia. |
| 2.2.22 | Telemetria eventów świata | Panel łączy status hosta eventu z najnowszym statusem rdzeni i pokazuje stojące/pokonane jednostki oraz uczestniczące boty. |
| 2.2.23 | Wygasłe sklepy offline | Karta postaci oznacza wygasły sklep, a statystyki gospodarki liczą wyłącznie aktywne sklepy i prawidłowe oferty. |
| 2.2.24 | Zakupy u handlarza i Marmur z Magicznego Pyłu w historii | Dodane nowe typy wpisów historii wyposażenia. |
| 2.2.24 | Zakupy w sklepach offline w historii | Dane z `log.ikarusshop_log` są łączone chronologicznie z historią przedmiotów wraz ze sprzedawcą i ceną. |
| 2.2.24 | Poprawny ranking broni 30 Lv | Zaawansowany panel już sortował po obliczonych średnich/umiejętnościach w SQL przed limitem, więc błąd panelu autora tu nie występował. |

Panel Tieru na porcie 7788 pozostaje referencyjnym panelem autora i nie jest modyfikowany przez to repozytorium. Funkcje administracyjne dostępne wyłącznie w nim zostały przeniesione do panelu 7790 tam, gdzie rdzeń udostępnia stabilny plik sterujący lub dane w bazie.
