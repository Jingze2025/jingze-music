"""
# jingze-music-pipeline / Step 4a
# AGNES flash 底图生成（纯视觉，不渲染文字）
#
# 用法:
#   export AGNES_API_KEY=<your_key>  python3 gen_cover.py <output_png> [size] [--prompt <file>]

环境变量:
  AGNES_API_KEY     AGNES API key (必需)
  AGNES_BASE_URL    可选, 默认 https://apihub.agnes-ai.com
  HTTPS_PROXY       可选代理, 默认 127.0.0.1:7890 (macOS 用户本地代理)
"""
import os
import sys
import argparse
import requests


# 默认封面 prompt：雨天玻璃窗 + 静物 + 35mm 胶片
# 关键纪律: 严禁 "text / writing / Chinese characters" 之类
DEFAULT_PROMPT = (
    "A cinematic still life photograph in dark blue tones. "
    "A rain-streaked windowpane in soft focus, with blurred warm city lights and silhouettes visible through the wet glass. "
    "On the wooden windowsill: a half-drunk cold coffee in a transparent glass, a stack of unopened postcards with one slightly tilted, "
    "and a small green plant (pothos) in a clay pot. "
    "Mood: melancholic but hopeful, urban solitude, late June, just past sunset, no people visible. "
    "Style: 35mm film grain, Fujifilm Classic Negative film simulation, shallow depth of field, moody, demoscopic indie aesthetic, "
    "no text no writing no letters no words no Chinese characters no calligraphy no annotations, "
    "no logos no watermarks no UI"
)


def get_key() -> str:
    """从 AGNES_API_KEY 环境变量读 key"""
    key = os.environ.get("AGNES_API_KEY")
    if not key:
        raise RuntimeError(
            "AGNES_API_KEY not set. Export it first, e.g.\n"
            "  export AGNES_API_KEY=<your_key>\n"
            "Then re-run."
        )
    return key.strip()


def get_proxy() -> str:
    """HTTPS 代理，macOS 默认 7890"""
    return os.environ.get("HTTPS_PROXY", "http://127.0.0.1:7890")


def gen(
    prompt: str,
    size: str = "1536x1536",
    output_path: str = "./cover_visual.png",
    base_url: str = None,
) -> str:
    if not base_url:
        base_url = os.environ.get("AGNES_BASE_URL", "https://apihub.agnes-ai.com")

    key = get_key()
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt,
        "n": 1,
        "size": size,
    }
    r = requests.post(
        f"{base_url}/v1/images/generations",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    print(f"[gen_cover] HTTP={r.status_code}")
    if r.status_code != 200:
        print(f"[gen_cover] Body: {r.text[:500]}")
        r.raise_for_status()
    data = r.json()
    url = data["data"][0]["url"]
    print(f"[gen_cover] URL: {url}")

    # 下载: 先直连, 失败走代理
    for proxy in [None, get_proxy()]:
        try:
            kwargs = {"timeout": 30}
            if proxy:
                kwargs["proxies"] = {"https": proxy, "http": proxy}
            resp = requests.get(url, **kwargs)
            if resp.status_code == 200 and len(resp.content) > 1000:
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                print(f"[gen_cover] Saved: {output_path} ({len(resp.content)} bytes) via {proxy or 'direct'}")
                return output_path
        except Exception as e:
            print(f"[gen_cover] Download via {proxy or 'direct'} failed: {e}")
    raise RuntimeError("Download failed")


def main():
    parser = argparse.ArgumentParser(description="AGNES image generator")
    parser.add_argument("output", default="./cover_visual.png", nargs="?")
    parser.add_argument("size", default="1536x1536", nargs="?")
    parser.add_argument("--prompt", help="Path to custom prompt .txt file (overrides DEFAULT_PROMPT)")
    args = parser.parse_args()

    prompt = DEFAULT_PROMPT
    if args.prompt:
        with open(args.prompt) as f:
            prompt = f.read().strip()
    print(f"[gen_cover] Prompt ({len(prompt)} chars): {prompt[:200]}...")
    print(f"[gen_cover] Size: {args.size}")
    gen(prompt, args.size, args.output)


if __name__ == "__main__":
    main()
