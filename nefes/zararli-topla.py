# Nefes zararlı yazılım listesi (her gün). Herkese açık, anahtarsız kaynaklardan dosya hash'leri, zararlı paket adları
# ve imza sertifikaları toplanır. Telefon büyük listeleri sıralı ikili dosya (.bin.gz) olarak indirip ikili aramayla
# sorgular.
#
# Çıktılar (nefes/zararli-cikti/ altında; workflow bunları gokhangeo/apk "nefes-zararli" sürümüne yükler):
#   z256-taban.bin.gz  SHA-256 (32 bayt, sıralı)  haftalık yeniden kurulur (MalwareBazaar*, MalShare son 60 gün, diğerleri)
#   z256-ek.bin.gz     SHA-256  günlük: tabanda olmayan yeni kayıtlar
#   zmd5-taban.bin.gz  MD5 (16 bayt)   haftalık: VirusShare son 12 liste + diğer MD5 kaynakları
#   zmd5-ek.bin.gz     MD5  günlük ek
#   z1.bin.gz          SHA-1 (20 bayt)  günlük, küçük
# Ayrıca nefes/zararli-liste.json: tarih, kaynaklar, sayılar, dosyaların sha256'sı, paket adları ve sertifikalar.
# (*) MalwareBazaar 2025'ten beri ücretsiz bir Auth-Key istiyor; depo gizlisi MB_AUTH_KEY varsa kullanılır.
import datetime, gzip, hashlib, io, json, os, re, sys, tarfile, time, urllib.request

OUT = "nefes/zararli-cikti"
META = "nefes/zararli-liste.json"
SURUM_URL = "https://github.com/gokhangeo/apk/releases/download/nefes-zararli/"
os.makedirs(OUT, exist_ok=True)

def al(u, zaman=120, basliklar=None, veri=None):
    h = {"User-Agent": "nefes-zararli-liste"}
    h.update(basliklar or {})
    for deneme in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(u, headers=h, data=veri), timeout=zaman).read()
        except Exception as e:
            if deneme == 2: raise
            time.sleep(3)

