#!/bin/bash
# jingze-music-pipeline / 端到端一键跑
#
# 用法: ./pipeline.sh <song_name> [working_dir]
#   song_name:   例如 "06_06"
#   working_dir: 默认 /tmp/jingze_music/<song_name>
#
# 前置环境变量（请在 shell 中 export）:
#   AGNES_API_KEY    AGNES 图像生成 key
#   MINIMAX_API_KEY  MiniMax 音乐生成 key
#
# 可选:
#   HTTPS_PROXY      默认 http://127.0.0.1:7890 (macOS 本地代理)

set -e

SONG_NAME="${1:-demo_song}"
WORK_DIR="${2:-/tmp/jingze_music/$SONG_NAME}"
PROXY="${HTTPS_PROXY:-http://127.0.0.1:7890}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

mkdir -p "$WORK_DIR/data"
echo "📁 Work dir: $WORK_DIR"

# 前置检查
if [ -z "$AGNES_API_KEY" ]; then
    echo "❌ AGNES_API_KEY 未设置. 请先 export AGNES_API_KEY=<your_key> 再跑" 1>&2
    exit 1
fi
if [ -z "$MINIMAX_API_KEY" ]; then
    echo "❌ MINIMAX_API_KEY 未设置. 请先 export MINIMAX_API_KEY=<your_key> 再跑" 1>&2
    exit 1
fi

# === Step 1: 拉榜单 (60s) ===
echo ""
echo "===== Step 1: 拉榜单 ====="
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

curl -s -x "$PROXY" -L -A "$UA" \
  -H "Referer: https://music.163.com/" \
  "https://music.163.com/api/playlist/detail?id=19723756" \
  -o "$WORK_DIR/data/netease_rising.json"

curl -s -x "$PROXY" -L -A "$UA" \
  -H "Referer: https://music.163.com/" \
  "https://music.163.com/api/playlist/detail?id=3778678" \
  -o "$WORK_DIR/data/netease_hot.json"

curl -s -x "$PROXY" -L -A "$UA" \
  "https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg?topid=27&format=json" \
  -o "$WORK_DIR/data/qq_rising.json"

curl -s -x "$PROXY" -L -A "$UA" \
  "https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg?topid=4&format=json" \
  -o "$WORK_DIR/data/qq_hot.json"

ls -la "$WORK_DIR/data/"
echo ""
echo "✅ 4 个榜单已下载"

# 合并 + 排序
python3 "$SCRIPT_DIR/merge_charts.py" "$WORK_DIR/data"
echo ""
echo "✅ 跨平台 Top 30 已生成"

# === Step 2: 风格对标 + 写词 + prompt (手工/agent 配合) ===
echo ""
echo "===== Step 2: 风格对标 + 写词 ====="
echo "⚠️ 此步骤需要 agent / 用户根据 merge_charts.py 输出:"
echo "   1. 选 Top 1 拆爆款元素 (时间锚点 / demo 直发 / 钩子 / 情感锚点)"
echo "   2. 写歌词到 $WORK_DIR/lyrics.txt (≤3500 字符, 含 [Intro]/[Verse]/[Pre-Chorus]/[Chorus]/[Bridge]/[Outro])"
echo "   3. 写 MiniMax prompt 到 $WORK_DIR/tags.txt (英文, 避免敏感词)"

if [ ! -f "$WORK_DIR/lyrics.txt" ]; then
    echo "❌ 缺少 $WORK_DIR/lyrics.txt — 退出"
    exit 1
fi

# === Step 3: 生歌 (90-180s) ===
echo ""
echo "===== Step 3: MiniMax Music-2.6 生歌 ====="
if [ -f "$WORK_DIR/tags.txt" ]; then
    python3 "$SCRIPT_DIR/gen_song.py" "$WORK_DIR/lyrics.txt" \
        "$WORK_DIR/song.mp3" \
        --tags-file "$WORK_DIR/tags.txt" 2>&1 | tail -20
else
    python3 "$SCRIPT_DIR/gen_song.py" "$WORK_DIR/lyrics.txt" \
        "$WORK_DIR/song.mp3" 2>&1 | tail -20
fi

# === Step 4: AGNES 封面 (60s) ===
echo ""
echo "===== Step 4: AGNES 封面底图 + PIL 文字 ====="
python3 "$SCRIPT_DIR/gen_cover.py" "$WORK_DIR/cover_visual.png"
python3 "$SCRIPT_DIR/add_text.py" "$WORK_DIR/cover_visual.png" "$WORK_DIR/cover"

# 重命名为统一名称
[ -f "$WORK_DIR/cover.png" ] && mv "$WORK_DIR/cover.png" "$WORK_DIR/cover_final.png"
[ -f "$WORK_DIR/cover.jpg" ] && mv "$WORK_DIR/cover.jpg" "$WORK_DIR/cover_final.jpg"
[ -f "$WORK_DIR/cover_jpeg.jpg" ] && mv "$WORK_DIR/cover_jpeg.jpg" "$WORK_DIR/cover_final_jpeg.jpg"
ls -la "$WORK_DIR/cover_"* 2>/dev/null

# === Step 5: 落地发飞书 (agent 处理) ===
echo ""
echo "===== Step 5: 落地发飞书 ====="
echo "✅ 全部产物在 $WORK_DIR:"
ls -la "$WORK_DIR/" | grep -E "cover_|song.mp3|lyrics|tags"
echo ""
echo "Agent 现在用 send_message(target='feishu') 发:"
echo "  MEDIA:$WORK_DIR/cover_final.png"
echo "  MEDIA:$WORK_DIR/song.mp3"
echo "  + 完整歌词文本"
