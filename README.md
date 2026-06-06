# jingze-music-pipeline

> **京择式 1:1 爆款对标音乐生产流水线** — 5 步从榜单到 MP3 + 封面 + 歌词

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Shell: bash](https://img.shields.io/badge/shell-bash-green.svg)](https://www.gnu.org/software/bash/)

把"听榜 → 对标 → 写词 → 生歌 → 出封面"做成 5 步流水线，**3 个产物一次交付**：

1. **封面图**（PNG/JPG/JPEG，1536×1536，< 10MB）
2. **完整歌词**（含结构标签 [Intro][Verse][Pre-Chorus][Chorus][Bridge][Outro]）
3. **音乐 MP3**（256 kbps，~170 秒 ≈ 2'50"）

## 适用场景

- 公众号「京择说」/ 个人品牌 **京择 AGI** 调性内容生产
- 周报 / 趋势分析之后的延伸内容
- 个人音乐厂牌 / 音乐 IP 矩阵

## 5 步流程（合计 5-10 分钟）

```
[1] 拉榜单 (60s)   →  [2] 对标+写词+prompt (180s)  →  [3] 生歌 (90-180s)  →  [4] 封面图 (60s)  →  [5] 落地
```

详细说明见 [`SKILL.md`](SKILL.md)（中文，~12k 字符）。

## 快速上手

### 1. 准备环境

```bash
# 必需环境变量
export AGNES_API_KEY=<your_ag...>  # 图像生成 (https://apihub.agnes-ai.com)
export MINIMAX_API_KEY=<your_...>  # 音乐生成 (https://api.minimaxi.com)

# 可选
export HTTPS_PROXY="http://127.0.0.1:7890"  # macOS 本地代理
```

### 2. 一键跑全流程

```bash
git clone https://github.com/Jingze2025/jingze-music.git
cd jingze-music/scripts
./pipeline.sh 06_06   # song_name 自定
```

### 3. 手工分步

```bash
# Step 1: 拉榜单
./pipeline.sh 06_06   # 自动下载到 /tmp/jingze_music/06_06/data/

# Step 2: 看输出选 Top 1，写歌词
python3 merge_charts.py /tmp/jingze_music/06_06/data
# 编辑 /tmp/jingze_music/06_06/lyrics.txt + tags.txt

# Step 3: 生歌
python3 gen_song.py /tmp/jingze_music/06_06/lyrics.txt /tmp/jingze_music/06_06/song.mp3 \
    --tags-file /tmp/jingze_music/06_06/tags.txt

# Step 4: 封面图
python3 gen_cover.py /tmp/jingze_music/06_06/cover_visual.png
python3 add_text.py /tmp/jingze_music/06_06/cover_visual.png /tmp/jingze_music/06_06/cover

# Step 5: 落地
ls /tmp/jingze_music/06_06/cover_final.* /tmp/jingze_music/06_06/song.mp3
```

## 文件结构

```
jingze-music-pipeline/
├── SKILL.md                          # 主文档 (12k, 中文)
├── LICENSE                           # MIT
├── .gitignore                        # 排除 .env / *.key / __pycache__ 等
├── README.md                         # 本文件
├── references/
│   ├── minimax-music-payloads.md     # 4 种模型 payload + 错误码
│   ├── agnes-cover-prompts.md        # 5 个验证过的封面 prompt
│   └── lyrics-templates.md           # 6 种歌词结构模板
└── scripts/
    ├── pipeline.sh                   # 一键端到端跑
    ├── merge_charts.py               # 跨平台榜单去重
    ├── gen_song.py                   # MiniMax Music-2.6
    ├── gen_cover.py                  # AGNES 底图
    └── add_text.py                   # PIL 文字叠加
```

## API 来源

| 用途 | 服务 | 文档 |
|------|------|------|
| 歌曲生成 | MiniMax Music-2.6 | https://platform.minimaxi.com/docs/api-reference/music-generation |
| 封面图 | AGNES (apihub.agnes-ai.com) | OpenAI-compatible, `/v1/images/generations` |
| 榜单数据 | 网易云 / QQ 音乐公开 API | 见 [SKILL.md](SKILL.md) Step 1 |

## 关键设计原则

1. **真实数据，不编造** — 所有榜单数据从公开 API 抓取
2. **AGNES 渲染中文会崩** — 底图纯视觉 + PIL 后处理叠加真实文字
3. **Hermes sandbox 过滤 curl Authorization** — 全部用 `requests` 库
4. **敏感词触发 input sensitive** — MiniMax prompt 用英文
5. **一次走对路** — 第一次就 state plan + 加载 skill + 一次发完整 payload

## 输出指标

- **歌曲**：256 kbps / 44.1 kHz / 立体声 / ~170 秒 / ~5.4 MB
- **封面**：1536×1536 / PNG ~3.5 MB / JPG ~0.75 MB
- **歌词**：≤ 3500 字符（含 [Intro]/[Verse]/[Pre-Chorus]/[Chorus]/[Bridge]/[Outro] 标签）

## 已知限制

- **酷狗榜单**（HTML JS 渲染）— 本流程跳过
- **AGNES flash** — 不支持 1920×1920 / 2048×2048 等非 1024/1536 倍数
- **AGNES flash 文字** — 中文乱码 / 英文拼错，必须用 PIL 叠加
- **AGNES flash 全脸近景** — 脚/手方向易错
- **真实名人** — AGNES 训练过滤，需用参考图
- **账号权限** — MiniMax 音乐/AGNES 图像需要订阅套餐支持

## License

MIT © 2026 京择 (Jingze)
