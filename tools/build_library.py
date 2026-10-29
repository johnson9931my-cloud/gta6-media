#!/usr/bin/env python3
"""Pre-generate the image library used by the cloud autopilot (which cannot push to git)."""
import subprocess, datetime, json, os
G = ["python3", "tools/make_post_image.py"]
LIB = "content-photo-ready/library"
def run(bg, out, **kw):
    cmd = G + (["--bg", f"content-photo/{bg}.jpg"] if bg else ["--stat"]) + ["--out", out]
    for k, v in kw.items():
        cmd += [f"--{k}", str(v)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
items = []
def ru_days(n):
    if n % 10 == 1 and n % 100 != 11: return "ДЕНЬ"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14): return "ДНЯ"
    return "ДНЕЙ"
# countdown: one per date
bgs = ["Vice_City_01","Jason_and_Lucia_02","Leonida_Keys_01","Lucia_Caminos_04","Vice_City_05","Jason_Duval_04","Port_Gellhorn_02",
       "Real_Dimez_02","Vice_City_08","Ambrosia_02","Jason_and_Lucia_10","Grassrivers_02","Vice_City_03","Lucia_Caminos_08",
       "Mount_Kalaga_National_Park_04","Jason_Duval_09","Vice_City_06","Raul_Bautista_02","Jason_and_Lucia_11","Vice_City_09","Jason_and_Lucia_12"]
release = datetime.date(2026, 11, 19)
d = datetime.date(2026, 10, 30); i = 0
while d <= release:
    n = (release - d).days
    out = f"{LIB}/otschet/{d.isoformat()}.jpg"
    if n == 0:
        run(bgs[i % len(bgs)], out, badge="РЕЛИЗ", line1="СЕГОДНЯ", line2="GTA 6 уже вышла")
    else:
        run(bgs[i % len(bgs)], out, badge="ОТСЧЁТ", line1=f"{n} {ru_days(n)}", line2="до релиза GTA 6")
    items.append({"type": "otschet", "date": d.isoformat(), "path": out, "bg": bgs[i % len(bgs)]})
    d += datetime.timedelta(days=1); i += 1
# holivar topics
hol = [
 ("pk_konsol","Vice_City_10","ПК","или","КОНСОЛЬ?",0.5),
 ("ps5_xbox","ULTIMATE_EDITION_01","PS5","или","XBOX?",0.5),
 ("dzheyson_lyusiya","Jason_and_Lucia_01","ДЖЕЙСОН","или","ЛЮСИЯ?",0.5),
 ("onlayn_syuzhet","Real_Dimez_01","ОНЛАЙН","или","СЮЖЕТ?",0.5),
 ("vc_ls","Vice_City_11","ВАЙС-СИТИ","или","ЛОС-САНТОС?",0.5),
 ("gta6_gta5","Vice_City_02","GTA 6","или","GTA 5?",0.5),
 ("disk_cifra","ULTIMATE_EDITION_WYMAN_CAR_COLLECTION_01","ДИСК","или","ЦИФРА?",0.5),
 ("hayp_obman","Jason_Duval_03","ХАЙП","или","РАЗОЧАРОВАНИЕ?",0.5),
 ("tachka_vertolet","ULTIMATE_EDITION_GROTTI_CHEETAH_01","ТАЧКА","или","ВЕРТОЛЁТ?",0.5),
 ("tiho_haos","Jason_Duval_07","ТИХО","или","ХАОС?",0.5),
 ("noch_den","Vice_City_07","НОЧЬ","или","ДЕНЬ?",0.5),
 ("gorod_bolota","Grassrivers_04","ГОРОД","или","БОЛОТА?",0.5),
 ("relize_vyhodnye","Lucia_Caminos_07","НОЧЬ РЕЛИЗА","или","ВЫХОДНЫЕ?",0.5),
 ("obzory_spoylery","Lucia_Caminos_09","ОБЗОРЫ","или","БЕЗ СПОЙЛЕРОВ?",0.5),
 ("vertical_classic","Port_Gellhorn_04","РЕАЛИЗМ","или","АРКАДА?",0.5),
 ("cal_boobie","Cal_Hampton_02","КЭЛ","или","БУБИ?",0.5),
 ("radio_spotify","Real_Dimez_03","РАДИО","или","СВОЯ МУЗЫКА?",0.5),
 ("lodka_motocikl","ULTIMATE_EDITION_SQUALO_01" if os.path.exists("content-photo/ULTIMATE_EDITION_SQUALO_01.jpg") else "Leonida_Keys_04","ЛОДКА","или","МОТОЦИКЛ?",0.5),
]
for slug,bg,a,m,b,f in hol:
    out=f"{LIB}/holivar/{slug}.jpg"; run(bg,out,badge="ХОЛИВАР ДНЯ",line1=a,mid=m,line2=b,focus=f)
    items.append({"type":"holivar","slug":slug,"text":f"{a} {m} {b}","path":out,"bg":bg})
# news backgrounds (generic, text is in the post)
news = ["Vice_City_04","Jason_and_Lucia_03","Lucia_Caminos_01","Jason_Duval_01","Vice_City_12","Ambrosia_04","Port_Gellhorn_05",
        "Leonida_Keys_06","DreQuan_Priest_01","Brian_Heder_02","Mount_Kalaga_National_Park_01","Boobie_Ike_02","Raul_Bautista_04",
        "Grassrivers_01","Jason_and_Lucia_08","ULTIMATE_EDITION_ELECTRIC_FANG_01","Vice_City_10","Lucia_Caminos_06"]
for bg in news:
    out=f"{LIB}/novost/{bg}.jpg"; run(bg,out,badge="НОВОСТИ GTA 6",line1="",line2="")
    items.append({"type":"novost","path":out,"bg":bg})
json.dump(items, open(f"{LIB}/manifest.json","w"), ensure_ascii=False, indent=1)
print(len(items))
