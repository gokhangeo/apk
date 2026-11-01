# Nefes ortak spam listesi: symbuzzer/Turkish-Spam-Numbers + nefes/ek-liste.json -> nefes/spam-listesi.json
import json, re, urllib.request, os
def norm(s):
    d = re.sub(r"\D", "", s)
    if d.startswith("00"): d = d[2:]
    elif d.startswith("0"): d = "90" + d[1:]
    elif len(d) == 10 and d.startswith("5"): d = "90" + d
    return "+" + d if 9 <= len(d) <= 15 else None
liste = {}
try:
    ham = urllib.request.urlopen("https://raw.githubusercontent.com/symbuzzer/Turkish-Spam-Numbers/main/numbers", timeout=30).read().decode()
    for s in ham.split():
        n = norm(s)
        if n: liste[n] = {"numara": n, "etiket": "Spam (topluluk)", "engelle": True}
except Exception as e:
    print("kaynak alınamadı:", e)
ek = "nefes/ek-liste.json"
if os.path.exists(ek):
    for o in json.load(open(ek)):
        n = norm(o["numara"])
        if n: liste[n] = {"numara": n, "etiket": o.get("etiket") or "Spam", "engelle": o.get("engelle", True)}
if liste:
    json.dump(sorted(liste.values(), key=lambda o: o["numara"]), open("nefes/spam-listesi.json", "w"), ensure_ascii=False, indent=0)
print(len(liste), "numara")
