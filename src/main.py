import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import difflib, ctypes

try:
    myappid = 'mycompany.prodifftool.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

FONT_MAIN  = ("Consolas", 12)
FONT_INPUT = ("Consolas", 10)
FONT_UI    = ("Microsoft YaHei", 9)


class ProDiffTool:
    def __init__(self, root):
        self.root = root
        root.title("文本对比工具")
        root.minsize(720, 520)

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{int(sw*.4)}x{int(sh*.8)}+{int(sw*.3)}+{int(sh*.1)}")

        try:
            if hasattr(sys, '_MEIPASS'):
                ico = os.path.join(sys._MEIPASS, '文档对比.ico')
            else:
                ico = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   '..', 'assets', '文档对比.ico')
            if os.path.exists(ico):
                root.iconbitmap(ico)
        except:
            pass

        self._reset_state()
        self._build_styles()
        self._build_ui()
        self.refresh_buttons()
        root.deiconify()

    def _reset_state(self):
        self.changes      = []
        self.diff_count   = 0
        self.cur          = None
        self.has_compared = False
        self.char_pos     = 0

    def _build_styles(self):
        s = ttk.Style(self.root)
        base = (FONT_UI[0], FONT_UI[1])
        bold = (FONT_UI[0], FONT_UI[1], "bold")
        s.configure("TButton",           font=base, padding=(6, 3))
        s.configure("Primary.TButton",   font=bold, foreground="#0056b3", padding=(10, 4))
        s.configure("Mini.TButton",      font=(FONT_UI[0], 8), padding=(3, 1))
        s.configure("Title.TLabel",      font=bold)
        s.configure("Stats.TLabel",      font=base)
        s.configure("TLabelframe.Label", font=bold)

    def _build_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)

        split = ttk.PanedWindow(main, orient=tk.VERTICAL)
        split.grid(row=0, column=0, sticky="nsew")

        upper = ttk.Frame(split)
        upper.grid_rowconfigure(0, weight=1)
        upper.grid_columnconfigure(0, weight=1)

        pane = ttk.PanedWindow(upper, orient=tk.HORIZONTAL)
        pane.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        self.txt_orig = self._make_input(pane, "原始文本")
        self.txt_mod  = self._make_input(pane, "修订文本")

        ctrl = ttk.Frame(upper, padding="4 4")
        ctrl.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.lbl_stats = ttk.Label(ctrl, text="就绪", foreground="gray",
                                   style="Stats.TLabel")
        self.lbl_stats.pack(side=tk.RIGHT, padx=8)

        bar = ttk.Frame(ctrl)
        bar.pack(side=tk.LEFT)
        btn_defs = [
            ("compare", "开始对比", self.run_compare,      "Primary.TButton", 9),
            ("prev",    "上一项",   self.prev_change,      "TButton",         7),
            ("next",    "下一项",   self.next_change,      "TButton",         7),
            ("accept",  "接受",     self.accept_change,    "TButton",         5),
            ("reject",  "拒绝",     self.reject_change,    "TButton",         5),
            ("locate",  "定位",     self.locate_selection, "TButton",         5),
            ("clear",   "清空",     self.clear_all,        "TButton",         5),
        ]
        self.buttons = {}
        for key, txt, cmd, style, w in btn_defs:
            b = ttk.Button(bar, text=txt, style=style, width=w, command=cmd)
            b.pack(side=tk.LEFT, padx=(0, 4))
            self.buttons[key] = b

        frame_prev = ttk.LabelFrame(split, text="差异预览", padding=6)
        self.txt_preview = scrolledtext.ScrolledText(
            frame_prev, font=FONT_MAIN, height=10,
            cursor="arrow",
            selectbackground="#a8c8f0", selectforeground="#1a1a1a")
        self.txt_preview.pack(fill=tk.BOTH, expand=True)
        self._make_readonly(self.txt_preview)

        split.add(upper, weight=3)
        split.add(frame_prev, weight=4)
        self._setup_tags()

    def _make_input(self, parent, title):
        f = ttk.Frame(parent)
        h = ttk.Frame(f)
        h.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(h, text=title, style="Title.TLabel").pack(side=tk.LEFT)
        c = ttk.Frame(f, relief=tk.GROOVE, borderwidth=1)
        c.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        t = scrolledtext.ScrolledText(c, font=FONT_INPUT, height=10, undo=True)
        t.pack(fill=tk.BOTH, expand=True)
        ttk.Button(h, text="粘贴", style="Mini.TButton",
                   command=lambda: self._paste(t)).pack(side=tk.RIGHT, padx=(0, 5))
        parent.add(f, weight=1)
        return t

    def _make_readonly(self, widget):
        """让 Text 组件只读但仍允许鼠标拖选。"""
        # 拦截所有可能修改内容的按键
        widget.bind("<Key>", lambda e: "break")
        # 允许 Ctrl+C 复制
        widget.bind("<Control-c>", lambda e: None)
        widget.bind("<Control-C>", lambda e: None)
        # 允许 Ctrl+A 全选
        widget.bind("<Control-a>", lambda e: widget.tag_add(tk.SEL, "1.0", tk.END) or "break")
        widget.bind("<Control-A>", lambda e: widget.tag_add(tk.SEL, "1.0", tk.END) or "break")
        # 禁止右键粘贴
        widget.bind("<<Paste>>", lambda e: "break")
        widget.bind("<<Cut>>",   lambda e: "break")

    def _setup_tags(self):
        p = self.txt_preview
        p.tag_config("diff_insert", foreground="#28a745", font=(*FONT_MAIN, "bold"))
        p.tag_config("diff_delete", foreground="#e06c75", font=(FONT_MAIN[0], FONT_MAIN[1], "overstrike"))
        p.tag_config("hover",        background="#fff9e6")
        p.tag_config("current_diff", background="#dbeafe")
        p.tag_config("sel",          background="#a8c8f0", foreground="#1a1a1a")
        p.tag_raise("current_diff")
        p.tag_raise("sel")

    def run_compare(self):
        t1 = self.txt_orig.get("1.0", tk.END).strip()
        t2 = self.txt_mod.get("1.0", tk.END).strip()
        if not t1 and not t2:
            self.clear_preview()
            return

        p = self.txt_preview
        p.delete("1.0", tk.END)
        self._reset_state()
        self.has_compared = True

        bid = 0
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, t1, t2, autojunk=False).get_opcodes():
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
                self.changes.append({
                    'id': cid, 'start': c_start, 'end': self.char_pos,
                    'orig_start': i1, 'orig_end': i2,
                    'mod_start':  j1, 'mod_end':  j2,
                    'orig_text': del_txt, 'mod_text': ins_txt,
                    'resolved': False,
                })


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

    def accept_change(self):
        self._resolve(use_mod=True)

    def reject_change(self):
        self._resolve(use_mod=False)

    def _resolve(self, use_mod: bool):
        if self.cur is None:
            return
        cid      = self.cur
        c        = self.changes[cid]
        new_text = c['mod_text'] if use_mod else c['orig_text']
        old_len  = c['end'] - c['start']
        delta    = len(new_text) - old_len

        p = self.txt_preview
        s_idx = p.index(f"1.0 + {c['start']} chars")
        e_idx = p.index(f"1.0 + {c['end']} chars")
        p.delete(s_idx, e_idx)
        if new_text:
            p.insert(s_idx, new_text)

        c['end']      = c['start'] + len(new_text)
        c['resolved'] = True

        if delta:
            for oc in self.changes[cid + 1:]:
                oc['start'] += delta
                oc['end']   += delta

        self.diff_count = sum(1 for ch in self.changes if not ch['resolved'])
        nxt = self._next_unresolved(cid)
        self.cur = nxt
        if nxt is not None:
            self.select_change(nxt)
        else:
            p.tag_remove("current_diff", "1.0", tk.END)
            self.update_stats()

    def _next_unresolved(self, after):
        for c in self.changes[after + 1:]:
            if not c['resolved']:
                return c['id']
        for c in self.changes[:after]:
            if not c['resolved']:
                return c['id']
        return None

    def select_change(self, cid):
        if cid is None or not (0 <= cid < len(self.changes)):
            return
        c = self.changes[cid]
        if c['resolved']:
            return
        p = self.txt_preview
        s = f"1.0 + {c['start']} chars"
        e = f"1.0 + {c['end']} chars"
        self.cur = cid
        p.tag_remove("current_diff", "1.0", tk.END)
        p.tag_remove(tk.SEL, "1.0", tk.END)
        p.tag_add("current_diff", s, e)
        p.tag_add(tk.SEL, s, e)
        p.mark_set(tk.INSERT, s)
        p.see(e)
        p.see(s)
        self.update_stats()

    def prev_change(self):
        ids = [c['id'] for c in self.changes if not c['resolved']]
        if not ids:
            return
        if self.cur is None:
            self.select_change(ids[0])
        else:
            before = [i for i in ids if i < self.cur]
            if before:
                self.select_change(before[-1])

    def next_change(self):
        ids = [c['id'] for c in self.changes if not c['resolved']]
        if not ids:
            return
        if self.cur is None:
            self.select_change(ids[0])
        else:
            after = [i for i in ids if i > self.cur]
            if after:
                self.select_change(after[0])

    def update_stats(self):
        if not self.has_compared:
            self.lbl_stats.config(text="就绪", foreground="gray")
        elif self.diff_count:
            pos_str = ""
            if self.cur is not None:
                ids = [c['id'] for c in self.changes if not c['resolved']]
                if self.cur in ids:
                    pos_str = f" | 当前 {ids.index(self.cur)+1}/{self.diff_count}"
            self.lbl_stats.config(text=f"剩余 {self.diff_count} 处差异{pos_str}",
                                  foreground="red")
        else:
            total = len(self.changes)
            msg   = f"全部 {total} 处差异已处理" if total else "未发现差异"
            self.lbl_stats.config(text=msg, foreground="green")
        self.refresh_buttons()

    def refresh_buttons(self):
        if not hasattr(self, "buttons"):
            return
        unres = [c for c in self.changes if not c['resolved']]
        cur   = self.cur
        has   = bool(unres)
        self.buttons["prev"].config(
            state=tk.NORMAL if cur is not None and any(c['id'] < cur for c in unres) else tk.DISABLED)
        self.buttons["next"].config(
            state=tk.NORMAL if cur is not None and any(c['id'] > cur for c in unres) else tk.DISABLED)
        ar = tk.NORMAL if cur is not None and has else tk.DISABLED
        self.buttons["accept"].config(state=ar)
        self.buttons["reject"].config(state=ar)
        self.buttons["locate"].config(state=tk.NORMAL if has else tk.DISABLED)

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
        self._reset_state()
        self.update_stats()

    def locate_selection(self):
        if not self.diff_count:
            messagebox.showinfo("提示", "请先开始对比")
            return
        if self.cur is None:
            unres = [c for c in self.changes if not c['resolved']]
            if unres:
                self.select_change(unres[0]['id'])
            return
        c = self.changes[self.cur]
        self._highlight_src(self.txt_orig, c['orig_start'], c['orig_end'], '#fff3cd')
        self._highlight_src(self.txt_mod,  c['mod_start'],  c['mod_end'],  '#d1e7dd')

    def _highlight_src(self, widget, start, end, color):
        pos = f"1.0 + {start} chars"
        widget.see(pos)
        widget.tag_remove("lh", "1.0", tk.END)
        end_pos = (f"1.0 + {end} chars" if end > start else f"{widget.index(pos)} lineend + 1c")
        widget.tag_add("lh", pos, end_pos)
        widget.tag_config("lh", background=color)


if __name__ == "__main__":
    root = tk.Tk()
    ProDiffTool(root)
    root.mainloop()