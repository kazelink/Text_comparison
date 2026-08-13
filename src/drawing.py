import tkinter as tk

_CORNER_CACHE = {}
_SS = 4


def _rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def _corner_images(r, fill, bg, outline=None, ow=0):
    key = (r, fill, bg, outline, ow)
    if key in _CORNER_CACHE:
        return _CORNER_CACHE[key]

    bgc = _rgb(bg)
    fgc = _rgb(fill) if fill else bgc
    oc = _rgb(outline) if outline else fgc
    step = 1.0 / _SS
    grid = []

    for py in range(r):
        row = []
        for px in range(r):
            out = inside = 0
            for sy in range(_SS):
                dy = py + (sy + .5) * step - r
                for sx in range(_SS):
                    dx = px + (sx + .5) * step - r
                    d2 = dx * dx + dy * dy
                    if d2 <= r * r:
                        out += 1
                        if d2 <= (r - ow) ** 2:
                            inside += 1
            ao = out / (_SS * _SS)
            ai = inside / (_SS * _SS)
            am = ao - ai
            row.append("#%02x%02x%02x" % tuple(
                round(bgc[i] * (1 - ao) + oc[i] * am + fgc[i] * ai)
                for i in range(3)))
        grid.append(row)

    def image(rows):
        img = tk.PhotoImage(width=len(rows[0]), height=len(rows))
        img.put(" ".join("{" + " ".join(line) + "}" for line in rows))
        return img

    images = (image(grid),
              image([line[::-1] for line in grid]),
              image(grid[::-1]),
              image([line[::-1] for line in grid[::-1]]))
    _CORNER_CACHE[key] = images
    return images


def draw_round_rect(cv, x1, y1, x2, y2, r, fill, bg,
                    outline=None, ow=0, tags="shape"):
    x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
    if x2 <= x1 or y2 <= y1:
        return
    r = max(0, min(int(r), (x2 - x1) // 2, (y2 - y1) // 2))
    ow = 0 if not outline else (min(ow, r) if r else ow)

    def rect(a, b, c, d, color):
        if color and c > a and d > b:
            cv.create_rectangle(a, b, c, d, fill=color, outline="", tags=tags)

    b = 1 if r else 0
    if ow:
        parts = ((x1 + r - b, y1, x2 - r + b, y1 + ow, outline),
                 (x1 + r - b, y2 - ow, x2 - r + b, y2, outline),
                 (x1, y1 + r - b, x1 + ow, y2 - r + b, outline),
                 (x2 - ow, y1 + r - b, x2, y2 - r + b, outline),
                 (x1 + r - b, y1 + ow, x2 - r + b, y2 - ow, fill),
                 (x1 + ow, y1 + r - b, x1 + r, y2 - r + b, fill),
                 (x2 - r, y1 + r - b, x2 - ow, y2 - r + b, fill))
    else:
        parts = ((x1 + r - b, y1, x2 - r + b, y2, fill),
                 (x1, y1 + r - b, x1 + r, y2 - r + b, fill),
                 (x2 - r, y1 + r - b, x2, y2 - r + b, fill))
    for a, b0, c, d, color in parts:
        rect(a, b0, c, d, color)

    if r:
        anchors = ((x1, y1, "nw"), (x2, y1, "ne"),
                   (x1, y2, "sw"), (x2, y2, "se"))
        for (x, y, anchor), image in zip(anchors, _corner_images(r, fill, bg, outline, ow)):
            cv.create_image(x, y, image=image, anchor=anchor, tags=tags)
