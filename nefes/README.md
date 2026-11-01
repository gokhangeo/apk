# Nefes ortak spam listesi

`spam-listesi.json` her gün 06:17'de (TR) otomatik yenilenir: topluluk listesi
(symbuzzer/Turkish-Spam-Numbers) + senin `ek-liste.json` dosyan. Nefes iOS ve Android bu dosyayı indirir.

Numara eklemek için `ek-liste.json`'a yaz:

```json
[{"numara": "0850 123 45 67", "etiket": "Sigorta satış", "engelle": true}]
```

## Zararlı listesi (Güvenlik taraması)
`zararli-topla.py` her gün (`.github/workflows/zararli-listesi.yml`) herkese açık, anahtarsız kaynaklardan zararlı dosya
hash'lerini (SHA-256 / SHA-1 / MD5), zararlı Android paket adlarını ve imza sertifikalarını toplar.
- Büyük listeler sıralı ikili dosya olarak (`z256-*.bin.gz`, `z1.bin.gz`, `zmd5-*.bin.gz`) **nefes-zararli** sürümüne yüklenir
  (depo geçmişi şişmesin diye); `taban` dosyaları haftada bir, `ek` dosyaları her gün yenilenir.
- `zararli-liste.json`: tarih, kaynaklar, sayılar, her ikili dosyanın sha256'sı, paket adları ve sertifikalar. Nefes yalnızca değişen dosyaları indirir.
- Kaynaklar: AssoEchap stalkerware-indicators, mvt-project/Amnesty göstergeleri, ESET malware-ioc, Doctor Web malware-iocs,
  Neo23x0 signature-base, TweetFeed, Botvrij.eu, ThreatView, SentinelPhishFeed, Droidwatch, MalShare, VirusShare (MD5).
- **MalwareBazaar** artık ücretsiz bir Auth-Key istiyor: auth.abuse.ch'den anahtar alıp bu depoya `MB_AUTH_KEY` gizlisi olarak
  eklerseniz liste MalwareBazaar'ın tüm SHA-256 kayıtlarıyla büyür (ayrı bir değişiklik gerekmez).
