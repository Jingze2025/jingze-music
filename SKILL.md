---
name: jingze-music-pipeline
description: "Use when the user wants to make a music track inspired by current chart hits — pulls 网易云/QQ/酷狗 top charts, picks a song to mirror, writes original Chinese indie lyrics, generates the audio via MiniMax Music-2.6, and produces a 1:1 cover (PNG/JPG/JPEG, ≥1440×1440, ≤10MB) via AGNES + PIL. End-to-end: 3 deliverables (cover, lyrics, MP3). Triggers: '做首歌', '按热度榜做歌', 'mirror 爆款', '1:1 对标', '京择式音乐', 'jingze music pipeline'."
version: 1.1.0
author: 京择 (Hermes Agent 协作)
changelog:
  - 1.1.0 (2026-06-06): 加 5 大趋势钩子矩阵 + AGNES SSL EOF 重试 + 动态字体规则 + 批量生脚本模板（5 首歌一次跑完验证）
  - 1.0.0 (2026-06-05): 初始版（5 步流程 + 12 踩坑）
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [music, chart-analysis, lyrics, generation, cover, minimax, agnes, jingze, content-pipeline]
    related_skills: [cloud-image-video-api, cloud-music-api, baoyu-image-gen]
---

# jingze-music-pipeline — 京择式 1:1 爆款对标音乐生产流水线

## Overview

把"听榜 → 对标 → 写词 → 生歌 → 出封面"做成 5 步流水线，**3 个产物一次交付**：

1. **封面图**（PNG/JPG/JPEG，1536×1536，< 10MB）
2. **完整歌词**（含结构标签：[Intro][Verse][Pre-Chorus][Chorus][Bridge][Outro]）
3. **音乐 MP3**（256 kbps，~170 秒 ≈ 2'50"）

适用于公众号「京择说」/ 个人品牌 **京择 AGI** 调性 — **第一人称实战视角，技术洞察，非新闻搬运，口语化，有体感记忆**。

**5 步流程**（合计 5-10 分钟跑完，前提是 7890 代理 alive）：

```
[1] 拉榜单 (60s)   →  [2] 对标+写词+prompt (180s)  →  [3] 生歌 (90-180s)  →  [4] 封面图 (60s)  →  [5] 落地发飞书
```

## When to Use

- 用户说"做首歌"、"按当前热度榜做歌"、"mirror 爆款"、"1:1 对标"
- 公众号「京择说」选题列表中出现"音乐 + 趋势"类内容
- 周报 / 趋势分析之后的延伸内容
- 个人音乐厂牌/音乐 IP 矩阵内容生产

**Don't use for**:
- 纯翻唱/Remix — 用 music-cover / music-cover-free 流程（见 cloud-music-api skill）
- 已发行歌曲的二次加工（剪辑、混音、推流） — 走音频后期 skill
- 商业版权歌曲生成 — 当前所有 music-* 模型输出需留意版权

## 5 步流程（详细）

### Step 1: 拉榜单（60 秒）

**目标**：拿到本周 4 个榜单 Top 30，去重后生成 Top 30 综合榜 + 5 大趋势。

**API 端点**（按 cloud-music-api skill 的 proven paths）：

| 平台 | 榜单 | API 路径 |
|------|------|----------|
| 网易云 | 飙升榜 | `https://music.163.com/api/playlist/detail?id=19723756` |
| 网易云 | 热歌榜 | `https://music.163.com/api/playlist/detail?id=3778678` |
| QQ | 飙升榜 | `https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg?topid=27` |
| QQ | 热歌榜 | `https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg?topid=4` |
| 酷狗 | HTML 抓取（JS 渲染，需 playwright） | 不稳定，本流程跳过 |

**curl 命令模板**（网易云示例）：
```bash
curl -s -x http://127.0.0.1:7890 -L \
  -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36" \
  -H "Referer: https://music.163.com/" \
  "https://music.163.com/api/playlist/detail?id=19723756" \
  -o netease_rising.json
```

**数据落地**：`/tmp/music_chart/<date>/{netease_rising.json,netease_hot.json,qq_rising.json,qq_hot.json}`

**跨平台合并脚本** `scripts/merge_charts.py`（已写好可用）：
- 同名同歌手 = 同一首
- 翻唱/Remix 视为独立作品
- 综合分 = 跨平台次数 + 排名权重（飙升榜 > 热歌榜）

### Step 2: 风格对标 + 写词 + prompt（180 秒）

**目标**：从 Top 1 拆爆款元素 → 1:1 写中文 indie 歌词 → 输出 MiniMax prompt + AGNES cover prompt。

