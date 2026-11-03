"""Operator-facing Forge text, with the panel's PL/EN/TR language choice."""
TEXT = {
    'title':('Kuźnia Łowcy',"Hunter's Forge",'Avcı Ocağı'),
    'intro':('Przemiana broni 30+9 w 50+0 dla graczy. Bonusy i kamienie zostają.',
             'Player-only conversion from level 30 +9 to level 50 +0. Bonuses and stones are preserved.',
             'Oyuncular için 30. seviye +9 silahtan 50. seviye +0 silaha dönüşüm. Efsunlar ve taşlar korunur.'),
    'proposal':('Domyślnie wyłączone. Propozycja balansu do zatwierdzenia przez Tieru.',
                'Disabled by default. Proposed balance requires Tieru approval.',
                'Varsayılan olarak kapalı. Önerilen denge için Tieru onayı gerekir.'),
    'enabled':('Włącz usługę dla graczy','Enable the service for players','Oyuncular için hizmeti etkinleştir'),
    'toggle':('Zapisz dostępność','Save availability','Kullanılabilirliği kaydet'),
    'off':('Usługa jest wyłączona.','The service is disabled.','Hizmet kapalı.'),
    'on':('Usługa jest włączona.','The service is enabled.','Hizmet açık.'),
    'fee':('Koszt w Yang','Yang fee','Yang ücreti'),
    'material':('Numer materiału','Material number','Malzeme numarası'),
    'count':('Liczba','Count','Adet'),
    'save':('Zapisz recepturę','Save recipe','Tarifi kaydet'),
    'saved':('Zapisano. Otwórz ponownie okno u Kowala.','Saved. Reopen the window at the Blacksmith.','Kaydedildi. Demircideki pencereyi yeniden açın.'),
    'stale':('Ustawienia zmieniły się. Odśwież stronę.','Settings have changed. Refresh the page.','Ayarlar değişti. Sayfayı yenileyin.'),
    'invalid':('Sprawdź koszt, materiały i ich liczby.','Check the fee, materials and counts.','Ücreti, malzemeleri ve adetleri kontrol edin.'),
    'missing':('Brakuje definicji dodatku. Uruchom standardową migrację serwera.','Addon definitions are missing. Run the normal server migration.','Eklenti tanımları eksik. Normal sunucu geçişini çalıştırın.'),
    'failed':('Nie zapisano zmian. Poprzednie ustawienia zachowano.','Changes were not saved. Previous settings were preserved.','Değişiklikler kaydedilmedi. Önceki ayarlar korundu.'),
    'rules':('Wytwarzanie bez limitu poziomu; noszenie od 50. Wynik +0, szansa 100%. Do czterech materiałów; puste pola pomijają materiał.',
             'No crafting level requirement; wearable from 50. Result +0, 100% success. Up to four materials; empty fields omit a material.',
             'Üretim için seviye şartı yok; 50. seviyeden itibaren giyilir. Sonuç +0, başarı %100. En fazla dört malzeme; boş alanlar malzemeyi çıkarır.'),
}

def text(key,language):
    return TEXT[key][{'pl':0,'en':1,'tr':2}.get(language,1)]
