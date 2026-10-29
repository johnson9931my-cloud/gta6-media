#!/usr/bin/env python3
"""TikTok + Instagram autoposting helper for the cloud routines (repo johnson9931my-cloud/gta6-media).

Videos arrive in videos/queue/<slug>.mp4 with <slug>.json (transcript, size, cover candidates) and
<slug>.jpg (storyboard), uploaded from the Mac by Инструменты/автопостинг.py upload. Every command prints JSON.

  python3 tools/tiktok_inst.py scan                 # queue items not yet scheduled (new or in reserve)
  python3 tools/tiktok_inst.py slots --network tiktok --best best.json --taken taken.json [--fallback other.json]
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
# Fallback audience activity (Dublin hours) when a network has no best-time data yet; from the brand's TikTok curve, 2026-10-29.
PRIOR = {9: 0.55, 10: 0.95, 11: 0.65, 12: 0.9, 13: 0.62, 14: 0.6, 15: 0.66, 16: 0.76, 17: 0.75, 18: 0.97, 19: 0.71, 20: 0.6, 21: 0.42}


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
        items.append({"slug": slug, "status": status, "media_url": RAW + f"videos/queue/{mp4.name}",
                      "size_mb": round(mp4.stat().st_size / 1e6, 1), "sheet": str(sheet) if sheet.exists() else None,
                      "meta": meta or "нет метаданных — смотри раскадровку или анализируй файл сам (ffmpeg)"})
    out({"queue": str(QUEUE), "items": items})


def cmd_slots(a):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--network", required=True)
    ap.add_argument("--best", required=True)
    ap.add_argument("--fallback")
    ap.add_argument("--taken")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--min-lead", type=float, default=8.0)
    ap.add_argument("--min-gap", type=float, default=4.0)
    ap.add_argument("--earliest-hour", type=int, default=9)
    ap.add_argument("--latest-hour", type=int, default=21)
    o = ap.parse_args(a)

    def curve(path):
        if not path or not Path(path).exists():
            return None
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        d = d.get("data", d)
        c = {(int(x["dayOfWeek"]), int(h["hourOfDay"])): float(h["value"]) for x in d for h in x["bestTimesByHour"]}
        return c if any(c.values()) else None

    own = curve(o.best)
    c = own or curve(o.fallback)
    source = "своя статистика" if own else ("статистика соседней сети" if c else "базовый профиль аудитории")
    top = max(c.values()) if c else 1.0
    taken = [datetime.fromisoformat(t).astimezone(TZ) for t in json.loads(Path(o.taken).read_text())] if o.taken and Path(o.taken).exists() else []
    now = datetime.now(TZ)
    cands = []
    for day in range(o.days + 1):
        d0 = (now + timedelta(days=day)).replace(minute=0, second=0, microsecond=0)
        for hour in range(o.earliest_hour, o.latest_hour + 1):
            t = d0.replace(hour=hour)
            if t < now + timedelta(hours=o.min_lead) or t > now + timedelta(days=o.days):
                continue
            score = (c.get((t.isoweekday(), hour), 0) / top) if c else PRIOR.get(hour, 0)
            if score <= 0:
                continue
            clash = any(abs((t - x).total_seconds()) < o.min_gap * 3600 for x in taken)
            if not clash:
                cands.append({"datetime": t.isoformat(timespec="minutes"), "weekday": t.strftime("%a"), "hour": hour, "score": round(score, 3)})
    cands.sort(key=lambda x: -x["score"])
    out({"network": o.network, "source": source, "timezone": "Europe/Dublin", "now": now.isoformat(timespec="minutes"),
         "top_free_slots": cands[:12], "note": "ставь на :40–:50 предыдущего часа перед сильным пиком"})


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
    for ext in (".json", ".jpg"):
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
