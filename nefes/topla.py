# Nefes ortak spam listesi (her gün): herkese açık kaynaklar + nefes/ek-liste.json
#  -> nefes/spam-listesi.json   tek numaralar [{"numara":"+90...","etiket":..,"engelle":true}]
#  -> nefes/spam-araliklari.json numara aralıkları [{"onEk":"+90850484","hane":4,"etiket":..}]  (+90850484#### = 10.000 numara)
import json, re, os, plistlib, urllib.request

def al(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "nefes"}), timeout=40).read()

def norm(s):
    d = re.sub(r"\D", "", s)
    if d.startswith("00"): d = d[2:]
    elif d.startswith("0"): d = "90" + d[1:]
    elif len(d) == 10 and d.startswith("5"): d = "90" + d
    return "+" + d if (d.startswith("90") and len(d) == 12) else None

tekler, araliklar, kaynak = {}, {}, []
def ekle(n, etiket):
    n = norm(n)
    if n and n not in tekler: tekler[n] = {"numara": n, "etiket": etiket, "engelle": True}

def satirlar(u, etiket, md=False):
    t = al(u).decode("utf-8", "ignore"); e = etiket
    for l in t.splitlines():
        l = l.strip()
        if md and l.startswith("#"):
            b = l.lstrip("#").strip(); e = etiket if (not b or b.upper().startswith(("NOT", "TR SPAM"))) else b; continue
        if "*" in l or not l: continue
        if md and not l.startswith(("-", "*")): continue
        ekle(l, e)

islemler = [
    ("symbuzzer/Turkish-Spam-Numbers", lambda: satirlar("https://raw.githubusercontent.com/symbuzzer/Turkish-Spam-Numbers/main/numbers", "Spam (topluluk)")),
    ("mavisland/tr-spam-calls", lambda: satirlar("https://raw.githubusercontent.com/mavisland/tr-spam-calls/master/README.md", "Dolandırıcı", md=True)),
    ("can-acar gist", lambda: satirlar("https://gist.githubusercontent.com/can-acar/fab8390c695ee01b4d7ab1b04ea56a2b/raw", "Spam")),
]
def begone():
    if True:
        for o in plistlib.loads(al("https://gist.githubusercontent.com/keremerkan/361c8d96aa74072038acd07fa1691355/raw/begone_engelleme.xml")):
            n, e = o.get("number", ""), o.get("title") or "Spam"
            k = n.count("#")
            if k == 0: ekle(n, e); continue
            on = norm(n.replace("#", "0"))
            if not on or not (2 <= k <= 5): continue
            on = on[:len(on) - k]
            araliklar[on] = {"onEk": on, "hane": k, "etiket": e}
islemler.append(("Begone topluluk listesi (keremerkan)", begone))

for ad, f in islemler:
    try:
        once = len(tekler) + len(araliklar); f(); kaynak.append(ad); print(ad, len(tekler) + len(araliklar) - once)
    except Exception as e:
        print("kaynak alınamadı:", ad, e)

if os.path.exists("nefes/ek-liste.json"):
    for o in json.load(open("nefes/ek-liste.json")):
        num = o.get("numara", "")
        if "#" in num:
            k = num.count("#"); on = norm(num.replace("#", "0"))
            if on: araliklar[on[:len(on)-k]] = {"onEk": on[:len(on)-k], "hane": k, "etiket": o.get("etiket") or "Spam"}
            continue
        n = norm(num)
        if n: tekler[n] = {"numara": n, "etiket": o.get("etiket") or "Spam", "engelle": o.get("engelle", True)}

# Aralığın içine düşen tek numaraları ayrıca tutma.
def kapsar(n): return any(n.startswith(a) for a in araliklar)
tek = [v for k, v in sorted(tekler.items()) if not kapsar(k)]
if tek or araliklar:
    json.dump(tek, open("nefes/spam-listesi.json", "w"), ensure_ascii=False, indent=0)
    json.dump(sorted(araliklar.values(), key=lambda o: o["onEk"]), open("nefes/spam-araliklari.json", "w"), ensure_ascii=False, indent=0)
toplam = len(tek) + sum(10 ** a["hane"] for a in araliklar.values())
print(len(tek), "tek numara,", len(araliklar), "aralık, toplam", toplam, "numara; kaynaklar:", ", ".join(kaynak))
