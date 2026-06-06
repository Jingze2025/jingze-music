#!/usr/bin/env python3
"""Batch generate covers (AGNES base + PIL text overlay) for all /tmp/jingze_music/<name>/.

For each subdir, reads cover_spec.json if exists, else uses defaults.
Saves: cover.png / cover.jpg / cover_jpeg.jpg (3 formats).

cover_spec.json schema (⚠️ pitfall #26: ALL 4 fields required):
  {
    "name": "半壶纱_Z",
    "prompt": "AGNES底图prompt (NO text/Chinese in prompt)",
    "title": "半壶纱",
    "subtitle": "半句古诗 半晌假",
    "brand": "京择说",
    "byline": "Music by 京择"
  }

⚠️ pitfall #24: 字段名是 `prompt`（不是 `agines_prompt`），写错 AGNES KeyError FATAL
⚠️ pitfall #26: title/subtitle/brand/byline 4 字段全要，缺一 PIL KeyError FATAL

Lessons baked in (2026-06-06):
  - 1536x1536 (NOT 1920, AGNES HTTP 500)
  - AGNES prompt NO text/writing/Chinese characters
  - AGNES Google Cloud Storage SSL EOF → 3x retry + sleep 5s (pitfall #23)
  - PIL title font size adapts to title length (3/4/5/6+ chars)
  - Bottom-right byline MUST use W-320 (avoid edge crop)
  - PIL bottom gradient + shadow text for readability
  - 3 formats: PNG optimize / JPEG quality 95 progressive
"""
import os, sys, time, json
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

KEY_PATH = os.path.expanduser("~/.baoyu-skills/.env")
PROXIES = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
BASE_DIR = "/tmp/jingze_music"
FONT_PATH = "/System/Library/Fonts/PingFang.ttc"

# --- 1. Read AGNES_API_KEY ---
key = None
for line in open(KEY_PATH).read().splitlines():
    if line.startswith("AGNES_API_KEY"):
        key = line[line.find("=") + 1:].strip()
        break
if not key or len(key) < 10:
    print(f"FATAL: AGNES key length {len(key) if key else 0}")
    sys.exit(1)
print(f"[AGNES] loaded ({len(key)} chars)")

# --- 2. Helper: PIL shadow text ---
def shadow_text(img, draw, pos, text, font, fill, offset=(6, 8), blur=8):
    x, y = pos
    sl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sl)
    sd.text((x + offset[0], y + offset[1]), text, font=font, fill=(0, 0, 0, 200))
    sl = sl.filter(ImageFilter.GaussianBlur(blur))
    img.paste(sl, (0, 0), sl)
    draw.text(pos, text, font=font, fill=fill)

def title_font_size(title_len):
    if title_len <= 3:   return 240
    elif title_len <= 4: return 200
    elif title_len <= 5: return 160
    else:                return 130

# --- 3. Discover specs ---
specs = []
default_dirs = sorted(os.listdir(BASE_DIR)) if len(sys.argv) < 2 else sys.argv[1].split("|")
# ⚠️ pitfall #26: 4 字段预校验 (title/subtitle/brand/byline) + pitfall #24 (字段名 prompt 不是 agines_prompt)
required_fields = ["prompt", "title", "subtitle", "brand", "byline"]
for d in default_dirs:
    spec_path = os.path.join(BASE_DIR, d, "cover_spec.json")
    if not os.path.isdir(os.path.join(BASE_DIR, d)):
        continue
    if not os.path.exists(spec_path):
        print(f"[SKIP] {d}: no cover_spec.json")
        continue
    spec = json.load(open(spec_path))
    missing = [f for f in required_fields if f not in spec]
    if missing:
        print(f"[SKIP] {d}: missing required fields: {missing}")
        continue
    specs.append((d, spec))
print(f"[COVERS] {len(specs)} specs found")