H64 = re.compile(rb"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
H40 = re.compile(rb"(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])")
H32 = re.compile(rb"(?<![0-9a-fA-F])[0-9a-fA-F]{32}(?![0-9a-fA-F])")

# Bilinen boş/zararsız dosyaların hash'leri asla listeye girmesin (boş dosya vb.).
ZARARSIZ = {
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # boş dosya sha256
    "da39a3ee5e6b4b0d3255bfef95601890afd80709",  # boş dosya sha1
    "d41d8cd98f00b204e9800998ecf8427e",  # boş dosya md5
}
# Herkese açık AOSP test anahtarları: bazı ROM'larda sistem uygulamaları da bunlarla imzalıdır, sertifika eşleşmesi yanıltır.
TEST_SERTIFIKA = {"61ED377E85D386A8DFEE6B864BD85B0BFAA5AF81", "27196E386B875E76ADF700E7EA84E4C6EEE33DFA",
                  "5B368CFF2DA2686996BC95EAC190EAA4F5630FE5", "B79DF4A82E90B57EA76525AB7037AB238A42F5D3"}
# Meşru uygulamaların paket adları zararlı örneklerde taklit edilir; bu öneklerle paket adı eşleşmesi yapılmaz.
KORUNAN_ONEK = ("com.android.", "com.google.", "android", "com.samsung.", "com.sec.", "com.whatsapp", "com.facebook.",
                "com.instagram.", "org.telegram.", "com.huawei.", "com.miui.", "com.xiaomi.", "com.oppo.", "com.coloros.",
                "com.oneplus.", "com.vivo.", "com.mediatek.", "com.qualcomm.", "com.qti.", "com.microsoft.", "com.zhiliaoapp.",
                "com.twitter.", "com.snapchat.", "com.spotify.", "com.netflix.", "tr.com.", "com.ziraat", "com.garanti",
                "com.akbank", "com.ykb.", "com.isbank", "com.vakifbank", "com.teb", "finansbank", "com.denizbank", "com.kuveytturk",
                "com.pozitron.", "com.ingbanktr", "com.halkbank", "com.turkcell.", "com.vodafone", "com.avea", "com.trendyol",
                "com.hepsiburada", "com.getir", "com.sahibinden", "com.yemeksepeti", "com.mobillium.papara", "com.paypal.")

s256, s1, md5 = set(), set(), set()
paketler, sert1, sert256 = {}, set(), set()
kaynaklar = {}

def hepsi(veri, s=True, h1=True, m=False):
    a = b = c = 0
    if s:
        for x in H64.findall(veri): s256.add(x.decode().lower()); a += 1
    if h1:
        for x in H40.findall(veri): s1.add(x.decode().lower()); b += 1
    if m:
        for x in H32.findall(veri): md5.add(x.decode().lower()); c += 1
    return a + b + c

def kaynak(ad, f):
    once = (len(s256), len(s1), len(md5), len(paketler), len(sert1) + len(sert256))
    try:
        f()
        sonra = (len(s256), len(s1), len(md5), len(paketler), len(sert1) + len(sert256))
        fark = [b - a for a, b in zip(once, sonra)]
        kaynaklar[ad] = {"sha256": fark[0], "sha1": fark[1], "md5": fark[2], "paket": fark[3], "sertifika": fark[4]}
        print(f"{ad}: +{fark}", flush=True)
    except Exception as e:
        print(f"kaynak alınamadı: {ad}: {e}", flush=True)

def paket_ekle(p, etiket):
    p = p.strip().strip("'\"")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+", p): return
    if p.lower().startswith(KORUNAN_ONEK): return
    paketler.setdefault(p, etiket)

def sert_ekle(c):
    c = re.sub(r"[^0-9A-Fa-f]", "", c).upper()
    if len(c) == 40 and c not in TEST_SERTIFIKA: sert1.add(c)
    elif len(c) == 64: sert256.add(c)

# ---- Kaynaklar ----
def stalkerware():
    import csv
    t = al("https://raw.githubusercontent.com/AssoEchap/stalkerware-indicators/master/samples.csv").decode("utf-8", "ignore")
    for r in csv.DictReader(io.StringIO(t)):
        h = (r.get("SHA256") or "").strip().lower()
        if re.fullmatch(r"[0-9a-f]{64}", h): s256.add(h)
        if r.get("Certificate"): sert_ekle(r["Certificate"])
        if r.get("Package Name"): paket_ekle(r["Package Name"], "Stalkerware: " + (r.get("App") or "").strip())
    y = al("https://raw.githubusercontent.com/AssoEchap/stalkerware-indicators/master/ioc.yaml").decode("utf-8", "ignore")
    ad, bolum = "Stalkerware", None
    for l in y.splitlines():
        m = re.match(r"^- name:\s*(.+)", l)
        if m: ad = "Stalkerware: " + m.group(1).strip(); bolum = None; continue
        m = re.match(r"^  (\w+):\s*$", l)
        if m: bolum = m.group(1); continue
        m = re.match(r"^  -\s*(\S+)", l)
        if m and bolum == "packages": paket_ekle(m.group(1), ad)
        elif m and bolum == "certificates": sert_ekle(m.group(1))

def mvt():
    y = al("https://raw.githubusercontent.com/mvt-project/mvt-indicators/main/indicators.yaml").decode()
    for o, r, b, p in re.findall(r"owner: (\S+)\s+repo: (\S+)\s+branch: (\S+)\s+path: (\S+)", y):
        try: t = al(f"https://raw.githubusercontent.com/{o}/{r}/{b}/{p}").decode("utf-8", "ignore")
        except Exception as e: print("  mvt atlandı", p, e); continue
        etiket = "Casus yazılım (" + p.split("/")[-1].replace(".stix2", "") + ")"
        for k, v in re.findall(r"\[([a-z\-]+:[a-zA-Z0-9_.\-']+)\s*=\s*'([^']+)'", t):
            k = k.lower()
            if k == "file:hashes.sha256" and re.fullmatch(r"[0-9a-fA-F]{64}", v): s256.add(v.lower())
            elif k in ("file:hashes.sha1", "file:hashes.'sha-1'") and re.fullmatch(r"[0-9a-fA-F]{40}", v): s1.add(v.lower())
            elif k == "file:hashes.md5" and re.fullmatch(r"[0-9a-fA-F]{32}", v): md5.add(v.lower())
            elif k == "app:id": paket_ekle(v, etiket)
            elif k in ("app:cert.sha1", "app:cert.sha256"): sert_ekle(v)

def github_tar(depo):
    def f():
        t = tarfile.open(fileobj=io.BytesIO(al(f"https://codeload.github.com/{depo}/tar.gz/HEAD", 300)))
        for m in t.getmembers():
            if m.isfile() and m.size < 40_000_000 and not m.name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf")):
                hepsi(t.extractfile(m).read(), m=True)
    return f

def duz(u, s=True, h1=True, m=False):
    return lambda: hepsi(al(u), s, h1, m)

def tweetfeed():
    for l in al("https://api.tweetfeed.live/v1/year/sha256").decode("utf-8", "ignore").splitlines():
        p = l.split(",")
        if len(p) > 3 and p[2] == "sha256" and re.fullmatch(r"[0-9a-fA-F]{64}", p[3]): s256.add(p[3].lower())

def droidwatch():
    d = json.loads(al("https://droidwatch.app/api/threat-feed?format=json&limit=500"))
    for o in d.get("items", []):
        if o.get("verdict") != "Malicious": continue
        if re.fullmatch(r"[0-9a-fA-F]{64}", o.get("sha256", "")): s256.add(o["sha256"].lower())
        if o.get("package"): paket_ekle(o["package"], "Android zararlısı (Droidwatch)")

def malshare_gun(gun):
    u = f"https://malshare.com/daily/{gun}/malshare_fileList.{gun}.sha256.txt"
    try: hepsi(al(u, 60), s=True, h1=False)
    except Exception:
        try: hepsi(al(f"https://malshare.com/daily/{gun}/malshare_fileList.{gun}.all.txt", 60), s=True, h1=False)
        except Exception as e: print("  malshare", gun, e)

def malshare(gunler):
    def f():
        bugun = datetime.date.today()
        for i in range(gunler):
            malshare_gun((bugun - datetime.timedelta(days=i + 1)).isoformat())
        hepsi(al("https://malshare.com/daily/malshare.current.sha256.txt"), s=True, h1=False)
    return f

def virusshare(adet):
    def f():
        sayfa = al("https://virusshare.com/hashes").decode("utf-8", "ignore")
        nolar = sorted(set(int(x) for x in re.findall(r"VirusShare_(\d+)\.md5", sayfa)))
        for n in nolar[-adet:]:
            for l in al(f"https://virusshare.com/hashfiles/VirusShare_{n:05d}.md5", 300).splitlines():
                l = l.strip()
                if len(l) == 32 and not l.startswith(b"#"): md5.add(l.decode().lower())
    return f

def malwarebazaar():
    anahtar = os.environ.get("MB_AUTH_KEY", "").strip()
    if not anahtar: raise RuntimeError("MB_AUTH_KEY yok (ücretsiz anahtar: auth.abuse.ch) — atlandı")
    alindi = False
    for u in (f"https://mb-api.abuse.ch/v2/files/exports/{anahtar}/sha256_full.txt.zip",
              f"https://bazaar.abuse.ch/export/txt/sha256/full/?auth-key={anahtar}",
              f"https://mb-api.abuse.ch/v2/files/exports/{anahtar}/sha256_recent.txt",
              f"https://bazaar.abuse.ch/export/txt/sha256/recent/?auth-key={anahtar}"):
        try: b = al(u, 600, {"Auth-Key": anahtar})
        except Exception as e: print("  mb", u.replace(anahtar, "***"), e); continue
        if b[:2] == b"PK":
            import zipfile
            z = zipfile.ZipFile(io.BytesIO(b))
            for n in z.namelist(): hepsi(z.read(n), s=True, h1=False)
        else: hepsi(b, s=True, h1=False)
        alindi = True
        if "full" in u: break
    # Android örnekleri ayrıca (API): en son APK'lar.
    try:
        d = json.loads(al("https://mb-api.abuse.ch/api/v1/", 120, {"Auth-Key": anahtar}, b"query=get_file_type&file_type=apk&limit=1000"))
        for o in d.get("data") or []:
            if o.get("sha256_hash"): s256.add(o["sha256_hash"].lower())
        alindi = True
    except Exception as e: print("  mb api", e)
    if not alindi: raise RuntimeError("MalwareBazaar indirilemedi")

# ---- İkili dosyalar ----
def bin_yaz(ad, kume, boy):
    veri = b"".join(sorted(bytes.fromhex(h) for h in kume if len(h) == boy * 2 and h not in ZARARSIZ))
    with open(os.path.join(OUT, ad), "wb") as f:
        f.write(gzip.compress(veri, 9, mtime=0))
    return len(veri) // boy

def bin_oku(ad, boy):
    try: b = gzip.decompress(al(SURUM_URL + ad, 300))
    except Exception as e: print("  önceki", ad, "yok:", e); return None
    return {b[i:i + boy].hex() for i in range(0, len(b) - boy + 1, boy)}

def main():
    eski = {}
    try: eski = json.load(open(META))
    except Exception: pass
    bugun = datetime.date.today()
    son_taban = eski.get("tabanTarih", "")
    haftalik = "--taban" in sys.argv or not son_taban or (bugun - datetime.date.fromisoformat(son_taban)).days >= 7
    t256 = tmd5 = None
    if not haftalik:
        t256 = bin_oku("z256-taban.bin.gz", 32); tmd5 = bin_oku("zmd5-taban.bin.gz", 16)
        if t256 is None or tmd5 is None: haftalik = True; print("Taban okunamadı, haftalık kurulum yapılıyor")

    kaynak("Stalkerware göstergeleri (AssoEchap)", stalkerware)
    kaynak("MVT casus yazılım göstergeleri (Amnesty/mvt-project)", mvt)
    kaynak("ESET malware-ioc", github_tar("eset/malware-ioc"))
    kaynak("Doctor Web malware-iocs", github_tar("DoctorWebLtd/malware-iocs"))
    kaynak("Neo23x0 signature-base", duz("https://raw.githubusercontent.com/Neo23x0/signature-base/master/iocs/hash-iocs.txt", m=True))
    kaynak("TweetFeed (son 1 yıl)", tweetfeed)
    kaynak("Botvrij.eu", lambda: [hepsi(al(f"https://www.botvrij.eu/data/ioclist.{t}"), m=True) for t in ("sha256", "sha1", "md5")])
    kaynak("ThreatView", lambda: [hepsi(al(u), m=True) for u in ("https://threatview.io/Downloads/SHA-HASH-FEED.txt", "https://threatview.io/Downloads/MD5-HASH-ALL.txt")])
    kaynak("SentinelPhishFeed", duz("https://raw.githubusercontent.com/rjn32s/SentinelPhishFeed/main/hashes.txt", m=True))
    kaynak("Droidwatch", droidwatch)
    kaynak("MalwareBazaar (abuse.ch)", malwarebazaar)
    kaynak("MalShare (son 60 gün)" if haftalik else "MalShare (son 3 gün)", malshare(60 if haftalik else 3))
    if haftalik: kaynak("VirusShare (son 12 liste, MD5)", virusshare(12))

    dosyalar = {}
    if haftalik:
        n256 = bin_yaz("z256-taban.bin.gz", s256, 32); bin_yaz("z256-ek.bin.gz", set(), 32)
        nmd5 = bin_yaz("zmd5-taban.bin.gz", md5, 16); bin_yaz("zmd5-ek.bin.gz", set(), 16)
        taban = {"z256-taban.bin.gz": n256, "zmd5-taban.bin.gz": nmd5}
        ek = {"z256-ek.bin.gz": 0, "zmd5-ek.bin.gz": 0}
        tabanTarih = bugun.isoformat()
    else:
        e256 = bin_yaz("z256-ek.bin.gz", s256 - t256, 32); emd5 = bin_yaz("zmd5-ek.bin.gz", md5 - tmd5, 16)
        taban = {k: v.get("adet", 0) for k, v in eski.get("dosyalar", {}).items() if "taban" in k}
        ek = {"z256-ek.bin.gz": e256, "zmd5-ek.bin.gz": emd5}
        tabanTarih = son_taban
    n1 = bin_yaz("z1.bin.gz", s1, 20)
    for ad, adet in list(taban.items()) + list(ek.items()) + [("z1.bin.gz", n1)]:
        yol = os.path.join(OUT, ad)
        if os.path.exists(yol):
            b = open(yol, "rb").read()
            dosyalar[ad] = {"sha256": hashlib.sha256(b).hexdigest(), "boyut": len(b), "adet": adet}
        elif ad in eski.get("dosyalar", {}):
            dosyalar[ad] = eski["dosyalar"][ad]
    toplam = sum(v["adet"] for v in dosyalar.values())
    meta = {
        "tarih": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "tabanTarih": tabanTarih,
        "adres": SURUM_URL, "toplam": toplam + len(paketler) + len(sert1) + len(sert256),
        "hashToplam": toplam, "dosyalar": dosyalar, "kaynaklar": kaynaklar,
        "paketler": [{"p": p, "e": e} for p, e in sorted(paketler.items())],
        "sertifikaSha1": sorted(sert1), "sertifikaSha256": sorted(sert256),
    }
    json.dump(meta, open(META, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"Toplam: {toplam} hash, {len(paketler)} paket, {len(sert1) + len(sert256)} sertifika; haftalık={haftalik}")

if __name__ == "__main__":
    main()
