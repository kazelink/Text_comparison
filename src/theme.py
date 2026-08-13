import tkinter.font as tkfont

BG, SURFACE = "#F3F3F3", "#FFFFFF"
TEXT_PRI, TEXT_SEC, TEXT_TER, TEXT_DIS = "#1B1B1B", "#5D5D5D", "#8A8A8A", "#A0A0A0"

ACCENT, ACCENT_HOVER, ACCENT_PRESS, ACCENT_DIS = "#0067C0", "#1975C5", "#3183CC", "#C9C9C9"

BTN_BG, BTN_HOVER, BTN_PRESS, BTN_BORDER = "#FBFBFB", "#F0F0F0", "#F5F5F5", "#DFDFDF"
BTN_DIS_BG, BTN_DIS_BD = "#F7F7F7", "#EBEBEB"
SUBTLE_HOVER, SUBTLE_PRESS = "#F0F0F0", "#E8E8E8"

SB_TRACK, SB_THIN, SB_THUMB = "#FBFBFB", "#B4B4B4", "#8A8A8A"
SB_THUMB_HOV, SB_THUMB_DRAG = "#767676", "#5D5D5D"
SB_ARROW, SB_ARROW_HOV = "#5D5D5D", "#EDEDED"

SEL_BG = "#CCE4F7"
DIFF_INS, DIFF_DEL = "#0F7B0F", "#C42B1C"
DIFF_CUR, DIFF_SEL_BG = "#A9D6F8", "#E3F0FB"
DIFF_HOVER = "#F0F0F0"
SRC_ORIG_BG, SRC_MOD_BG = "#FFD5D6", "#C9EFC9"

OK_FG, WARN_FG = "#0F7B0F", "#C42B1C"

CARD_RADIUS, CARD_INSET, BTN_RADIUS, BTN_H, GUTTER = 8, 3, 4, 30, 12

F = {}


def _pick_family(root, *candidates):
    families = set(tkfont.families(root))
    return next((name for name in candidates if name in families), candidates[-1])


def init_fonts(root):
    ui = _pick_family(root, "Microsoft YaHei UI", "Segoe UI", "Microsoft YaHei")
    ed = _pick_family(root, "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI")
    F.update(ui=(ui, 9), ui_sb=(ui, 9, "bold"), ui_sm=(ui, 8),
             input=(ed, 10), diff=(ed, 11),
             diff_i=(ed, 11, "bold"), diff_d=(ed, 11, "overstrike"))
    icon = _pick_family(root, "Segoe Fluent Icons", "Segoe MDL2 Assets", "")
    F["icon"] = (icon, 6) if icon else None
