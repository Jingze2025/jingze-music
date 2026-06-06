# AGNES 封面 Prompt 验证集（5 个 proven 模板）

> 关键纪律：**prompt 绝不含 "text/writing/Chinese characters/annotations"**，否则文字会崩成 gibberish（pitfall #21）。文字全部用 PIL 后处理。

## 模板 1: 雨天玻璃窗 + 静物（最稳定，6/6 成功）

**适用**：indie pop / 民谣 / 城市感 / 怀旧

```
A cinematic still life photograph in dark blue tones.
A rain-streaked windowpane in soft focus, with blurred warm city lights and silhouettes visible through the wet glass.
On the wooden windowsill: a half-drunk cold coffee in a transparent glass, a stack of unopened postcards with one slightly tilted, and a small green plant (pothos) in a clay pot.
Mood: melancholic but hopeful, urban solitude, late June, just past sunset, no people visible.
Style: 35mm film grain, Fujifilm Classic Negative film simulation, shallow depth of field, moody, demoscopic indie aesthetic,
no text no writing no letters no words no Chinese characters no calligraphy no annotations,
no logos no watermarks no UI
```

**尺寸**：1536×1536（1:1）
**实测**：1 次成功，物体全部清晰

---

## 模板 2: 海边公路 + 复古车（适合 indie rock / 公路歌曲）

```
A vintage photograph in faded warm tones.
A lone empty road along the Pacific coastline at golden hour, with a rusted 1970s station wagon parked on the shoulder.
Waves crashing in the distance, the sun melting into the horizon line.
Mood: nostalgic, dreamy, summer road trip, freedom, escape.
Style: kodak portra 400 film simulation, slight overexposure, dust and scratches, wide angle,
no text no writing no letters no words no Chinese characters no calligraphy no annotations,
no logos no watermarks no UI
```

**尺寸**：1536×1024（3:2 横版）或 1536×1536

---

## 模板 3: 老式录音棚 + 麦克风（适合原创音乐人形象）

```
A moody photograph of an old analog recording studio.
Vintage Neumann U47 tube microphone in foreground, reel-to-reel tape machine in background, warm wood paneling.
Soft warm tungsten light from a single lamp.
Mood: craftsmanship, authenticity, indie music production, late 1970s.
Style: Hasselblad medium format film, shallow depth of field, f/2.8, warm grain,
no text no writing no letters no words no Chinese characters no calligraphy no annotations,
no logos no watermarks no UI
```

---

## 模板 4: 雪地小木屋（适合 winter folk / 寒带歌曲）

```
A cozy photograph of a wooden cabin in a snowy forest at night.
Warm yellow light glowing from the windows, smoke rising from the chimney, fresh snow on the pine trees.
The Milky Way visible in the dark blue sky above.
Mood: warm cozy, retreat, winter storytelling, folk tale.
Style: long exposure, astrophotography, warm-cool color contrast, f/1.4,
no text no writing no letters no words no Chinese characters no calligraphy no annotations,
no logos no watermarks no UI
```

---

## 模板 5: 城市霓虹（适合 synthwave / city pop / K-Pop remix）

```
A cyberpunk photograph of a Hong Kong night street.
Neon signs in pink and cyan reflecting off wet pavement, a lone figure with their back to the camera.
Dense stacked apartment buildings with glowing windows in the background.
Mood: lonely, futuristic, nostalgic, neon-noir.
Style: cinematic Blade Runner aesthetic, anamorphic lens flare, rain-soaked surfaces,
no text no writing no letters no words no Chinese characters no calligraphy no annotations,
no logos no watermarks no UI
```

> ⚠️ 模板 5 含 "lone figure with their back" — AGNES flash 静态人像稳定，但**避免正脸/全脸**（避免 pitfall #22 脸部和脚部方向矛盾）。

---

## 通用禁忌

| 禁用 | 原因 |
|------|------|
| text / writing / letters / words | AGNES 渲染文字会崩 |
| Chinese characters / calligraphy / annotations | 同上 |
| 真实名人名字（张三/王菲等） | AGNES 训练过滤，不画 |
| 1920×1920 / 2048×2048 / 1280×720 | 非 1024/1536 倍数 → HTTP 500 |
| 多手指 / 多手 / 漂浮物体 | flash 空间一致性弱 |
| 全脸近景（脚部方向易错） | 远离参考 pitfall #22 |

## PIL 文字叠加规范（4 行版式）

```python
# 字体（macOS）
font_path = "/System/Library/Fonts/PingFang.ttc"

# 大小（按 1536 比例 1.5x）
font_title_size  = 330  # "06.06" 歌名
font_sub_size    = 84   # 副标题
font_brand_size  = 57   # 品牌
font_byline_size = 42   # byline

# 位置
title_x, title_y = 105, H - 660  # 偏左下
sub_x = title_x
sub_y = title_y + 315
line_y = sub_y + 135
brand_y = line_y + 27
byline_y = brand_y + 72

# 颜色
title_color  = (255, 245, 230, 245)  # 暖白
sub_color    = (255, 255, 255, 220)  # 白
brand_color  = (220, 220, 220, 200)  # 浅灰

# 投影（text_shadow 偏移 + 模糊）
shadow_offset = (6, 8)
shadow_blur = 12
```

## 三格式输出（PIL）

```python
final.save("cover.png", "PNG", optimize=True)        # ~3.5 MB
final.save("cover.jpg", "JPEG", quality=95, optimize=True, progressive=True)  # ~0.75 MB
final.save("cover_jpeg.jpg", "JPEG", quality=95, optimize=True, progressive=True)  # ~0.75 MB
```

**全部 ≤10 MB**。验证：`ls -la` + `python3 -c "from PIL import Image; print(Image.open(p).size)"`