# --- 4. For each: AGNES + PIL ---
for name, spec in specs:
    base_dir = os.path.join(BASE_DIR, name)
    base_path = os.path.join(base_dir, "cover_visual_1536.png")
    png_path  = os.path.join(base_dir, "cover.png")
    jpg_path  = os.path.join(base_dir, "cover.jpg")
    jpeg_path = os.path.join(base_dir, "cover_jpeg.jpg")

    if (os.path.exists(png_path) and os.path.getsize(png_path) > 100_000 and
        os.path.exists(jpg_path) and os.path.getsize(jpg_path) > 100_000):
        print(f"\n[SKIP] {name}: cover files exist")
        continue

    print(f"\n=== [{name}] AGNES base ===")
    # --- 4a. AGNES (with 3x retry on SSL EOF) ---
    if os.path.exists(base_path) and os.path.getsize(base_path) > 1_000_000:
        print(f"  reusing cached base ({os.path.getsize(base_path)/1024/1024:.1f}MB)")
    else:
        success = False
        for attempt in range(3):
            try:
                t0 = time.time()
                r = requests.post(
                    "https://apihub.agnes-ai.com/v1/images/generations",
                    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
                    json={"model": "agnes-image-2.1-flash",
                          "prompt": spec["prompt"], "size": "1536x1536", "n": 1},
                    timeout=180, proxies=PROXIES,
                )
                print(f"  AGNES HTTP {r.status_code} in {time.time()-t0:.1f}s")
                if r.status_code != 200:
                    print(f"  BODY: {r.text[:300]}")
                    continue
                data = r.json()
                if "data" not in data or not data["data"]:
                    continue
                url = data["data"][0].get("url")
                if not url:
                    continue
                # Download with 3x retry on SSL EOF
                for d_attempt in range(3):
                    try:
                        t1 = time.time()
                        img_resp = requests.get(url, timeout=120, proxies=PROXIES)
                        print(f"  download {img_resp.status_code} in {time.time()-t1:.1f}s, {len(img_resp.content)}B")
                        if img_resp.status_code == 200 and len(img_resp.content) > 1_000_000:
                            with open(base_path, "wb") as f:
                                f.write(img_resp.content)
                            print(f"  base saved ({os.path.getsize(base_path)/1024/1024:.1f}MB)")
                            success = True
                            break
                    except requests.exceptions.SSLError as e:
                        print(f"  download SSL EOF attempt {d_attempt+1}: {e}")
                        if d_attempt < 2:
                            time.sleep(5)  # pitfall #23: sleep 3s → 5s
                if success:
                    break
            except Exception as e:
                print(f"  AGNES exception attempt {attempt+1}: {e}")
                if attempt < 2:
                    time.sleep(5)  # pitfall #23: sleep 3s → 5s
        if not success:
            print(f"  FATAL: {name} AGNES failed after 3 attempts, skipping")
            continue

    # --- 4b. PIL overlay ---
    img = Image.open(base_path).convert("RGBA")
    W, H = img.size
    gradient = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grad_top_y = int(H * 0.5)
    for y in range(grad_top_y, H):
        rel = (y - grad_top_y) / (H - grad_top_y)
        alpha = int(220 * rel ** 2.2)
        gradient.paste((0, 0, 0, min(alpha, 200)), (0, y, W, y + 1))
    img_with_grad = Image.alpha_composite(img, gradient)
    draw = ImageDraw.Draw(img_with_grad)

    fts = title_font_size(len(spec["title"]))
    ft  = ImageFont.truetype(FONT_PATH, fts)
    fs  = ImageFont.truetype(FONT_PATH, 84)
    fb  = ImageFont.truetype(FONT_PATH, 57)
    fbl = ImageFont.truetype(FONT_PATH, 42)

    shadow_text(img_with_grad, draw, (105, H - 480), spec["title"], ft, fill=(255, 245, 220, 255))
    shadow_text(img_with_grad, draw, (105, H - 250), spec["subtitle"], fs, fill=(255, 235, 200, 255))
    shadow_text(img_with_grad, draw, (W - 230, 90), spec["brand"], fb,
                fill=(255, 250, 235, 230), offset=(3, 4), blur=5)
    draw.text((W - 320, H - 110), spec["byline"], font=fbl, fill=(230, 220, 200, 200))

    final = img_with_grad.convert("RGB")
    final.save(png_path, "PNG", optimize=True)
    final.save(jpg_path, "JPEG", quality=95, optimize=True, progressive=True)
    final.save(jpeg_path, "JPEG", quality=95, optimize=True, progressive=True)
    print(f"  PNG: {os.path.getsize(png_path)/1024/1024:.2f}MB / JPG: {os.path.getsize(jpg_path)/1024/1024:.2f}MB")
    print(f"  ✓ {name} DONE")

print("\n=== ALL COVERS DONE ===")
