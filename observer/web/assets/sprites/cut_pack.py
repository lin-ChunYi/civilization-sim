"""Cut ART-PACK-001 white-bg JPGs into aligned transparent PNGs.

Source dir is read-only. Walk frames are distinct poses, not a verified loop.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

SRC = Path("/Users/ecool/Desktop/civilization/art-assets/grok-imagine-20260912")
DST = Path(__file__).resolve().parent
REPORT = []


def is_paper(r, g, b, a=255):
    if a == 0:
        return True
    if abs(r - g) > 18 or abs(g - b) > 18:
        return False
    return min(r, g, b) >= 232


def knockout(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    seen = bytearray(w * h)
    q = deque()

    def push(x, y):
        if 0 <= x < w and 0 <= y < h and not seen[y * w + x]:
            seen[y * w + x] = 1
            q.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    while q:
        x, y = q.popleft()
        r, g, b, a = px[x, y]
        if not is_paper(r, g, b, a):
            continue
        m = min(r, g, b)
        if m >= 248:
            px[x, y] = (r, g, b, 0)
        elif m >= 232:
            px[x, y] = (r, g, b, int(255 * (248 - m) / 16))
        else:
            continue
        push(x + 1, y)
        push(x - 1, y)
        push(x, y + 1)
        push(x, y - 1)

    # fringe: remaining near-white next to empty becomes transparent
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0 or not is_paper(r, g, b, a):
                continue
            edge = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][3] == 0:
                    edge = True
                    break
            if edge:
                px[x, y] = (r, g, b, 0)

    # drop tiny leftover specks
    visited = bytearray(w * h)
    for y in range(h):
        row = y * w
        for x in range(w):
            i = row + x
            if visited[i] or px[x, y][3] == 0:
                continue
            stack = [(x, y)]
            visited[i] = 1
            blob = [(x, y)]
            while stack:
                sx, sy = stack.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = sx + dx, sy + dy
                    if nx < 0 or ny < 0 or nx >= w or ny >= h:
                        continue
                    ni = ny * w + nx
                    if visited[ni] or px[nx, ny][3] == 0:
                        continue
                    visited[ni] = 1
                    stack.append((nx, ny))
                    blob.append((nx, ny))
            if len(blob) <= 28:
                for bx, by in blob:
                    px[bx, by] = (0, 0, 0, 0)
    return im


def tight(im: Image.Image, pad=4) -> Image.Image:
    alpha = im.split()[-1]
    box = alpha.getbbox()
    if not box:
        return im
    l, t, r, b = box
    l = max(0, l - pad)
    t = max(0, t - pad)
    r = min(im.width, r + pad)
    b = min(im.height, b + pad)
    return im.crop((l, t, r, b))


def split_grid(im: Image.Image, cols: int, rows: int, margin=0.07):
    w, h = im.size
    cw, ch = w / cols, h / rows
    out = []
    for r in range(rows):
        for c in range(cols):
            box = (
                int(c * cw + cw * margin),
                int(r * ch + ch * margin),
                int((c + 1) * cw - cw * margin),
                int((r + 1) * ch - ch * margin),
            )
            cell = knockout(im.crop(box))
            out.append(tight(cell))
    return out


def crop_frac(im: Image.Image, l, t, r, b):
    w, h = im.size
    cell = knockout(im.crop((int(l * w), int(t * h), int(r * w), int(b * h))))
    return tight(cell)


def feet_canvas(im: Image.Image, tw: int, th: int) -> Image.Image:
    im = tight(im, 2)
    scale = min((tw - 8) / max(1, im.width), (th - 10) / max(1, im.height))
    nw = max(1, int(im.width * scale))
    nh = max(1, int(im.height * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    x = (tw - nw) // 2
    y = th - nh - 4
    canvas.paste(im, (x, y), im)
    return canvas


def center_canvas(im: Image.Image, tw: int, th: int) -> Image.Image:
    im = tight(im, 2)
    scale = min((tw - 6) / max(1, im.width), (th - 6) / max(1, im.height))
    nw = max(1, int(im.width * scale))
    nh = max(1, int(im.height * scale))
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    canvas.paste(im, ((tw - nw) // 2, (th - nh) // 2), im)
    return canvas


def save(im: Image.Image, name: str, note=""):
    path = DST / name
    im.save(path, "PNG", optimize=True)
    REPORT.append({"file": name, "w": im.width, "h": im.height, "bytes": path.stat().st_size, "note": note})
    print("  wrote", name, im.size, path.stat().st_size)


def open_src(rel: str) -> Image.Image:
    return Image.open(SRC / rel).convert("RGB")


def halo_score(im: Image.Image) -> float:
    px = im.load()
    w, h = im.size
    n = 0
    bad = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 16 or a > 240:
                continue
            n += 1
            if min(r, g, b) >= 236 and abs(r - g) < 12:
                bad += 1
    return 0 if n == 0 else bad / n


def main():
    DST.mkdir(parents=True, exist_ok=True)
    chars = split_grid(open_src("01-characters/variant-01.jpg"), 3, 2, 0.06)
    names = ["char-staff", "char-scout", "char-gather", "char-stocky", "char-cloak", "char-elder"]
    for n, im in zip(names, chars):
        save(feet_canvas(im, 128, 176), n + ".png", "idle group representative; not an individual biography")

    walks = split_grid(open_src("02-walk-scout/variant-01.jpg"), 4, 2, 0.05)
    save(feet_canvas(walks[0], 128, 176), "walk-a.png", "approximate walk pose A; not a verified cycle")
    save(feet_canvas(walks[4], 128, 176), "walk-b.png", "approximate walk pose B; not a verified cycle")

    hexes = split_grid(open_src("05-resource-hexes/variant-01.jpg"), 3, 3, 0.04)
    save(center_canvas(hexes[1], 128, 112), "hex-res-low.png", "decorative resource look; value still from ledger")
    save(center_canvas(hexes[4], 128, 112), "hex-res-mid.png", "decorative resource look; value still from ledger")
    save(center_canvas(hexes[7], 128, 112), "hex-res-high.png", "decorative resource look; value still from ledger")

    blocked = split_grid(open_src("06-blocked-memory-hexes/variant-01.jpg"), 3, 3, 0.04)
    save(center_canvas(blocked[0], 128, 112), "hex-block.png", "impassable cell look; not a mountain")
    save(center_canvas(blocked[1], 128, 112), "hex-unknown.png", "memory unknown; not a new biome")
    save(center_canvas(blocked[4], 128, 112), "hex-mem.png", "remembered cell look")

    ports = split_grid(open_src("12-portraits/variant-01.jpg"), 3, 2, 0.05)
    pnames = ["port-staff", "port-scout", "port-gather", "port-stocky", "port-cloak", "port-elder"]
    for n, im in zip(pnames, ports):
        save(center_canvas(im, 160, 160), n + ".png", "group dossier portrait; not a personal history")

    emblems = split_grid(open_src("11-event-emblems/variant-01.jpg"), 4, 3, 0.05)
    save(center_canvas(emblems[0], 96, 96), "emblem-migrate.png", "migrate mark")
    save(center_canvas(emblems[4], 96, 96), "emblem-aid.png", "aid mark")
    save(center_canvas(emblems[3], 96, 96), "emblem-share.png", "share mark")
    save(center_canvas(emblems[1], 96, 96), "emblem-split.png", "split mark; still no map locate")
    save(center_canvas(emblems[5], 96, 96), "emblem-repay.png", "repay mark")

    fx = split_grid(open_src("14-selection-effects/variant-01.jpg"), 4, 3, 0.06)
    save(center_canvas(fx[0], 128, 80), "sel-ring.png", "selection ring")
    save(center_canvas(fx[8], 64, 64), "fx-spark.png", "event spark")
    save(center_canvas(fx[3], 96, 96), "sel-corners.png", "selection corners")

    aid = split_grid(open_src("04-aid-interactions/variant-01.jpg"), 4, 2, 0.04)
    save(feet_canvas(aid[2], 200, 176), "pair-aid.png", "aid/repay pose pair; event still uses e.cell")

    talk = split_grid(open_src("16-social-actions/variant-01.jpg"), 4, 2, 0.04)
    save(feet_canvas(talk[2], 200, 176), "pair-share.png", "share pose pair; event still uses e.cell")

    states = split_grid(open_src("15-character-states/variant-01.jpg"), 4, 2, 0.05)
    save(feet_canvas(states[0], 128, 176), "state-idle.png", "gatherer idle pose; not a mood record")
    save(feet_canvas(states[1], 128, 176), "state-wave.png", "gatherer wave pose; select overlay only")
    save(feet_canvas(states[4], 128, 176), "state-give.png", "gatherer give pose; event still uses e.cell")

    dirs_ = split_grid(open_src("03-directions-idle/variant-01.jpg"), 4, 2, 0.05)
    save(feet_canvas(dirs_[2], 128, 176), "face-east.png", "hooded facing east; walk facing helper, not a new band")
    save(feet_canvas(dirs_[6], 128, 176), "face-west.png", "hooded facing west; walk facing helper, not a new band")

    props = split_grid(open_src("08-camp-props/variant-01.jpg"), 4, 3, 0.06)
    save(center_canvas(props[0], 96, 72), "prop-bedroll.png", "decorative camp prop; not a city or building")
    save(center_canvas(props[2], 96, 96), "prop-pack.png", "decorative camp prop; not a city or building")

    icos = split_grid(open_src("09-ui-controls/variant-01.jpg"), 4, 4, 0.08)
    inames = [
        "ico-play", "ico-pause", "ico-next", "ico-prev",
        "ico-home", "ico-zoomin", "ico-zoomout", "ico-compass",
        "ico-eye", "ico-person", "ico-link", "ico-book",
        "ico-mark", "ico-back", "ico-sound", "ico-mute",
    ]
    for n, im in zip(inames, icos):
        save(center_canvas(im, 64, 64), n + ".png", "UI control; keep accessible name")

    panels = open_src("10-ui-panels/variant-01.jpg")
    save(center_canvas(crop_frac(panels, 0.02, 0.02, 0.48, 0.20), 512, 96), "panel-banner.png", "HUD/menu panel; not a map tile")
    save(center_canvas(crop_frac(panels, 0.16, 0.22, 0.42, 0.58), 256, 256), "panel-card.png", "sel-sheet panel; must not crowd the map")
    save(center_canvas(crop_frac(panels, 0.04, 0.60, 0.22, 0.70), 160, 48), "panel-pill.png", "chip/pill; keep text labels")

    bg = open_src("13-world-background/variant-01.jpg")
    bg = bg.resize((1280, 720), Image.Resampling.LANCZOS)
    bg.save(DST / "menu-bg.jpg", "JPEG", quality=78, optimize=True)
    REPORT.append({"file": "menu-bg.jpg", "w": 1280, "h": 720, "note": "menu/hud illustration only; not the replay map"})
    print("  wrote menu-bg.jpg")

    preview = Image.new("RGBA", (920, 720), (18, 14, 10, 255))
    draw = ImageDraw.Draw(preview)
    draw.text((12, 8), "ART-PACK-001 processed sprites (dark ground, not map)", fill=(243, 222, 170, 255))
    samples = [
        "char-staff.png", "char-scout.png", "char-gather.png", "char-stocky.png",
        "char-cloak.png", "char-elder.png", "walk-a.png", "walk-b.png",
        "hex-res-low.png", "hex-res-mid.png", "hex-res-high.png", "hex-block.png",
        "port-staff.png", "pair-aid.png", "pair-share.png", "sel-ring.png",
        "emblem-aid.png", "emblem-migrate.png", "ico-play.png", "prop-pack.png",
    ]
    for i, name in enumerate(samples):
        p = DST / name
        if not p.exists():
            continue
        im = Image.open(p).convert("RGBA")
        im.thumbnail((128, 128), Image.Resampling.LANCZOS)
        x = 16 + (i % 8) * 112
        y = 36 + (i // 8) * 140
        preview.paste(im, (x, y), im)
    preview.convert("RGB").save(DST / "_preview.jpg", "JPEG", quality=82)
    print("  wrote _preview.jpg")

    (DST / "PACK.json").write_text(json.dumps({
        "source": str(SRC),
        "style": "variant-01 across 01-16",
        "walk": "two approximate poses, not a verified loop",
        "files": REPORT,
        "halo": {item["file"]: round(halo_score(Image.open(DST / item["file"])), 4)
                 for item in REPORT if item["file"].endswith(".png")},
    }, indent=2), encoding="utf-8")
    print("done", len(REPORT), "files")


if __name__ == "__main__":
    main()
