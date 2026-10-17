# Metin2 Playerbots — Advanced Web Panel (Seban Panel)

> Bu dosya [README.md](README.md) dosyasının Türkçe çevirisidir. Aralarında bir fark olursa Lehçe sürüm geçerlidir.

**Metin2 [Playerbots by Tieru](https://github.com/TieruYT/metin2-playerbots)**
sunucuları (mt2009 hattı) için alternatif, kapsamlı bir yönetim paneli.
Klasik Tieru Paneli'nin yanında çalışır — onun yerini almaz ve veri taşıma
(migration) gerektirmez; yalnızca dünyanın ikinci, daha modern bir görünümünü
ve kendi araçlarını ekler.

Bu depo **Playerbots by Tieru için hayran yapımı bir eklentidir** — bu motor
üzerinde bir sunucu çalıştırmıyorsan bu proje işine yaramaz.

## Nasıl kurulu

Bu panel **kendi `docker-compose.yml` dosyası olan bağımsız bir proje değildir**.
Mevcut Playerbots stack'ine takılan bir alt klasördür — Tieru'nun
`docker-compose.yml` dosyası onu buradan (`context: /opt/seban-panel-custom`),
oyunun ve veritabanının yanında üç ek hizmet olarak derler:

- `seban-panel` — web uygulamasının kendisi (Flask + gunicorn), dışarıya açık
  port `7790`;
- `seban-collector` — birkaç dakikada bir anlık görüntüleri (haritalar,
  ekonomi, host telemetrisi) kendi `player.web_seban_*` tablolarına toplayan
  arka plan süreci;
- `seban-item-grants` — aktif karakterlere toplu eşya dağıtımını yürüten
  hizmet.

Panel, stack'in geri kalanıyla aynı MariaDB veritabanını, aynı Playerbots
durum dosyalarını (`playerbot_status.tsv`) ve aynı yönetim kuyruğunu okur —
hiçbir şeyi taşımak ya da çoğaltmak gerekmez.

## Kurulum (mevcut bir Playerbots sunucusunun parçası olarak)

1. Sunucu klasöründe (`linux-port/docker/docker-compose.yml` dosyasının
   yanında) bu depoyu `seban-panel-custom` adıyla klonla:

   ```bash
   git clone https://github.com/krajevsky/metin2-playerbots-advanced-webpanel.git seban-panel-custom
   ```

2. Onu stack'e bağla — en kolayı, Tieru'nun dosyasına doğrudan dokunmamak için
   `linux-port/docker/` içindeki bir `docker-compose.override.yml` üzerinden
   (böylece motorun her güncellemesinden sağ çıkar):

   ```yaml
   services:
     seban-panel:
       build:
         context: /ścieżka/do/seban-panel-custom
   ```

3. Derle ve çalıştır:

   ```bash
   docker compose build seban-panel seban-collector seban-item-grants
   docker compose up -d seban-panel seban-collector seban-item-grants
   ```

4. `http://adres-serwera:7790/setup` adresine git — sihirbaz panelin adını,
   temasını ve isteğe bağlı bir parolayı sorar.

Panelin beklediği ortam değişkenleri (genellikle elle değil, Tieru'nun
`docker-compose.yml` dosyası tarafından ayarlanır — o dosyadaki
`environment: &seban-env` kısmına bak):

| Değişken | Anlamı |
| --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` | MariaDB veritabanı bağlantısı. |
| `PLAYERBOTS_GAME_HOST` | Oyun konteynerinin Compose ağındaki adı. |
| `PLAYERBOTS_LOGIN_PORT`, `PLAYERBOTS_WORLD_PORT` | Oyun çekirdeğinin portları — yeniden başlatma aşamasının denetimi. |
| `PLAYERBOTS_STATUS_GLOB` | `playerbot_status.tsv` dosyalarının yolu. |
| `PLAYERBOTS_VERSION` | Kontrol panelinde (dashboard) gösterilen Playerbots sürümü. |
| `TIERU_PANEL_URL` | Klasik Tieru Paneli'nin herkese açık adresi (menüdeki bağlantı). |
| `SEBAN_SESSION_SECRET` | Flask oturum sırrı. Değerini asla yayımlama. |
| `SEBAN_COLLECTOR_INTERVAL` | Toplayıcının saniye cinsinden çalışma aralığı (varsayılan `300`). |
| `SEBAN_M2_ROOT` | Host'taki sunucu klasörünün yolu — `seban-collector` tarafından bot takma adı havuzunu bir kereliğine yüklemek için kullanılır. |

## Güncelleme (en yeni sürümü nasıl çekersin)

```bash
cd /ścieżka/do/seban-panel-custom
git pull
docker compose build seban-panel seban-collector seban-item-grants
docker compose up -d seban-panel seban-collector seban-item-grants
```

Geçmiş tabloları ve panel ayarları veritabanında kalır — `git pull` yalnızca
uygulamanın koduna dokunur, hiçbir şeyi silmez.

## Panel neler sunuyor

Özelliklerin tam listesi için her değişiklikle güncel tutulan
[CHANGELOG.md](CHANGELOG.md) dosyasına bak. Kısaca:

- seviye filtreleri ve arama ile botların canlı dünya haritası (konumlar,
  gruplar, Metin Taşı savaşları, takılıp kalmış olabilecek botlar);
- eksiksiz karakter profilleri: oyundaki gibi ipuçlu (tooltip)
  ekipman/depo, istatistikler, HP/MP/EXP, at, rütbe, olay geçmişi;
- bot sıralamaları (seviye, Yang, silah, zırh, at, 30. seviye silahlar);
- ekonomi: fiyat geçmişi, çevrimdışı dükkânlar, ItemShop, Yang dolaşımı;
- host telemetrisi (CPU/RAM/disk), Playerbots sürümü ve aktif bonus
  etkinliklerinin sayacıyla birlikte sunucu oranlarını gösteren kontrol
  paneli (dashboard);
- zil simgesi ve canlı bildirimlerle bildirim sistemi (etkinlik sonu, yeni
  Playerbots sürümü, günün özeti);
- yönetim: oranlar, bot sayısı, yapay zekâ davranışları, haritalardaki
  yeniden doğma (respawn), yeniden başlatma;
- karakter oluşturucu, eşya veritabanı, GM komutları, hesaplar ve GM'ler (bot
  takma adı havuzunu görüntüleme/düzenleme dahil);
- panel günlükleri (menüde: Diagnostyka → Logi panelu, yani Tanılama → Panel
  günlükleri) — hata bildirirken eklemek için.

## Güvenlik

- Panel güvenilir ağın dışından da erişilebilir olacaksa, ilk çalıştırma
  sihirbazında parolayı etkinleştir.
- MariaDB portunu herkese açma.
- `SEBAN_SESSION_SECRET` asla depoya ya da herkese açık bir hata bildirimine
  girmemeli.

## Geliştirme

Bu panel belirli bir sunucu için sürekli geliştiriliyor — değişiklikler buraya
ayrı ayrı değil, devreye almayla (deployment) birlikte gelir. Issue/PR'lar
memnuniyetle karşılanır, ama bu herkes için evrensel, desteklenen bir araç
olarak düşünülmüş bir proje değil — kullanım sorumluluğu sana aittir.
