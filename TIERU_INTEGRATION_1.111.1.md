# Integracja wydania 1.111.1 z Playerbots — informacje dla Tieru

Wydanie webpanelu 1.111.1 przygotowano na MT2009 Playerbots 2.2.69, a następnie zespół Playerbots sprawdził wszystkie 57 stron na świecie testowym z wersją 2.2.70. Webpanel i jego zasoby są budowane jako osobny obraz seban-panel.

## Dane pobierane z silnika

1. playerbot_status.tsv z każdego kanału dostarcza PID, mapę, współrzędne, kanał i aktywność. Kierunek znacznika jest wyliczany w przeglądarce z dwóch kolejnych pozycji, więc rdzeń nie musi eksportować kąta.
2. player.player, player.item i player.item_proto dostarczają statystyki, ścieżkę umiejętności, okna INVENTORY, EQUIPMENT, SAFEBOX i DRAGON_SOUL_INVENTORY, rozmiary, gniazda, atrybuty oraz wartości prototypów.
3. Smocza Alchemia korzysta z typu 29, rodziny i jakości kodowanych w VNUM, stopnia +0–+6, czasu, gniazd i atrybutów. APPLY 97/98 są prezentowane jako Magic Attack Value/Magic Defense.
4. Sklep offline korzysta z player.ikashop_offlineshop, rekordów ofert i log.ikarusshop_log.
5. Biolog korzysta z flag collect_quest_lv30, 40, 50, 60, 70, 80, 85 i 90. Sześć analiz ziół daje pełną numerację 1–14. Etap lv50 używa przedmiotu 30015 „Pamiątka po Demonie”, a lv60 przedmiotu 30050 „Matowy Lód”.
6. Sezony i rankingi korzystają z player.player_special_flag, log.ikarusshop_log, player.player.skill_group i player.item_proto.value4/value5.
7. Wiadomości o ulepszeniach łączą log.refinelog z log.log, aby odzyskać +9 i prawdziwą metodę ulepszenia.

## Zakres kompilacji

- Przy aktualizacji Playerbots obraz usługi game jest przebudowywany z linux-port/docker/game; integrację wydania zweryfikowano na 2.2.70.
- Nie dodawano nowego protokołu, tabeli ani eksportera C++ specjalnie dla UI 1.111.1. Panel wykorzystuje dane już zapisywane przez Playerbots.
- Nie zmieniano NotifyRefineSuccess() zapisującego w refinelog nazwę przedmiotu sprzed ulepszenia. Panel obchodzi problem przez połączenie log.log i log.refinelog. Docelowa poprawka rdzenia może przekazywać wynikowy przedmiot +9, ale nie jest wymagana.

## Zgodność przyszłych wydań

- Zachować samopisujący nagłówek i pola playerbot_status.tsv; panel czyta kolumny po nazwach.
- Zachować znaczenie okien INVENTORY, EQUIPMENT, SAFEBOX i DRAGON_SOUL_INVENTORY.
- Zmiany schematów ikashop_offlineshop, ikarusshop_log, refinelog i player_special_flag wymagają migracji panelu.
- Aktualizować razem plik VERSION i M2_PLAYERBOTS_VERSION. Panel porównuje je ze statusem aktualizatora i wybiera najwyższy prawidłowy numer.
- Przy poprawce +9 zachować refinelog.setType: POWER, GUILD, DEVILTOWER i SCROLL:vnum.
- Kolejka web_admin_queue może zakończyć wydawanie przedmiotów stanami full, qty_too_big, player_offline, no_skill, has_item oraz partial. Są one częścią QUEUE_FINAL_STATUSES, aby panel nie czekał do timeoutu po poprawnej odpowiedzi rdzenia.

## Test integracyjny

1. Otworzyć /player/ postaci z przedmiotami wielopolowymi, magazynem, sklepem i Smoczymi Kamieniami.
2. Sprawdzić cztery strony ekwipunku, trzy strony magazynu i brak nakładania ikon.
3. Porównać mapę oraz kanał z playerbot_status.tsv.
4. Sprawdzić biologa przynajmniej na etapach lv30, lv40, lv50 i lv60.
5. Wykonać +9 kowalem i zwojem; oba zdarzenia powinny trafić do /world-feed/ z właściwą metodą.
6. Porównać sprzedaż offline z BUY_ITEM/TAX w log.ikarusshop_log.
7. Sprawdzić język polski, angielski i wersję Playerbots na dashboardzie.
