"""设计令牌：颜色、字体、间距 —— 全应用唯一的视觉常量来源。"""

import tkinter.font as tkfont

# ── 基础色 ──────────────────────────────────────────────────────────
BG       = "#F3F3F3"   # 窗口底色（记事本的 Mica 背景）
SURFACE  = "#FFFFFF"   # 卡片 / 编辑区
TEXT_PRI = "#1B1B1B"
TEXT_SEC = "#5D5D5D"
TEXT_TER = "#8A8A8A"   # 提示、快捷键说明
TEXT_DIS = "#A0A0A0"

ACCENT        = "#0067C0"
ACCENT_HOVER  = "#1975C5"
ACCENT_PRESS  = "#3183CC"
ACCENT_DIS    = "#C9C9C9"

BTN_BG      = "#FBFBFB"
BTN_HOVER   = "#F0F0F0"
BTN_PRESS   = "#F5F5F5"
BTN_BORDER  = "#DFDFDF"
BTN_DIS_BG  = "#F7F7F7"
BTN_DIS_BD  = "#EBEBEB"

SUBTLE_HOVER = "#F0F0F0"
SUBTLE_PRESS = "#E8E8E8"

# ── 滚动条（Windows 11 覆盖式） ─────────────────────────────────────
SB_TRACK      = "#FBFBFB"
SB_THIN       = "#B4B4B4"   # 收起态细条
SB_THUMB      = "#8A8A8A"
SB_THUMB_HOV  = "#767676"
SB_THUMB_DRAG = "#5D5D5D"
SB_ARROW      = "#5D5D5D"
SB_ARROW_HOV  = "#EDEDED"

# ── 差异语义色 ──────────────────────────────────────────────────────
SEL_BG      = "#CCE4F7"
DIFF_INS    = "#0F7B0F"
DIFF_DEL    = "#C42B1C"
DIFF_CUR    = "#CCE4F7"
DIFF_HOVER  = "#F0F0F0"
SRC_ORIG_BG = "#FDE7E9"
SRC_MOD_BG  = "#DFF6DD"

OK_FG   = "#0F7B0F"
WARN_FG = "#C42B1C"

# ── 几何 ────────────────────────────────────────────────────────────
CARD_RADIUS = 8     # Win11 卡片/面板圆角
CARD_INSET  = 3     # 内容内缩，须 ≥ 0.293×半径，否则直角会戳出圆角外
BTN_RADIUS  = 4     # Win11 控件圆角
BTN_H       = 30
GUTTER      = 12    # 统一栅格间距

# 字体表，init_fonts() 后填充
F = {}


def _pick_family(root, *candidates):
    """按优先级挑一个系统里真实存在的字族。"""
    families = set(tkfont.families(root))
    for name in candidates:
        if name in families:
            return name
    return candidates[-1]


def init_fonts(root):
    """探测系统字体并填充字体表（须在创建任何控件前调用）。"""
    ui = _pick_family(root, "Microsoft YaHei UI", "Segoe UI", "Microsoft YaHei")
    ed = _pick_family(root, "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI")
    F["ui"]     = (ui, 9)
    F["ui_sb"]  = (ui, 9, "bold")
    F["ui_sm"]  = (ui, 8)
    F["input"]  = (ed, 10)
    F["diff"]   = (ed, 11)
    F["diff_i"] = (ed, 11, "bold")
    F["diff_d"] = (ed, 11, "overstrike")

    # Win11 自带的图标字体，用来画滚动条的小箭头（矢量、带抗锯齿）
    icon = _pick_family(root, "Segoe Fluent Icons", "Segoe MDL2 Assets", "")
    F["icon"] = (icon, 6) if icon else None
