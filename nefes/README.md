# Nefes ortak spam listesi

`spam-listesi.json` her gün 06:17'de (TR) otomatik yenilenir: topluluk listesi
(symbuzzer/Turkish-Spam-Numbers) + senin `ek-liste.json` dosyan. Nefes iOS ve Android bu dosyayı indirir.

Numara eklemek için `ek-liste.json`'a yaz:

```json
[{"numara": "0850 123 45 67", "etiket": "Sigorta satış", "engelle": true}]
```
