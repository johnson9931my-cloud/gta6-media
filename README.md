# gta6-media

Media for @jonny_gta6 Threads posts (GTA 6, Russian-speaking audience).

- `content-photo/` — official GTA 6 screenshots by Rockstar Games (promotional material, © Rockstar Games). Used in commentary/news posts with credit «📸 Rockstar Games» / «кадр: Rockstar Games».
- `content-photo-ready/YYYY-MM-DD/` — finished post images (screenshot + branded text, infographics).
- `clips/` — short vertical video clips cut from official trailers/gameplay.
- `tools/make_post_image.py` — generator for branded 1080×1350 images.

Public URL of any file:
`https://raw.githubusercontent.com/johnson9931my-cloud/gta6-media/main/<path>`
Metricool accepts these URLs in `media` (tested 27.10.2026).

Rules: only official Rockstar material or our own graphics. No Pinterest/fan art, no photos of real people, no other bloggers' content.

## TikTok + Instagram autoposting

- `videos/queue/<slug>.mp4` — finished vertical videos waiting to be scheduled, each with `<slug>.json` (title, transcript, duration, cover candidates, notes) and `<slug>.jpg` (storyboard). Uploaded from the Mac by `Инструменты/автопостинг.py upload` (compressed to ~15 MB, ASCII slug so the raw URL is clean).
- `videos/published/` — json/jpg of published videos; the mp4 is removed after publication to keep the repo small.
- `tiktok-inst/strategy.md` — timing, cadence, captions, hashtags, post template; `tiktok-inst/ledger.json` — state; `tiktok-inst/reports/` — daily reports.
- `tools/tiktok_inst.py` — helper used by the cloud routines «TikTok + Instagram — утро/день».