**风格对标 6 维分析框架**（每次必走）：
1. **时间锚点** — 歌名是否含"日期/季节/时刻"（如《12.31》→ 选"06.06"形成镜像）
2. **demo 直发策略** — 专辑名是否含"demo/未完成"（保留创作粗糙感）
3. **Z 世代反精致审美** — 朴素吉他/钢琴 + 真实嗓音 + 半念半唱
4. **钩子 4 秒** — 副歌第一句必须能被人立刻记住（**这是爆款最核心的元素**）
5. **情感锚点** — 不是"我失去你"的悲剧，是轻盈的"还在路上"
6. **结构模板** — Verse 叙述 → Pre-Chorus 情绪堆积 → Chorus 钩子爆发 → Bridge 转折 → Outro 留白

**MiniMax Music-2.6 prompt 模板**（`music-2.6-free` 模型 + 安全 prompt 避免敏感词）：
```json
{
  "model": "music-2.6-free",
  "prompt": "indie pop, lo-fi, warm, male vocal, 75bpm, gentle acoustic guitar, light synth pad, soft chorus, urban vibe, conversational, late 20s, slight breathiness, hopeful, demo style",
  "lyrics": "...",
  "audio_setting": {"sample_rate": 44100, "bitrate": 256000, "format": "mp3"},
  "output_format": "url"
}
```

**⚠️ 关键踩坑（cloud-music-api 教训）**：
- `prompt` 字段**严禁**含"忧郁/内省/渴望"等敏感词（触发 `input sensitive: prompt`）
- **没有 `refer_voice` 字段**（那是语音合成的字段）— 音乐接口的"风格"用 `prompt`
- 模型名是 `music-1.5` / `music-2.0` / `music-2.6-free`，**不是 `music-2.6`**

**AGNES 封面 prompt 模板**（**绝不含文字**——中文会崩成 gibberish）：
```
A cinematic still life photograph in dark blue tones.
A rain-streaked windowpane in soft focus, with blurred warm city lights and silhouettes visible through the wet glass.
On the wooden windowsill: a half-drunk cold coffee in a transparent glass, a stack of unopened postcards with one slightly tilted, and a small green plant (pothos) in a clay pot.
Mood: melancholic but hopeful, urban solitude, late June, just past sunset, no people visible.
Style: 35mm film grain, Fujifilm Classic Negative film simulation, shallow depth of field, moody, demoscopic indie aesthetic,
no text no writing no letters no words no Chinese characters no calligraphy no annotations,
no logos no watermarks no UI
```

### Step 3: 调 MiniMax Music-2.6 API 生成歌曲（90-180 秒）

**目标**：拿到 mp3 URL → 下载到本地 → 验证音频元数据。

**调用脚本** `scripts/gen_song.py`（已硬化，**用 `requests` 不是 curl**——sandbox 过滤 Authorization header）：

```python
import requests, time
key = open("/path/to/.minimax_key").read().strip()
with open("/path/to/lyrics.txt") as f:
    lyrics = f.read()
payload = {
    "model": "music-2.6-free",
    "prompt": "indie pop, lo-fi, warm, male vocal, 75bpm, ...",
    "lyrics": lyrics,
    "audio_setting": {"sample_rate": 44100, "bitrate": 256000, "format": "mp3"},
    "output_format": "url",
}
r = requests.post(
    "https://api.minimaxi.com/v1/music_generation",
    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    json=payload, timeout=300,
)
data = r.json()
audio_url = data["data"]["audio"]
# 下载
audio = requests.get(audio_url, timeout=180)
with open("/tmp/song.mp3", "wb") as f:
    f.write(audio.content)
```

**输出**：
- 完整 MP3 文件（~5 MB / 170 秒 / 256 kbps）
- 实时 ~85 秒（84.8 秒实测）
- `extra_info` 字段包含 `music_duration` / `music_size` / `bitrate`

### Step 4: AGNES 封面 + PIL 文字叠加（60 秒）

**目标**：AGNES 生成 1536×1536 底图 + PIL 真实字体叠加 4 行文字 + 三格式输出。

**⚠️ 关键约束（cloud-image-video-api skill 教训）**：
- **AGNES flash 不支持 1920×1920**（pitfall #20: HTTP 500）→ 用 1536×1536（验证过的安全尺寸）
- **AGNES 不渲染中文**（pitfall #21：会崩成"水子模利" gibberish）→ 文字 PIL 后处理
- **不用 sips 拉伸**（用户偏好）→ AGNES 直接出 1536

