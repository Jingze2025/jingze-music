# MiniMax Music API Payload 模板

## 4 个模型（按 API 真实名）

| 模型名 | 类型 | 配额 | RPM |
|--------|------|------|-----|
| `music-1.5` | 文本生音乐 | 付费 | 较高 |
| `music-2.0` | 文本生音乐 | 付费 | 较高 |
| `music-2.6-free` | 文本生音乐（限免） | 所有 API Key | 较低 |
| `music-cover-free` | 翻唱（限免） | 所有 API Key | 较低 |

> **不要用 `music-2.6`** — 这是 UI 广告名，API 上不存在。

## Payload 模板（music-2.6-free）

```json
{
  "model": "music-2.6-free",
  "prompt": "indie pop, lo-fi, warm, male vocal, 75bpm, gentle acoustic guitar, light synth pad, soft chorus, urban vibe, conversational, late 20s, slight breathiness, hopeful, demo style",
  "lyrics": "[Intro]\n...\n\n[Chorus]\n...",
  "audio_setting": {"sample_rate": 44100, "bitrate": 256000, "format": "mp3"},
  "output_format": "url"
}
```

## Payload 模板（music-cover-free）

```json
{
  "model": "music-cover-free",
  "prompt": "moody, jazz-influenced, R&B vocal style, 70bpm, piano and brush drums",
  "lyrics": "[verse]\n...",
  "ref_song_url": "https://storage.googleapis.com/.../reference.mp3",
  "ref_song_type": "song",
  "audio_setting": {"sample_rate": 44100, "bitrate": 256000, "format": "mp3"},
  "output_format": "url"
}
```

## 错误码速查

| status_code | status_msg | 含义 | 修复 |
|-------------|------------|------|------|
| 0 | success | 成功 | - |
| 1004 | login fail | 鉴权失败 | 解码 JWT 看 exp（pitfall #26） |
| 2013 | invalid params, input sensitive: prompt | prompt 含敏感词 | 改用英文，避免"忧郁/内省" |
| 2013 | invalid params, biz error: amadeus play err, get vocal failed | 业务层无权限 | 检查账号是否开通 music 权限 |
| 2013 | invalid model | 模型名错 | 改为 music-2.6-free 等真实名 |

## `prompt` 安全词清单

**禁词**（会触发 input sensitive）：
- 忧郁、内省、渴望、悲伤、死亡、痛苦、绝望
- 暴力、血腥、色情、裸体
- 政治敏感、宗教极端、恐怖主义

**替代词**：
- 忧郁 → warm, gentle, soft
- 内省 → conversational, reflective
- 渴望 → hopeful, yearning
- 悲伤 → melancholy（**这个也可以**）, bittersweet

## 歌词结构标签

| 标签 | 用途 |
|------|------|
| [Intro] | 前奏 / 半念白 |
| [Verse] | 主歌（叙述） |
| [Pre-Chorus] | 预副歌（情绪堆积） |
| [Chorus] | 副歌（钩子爆发） |
| [Post-Chorus] | 副歌后（过渡） |
| [Bridge] | 桥段（转折） |
| [Outro] | 结尾（半念白） |
| [Inst] | 纯器乐 |
| [Solo] | 独奏 |
| [Hook] | 钩子重复 |
| [Interlude] | 间奏 |
| [Break] | 停顿 |
| [Build Up] | 渐强 |
| [Transition] | 转场 |

> 注意大小写：标签用 `[Verse]` 而不是 `[verse]`，MIDI 兼容性更好。

## `is_instrumental: true` 模式（纯音乐）

```json
{
  "model": "music-2.6-free",
  "prompt": "ambient, cinematic, strings, slow build-up, emotional, no vocals, 90bpm",
  "is_instrumental": true,
  "lyrics_optimizer": false,
  "audio_setting": {"sample_rate": 44100, "bitrate": 256000, "format": "mp3"},
  "output_format": "url"
}
```

- `lyrics` 字段可省略
- `lyrics_optimizer: false` 避免模型自动加歌词
