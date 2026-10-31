# MEGSIS Otomatik Onay

MEGSIS "Onay Bekleyen Başvurular" listesini Edge / Chrome / Firefox / Internet Explorer üzerinden, ekranı okuyarak (Windows yerel OCR) ve fare/klavye ile işleyen yerel Windows aracı.

- Her başvuruda Onay Durumu = **Onaylandı**, SMS Durumu = **Gönderme** seçer; iki ayrı görüntüde doğrulamadan onay düğmesine basmaz.
- Hata çıkarsa hata metnini kopyalar, yerel geçmişe yazar, **Açıklama Ekle** alanına yapıştırır ve sonraki başvuruya geçer.
- Aynı başvuruyu ikinci kez denemez (yerel geçmiş: `%LOCALAPPDATA%\MEGSIS-Otomatik-Onay`).
- **F5** başlat, **F8** acil durdurma. Deneme modu yoktur: her çalıştırma gerçek onaydır (başlamadan önce tek onay sorusu sorulur).
- Tek dosya: `MEGSIS-Otomatik-Onay.exe`. Kurulum gerekmez, registry'ye yazmaz, yönetici yetkisi istemez.
- Açılışta yalnızca güncelleme için `gokhangeo/apk` deposundaki `megsis/version.json` dosyasına bakar; yeni sürüm varsa indirir, SHA-256 doğrular, kendini değiştirip yeniden açılır. Başka hiçbir yere veri göndermez.

## Derleme

GitHub Actions (`.github/workflows/megsis-otomatik-onay.yml`) her değişiklikte Windows'ta derler, `megsis-otomatik-onay-v2.19.N` sürümü olarak yayınlar ve exe'yi herkese açık **https://github.com/gokhangeo/apk/tree/main/megsis** klasörüne koyar.

Sabit indirme adresi: https://github.com/gokhangeo/apk/raw/main/megsis/MEGSIS-Otomatik-Onay.exe

Elle: `dotnet build -c Release` (hedef .NET Framework 4.8, x64).

## Komut satırı

- `--self-test [çıktı.txt]` tıklama göndermeden iç testleri çalıştırır.
- `--diagnose-rows <ekran.png> <çıktı.txt>`, `--diagnose-explanation <ekran.png> <çıktı.txt>` kayıtlı ekran görüntüsü üzerinde algılamayı dener.

## Tanı Raporu

Butonlar bulunamıyorsa uygulamadaki **Tanı Raporu** düğmesine basın. `%LOCALAPPDATA%\MEGSIS-Otomatik-Onay\Tani\<zaman>` klasörüne ekran görüntüsü, ekran/DPI bilgisi, algılama sonucu, OCR metni ve tarayıcının UI Automation ağacı yazılır. Otomasyon hata verdiğinde aynı rapor otomatik alınır. Rapor ekranda görünen başvuru bilgilerini içerebilir; yalnızca yetkili kişilerle paylaşın.

Kaynak, v2.14 ikili dosyasından geri açılıp düzenlenmiştir.