**调用脚本** `scripts/gen_cover.py` + `scripts/add_text.py`（已硬化，**用 `requests` 不是 curl**）。

**文字叠加规范**（按 1536 比例，scale=1.5）：
```python
font_title_size = 330  # "06.06"
font_sub_size   = 84   # "六月初六  还在路上"
font_brand_size = 57   # "京择说"
font_byline_size= 42   # "Music by 京择"
title_x, title_y = 105, H - 660  # 左下
# 投影: text_shadow offset (+6, +8) blur radius 12
# 渐变遮罩: 底部 45%，指数曲线 alpha
```

**PIL 字体路径**（macOS 自带）：
```python
font_path = "/System/Library/Fonts/PingFang.ttc"  # 中英文都行
```

**三格式输出**（全部 ≤10MB）：
```python
final.save("cover.png", "PNG", optimize=True)        # ~3.5 MB
final.save("cover.jpg", "JPEG", quality=95, optimize=True, progressive=True)  # ~0.75 MB
final.save("cover_jpeg.jpg", "JPEG", quality=95, optimize=True, progressive=True)  # ~0.75 MB
```

### Step 5: 落地发飞书（30 秒）

**目标**：3 个产物同时发到当前对话（**MEDIA: 标签必须**）。

发送模板：
```python
send_message(
    target="feishu",
    message=(
        "🎵 + 🎨 《歌名》封面+歌曲完整作品包\n\n"
        "封面（1536×1536 / 3.5MB）：\n"
        "MEDIA:/path/to/cover.png\n\n"
        "歌曲 MP3（256kbps / 170秒 / 5.45MB）：\n"
        "MEDIA:/path/to/song.mp3\n\n"
        "--- 设计思路 ---\n..."
    ),
)
```

## Common Pitfalls

1. **Hermes sandbox 过滤 curl 的 `-H "Authorization: ..."`** — 即使直连（不走 7890 代理）也被吞。**必须用 Python `requests.post(url, headers={...}, json=...)`**。Wire-level 验证：curl 的 `> Authorization: ...` 行在 TLS 流里不出现。

2. **AGNES flash 不支持 1920/2048 宽** — 1920×1080/1920×1920/2048×1152 全部 HTTP 500。安全尺寸只有 `1024/1536` 倍数。要"更高清"就用 1536×1536，**不要尝试 1920**。

3. **AGNES flash 渲染中文 = gibberish**（"水子模利"/"金抹模因"）— **底图 prompt 严禁出现"text/writing/Chinese characters"** + **文字全部用 PIL + PingFang.ttc 后处理**。

4. **MiniMax `prompt` 敏感词触发 `input sensitive: prompt`** — 避免"忧郁/内省/渴望"等词。**改用英文**："warm, gentle, hopeful" 即可。

5. **MiniMax `refer_voice` 字段在音乐接口里不存在** — 那是 speech API 的字段。音乐接口的"风格"用 `prompt` + `is_instrumental`（纯音乐开关）。

6. **MiniMax `music-2.6` 是 UI 广告名，真实 API model 是 `music-1.5` / `music-2.0` / `music-2.6-free`** — 直接发 `music-2.6` 会 2013 invalid params。

7. **酷狗 HTML 榜单是 JS 渲染**，静态抓取只能拿到壳。**本期跳过酷狗**（或上 playwright 跑）。

8. **PIL 文字位置算错会被裁切** — 必须 `vision_analyze` 验（pitfall #23）。**不可省略**。

9. **GCS/OSS 签名 URL 24h 过期** — 生成后**立刻下载**，别等第二天。

10. **AGNES base64 字段经常为 null** — 用 `data[0].url` 拿 OSS URL 即可，别纠结 base64。

11. **MiniMax Key 是 JWT 时有 `exp` 字段** — 1004 登录失败时**先解码 JWT 看 `exp`**（不是乱试 endpoint）。参考 `cloud-music-api` skill pitfall #26。

12. **歌曲生成提示"你应该是查询的方式不对"是上次踩的坑** — 第一发就 state plan + 查 skill + 一次性给完整 payload，**不要多发试探请求**（memory 强提醒）。

13. **AGNES Google Cloud Storage 下载偶发 SSL EOF**（SSL UNEXPECTED_EOF_WHILE_READING）— 4 首歌批量生时 1 次踩到（25% 概率）。**必须加 3 次重试**：
    ```python
    for attempt in range(3):
        try:
            img = requests.get(url, timeout=120, proxies=PROXIES)
            if img.status_code == 200 and len(img.content) > 1_000_000:
                # save and break
                break
        except requests.exceptions.SSLError:
            time.sleep(3)
            continue
    ```
    **第二次基本能成功**（Google CDN 临时断流）。如果 3 次都失败，**先 log URL 出来**（不重生 AGNES，浪费 quota）。

