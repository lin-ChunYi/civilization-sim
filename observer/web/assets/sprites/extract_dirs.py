"""Extract 03 eight facings and two extra walk poses. Source dir stays read-only."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cut_pack import feet_canvas, open_src, save, split_grid, REPORT


def main():
    dirs_ = split_grid(open_src("03-directions-idle/variant-01.jpg"), 4, 2, 0.05)
    names = ["face-s", "face-se", "face-e", "face-ne", "face-n", "face-nw", "face-w", "face-sw"]
    notes = "hooded 8-dir travel pose; not a new band identity"
    for n, im in zip(names, dirs_):
        save(feet_canvas(im, 128, 176), n + ".png", notes)

    walks = split_grid(open_src("02-walk-scout/variant-01.jpg"), 4, 2, 0.05)
    save(feet_canvas(walks[3], 128, 176), "walk-c.png", "approximate walk pose C; not a verified cycle")
    save(feet_canvas(walks[7], 128, 176), "walk-d.png", "approximate walk pose D; not a verified cycle")
    print("extra", len(REPORT), "files")


if __name__ == "__main__":
    main()
