"""抗锯齿圆角绘制（4×4 超采样角贴图，纯标准库）。"""

import tkinter as tk

_CORNER_CACHE = {}
_SS = 4                     # 每像素超采样 4×4


def _rgb(c):
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


def _corner_images(r, fill, bg, outline=None, ow=0):
    """生成圆角四个角的抗锯齿贴图，返回 (nw, ne, sw, se)。

    Tk 的 Canvas 多边形不做抗锯齿，直接画圆角矩形会在弧线处留下明显毛边
    —— 深色按钮压在浅色底上时，那圈毛边看起来就像一道白边。这里按 4×4
    超采样算出每个角落像素的覆盖率，混色后写进 PhotoImage 再贴上去；
    直边部分仍用普通矩形（本来就不需要抗锯齿）。结果按参数缓存。
    """
    key = (r, fill, bg, outline, ow)
    hit = _CORNER_CACHE.get(key)
    if hit:
        return hit

    br, bgc, bb = _rgb(bg)
    fr, fgc, fb = _rgb(fill) if fill else (br, bgc, bb)
    orr, ogc, ob = _rgb(outline) if outline else (fr, fgc, fb)

    step = 1.0 / _SS
    grid = []
    for py in range(r):
        row = []
        for px in range(r):
            n_out = n_in = 0
            for sy in range(_SS):
                dy = py + (sy + .5) * step - r
                for sx in range(_SS):
                    dx = px + (sx + .5) * step - r
                    d2 = dx * dx + dy * dy
                    if d2 <= r * r:
                        n_out += 1
                        if d2 <= (r - ow) ** 2:
                            n_in += 1
            a_out = n_out / (_SS * _SS)
            a_in  = n_in / (_SS * _SS)
            a_mid = a_out - a_in
            row.append("#%02x%02x%02x" % (
                round(br * (1 - a_out) + orr * a_mid + fr * a_in),
                round(bgc * (1 - a_out) + ogc * a_mid + fgc * a_in),
                round(bb * (1 - a_out) + ob * a_mid + fb * a_in)))
        grid.append(row)

    def make(g):
        img = tk.PhotoImage(width=len(g[0]), height=len(g))
        img.put(" ".join("{" + " ".join(row) + "}" for row in g))
        return img

    imgs = (make(grid),
            make([row[::-1] for row in grid]),
            make(grid[::-1]),
            make([row[::-1] for row in grid[::-1]]))
    _CORNER_CACHE[key] = imgs
    return imgs


def draw_round_rect(cv, x1, y1, x2, y2, r, fill, bg,
                    outline=None, ow=0, tags="shape"):
    """在 Canvas 上画抗锯齿圆角矩形，占据像素 [x1,x2) × [y1,y2)。"""
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    if x2 <= x1 or y2 <= y1:
        return
    r = max(0, min(int(r), (x2 - x1) // 2, (y2 - y1) // 2))
    if not outline:
        ow = 0
    ow = min(ow, r) if r else ow

    def rect(a, b, c, d, col):
        if col and c > a and d > b:
            cv.create_rectangle(a, b, c, d, fill=col, outline="", tags=tags)

    # 直边先画，四角贴图后画盖在上面。Tk 对 create_rectangle 的边界像素
    # 归属有歧义，所以每条直边都朝圆角方向多铺 1px，无论差一格还是多一格
    # 都会被角落贴图正确覆盖，接缝处不会露出底色。
    b = 1 if r else 0
    if ow:
        rect(x1 + r - b, y1, x2 - r + b, y1 + ow, outline)      # 上边
        rect(x1 + r - b, y2 - ow, x2 - r + b, y2, outline)      # 下边
        rect(x1, y1 + r - b, x1 + ow, y2 - r + b, outline)      # 左边
        rect(x2 - ow, y1 + r - b, x2, y2 - r + b, outline)      # 右边
        rect(x1 + r - b, y1 + ow, x2 - r + b, y2 - ow, fill)    # 内部（中）
        rect(x1 + ow, y1 + r - b, x1 + r, y2 - r + b, fill)     # 内部（左）
        rect(x2 - r, y1 + r - b, x2 - ow, y2 - r + b, fill)     # 内部（右）
    else:
        rect(x1 + r - b, y1, x2 - r + b, y2, fill)
        rect(x1, y1 + r - b, x1 + r, y2 - r + b, fill)
        rect(x2 - r, y1 + r - b, x2, y2 - r + b, fill)

    if r:
        nw, ne, sw, se = _corner_images(r, fill, bg, outline, ow)
        cv.create_image(x1, y1, image=nw, anchor="nw", tags=tags)
        cv.create_image(x2, y1, image=ne, anchor="ne", tags=tags)
        cv.create_image(x1, y2, image=sw, anchor="sw", tags=tags)
        cv.create_image(x2, y2, image=se, anchor="se", tags=tags)