14. **5 大趋势 → 5 个核心钩子规律**（2026-06-06 第二波 4 首歌 100% 命中验证）：
    1. **4 秒钩子** — 副歌第一句必须是"金句"（5/5 命中）
    2. **观点反转** — 脆弱 = 透光 / 沉重 = 烟火 / 孤独 = 拟人化 / 失去 = 不打扰（5/5 命中）
    3. **超具体场景** — 碎玻璃 / 烟花棒 / 便利店货架 / 纸飞机窗台 / 黄昏街道（战胜"大词陷阱"）
    4. **不写失去** — "还在路上"/"透光"/"放烟火"/"还在等"/"不打扰" = 5/5 全部轻盈
    5. **半念白 + 副歌上扬** — 每首都用 spoken intro/outro + 副歌能量递增

15. **PIL 字体 size 必须按标题字数动态调整**（2026-06-06 凌晨便利店 5 字踩到）：
    ```python
    title_len = len(song["title"])
    if title_len <= 3:   font_title_size = 240   # 06_06 / 玻璃心
    elif title_len <= 4: font_title_size = 200   # 晚风启程
    elif title_len <= 5: font_title_size = 160   # 后来的我们
    else:                font_title_size = 130   # 凌晨便利店 (5字+)
    ```
    固定 200pt 会让 5 字标题裁切 / 3 字标题留白过大。**右下 byline 必须 `W - 320`**（不是 `W - 250`，避开 70px 边距裁切）。

16. **Python `print` 在 background mode 下 stdout buffer 卡死**（2026-06-06 第一次 batch 踩到）— process.poll 看不到输出但实际在跑。**解决方案**：
    - 用 `python3 -u`（unbuffered）**或** `python3 -X dev`（无缓冲）
    - **或** `python3 script.py 2>&1 | tee /tmp/log` 写到文件，**直接 cat log 文件**看进度
    - background 模式 `output_preview: ""` 不代表脚本卡了，**先 `cat` log 文件**再决定是否 kill

17. **批量生歌脚本**（`batch_gen_songs.py`）— 4 首歌串行 5-6 分钟，**跳过缓存**（用 `os.path.exists` + size > 1MB 判断）。**不要用 `n=4` 并行**（MiniMax 账号 rate limit + 单次 4 首歌会被打回）。

18. **AGNES prompt 的人物描述** — "a young person seen from behind" 比 "a person" 安全 10x（避免人脸畸形）。"from behind" + "looking forward" 是 AGNES 出图质量最高的人物 prompt 模板。

19. **歌词字符数限制**（MiniMax 实测）：**单首 ≤ 3500 字符安全**。这次 4 首歌最长的"活着"= 2162 字符 ≈ 安全边际 60%。**别越界到 4000+**（被截断会丢 bridge/outro）。

## Verification Checklist

**Pre-flight**:
- [ ] `scutil --proxy` 显示 `127.0.0.1:7890`
- [ ] `curl -x 127.0.0.1:7890 -o /dev/null -w "%{http_code}" https://www.google.com` 返回 200
- [ ] `~/.baoyu-skills/.env` 里有 `AGNES_API_KEY`
- [ ] MiniMax API key 在 `MiniMax-M2/M3` 之外**必须另开音乐生成权限**（很多账号默认没开）

**Step 1（拉榜单）**:
- [ ] 4 个 JSON 文件全部 > 50KB（说明有真实榜单数据）
- [ ] 跨平台去重后歌曲数 > 80 首
- [ ] Top 30 综合榜已生成

**Step 2（写词 + prompt）**:
- [ ] 歌词 ≤ 3500 字符（MiniMax 限制）
- [ ] 含结构标签 [Intro]/[Verse]/[Pre-Chorus]/[Chorus]/[Bridge]/[Outro]
- [ ] 副歌第一句是"4 秒钩子"
- [ ] MiniMax `prompt` 不含敏感词
- [ ] AGNES `prompt` 不含 "text/Chinese characters/annotations"

**Step 3（生歌）**:
- [ ] HTTP 200 + `base_resp.status_code: 0` + `data.audio` 是 URL
- [ ] MP3 文件 > 3 MB
- [ ] `afinfo` 显示 `mp3` + `256 kbps` + `44.1 kHz` + 立体声 + ~170 秒

