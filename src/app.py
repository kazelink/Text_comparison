"""应用主控制器：界面装配、对比流程、导航与状态管理。"""

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from diff import Change, leading_offsets, opcodes
from theme import (BG, DIFF_CUR, DIFF_DEL, DIFF_HOVER, DIFF_INS, F,
                   GUTTER, OK_FG, SEL_BG, SRC_MOD_BG, SRC_ORIG_BG,
                   SURFACE, TEXT_PRI, TEXT_SEC, TEXT_TER, WARN_FG,
                   init_fonts)
from widgets import Card, FluentButton, FluentScrollbar

# 预览只读区允许透传的按键（光标移动、选择、复制、切换焦点等）
_NAV_KEYS = {"Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next",
             "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
             "F1", "F2", "F3", "F4", "Escape", "Tab"}
_CTRL_OK = {"a", "A", "c", "C", "Home", "End", "Left", "Right",
            "Up", "Down", "Prior", "Next", "Insert", "Return"}


class ProDiffTool:
    """文本对比工具主界面。"""

    def __init__(self, root):
        self.root = root
        root.title("文本对比工具")
        root.minsize(760, 540)
        root.configure(bg=BG)

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{int(sw*.42)}x{int(sh*.8)}+{int(sw*.29)}+{int(sh*.1)}")
        self._set_icon(root)

        init_fonts(root)
        self._reset_state()
        self._build_styles()
        self._build_ui()
        self._bind_keys()
        self.refresh_buttons()
        root.deiconify()

    @staticmethod
    def _set_icon(root):
        """加载应用图标；打包为 EXE 时从 _MEIPASS 读取。"""
        try:
            if hasattr(sys, '_MEIPASS'):
                ico = os.path.join(sys._MEIPASS, '文档对比.ico')
            else:
                ico = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '..', 'assets', '文档对比.ico')
            if os.path.exists(ico):
                root.iconbitmap(ico)
        except Exception:
            pass

    # ── 状态 ──────────────────────────────────────────────────────────
    def _reset_state(self):
        self.changes      = []
        self.diff_count   = 0
        self.cur          = None
        self.has_compared = False
        self.char_pos     = 0
        self.off_orig     = 0   # 原始文本前导空白长度，用于换算回输入框坐标
        self.off_mod      = 0

    # ── 样式 ──────────────────────────────────────────────────────────
    def _build_styles(self):
        # 仅 PanedWindow 还用 ttk（它的 weight 才能做等比拉伸）；clam 是唯一
        # 允许自定义配色的内置主题，Windows 默认的 vista 会忽略颜色设置。
        s = ttk.Style(self.root)
        s.theme_use("clam")
        s.configure("TPanedwindow", background=BG)
        s.configure("Sash", sashthickness=GUTTER, gripcount=0,
                    background=BG, lightcolor=BG, darkcolor=BG, bordercolor=BG)

    # ── 界面搭建 ──────────────────────────────────────────────────────
    def _build_ui(self):
        root = self.root
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        self._build_toolbar(root)

        # 工作区：上（双栏输入）/ 下（差异预览），可拖拽分配高度
        split = ttk.PanedWindow(root, orient=tk.VERTICAL)
        split.grid(row=1, column=0, sticky="nsew", padx=GUTTER)

        upper = tk.Frame(split, bg=BG)
        upper.grid_rowconfigure(0, weight=1)
        upper.grid_columnconfigure(0, weight=1)
        pane = ttk.PanedWindow(upper, orient=tk.HORIZONTAL)
        pane.grid(row=0, column=0, sticky="nsew")
        self.txt_orig, sb_orig = self._make_pane(pane, "原始文本")
        self.txt_mod,  sb_mod  = self._make_pane(pane, "修订文本")
        self._link_scroll(self.txt_orig, sb_orig, self.txt_mod, sb_mod)

        lower = tk.Frame(split, bg=BG)
        lower.grid_rowconfigure(0, weight=1)
        lower.grid_columnconfigure(0, weight=1)
        card = Card(lower, height=250)
        card.grid(row=0, column=0, sticky="nsew")
        self.txt_preview, _sb = self._make_surface(
            card, "差异预览", font=F["diff"], cursor="arrow", height=12)
        self._make_readonly(self.txt_preview)

        split.add(upper, weight=1)
        split.add(lower, weight=1)

        self._build_statusbar(root)
        self._setup_tags()

    def _build_toolbar(self, parent):
        """命令栏：主操作 → 导航 → 采纳 → 清空。组内 4px，组间 16px，
        用间距分组而不是分隔线，避免多余的灰线。"""
        bar = tk.Frame(parent, bg=BG)
        bar.grid(row=0, column=0, sticky="ew", padx=GUTTER, pady=(GUTTER, 10))

        groups = (
            (("compare", "开始对比", self.run_compare,   "accent",   96),),
            (("prev",    "上一项",   self.prev_change,   "standard", 64),
             ("next",    "下一项",   self.next_change,   "standard", 64)),
            (("accept",  "接受",     self.accept_change, "standard", 56),
             ("reject",  "拒绝",     self.reject_change, "standard", 56)),
            (("clear",   "清空",     self.clear_all,     "standard", 56),),
        )
        self.buttons = {}
        for gi, group in enumerate(groups):
            for bi, (key, text, cmd, variant, min_w) in enumerate(group):
                b = FluentButton(bar, text=text, command=cmd, variant=variant,
                                 min_width=min_w)
                left = 0 if (gi == 0 and bi == 0) else (4 if bi else 16)
                b.pack(side=tk.LEFT, padx=(left, 0))
                self.buttons[key] = b

    def _build_statusbar(self, parent):
        """底部状态栏：左侧快捷键提示，右侧对比进度。仿记事本，无分隔线。"""
        bar = tk.Frame(parent, bg=BG)
        bar.grid(row=2, column=0, sticky="ew", padx=GUTTER + 2, pady=(8, 8))
        tk.Label(bar, text="Ctrl+Enter 对比    F1 / F2 切换差异    F3 / F4 接受 / 拒绝",
                 bg=BG, fg=TEXT_TER, font=F["ui_sm"]).pack(side=tk.LEFT)
        self.lbl_stats = tk.Label(bar, text="就绪", bg=BG, fg=TEXT_SEC,
                                  font=F["ui"], anchor="e")
        self.lbl_stats.pack(side=tk.RIGHT)

    def _make_surface(self, card, title, paste=False, font=None, **text_kw):
        """把标题栏做进白色面板内部，面板即是一个完整单元 —— 标题不再
        浮在灰底上，也就没有额外的分隔线。返回 (text, scrollbar)。"""
        head = tk.Frame(card.body, bg=SURFACE)
        head.pack(fill=tk.X, padx=(14, 6), pady=(9, 5))
        tk.Label(head, text=title, bg=SURFACE, fg=TEXT_PRI,
                 font=F["ui_sb"]).pack(side=tk.LEFT)

        wrap = tk.Frame(card.body, bg=SURFACE)
        wrap.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        t = tk.Text(wrap, font=font or F["input"], bd=0, highlightthickness=0,
                    relief="flat", bg=SURFACE, fg=TEXT_PRI,
                    insertbackground=TEXT_PRI, insertwidth=1,
                    selectbackground=SEL_BG, selectforeground=TEXT_PRI,
                    padx=14, pady=2, wrap="char", **text_kw)
        sb = FluentScrollbar(wrap, command=t.yview, bg=SURFACE)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        t.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        t.config(yscrollcommand=sb.set)
        sb.attach(t)

        if paste:
            FluentButton(head, text="粘贴", command=lambda: self._paste(t),
                         variant="subtle", height=24, bg=SURFACE).pack(side=tk.RIGHT)
        return t, sb

    def _make_pane(self, parent, title):
        card = Card(parent)
        t, sb = self._make_surface(card, title, paste=True, undo=True, height=10)
        parent.add(card, weight=1)
        return t, sb

    def _link_scroll(self, a, sb_a, b, sb_b):
        """左右两栏滚动同步：按可视比例联动，滚轮/滚动条/键盘都生效。"""
        self._sync_lock = False

        def bridge(own_sb, other):
            def on_scroll(first, last):
                own_sb.set(first, last)
                if self._sync_lock:
                    return
                self._sync_lock = True
                try:
                    if other.yview()[0] != float(first):
                        other.yview_moveto(first)
                finally:
                    self._sync_lock = False
            return on_scroll

        a.config(yscrollcommand=bridge(sb_a, b))
        b.config(yscrollcommand=bridge(sb_b, a))

    def _make_readonly(self, widget):
        """只读，但保留光标移动、选择、复制 —— 原来一律 break 掉，
        连方向键都用不了。"""
        def on_key(e):
            if e.state & 0x4:                       # Ctrl 组合
                return None if e.keysym in _CTRL_OK else "break"
            return None if e.keysym in _NAV_KEYS else "break"

        widget.bind("<Key>", on_key)
        widget.bind("<Control-a>",
                    lambda e: (widget.tag_add(tk.SEL, "1.0", tk.END), "break")[1])
        widget.bind("<Control-A>",
                    lambda e: (widget.tag_add(tk.SEL, "1.0", tk.END), "break")[1])
        widget.bind("<<Paste>>", lambda e: "break")
        widget.bind("<<Cut>>",   lambda e: "break")

    def _bind_keys(self):
        r = self.root
        r.bind("<Control-Return>", lambda e: self.run_compare())
        r.bind("<F1>",             lambda e: self.prev_change())
        r.bind("<F2>",             lambda e: self.next_change())
        r.bind("<F3>",             lambda e: self.accept_change())
        r.bind("<F4>",             lambda e: self.reject_change())

    def _setup_tags(self):
        p = self.txt_preview
        p.tag_config("diff_insert",  foreground=DIFF_INS, font=F["diff_i"])
        p.tag_config("diff_delete",  foreground=DIFF_DEL, font=F["diff_d"])
        p.tag_config("hover",        background=DIFF_HOVER)
        p.tag_config("current_diff", background=DIFF_CUR)
        p.tag_config("sel",          background=SEL_BG, foreground=TEXT_PRI)
        p.tag_raise("current_diff")
        p.tag_raise("sel")
        for w, color in ((self.txt_orig, SRC_ORIG_BG), (self.txt_mod, SRC_MOD_BG)):
            w.tag_config("lh", background=color)

    # ── 对比 ──────────────────────────────────────────────────────────
    def run_compare(self):
        raw1 = self.txt_orig.get("1.0", "end-1c")
        raw2 = self.txt_mod.get("1.0", "end-1c")
        t1, t2 = raw1.strip(), raw2.strip()
        if not t1 and not t2:
            self.clear_preview()
            return

        p = self.txt_preview
        p.delete("1.0", tk.END)
        self._reset_state()
        self.has_compared = True
        # diff 跑在 strip 后的文本上，而联动高亮要落回未 strip 的输入框，
        # 所以记下前导空白长度作为坐标偏移。
        self.off_orig, self.off_mod = leading_offsets(raw1, raw2)

        bid = 0
        for op, i1, i2, j1, j2 in opcodes(t1, t2):
            if op == 'equal':
                p.insert(tk.END, t1[i1:i2])
                self.char_pos += i2 - i1
            else:
                del_txt = t1[i1:i2] if op in ('replace', 'delete') else ''
                ins_txt = t2[j1:j2] if op in ('replace', 'insert') else ''
                cid     = len(self.changes)
                c_start = self.char_pos
                if del_txt:
                    tag = f"D{bid}"; bid += 1
                    p.insert(tk.END, del_txt, (tag, "diff_delete"))
                    self._bind_tag(tag, cid)
                    self.char_pos += len(del_txt)
                if ins_txt:
                    tag = f"I{bid}"; bid += 1
                    p.insert(tk.END, ins_txt, (tag, "diff_insert"))
                    self._bind_tag(tag, cid)
                    self.char_pos += len(ins_txt)
                self.changes.append(Change(
                    id=cid, start=c_start, end=self.char_pos,
                    orig_start=i1, orig_end=i2,
                    mod_start=j1, mod_end=j2,
                    orig_text=del_txt, mod_text=ins_txt,
                ))

        self.diff_count = len(self.changes)
        if self.diff_count:
            self.select_change(0)
        else:
            self.update_stats()

    def _bind_tag(self, tag, cid):
        p = self.txt_preview
        p.tag_bind(tag, "<Button-1>", lambda e, c=cid: self._on_click(c))
        p.tag_bind(tag, "<Enter>",    lambda e, t=tag: self._hover(t, True))
        p.tag_bind(tag, "<Leave>",    lambda e, t=tag: self._hover(t, False))

    def _on_click(self, cid):
        self.select_change(cid)
        return "break"

    def _hover(self, tag, on):
        self.txt_preview.config(cursor="hand2" if on else "arrow")
        fn = self.txt_preview.tag_add if on else self.txt_preview.tag_remove
        fn("hover", f"{tag}.first", f"{tag}.last")

    # ── 接受 / 拒绝 ───────────────────────────────────────────────────
    def accept_change(self):
        self._resolve(use_mod=True)

    def reject_change(self):
        self._resolve(use_mod=False)

    def _resolve(self, use_mod: bool):
        if self.cur is None:
            return
        cid      = self.cur
        c        = self.changes[cid]
        new_text = c.mod_text if use_mod else c.orig_text
        old_len  = c.end - c.start
        delta    = len(new_text) - old_len

        p = self.txt_preview
        s_idx = p.index(f"1.0 + {c.start} chars")
        e_idx = p.index(f"1.0 + {c.end} chars")
        p.delete(s_idx, e_idx)
        if new_text:
            p.insert(s_idx, new_text)

        c.end      = c.start + len(new_text)
        c.resolved = True

        if delta:
            for oc in self.changes[cid + 1:]:
                oc.start += delta
                oc.end   += delta

        self.diff_count = sum(1 for ch in self.changes if not ch.resolved)
        nxt = self._next_unresolved(cid)
        self.cur = nxt
        if nxt is not None:
            self.select_change(nxt)
        else:
            p.tag_remove("current_diff", "1.0", tk.END)
            self._clear_src_highlight()
            self.update_stats()

    def _next_unresolved(self, after):
        for c in self.changes[after + 1:]:
            if not c.resolved:
                return c.id
        for c in self.changes[:after]:
            if not c.resolved:
                return c.id
        return None

    # ── 导航 ──────────────────────────────────────────────────────────
    def select_change(self, cid):
        if cid is None or not (0 <= cid < len(self.changes)):
            return
        c = self.changes[cid]
        if c.resolved:
            return
        p = self.txt_preview
        s = f"1.0 + {c.start} chars"
        e = f"1.0 + {c.end} chars"
        self.cur = cid
        p.tag_remove("current_diff", "1.0", tk.END)
        p.tag_remove(tk.SEL, "1.0", tk.END)
        p.tag_add("current_diff", s, e)
        p.tag_add(tk.SEL, s, e)
        p.mark_set(tk.INSERT, s)
        p.see(e)
        p.see(s)
        self._sync_src_highlight(c)
        self.update_stats()

    def prev_change(self):
        ids = [c.id for c in self.changes if not c.resolved]
        if not ids:
            return
        if self.cur is None:
            self.select_change(ids[0])
        else:
            before = [i for i in ids if i < self.cur]
            if before:
                self.select_change(before[-1])

    def next_change(self):
        ids = [c.id for c in self.changes if not c.resolved]
        if not ids:
            return
        if self.cur is None:
            self.select_change(ids[0])
        else:
            after = [i for i in ids if i > self.cur]
            if after:
                self.select_change(after[0])

    # ── 源文联动 ──────────────────────────────────────────────────────
    def _sync_src_highlight(self, c):
        """选中差异时，自动在原文与修订文本中高亮对应片段。"""
        # 两栏滚动是联动的，这里要让各自定位到自己的片段，
        # 因此临时挂起同步，否则后定位的一栏会把另一栏拽走。
        self._sync_lock = True
        try:
            self._highlight_src(self.txt_orig, c.orig_start + self.off_orig,
                                c.orig_end + self.off_orig)
            self._highlight_src(self.txt_mod, c.mod_start + self.off_mod,
                                c.mod_end + self.off_mod)
        finally:
            self._sync_lock = False

    def _highlight_src(self, widget, start, end):
        pos = f"1.0 + {start} chars"
        widget.see(pos)
        widget.tag_remove("lh", "1.0", tk.END)
        end_pos = (f"1.0 + {end} chars" if end > start
                   else f"{widget.index(pos)} lineend + 1c")
        widget.tag_add("lh", pos, end_pos)

    def _clear_src_highlight(self):
        self.txt_orig.tag_remove("lh", "1.0", tk.END)
        self.txt_mod.tag_remove("lh", "1.0", tk.END)

    # ── 状态与按钮 ────────────────────────────────────────────────────
    def update_stats(self):
        if not self.has_compared:
            self.lbl_stats.config(text="就绪", fg=TEXT_SEC)
        elif self.diff_count:
            pos_str = ""
            if self.cur is not None:
                ids = [c.id for c in self.changes if not c.resolved]
                if self.cur in ids:
                    pos_str = f"　·　当前 {ids.index(self.cur)+1}/{self.diff_count}"
            self.lbl_stats.config(text=f"剩余 {self.diff_count} 处差异{pos_str}",
                                  fg=WARN_FG)
        else:
            total = len(self.changes)
            msg   = f"全部 {total} 处差异已处理" if total else "未发现差异"
            self.lbl_stats.config(text=msg, fg=OK_FG)
        self.refresh_buttons()

    def refresh_buttons(self):
        if not hasattr(self, "buttons"):
            return
        unres = [c for c in self.changes if not c.resolved]
        cur   = self.cur
        has   = bool(unres)
        self.buttons["prev"].config(
            state=tk.NORMAL if cur is not None and any(c.id < cur for c in unres) else tk.DISABLED)
        self.buttons["next"].config(
            state=tk.NORMAL if cur is not None and any(c.id > cur for c in unres) else tk.DISABLED)
        ar = tk.NORMAL if cur is not None and has else tk.DISABLED
        self.buttons["accept"].config(state=ar)
        self.buttons["reject"].config(state=ar)

    # ── 杂项 ──────────────────────────────────────────────────────────
    def _paste(self, widget):
        try:
            widget.delete("1.0", tk.END)
            widget.insert("1.0", self.root.clipboard_get())
        except tk.TclError:
            messagebox.showwarning("提示", "剪贴板为空")

    def clear_all(self):
        self.txt_orig.delete("1.0", tk.END)
        self.txt_mod.delete("1.0", tk.END)
        self.clear_preview()

    def clear_preview(self):
        p = self.txt_preview
        p.delete("1.0", tk.END)
        self._clear_src_highlight()
        self._reset_state()
        self.update_stats()
