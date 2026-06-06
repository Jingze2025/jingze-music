"""
jingze-music-pipeline / Step 1
跨平台榜单去重 + 排序 — 网易云 + QQ (Top 30 综合)
用法: python3 merge_charts.py <data_dir>
"""
import json
import os
import sys
from collections import defaultdict


def load_netease(path: str):
    """解析网易云 playlist detail JSON → [{name, artist, album, source}]"""
    with open(path) as f:
        data = json.load(f)
    if "result" not in data or "tracks" not in data["result"]:
        return []
    out = []
    for t in data["result"]["tracks"][:30]:
        out.append({
            "name": t.get("name", ""),
            "artist": "/".join([a["name"] for a in t.get("artists", [])]),
            "album": t.get("album", {}).get("name", ""),
            "source": "netease",
        })
    return out


def load_qq(path: str):
    """解析 QQ 音乐 top list JSON → [{name, artist, album, source}]"""
    with open(path) as f:
        data = json.load(f)
    if "songlist" not in data:
        return []
    out = []
    for s in data["songlist"][:30]:
        out.append({
            "name": s.get("data", {}).get("songname", s.get("songname", "")),
            "artist": "/".join(s.get("data", {}).get("singer", [{}])[i].get("name", "")
                              for i in range(len(s.get("data", {}).get("singer", [])))),
            "album": s.get("data", {}).get("albumname", ""),
            "source": "qq",
        })
    return out


def dedup_and_rank(netease_rising, netease_hot, qq_rising, qq_hot):
    """同名同歌手 = 同一首；翻唱/Remix 独立；飙升权重 > 热歌"""
    songs = defaultdict(lambda: {
        "name": "", "artist": "", "album": "",
        "sources": [], "positions": [], "is_rising": False,
    })
    for label, lst, is_rising in [
        ("网易云飙升", netease_rising, True),
        ("网易云热歌", netease_hot, False),
        ("QQ飙升", qq_rising, True),
        ("QQ热歌", qq_hot, False),
    ]:
        for i, s in enumerate(lst, 1):
            key = (s["name"], s["artist"])
            entry = songs[key]
            entry["name"] = s["name"]
            entry["artist"] = s["artist"]
            entry["album"] = s["album"]
            if label not in entry["sources"]:
                entry["sources"].append(label)
            entry["positions"].append((label, i))
            if is_rising:
                entry["is_rising"] = True
    # 综合分排序
    def score(s):
        total = 0
        for src, pos in s["positions"]:
            if "飙升" in src:
                total += 50 + (100 - pos * 2)
            else:
                total += 30 + (100 - pos)
        return -total
    ranked = sorted(songs.values(), key=score)
    return ranked


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 merge_charts.py <data_dir>")
        sys.exit(1)
    data_dir = sys.argv[1]
    netease_rising = load_netease(os.path.join(data_dir, "netease_rising.json"))
    netease_hot = load_netease(os.path.join(data_dir, "netease_hot.json"))
    qq_rising = load_qq(os.path.join(data_dir, "qq_rising.json"))
    qq_hot = load_qq(os.path.join(data_dir, "qq_hot.json"))

    print(f"Loaded: 网易云飙升={len(netease_rising)} 网易云热歌={len(netease_hot)} "
          f"QQ飙升={len(qq_rising)} QQ热歌={len(qq_hot)}")

    ranked = dedup_and_rank(netease_rising, netease_hot, qq_rising, qq_hot)
    print(f"\nTop 30 综合榜 (共 {len(ranked)} 首去重):")
    for i, s in enumerate(ranked[:30], 1):
        pos = " | ".join([f"{p[0]}#{p[1]}" for p in s["positions"]])
        flag = "🔥" if s["is_rising"] else "  "
        print(f"{i:2d}. {flag} {s['name']:20s} - {s['artist']:15s}  [{pos}]")

    out = os.path.join(data_dir, "sorted_songs.json")
    with open(out, "w") as f:
        json.dump(ranked, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