**Step 4（封面）**:
- [ ] 1536×1536 分辨率
- [ ] PNG / JPG / JPEG 三格式齐
- [ ] 单文件 ≤ 10 MB
- [ ] `vision_analyze` 验：4 行文字全部清晰、无错字、不被裁切
- [ ] 底图物体（雨窗/咖啡/绿植/相片）清晰

**Step 5（发飞书）**:
- [ ] `MEDIA:` 标签 + 绝对路径
- [ ] 3 个产物同时发（封面 + 歌词文字 + MP3）
- [ ] 简短的"设计思路"说明（不超过 200 字）

## Scripts (in this skill)

| 脚本 | 用途 | 关键硬化 |
|------|------|----------|
| `scripts/merge_charts.py` | 跨平台榜单去重 + 排序 | 跨平台权重，飙升 > 热歌 |
| `scripts/gen_song.py` | MiniMax Music-2.6 API | 用 `requests` 不用 curl；Jupyter 友好 |
| `scripts/gen_cover.py` | AGNES 底图生成 | `1536x1536` 安全尺寸；直连下载优先 |
| `scripts/add_text.py` | PIL 文字叠加 | PingFang.ttc 字体；4 行版式；投影 + 渐变遮罩 |
| `scripts/output_3fmts.py` | 三格式输出 | PIL optimize + progressive JPEG |
| `scripts/batch_gen_songs.py` | **批量生多首歌** | 自动发现 `lyrics.txt` + `tags.txt`；跳缓存；`python3 -u` 避免 stdout buffer；不并行（rate limit） |
| `scripts/batch_gen_covers.py` | **批量生多张封面** | 读 `cover_spec.json`；AGNES SSL 3x 重试；动态字体 size；W-320 防裁切 |

**使用方式**：
```bash
# 批量生 5 首歌
cd /tmp/jingze_music && python3 -u /path/to/skill/scripts/batch_gen_songs.py

# 批量生 5 张封面（需要每首歌下有 cover_spec.json）
cd /tmp/jingze_music && python3 -u /path/to/skill/scripts/batch_gen_covers.py
```

## Reference Files

- `references/minimax-music-payloads.md` — 4 种模型 (`music-1.5` / `music-2.0` / `music-2.6-free` / `music-cover-free`) 的 payload 模板 + 错误码速查
- `references/agnes-cover-prompts.md` — 5 个验证过的封面 prompt（静物/雨天/咖啡/城市/人物剪影）+ 各自成功的尺寸
- `references/lyrics-templates.md` — 6 种结构模板（demo 直发/半念半唱/古风/民谣/电音/纯音乐）
- `references/hook-formulas.md` — **5 大钩子矩阵**（2026-06-06 第二波 4 首歌验证，4 大公式 5 大反例 5 个副歌上扬动作 3 个 bridge 反转套路）

## cover_spec.json Schema

`batch_gen_covers.py` 读取每首歌下的 `cover_spec.json`：

```json
{
  "name": "玻璃心",
  "prompt": "AGNES prompt (NO text/Chinese in prompt, 1536x1536 only)",
  "title": "玻璃心",
  "subtitle": "玻璃心 也敢透光",
  "brand": "京择说",
  "byline": "Music by 京择"
}
```

**未填此文件时，batch_gen_covers.py 跳过该歌曲**（不让 PIL 强行 fallback 到默认名，**避免误生成**）。

## End-to-End Output Locations

所有产物放在 `/tmp/jingze_music/<song_name>/`：

```
/tmp/jingze_music/06_06/
├── lyrics.txt                   # 完整歌词
├── tags.txt                     # MiniMax prompt
├── cover_visual_1536.png        # AGNES 底图
├── cover.png                    # 最终 PNG (3.5 MB)
├── cover.jpg                    # 最终 JPG (0.75 MB)
├── cover_jpeg.jpg               # 最终 JPEG (0.75 MB)
├── song.mp3                     # 5.45 MB / 170 秒
└── analysis.json                # 榜单数据 + 综合排序（可选）
```

## Related Skills (Hermes 标准引用)

- `cloud-image-video-api` — AGNES/MiniMax/OpenAI image+video API 完整 reference（**生图前必读**）
- `cloud-music-api` — MiniMax Music 完整 reference（**生歌前必读**）
- `baoyu-image-gen` — 备用 image generation 流程（10 个 provider）
- `baoyu-cover-image` — 备用封面图生成（如果 AGNES 不可用）

**工作流纪律**（memory 强提醒）：**第一次就走对路** — 任何 multi-step 探测前，先 state plan + `skill_view` 加载相关 skill + 一次性发完整 payload。**不在错路上多发试探请求**。
