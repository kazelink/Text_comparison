import tkinter as tk

from drawing import draw_round_rect
from theme import BG, CARD_INSET, CARD_RADIUS, SURFACE


class Card(tk.Canvas):
    def __init__(self, master, bg=BG, surface=SURFACE, radius=CARD_RADIUS,
                 width=320, height=200):
        super().__init__(master, highlightthickness=0, bd=0, bg=bg,
                         width=width, height=height)
        self._surface, self._bg, self._r = surface, bg, radius
        self.body = tk.Frame(self, bg=surface)
        self.body.place(x=CARD_INSET, y=CARD_INSET, relwidth=1.0, relheight=1.0,
                        width=-2 * CARD_INSET, height=-2 * CARD_INSET)
        self.bind("<Configure>", lambda e: self._redraw())

    def _redraw(self):
        w, h = self.winfo_width(), self.winfo_height()
        if w <= 4 or h <= 4:
            return
        self.delete("all")
        draw_round_rect(self, 0, 0, w, h, self._r, self._surface, self._bg)
