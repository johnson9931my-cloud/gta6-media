#!/usr/bin/env python3
"""TikTok + Instagram autoposting helper for the cloud routines (repo johnson9931my-cloud/gta6-media).

Videos arrive in videos/queue/<slug>.mp4 with <slug>.json (transcript, size, cover candidates) and
<slug>.jpg (storyboard), sometimes with <slug>_cover.jpg (the author's cover photo, cover_url in the json), uploaded from the Mac by Инструменты/автопостинг.py upload. Every command prints JSON.

  python3 tools/tiktok_inst.py scan                 # queue items not yet scheduled (new or in reserve)
  python3 tools/tiktok_inst.py slots --network tiktok --taken taken.json   # free daily slots, nearest first
  python3 tools/tiktok_inst.py record <slug> <key> '<json>'
  python3 tools/tiktok_inst.py published <slug>     # after every network is out: drop the mp4, keep json/jpg in videos/published/
  python3 tools/tiktok_inst.py ledger
"""
import json, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent
QUEUE = REPO / "videos/queue"
PUBLISHED = REPO / "videos/published"
LEDGER = REPO / "tiktok-inst/ledger.json"
RAW = "https://raw.githubusercontent.com/johnson9931my-cloud/gta6-media/main/"
TZ = ZoneInfo("Europe/Dublin")
# The two daily slots, Dublin time: 15 minutes before the strongest TikTok peaks, 10:00 and 18:00 on Metricool's curve (checked 2026-11-02).
# Instagram has no curve of its own yet, so it follows TikTok.
SLOTS = {"tiktok": [(9, 45), (17, 45)], "instagram": [(9, 50), (17, 50)]}


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=1))


def load():
    return json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else {"videos": {}}


def save(led):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(led, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def cmd_scan(_):
    led, items = load(), []
    for mp4 in sorted(QUEUE.glob("*.mp4")):
        slug = mp4.stem
        status = led["videos"].get(slug, {}).get("status", "новое")
        if status not in ("новое", "Резерв"):
            continue
        meta_path = mp4.with_suffix(".json")
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        sheet = mp4.with_suffix(".jpg")
        cover = meta.get("cover_url")
        items.append({"slug": slug, "status": status, "media_url": RAW + f"videos/queue/{mp4.name}", "cover_url": cover,
                      **({"cover_rule": "обложка от автора: videoThumbnailUrl = cover_url, videoCoverMilliseconds не передавать"} if cover else {}),
                      "size_mb": round(mp4.stat().st_size / 1e6, 1), "sheet": str(sheet) if sheet.exists() else None,
                      "meta": meta or "нет метаданных — смотри раскадровку или анализируй файл сам (ffmpeg)"})
    out({"queue": str(QUEUE), "items": items})


def cmd_slots(a):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", required=True, choices=sorted(SLOTS))
    ap.add_argument("--taken")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--min-lead", type=float, default=1.0)
    ap.add_argument("--min-gap", type=float, default=4.0)
    ap.add_argument("--best")  # not used since the slots became fixed; kept so an older prompt still runs
    ap.add_argument("--fallback")
    o = ap.parse_args(a)

    taken = [datetime.fromisoformat(t).astimezone(TZ) for t in json.loads(Path(o.taken).read_text())] if o.taken and Path(o.taken).exists() else []
    now = datetime.now(TZ)
    free = []
    for day in range(o.days + 1):
        for hour, minute in SLOTS[o.network]:
            t = (now + timedelta(days=day)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            if t < now + timedelta(hours=o.min_lead) or t > now + timedelta(days=o.days):
                continue
            if not any(abs((t - x).total_seconds()) < o.min_gap * 3600 for x in taken):
                free.append({"datetime": t.isoformat(timespec="minutes"), "weekday": t.strftime("%a")})
    out({"network": o.network, "timezone": "Europe/Dublin", "now": now.isoformat(timespec="minutes"), "free_slots": free,
         "note": "бери первый из free_slots: ролик идёт в ближайший свободный слот"})


def cmd_record(a):
    slug, key, val = a[0], a[1], json.loads(a[2])
    led = load()
    v = led["videos"].setdefault(slug, {"added": datetime.now(TZ).isoformat(timespec="minutes")})
    if isinstance(val, dict) and isinstance(v.get(key), dict):
        v[key].update(val)
    else:
        v[key] = val
    save(led)
    out({"ok": True, "slug": slug, key: v[key]})


def cmd_published(a):
    slug = a[0]
    PUBLISHED.mkdir(parents=True, exist_ok=True)
    for ext in (".json", ".jpg", "_cover.jpg"):
        f = QUEUE / f"{slug}{ext}"
        if f.exists():
            subprocess.run(["git", "-C", str(REPO), "mv", "-f", str(f), str(PUBLISHED / f.name)], check=True)
    mp4 = QUEUE / f"{slug}.mp4"
    if mp4.exists():
        subprocess.run(["git", "-C", str(REPO), "rm", "-q", str(mp4)], check=True)
    led = load()
    led["videos"].setdefault(slug, {})["status"] = "Опубликовано"
    save(led)
    out({"ok": True, "slug": slug})


def cmd_ledger(_):
    out(load())


if __name__ == "__main__":
    cmds = {"scan": cmd_scan, "slots": cmd_slots, "record": cmd_record, "published": cmd_published, "ledger": cmd_ledger}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        sys.exit(1)
    cmds[sys.argv[1]](sys.argv[2:])
