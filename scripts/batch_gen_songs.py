#!/usr/bin/env python3
"""Batch generate songs from /tmp/jingze_music/<name>/{lyrics.txt, tags.txt} → song.mp3.

Usage:
  python3 scripts/batch_gen_songs.py "歌1|歌2|歌3|..."
  # default: reads all subdirs of /tmp/jingze_music/

Lessons baked in (2026-06-06):
  - requests + 7890 proxy (NOT curl, sandbox filters Authorization header)
  - key via startswith("MINIMAX_CN_API_KEY") (NOT string parsing, sandbox truncates "=")
  - music-2.6-free model (NOT music-2.6, that's the UI ad name)
  - Skip cached: mp3 exists + size > 1MB
  - python3 -u when run in background (avoid stdout buffer deadlock)
  - Sequential (NOT parallel — MiniMax rate limit)
"""
import os, sys, time, json
import requests

KEY_PATH = os.path.expanduser("~/.hermes/.env")
PROXIES = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
BASE_DIR = "/tmp/jingze_music"

# --- 1. Read MINIMAX_CN_API_KEY safely ---
key = None
for line in open(KEY_PATH).read().splitlines():
    if line.startswith("MINIMAX_CN_API_KEY"):
        key = line[line.find("=") + 1:].strip()
        break
if not key or len(key) < 20:
    print(f"FATAL: key length {len(key) if key else 0}")
    sys.exit(1)
print(f"[KEY] loaded ({len(key)} chars)")

# --- 2. Discover songs ---
if len(sys.argv) > 1:
    names = sys.argv[1].split("|")
else:
    names = [d for d in sorted(os.listdir(BASE_DIR))
             if os.path.isdir(os.path.join(BASE_DIR, d))
             and os.path.exists(os.path.join(BASE_DIR, d, "lyrics.txt"))]
print(f"[SONGS] {len(names)}: {names}")

# --- 3. For each: POST + download ---
results = []
for name in names:
    base_dir = os.path.join(BASE_DIR, name)
    lyrics_path = os.path.join(base_dir, "lyrics.txt")
    tags_path   = os.path.join(base_dir, "tags.txt")
    mp3_path    = os.path.join(base_dir, "song.mp3")
    meta_path   = os.path.join(base_dir, "song_meta.json")

    if not os.path.exists(lyrics_path) or not os.path.exists(tags_path):
        print(f"\n[SKIP] {name}: missing lyrics.txt or tags.txt")
        continue
    if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1_000_000:
        print(f"\n[SKIP] {name}: song.mp3 cached ({os.path.getsize(mp3_path)/1024/1024:.1f}MB)")
        results.append({"name": name, "status": "cached"})
        continue

    lyrics = open(lyrics_path).read()
    prompt = open(tags_path).read().strip()
    print(f"\n=== [{name}] lyrics={len(lyrics)}B prompt={len(prompt)}B ===")
    if len(lyrics) > 3500:
        print(f"  WARNING: lyrics > 3500 chars (MiniMax limit), may truncate")

    payload = {
        "model": "music-2.6-free",
        "prompt": prompt,
        "lyrics": lyrics,
        "audio_setting": {"sample_rate": 44100, "bitrate": 256000, "format": "mp3"},
        "output_format": "url"
    }

    t0 = time.time()
    try:
        r = requests.post(
            "https://api.minimaxi.com/v1/music_generation",
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            json=payload, timeout=300, proxies=PROXIES,
        )
        elapsed = time.time() - t0
        print(f"  HTTP {r.status_code} in {elapsed:.1f}s")
        if r.status_code != 200:
            print(f"  BODY: {r.text[:500]}")
            results.append({"name": name, "status": "api_error", "code": r.status_code})
            continue

        data = r.json()
        base = data.get("base_resp", {})
        print(f"  base_resp: {base}")
        if base.get("status_code") != 0:
            results.append({"name": name, "status": "biz_error", "base_resp": base})
            continue

        audio_url = data["data"]["audio"]
        print(f"  audio_url: {audio_url[:90]}...")

        # Download
        audio = requests.get(audio_url, timeout=180, proxies=PROXIES)
        print(f"  download {audio.status_code}, {len(audio.content)}B")
        with open(mp3_path, "wb") as f:
            f.write(audio.content)
        json.dump({"audio_url": audio_url, "elapsed_api_s": round(elapsed, 1),
                   "file_size": len(audio.content)}, open(meta_path, "w"),
                  indent=2, ensure_ascii=False)
        results.append({"name": name, "status": "ok", "size": len(audio.content),
                        "elapsed": round(elapsed, 1)})
        print(f"  ✓ {mp3_path}")
    except Exception as e:
        print(f"  EXCEPTION: {e}")
        results.append({"name": name, "status": "exception", "err": str(e)})

# --- 4. Summary ---
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
ok = sum(1 for r in results if r["status"] == "ok")
cached = sum(1 for r in results if r["status"] == "cached")
err = len(results) - ok - cached
print(f"  ok: {ok}  cached: {cached}  err: {err}")
for r in results:
    print(f"  {r['name']:20s}  {r['status']:12s}  {r.get('size', '?')}")
