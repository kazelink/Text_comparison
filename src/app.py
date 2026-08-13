import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from diff import Change, leading_offsets, opcodes
from theme import (BG, DIFF_CUR, DIFF_DEL, DIFF_HOVER, DIFF_INS,
                   DIFF_SEL_BG, F, GUTTER, OK_FG, SEL_BG, SRC_MOD_BG,
                   SRC_ORIG_BG, SURFACE, TEXT_PRI, TEXT_SEC, TEXT_TER,
                   WARN_FG, init_fonts)
from widgets import Card, FluentButton, FluentScrollbar

_NAV_KEYS = {"Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next",
             "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
             "F1", "F2", "F3", "F4", "Escape", "Tab"}
_CTRL_OK = {"a", "A", "c", "C", "Home", "End", "Left", "Right",
            "Up", "Down", "Prior", "Next", "Insert", "Return"}


class ProDiffTool:
    def __init__(self, root):
        self.root = root
        root.title("文本对比工具")
        root.minsize(760, 540)
        root.configure(bg=BG)

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{int(sw * .42)}x{int(sh * .8)}+{int(sw * .29)}+{int(sh * .1)}")
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
        try:
            base = (sys._MEIPASS if hasattr(sys, "_MEIPASS")
                    else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))
            ico = os.path.join(base, "文档对比.ico")
            if os.path.exists(ico):
                root.iconbitmap(ico)
        except Exception:
            pass

    def _reset_state(self):
        self.changes, self.diff_count, self.cur, self.has_compared = [], 0, None, False
        self.char_pos = self.off_orig = self.off_mod = 0

    def _build_styles(self):
        s = ttk.Style(self.root)
        s.theme_use("clam")
        s.configure("TPanedwindow", background=BG)
        s.configure("Sash", sashthickness=GUTTER, gripcount=0,
                    background=BG, lightcolor=BG, darkcolor=BG, bordercolor=BG)

    def _build_ui(self):
        root = self.root
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)
        self._build_toolbar(root)

        split = ttk.PanedWindow(root, orient=tk.VERTICAL)
        split.grid(row=1, column=0, sticky="nsew", padx=GUTTER)

        upper = tk.Frame(split, bg=BG)
        pane = ttk.PanedWindow(upper, orient=tk.HORIZONTAL)
        pane.grid(row=0, column=0, sticky="nsew")
        self.txt_orig, sb_orig = self._make_pane(pane, "原始文本")
        self.txt_mod, sb_mod = self._make_pane(pane, "修订文本", copy=True)
        self._link_scroll(self.txt_orig, sb_orig, self.txt_mod, sb_mod)

        lower = tk.Frame(split, bg=BG)
        card = Card(lower, height=250)
        card.grid(row=0, column=0, sticky="nsew")
        self.txt_preview, _ = self._make_surface(
            card, "差异预览", font=F["diff"], cursor="arrow", height=12)
        self.txt_preview.configure(selectbackground=DIFF_SEL_BG)
        self._make_readonly(self.txt_preview)

        split.add(upper, weight=1)
        split.add(lower, weight=1)
        for frame in (upper, lower):
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)
        self._build_statusbar(root)
        self._setup_tags()

    def _build_toolbar(self, parent):
        bar = tk.Frame(parent, bg=BG)
        bar.grid(row=0, column=0, sticky="ew", padx=GUTTER, pady=(GUTTER, 10))
        groups = (
            (("compare", "开始对比", self.run_compare, "accent", 96),),
            (("prev", "上一项", self.prev_change, "standard", 64),
             ("next", "下一项", self.next_change, "standard", 64)),
            (("reject", "拒绝", self.reject_change, "standard", 56),),
            (("clear", "清空", self.clear_all, "standard", 56),),
        )
        self.buttons = {}
        for gi, group in enumerate(groups):
            for bi, (key, text, command, variant, min_w) in enumerate(group):
                btn = FluentButton(bar, text=text, command=command, variant=variant,
                                   min_width=min_w)
                btn.pack(side=tk.LEFT, padx=(0 if gi == bi == 0 else 8, 0))
                self.buttons[key] = btn

    def _build_statusbar(self, parent):
        bar = tk.Frame(parent, bg=BG)
        bar.grid(row=2, column=0, sticky="ew", padx=GUTTER + 2, pady=(8, 8))
        tk.Label(bar, text="Ctrl+Enter 对比    F1 / F2 上一项 / 下一项    F4 拒绝",
                 bg=BG, fg=TEXT_TER, font=F["ui_sm"]).pack(side=tk.LEFT)
        self.lbl_stats = tk.Label(bar, text="就绪", bg=BG, fg=TEXT_SEC,
                                  font=F["ui"], anchor="e")
        self.lbl_stats.pack(side=tk.RIGHT)

    def _make_surface(self, card, title, paste=False, copy=False, font=None, **text_kw):
        head = tk.Frame(card.body, bg=SURFACE)
        head.pack(fill=tk.X, padx=(14, 6), pady=(9, 5))
        tk.Label(head, text=title, bg=SURFACE, fg=TEXT_PRI,
                 font=F["ui_sb"]).pack(side=tk.LEFT)

        wrap = tk.Frame(card.body, bg=SURFACE)
        wrap.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        text = tk.Text(wrap, font=font or F["input"], bd=0, highlightthickness=0,
                       relief="flat", bg=SURFACE, fg=TEXT_PRI,
                       insertbackground=TEXT_PRI, insertwidth=1,
                       selectbackground=SEL_BG, selectforeground=TEXT_PRI,
                       padx=14, pady=2, wrap="char", **text_kw)
        sb = FluentScrollbar(wrap, command=text.yview, bg=SURFACE)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text.config(yscrollcommand=sb.set)
        sb.attach(text)

        actions = []
        if paste:
            actions.append(("粘贴", lambda: self._paste(text)))
        if copy:
            actions.append(("复制", lambda: self._copy(text)))
        for label, command in actions:
            FluentButton(head, text=label, command=command,
                         variant="subtle", height=24, bg=SURFACE).pack(side=tk.RIGHT)
        return text, sb

    def _make_pane(self, parent, title, copy=False):
        card = Card(parent)
        text, sb = self._make_surface(card, title, paste=True, copy=copy,
                                      undo=True, height=10)
        parent.add(card, weight=1)
        return text, sb

    def _link_scroll(self, a, sb_a, b, sb_b):
        self._sync_lock = False

        def bridge(own_sb, other):
            def on_scroll(first, last):
                own_sb.set(first, last)
                if self._sync_lock:
                    return
                first_f = float(first)
                self._sync_lock = True
                try:
                    if abs(other.yview()[0] - first_f) > 1e-9:
                        other.yview_moveto(first_f)
                finally:
                    self._sync_lock = False
            return on_scroll

        a.config(yscrollcommand=bridge(sb_a, b))
        b.config(yscrollcommand=bridge(sb_b, a))

    def _make_readonly(self, widget):
        def allow(e):
            keys = _CTRL_OK if e.state & 0x4 else _NAV_KEYS
            return None if e.keysym in keys else "break"

        def select_all(_e):
            widget.tag_add(tk.SEL, "1.0", tk.END)
            return "break"

        widget.bind("<Key>", allow)
        widget.bind("<Control-a>", select_all)
        widget.bind("<Control-A>", select_all)
        widget.bind("<<Paste>>", lambda e: "break")
        widget.bind("<<Cut>>", lambda e: "break")

    def _bind_keys(self):
        for seq, command in (("<Control-Return>", self.run_compare),
                             ("<F1>", self.prev_change),
                             ("<F2>", self.next_change),
                             ("<F4>", self.reject_change)):
            self.root.bind(seq, lambda e, c=command: c())

    def _setup_tags(self):
        preview = self.txt_preview
        preview.tag_config("diff_insert", foreground=DIFF_INS, font=F["diff_i"])
        preview.tag_config("diff_delete", foreground=DIFF_DEL, font=F["diff_d"])
        preview.tag_config("hover", background=DIFF_HOVER)
        preview.tag_config("current_diff", background=DIFF_CUR)
        preview.tag_config("sel", background=DIFF_SEL_BG, foreground=TEXT_PRI)
        preview.tag_raise("current_diff")
        preview.tag_raise("sel")

        for widget, color in ((self.txt_orig, SRC_ORIG_BG),
                              (self.txt_mod, SRC_MOD_BG)):
            widget.tag_config("cur", background=color)
            widget.tag_raise("cur")
            widget.tag_raise("sel")

    def run_compare(self):
        raw1 = self.txt_orig.get("1.0", "end-1c")
        raw2 = self.txt_mod.get("1.0", "end-1c")
        t1, t2 = raw1.strip(), raw2.strip()
        if not t1 and not t2:
            self.clear_preview()
            return

        preview = self.txt_preview
        preview.delete("1.0", tk.END)
        self._reset_state()
        self.has_compared = True
        self.off_orig, self.off_mod = leading_offsets(raw1, raw2)

        bid = 0
        for op, i1, i2, j1, j2 in opcodes(t1, t2):
            if op == "equal":
                preview.insert(tk.END, t1[i1:i2])
                self.char_pos += i2 - i1
                continue

            del_txt = t1[i1:i2] if op != "insert" else ""
            ins_txt = t2[j1:j2] if op != "delete" else ""
            cid = len(self.changes)
            start = self.char_pos
            for prefix, text, style in (("D", del_txt, "diff_delete"),
                                        ("I", ins_txt, "diff_insert")):
                if not text:
                    continue
                tag = f"{prefix}{bid}"
                bid += 1
                preview.insert(tk.END, text, (tag, style))
                self._bind_tag(tag, cid)
                self.char_pos += len(text)
            self.changes.append(Change(
                id=cid, start=start, end=self.char_pos,
                orig_start=i1, orig_end=i2, mod_start=j1, mod_end=j2,
                orig_text=del_txt, mod_text=ins_txt))

        self.diff_count = len(self.changes)
        self._apply_diff_marks()
        if self.diff_count:
            self.select_change(0)
        else:
            self.update_stats()

    def _bind_tag(self, tag, cid):
        preview = self.txt_preview
        preview.tag_bind(tag, "<Button-1>", lambda e, c=cid: self._jump(c))
        preview.tag_bind(tag, "<Enter>", lambda e, t=tag: self._hover(t, True))
        preview.tag_bind(tag, "<Leave>", lambda e, t=tag: self._hover(t, False))

    def _jump(self, cid):
        self.select_change(cid)
        return "break"

    def _hover(self, tag, on):
        self.txt_preview.config(cursor="hand2" if on else "arrow")
        fn = self.txt_preview.tag_add if on else self.txt_preview.tag_remove
        fn("hover", f"{tag}.first", f"{tag}.last")

    def reject_change(self):
        if self.cur is not None:
            self._reject_to_mod(self.changes[self.cur])
            self._resolve(use_mod=False)

    def _reject_to_mod(self, c):
        s = f"1.0 + {c.mod_start + self.off_mod} chars"
        e = f"1.0 + {c.mod_end + self.off_mod} chars"
        self.txt_mod.replace(s, e, c.orig_text)
        delta = len(c.orig_text) - (c.mod_end - c.mod_start)
        c.mod_end = c.mod_start + len(c.orig_text)
        if delta:
            for other in self.changes:
                if other.id > c.id:
                    other.mod_start += delta
                    other.mod_end += delta
        self._apply_diff_marks()

    def _resolve(self, use_mod):
        if self.cur is None:
            return
        cid = self.cur
        c = self.changes[cid]
        new_text = c.mod_text if use_mod else c.orig_text
        delta = len(new_text) - (c.end - c.start)

        preview = self.txt_preview
        s = preview.index(f"1.0 + {c.start} chars")
        e = preview.index(f"1.0 + {c.end} chars")
        preview.replace(s, e, new_text)
        c.end = c.start + len(new_text)
        c.resolved = True

        if delta:
            for other in self.changes[cid + 1:]:
                other.start += delta
                other.end += delta

        self.diff_count = sum(not c.resolved for c in self.changes)
        nxt = self._next_unresolved(cid)
        self.cur = nxt
        if nxt is not None:
            self.select_change(nxt)
        else:
            preview.tag_remove("current_diff", "1.0", tk.END)
            preview.tag_remove(tk.SEL, "1.0", tk.END)
            self._clear_src_highlight()
            self.update_stats()

    def _next_unresolved(self, after):
        for c in self.changes[after + 1:] + self.changes[:after]:
            if not c.resolved:
                return c.id
        return None

    def select_change(self, cid):
        if cid is None or not (0 <= cid < len(self.changes)):
            return
        c = self.changes[cid]
        if c.resolved:
            return
        self.cur = cid
        preview = self.txt_preview
        s = f"1.0 + {c.start} chars"
        e = f"1.0 + {c.end} chars"
        preview.tag_remove("current_diff", "1.0", tk.END)
        preview.tag_remove(tk.SEL, "1.0", tk.END)
        preview.tag_add("current_diff", s, e)
        preview.tag_add(tk.SEL, s, e)
        preview.mark_set(tk.INSERT, s)
        preview.see(e)
        preview.see(s)
        self._sync_src_highlight(c)
        self.update_stats()

    def _step_change(self, direction):
        ids = [c.id for c in self.changes if not c.resolved]
        if not ids:
            return
        if self.cur is None:
            self.select_change(ids[0])
            return
        candidates = ([i for i in ids if i < self.cur] if direction < 0
                      else [i for i in ids if i > self.cur])
        if candidates:
            self.select_change(candidates[-1] if direction < 0 else candidates[0])

    def prev_change(self):
        self._step_change(-1)

    def next_change(self):
        self._step_change(1)

    def _apply_diff_marks(self):
        self._clear_source_marks()
        for widget in (self.txt_orig, self.txt_mod):
            widget.tag_remove("cur", "1.0", tk.END)
            widget.tag_raise("diff")
            widget.tag_raise("cur")
            widget.tag_raise("sel")

        for c in self.changes:
            def mark(widget, prefix, start, end):
                if end <= start:
                    return
                tag = f"{prefix}{c.id}"
                s = f"1.0 + {start} chars"
                e = f"1.0 + {end} chars"
                widget.tag_add("diff", s, e)
                widget.tag_add(tag, s, e)
                widget.tag_bind(tag, "<Button-1>",
                                lambda ev, cid=c.id: self._jump(cid))

            mark(self.txt_orig, "O", c.orig_start + self.off_orig,
                 c.orig_end + self.off_orig)
            mark(self.txt_mod, "M", c.mod_start + self.off_mod,
                 c.mod_end + self.off_mod)

    def _sync_src_highlight(self, c):
        self._sync_lock = True
        try:
            self._highlight_src(self.txt_orig,
                                c.orig_start + self.off_orig,
                                c.orig_end + self.off_orig)
            self._highlight_src(self.txt_mod,
                                c.mod_start + self.off_mod,
                                c.mod_end + self.off_mod)
        finally:
            self._sync_lock = False

    def _highlight_src(self, widget, start, end):
        try:
            pos = f"1.0 + {start} chars"
            widget.see(pos)
            widget.tag_remove("cur", "1.0", tk.END)
            if end > start:
                end_pos = f"1.0 + {end} chars"
            else:
                idx = widget.index(pos)
                end_pos = (f"{idx} + 1c" if widget.compare(idx, "<", "end")
                           else idx)
            widget.tag_add("cur", pos, end_pos)
        except tk.TclError:
            widget.tag_remove("cur", "1.0", tk.END)

    def _clear_src_highlight(self):
        self.txt_orig.tag_remove("cur", "1.0", tk.END)
        self.txt_mod.tag_remove("cur", "1.0", tk.END)

    def _clear_source_marks(self):
        for widget in (self.txt_orig, self.txt_mod):
            for tag in list(widget.tag_names()):
                if tag[:1] in ("O", "M") and tag[1:].isdigit():
                    widget.tag_delete(tag)
            widget.tag_remove("diff", "1.0", tk.END)

    def update_stats(self):
        if not self.has_compared:
            self.lbl_stats.config(text="就绪", fg=TEXT_SEC)
        elif self.diff_count:
            ids = [c.id for c in self.changes if not c.resolved]
            pos = (f"　·　当前 {ids.index(self.cur) + 1}/{self.diff_count}"
                   if self.cur in ids else "")
            self.lbl_stats.config(text=f"剩余 {self.diff_count} 处差异{pos}",
                                  fg=WARN_FG)
        else:
            total = len(self.changes)
            msg = f"全部 {total} 处差异已处理" if total else "未发现差异"
            self.lbl_stats.config(text=msg, fg=OK_FG)
        self.refresh_buttons()

    def refresh_buttons(self):
        if not hasattr(self, "buttons"):
            return
        unresolved = [c for c in self.changes if not c.resolved]
        cur = self.cur
        has = bool(unresolved)
        self.buttons["prev"].config(
            state=tk.NORMAL if cur is not None and any(c.id < cur for c in unresolved)
            else tk.DISABLED)
        self.buttons["next"].config(
            state=tk.NORMAL if has and (cur is None or any(c.id > cur for c in unresolved))
            else tk.DISABLED)
        self.buttons["reject"].config(
            state=tk.NORMAL if cur is not None and has else tk.DISABLED)

    def _paste(self, widget):
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            messagebox.showwarning("提示", "剪贴板为空")
            return
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)

    def _copy(self, widget):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(widget.get("1.0", "end-1c"))
        except tk.TclError:
            pass

    def clear_all(self):
        self.txt_orig.delete("1.0", tk.END)
        self.txt_mod.delete("1.0", tk.END)
        self.clear_preview()

    def clear_preview(self):
        self.txt_preview.delete("1.0", tk.END)
        self._clear_src_highlight()
        self._clear_source_marks()
        self._reset_state()
        self.update_stats()
