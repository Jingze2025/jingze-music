"""
jingze-music-pipeline / Step 3
MiniMax Music-2.6 歌曲生成（通用 CLI）

用法:
  export MINIMAX_API_KEY=sk-cp-...
  python3 gen_song.py <lyrics_file> [output_mp3] [--tags-file <tags.txt>]

环境变量:
  MINIMAX_API_KEY  MiniMax API key (必需)
  MINIMAX_BASE_URL 可选, 默认 https://api.minimaxi.com
"""
import os
import sys
import json
import time
import argparse
import requests


def get_key() -> str:
    """从 MINIMAX_API_KEY 环境变量读 key。绝不写死路径。"""
    key = os.environ.get("MINIMAX_API_KEY")
    if not key:
        raise RuntimeError(
            "MINIMAX_API_KEY not set. Export it first, e.g.\n"
            "  export MINIMAX_API_KEY=<your_key>\n"
            "Then re-run."
        )
    return key.strip()


def default_tags() -> str:
    """默认 prompt（中文 indie demo 直发风格）"""
    return (
        "indie pop, lo-fi, warm, male vocal, 75bpm, "
        "gentle acoustic guitar, light synth pad, soft chorus, "
        "urban vibe, conversational, late 20s, slight breathiness, "
        "hopeful, demo style"
    )


def generate(
    lyrics: str,
    output_path: str,
    tags: str = None,
    base_url: str = None,
) -> dict:
    if not base_url:
        base_url = os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com")

    key = get_key()
    payload = {
        "model": "music-2.6-free",
        "prompt": tags or default_tags(),
        "lyrics": lyrics,
        "audio_setting": {"sample_rate": 44100, "bitrate": 256000, "format": "mp3"},
        "output_format": "url",
    }
    t0 = time.time()
    r = requests.post(
        f"{base_url}/v1/music_generation",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        json=payload,
        timeout=300,
    )
    print(f"[gen_song] HTTP={r.status_code}, elapsed={time.time()-t0:.1f}s")
    result = r.json()
    if r.status_code != 200 or result.get("base_resp", {}).get("status_code", 0) != 0:
        print(f"[gen_song] FAILED: {json.dumps(result, ensure_ascii=False)[:500]}")
        return result

    audio_url = result["data"]["audio"]
    extra = result.get("extra_info", {})
    print(f"[gen_song] URL: {audio_url[:120]}...")
    print(f"[gen_song] Meta: {json.dumps(extra, ensure_ascii=False)}")

    # 下载
    audio = requests.get(audio_url, timeout=180)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio.content)
    print(f"[gen_song] Saved: {output_path} ({len(audio.content)} bytes)")
    return result


def main():
    parser = argparse.ArgumentParser(description="MiniMax Music-2.6 song generator")
    parser.add_argument("lyrics_file", help="Path to lyrics .txt file")
    parser.add_argument("output", nargs="?", default="./song.mp3", help="Output MP3 path")
    parser.add_argument("--tags-file", help="Path to MiniMax prompt (tags) .txt file")
    args = parser.parse_args()

    with open(args.lyrics_file) as f:
        lyrics = f.read()
    tags = None
    if args.tags_file:
        with open(args.tags_file) as f:
            tags = f.read().strip()
    generate(lyrics, args.output, tags=tags)


if __name__ == "__main__":
    main()
