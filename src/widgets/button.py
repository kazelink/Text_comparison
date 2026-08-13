import tkinter as tk
from tkinter import font as tkfont

from drawing import draw_round_rect
from theme import (ACCENT, ACCENT_DIS, ACCENT_HOVER, ACCENT_PRESS,
                   BG, BTN_BG, BTN_BORDER, BTN_DIS_BG, BTN_DIS_BD,
                   BTN_H, BTN_HOVER, BTN_PRESS, BTN_RADIUS, F,
                   SUBTLE_HOVER, SUBTLE_PRESS, TEXT_DIS, TEXT_PRI, TEXT_SEC)


class FluentButton(tk.Canvas):
    def __init__(self, master, text="", command=None, variant="standard",
                 height=BTN_H, min_width=0, bg=BG):
        self._text = text
        self._command = command
        self._variant = variant
        self._font = F["ui"]
        self._state = tk.NORMAL
        self._hover = self._press = False

        pad = 14 if variant != "subtle" else 10
        width = max(min_width,
                    tkfont.Font(root=master, font=self._font).measure(text) + 2 * pad)
        super().__init__(master, width=width, height=height,
                         highlightthickness=0, bd=0, bg=bg, takefocus=1)

        self.bind("<Configure>", lambda e: self._redraw())
        self.bind("<Enter>", lambda e: self._set(hover=True))
        self.bind("<Leave>", lambda e: self._set(hover=False, press=False))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<space>", lambda e: self._invoke())
        self.bind("<Return>", lambda e: self._invoke())

    def _set(self, **kw):
        for key, value in kw.items():
            setattr(self, "_" + key, value)
        self._redraw()

    def _on_press(self, _e):
        if self._state == tk.DISABLED:
            return
        self.focus_set()
        self._set(press=True)

    def _on_release(self, _e):
        if self._state == tk.DISABLED or not self._press:
            return
        self._set(press=False)
        if self._hover:
            self._invoke()

    def _invoke(self):
        if self._state != tk.DISABLED and self._command:
            self._command()
        return "break"

    def configure(self, cnf=None, **kw):
        opts = dict(cnf or {})
        opts.update(kw)
        if "state" in opts:
            self._state = str(opts.pop("state"))
            if self._state == tk.DISABLED:
                self._hover = self._press = False
            self._redraw()
        return super().configure(opts) if opts else None

    config = configure

    def _colors(self):
        if self._state == tk.DISABLED:
            if self._variant == "accent":
                return ACCENT_DIS, None, 0, "#FFFFFF"
            if self._variant == "subtle":
                return None, None, 0, TEXT_DIS
            return BTN_DIS_BG, BTN_DIS_BD, 1, TEXT_DIS

        if self._variant == "accent":
            fill = ACCENT_PRESS if self._press else ACCENT_HOVER if self._hover else ACCENT
            return fill, None, 0, "#E8F0F8" if self._press else "#FFFFFF"

        if self._variant == "subtle":
            fill = SUBTLE_PRESS if self._press else SUBTLE_HOVER if self._hover else None
            return fill, None, 0, TEXT_SEC if self._press else ACCENT

        fill = BTN_PRESS if self._press else BTN_HOVER if self._hover else BTN_BG
        return fill, BTN_BORDER, 1, TEXT_SEC if self._press else TEXT_PRI

    def _redraw(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 1 or h <= 1:
            return
        self.delete("all")
        fill, outline, ow, fg = self._colors()
        bg = self["bg"]
        draw_round_rect(self, 0, 0, w, h, BTN_RADIUS,
                        fill or bg, bg, outline, ow)
        self.create_text(w / 2, h / 2, text=self._text, fill=fg, font=self._font)
