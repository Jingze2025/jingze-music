"""
PIL 后处理 - 在 1536x1536 底图上叠加真实文字
- 字体大小按 1536/1024 = 1.5 倍放大
- 输出 PNG / JPG / JPEG 三种格式，全部 ≤10MB，分辨率 ≥1440
- 禁用 sips 拉伸（pitfall #20 + 用户偏好）
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def add_text_to_cover(
    bg_path: str,
    out_path_base: str,
    title: str = "06.06",
    subtitle: str = "六月初六  还在路上",
    brand: str = "京择说",
    byline: str = "Music by 京择",
):
    img = Image.open(bg_path).convert("RGBA")
    W, H = img.size
    print(f"Base size: {W}x{H}")
    assert W >= 1440 and H >= 1440, f"Resolution too low: {W}x{H} < 1440"

    # 1. 底部深色渐变遮罩
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    gradient_h = int(H * 0.45)
    for y in range(gradient_h):
        ratio = y / gradient_h
        alpha = int(180 * (ratio ** 1.5))
        draw_overlay.line([(0, H - gradient_h + y), (W, H - gradient_h + y)],
                          fill=(0, 0, 0, alpha), width=1)
    img = Image.alpha_composite(img, overlay)

    # 2. 字体（按 1536 比例放大约 1.5 倍）
    font_path = "/System/Library/Fonts/PingFang.ttc"
    scale = W / 1024.0  # 1.5 for 1536
    font_title = ImageFont.truetype(font_path, int(220 * scale))   # ~330
    font_sub = ImageFont.truetype(font_path, int(56 * scale))      # ~84
    font_brand = ImageFont.truetype(font_path, int(38 * scale))    # ~57
    font_byline = ImageFont.truetype(font_path, int(28 * scale))   # ~42

    title_color = (255, 245, 230, 245)
    sub_color = (255, 255, 255, 220)
    brand_color = (220, 220, 220, 200)

    # 3. 文字位置（底部 1/3，按 1536 比例）
    title_x = int(70 * scale)
    title_y = H - int(440 * scale)  # ~660 from bottom for 1536
    sub_x = title_x

    # 投影
    shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.text((title_x + 6, title_y + 8), title, font=font_title, fill=(0, 0, 0, 160))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=12))
    img = Image.alpha_composite(img, shadow_layer)

    # 4. 文字层
    text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    draw.text((title_x, title_y), title, font=font_title, fill=title_color)

    sub_y = title_y + int(210 * scale)
    draw.text((sub_x, sub_y), subtitle, font=font_sub, fill=sub_color)

    line_y = sub_y + int(90 * scale)
    draw.line([(sub_x, line_y), (sub_x + int(80 * scale), line_y)],
              fill=(255, 255, 255, 180), width=2)

    brand_y = line_y + int(18 * scale)
    draw.text((sub_x, brand_y), brand, font=font_brand, fill=brand_color)
    byline_y = brand_y + int(48 * scale)
    draw.text((sub_x, byline_y), byline, font=font_byline, fill=brand_color)

    img = Image.alpha_composite(img, text_layer)
    final = img.convert("RGB")

    # 5. 三种格式输出
    outputs = [
        (f"{out_path_base}.png", "PNG", {"optimize": True}),
        (f"{out_path_base}.jpg", "JPEG", {"quality": 95, "optimize": True, "progressive": True}),
        (f"{out_path_base}_jpeg.jpg", "JPEG", {"quality": 95, "optimize": True, "progressive": True}),
    ]
    # 清理同名旧文件
    for path, _, _ in outputs:
        if os.path.exists(path):
            os.remove(path)
    results = []
    for path, fmt, kwargs in outputs:
        final.save(path, fmt, **kwargs)
        size = os.path.getsize(path)
        size_mb = size / (1024 * 1024)
        with Image.open(path) as check:
            cw, ch = check.size
        ok_resolution = cw >= 1440 and ch >= 1440
        ok_size = size_mb <= 10
        flag = "✓" if (ok_resolution and ok_size) else "✗"
        print(f"{flag} {path}: {cw}x{ch}, {size_mb:.2f} MB")
        results.append((path, cw, ch, size, ok_resolution, ok_size))
    return results


if __name__ == "__main__":
    bg = "/tmp/minimax_music/cover_visual_1536.png"
    out_base = "/tmp/minimax_music/cover_06_06"
    add_text_to_cover(bg, out_base)
