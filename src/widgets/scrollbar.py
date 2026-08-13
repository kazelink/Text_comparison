import tkinter as tk

from drawing import draw_round_rect
from theme import (F, SB_ARROW, SB_ARROW_HOV, SB_THIN, SB_THUMB,
                   SB_THUMB_DRAG, SB_THUMB_HOV, SB_TRACK, SURFACE)


class FluentScrollbar(tk.Canvas):
    GUTTER, W_THIN, W_THUMB, W_TRACK = 14, 3, 6, 12
    ARROW_H, MIN_THUMB = 14, 24
    CH_UP, CH_DOWN = "\ue96d", "\ue96e"

    def __init__(self, master, command=None, bg=SURFACE):
        super().__init__(master, width=self.GUTTER, highlightthickness=0,
                         bd=0, bg=bg, takefocus=0)
        self._command = command
        self._bg = bg
        self._first, self._last = 0.0, 1.0
        self._expanded = self._thumb_hot = False
        self._drag_off = self._hot_zone = self._anim = self._collapse = None
        self._w_cur = float(self.W_THIN)

        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Enter>", lambda e: self._hot(True))
        self.bind("<Leave>", self._on_leave)
        self.bind("<Motion>", self._on_motion)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<MouseWheel>", self._on_wheel)
        self.bind("<Destroy>", lambda e: self._cancel_jobs())

    def attach(self, text):
        text.bind("<Enter>", lambda e: self._hot(True), add="+")
        text.bind("<Leave>", lambda e: self._hot(False), add="+")

    def set(self, first, last):
        self._first, self._last = float(first), float(last)
        self._redraw()

    @property
    def _scrollable(self):
        return self._first > 0.0 or self._last < 1.0

    def _cancel_jobs(self):
        for job in (self._anim, self._collapse):
            if job:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
        self._anim = self._collapse = None

    def _hot(self, on):
        if self._collapse:
            self.after_cancel(self._collapse)
            self._collapse = None
        if on:
            self._set_expanded(True)
        elif self._drag_off is None:
            self._collapse = self.after(350, lambda: self._set_expanded(False))

    def _on_leave(self, _e):
        self._hot_zone = None
        self._thumb_hot = False
        self._hot(False)

    def _set_expanded(self, on):
        if on == self._expanded:
            return
        self._expanded = on
        if self._anim:
            self.after_cancel(self._anim)
        self._tick()

    def _tick(self):
        if not self.winfo_exists():
            return
        target = float(self.W_THUMB if self._expanded else self.W_THIN)
        if abs(self._w_cur - target) < 0.4:
            self._w_cur, self._anim = target, None
        else:
            self._w_cur += (target - self._w_cur) * 0.45
            self._anim = self.after(16, self._tick)
        self._redraw()

    def _metrics(self):
        h = self.winfo_height()
        top, bot = (self.ARROW_H, self.ARROW_H) if self._expanded else (2, 2)
        track = max(1, h - top - bot)
        span = max(0.0, min(1.0, self._last - self._first))
        thumb = min(track, max(self.MIN_THUMB, span * track))
        return top, track, thumb, track - thumb, span

    def _thumb_geom(self):
        top, _track, thumb, room, span = self._metrics()
        denom = 1.0 - span
        ratio = (self._first / denom) if denom > 1e-9 else 0.0
        y0 = top + max(0.0, min(1.0, ratio)) * room
        return y0, y0 + thumb

    def _redraw(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1:
            return
        self.delete("all")
        if not self._scrollable:
            return

        if self._expanded:
            draw_round_rect(self, w - self.W_TRACK, 0, w, h, 0,
                            SB_TRACK, self._bg)
            self._arrow(w, 0, self.ARROW_H, self.CH_UP, "up")
            self._arrow(w, h - self.ARROW_H, self.ARROW_H, self.CH_DOWN, "down")

        tw = max(2, int(round(self._w_cur)))
        y0, y1 = self._thumb_geom()
        if self._drag_off is not None:
            color = SB_THUMB_DRAG
        elif self._thumb_hot:
            color = SB_THUMB_HOV
        elif self._expanded:
            color = SB_THUMB
        else:
            color = SB_THIN
        x0 = (w - (self.W_TRACK + tw) // 2) if self._expanded else (w - tw - 2)
        under = SB_TRACK if self._expanded else self._bg
        draw_round_rect(self, x0, int(y0), x0 + tw, int(y1), tw // 2, color, under)

    def _arrow(self, w, y, size, glyph, zone):
        if self._hot_zone == zone:
            draw_round_rect(self, w - self.W_TRACK, y, w, y + size, 3,
                            SB_ARROW_HOV, SB_TRACK)
        cx, cy = w - self.W_TRACK / 2, y + size / 2
        if F.get("icon"):
            self.create_text(cx, cy, text=glyph, font=F["icon"], fill=SB_ARROW)
        else:
            d = -3 if zone == "up" else 3
            self.create_line(cx - 3, cy - d / 2, cx, cy + d / 2,
                             cx + 3, cy - d / 2, fill=SB_ARROW, width=1)

    def _zone(self, y):
        h = self.winfo_height()
        if self._expanded:
            if y < self.ARROW_H:
                return "up"
            if y > h - self.ARROW_H:
                return "down"
        return None

    def _on_motion(self, e):
        if not self._scrollable:
            return
        zone = self._zone(e.y)
        y0, y1 = self._thumb_geom()
        hot = zone is None and y0 <= e.y <= y1
        if zone != self._hot_zone or hot != self._thumb_hot:
            self._hot_zone, self._thumb_hot = zone, hot
            self._redraw()

    def _on_press(self, e):
        if not self._scrollable or not self._command:
            return
        zone = self._zone(e.y)
        if zone in ("up", "down"):
            self._command("scroll", -1 if zone == "up" else 1, "units")
            return
        y0, y1 = self._thumb_geom()
        if y0 <= e.y <= y1:
            self._drag_off = e.y - y0
            self._redraw()
        else:
            self._command("scroll", 1 if e.y > y1 else -1, "pages")

    def _on_drag(self, e):
        if self._drag_off is None or not self._command:
            return
        top, _track, _thumb, room, span = self._metrics()
        if room <= 0:
            return
        frac = (e.y - self._drag_off - top) / room * (1.0 - span)
        self._command("moveto", max(0.0, min(1.0 - span, frac)))

    def _on_release(self, _e):
        if self._drag_off is not None:
            self._drag_off = None
            self._redraw()

    def _on_wheel(self, e):
        if self._command:
            self._command("scroll", -1 if e.delta > 0 else 1, "units")
        return "break"
