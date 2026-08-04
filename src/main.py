"""应用入口：进程级初始化（高 DPI、任务栏标识）+ 启动主循环。"""

import ctypes
import tkinter as tk

from app import ProDiffTool

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        'mycompany.prodifftool.1.0')
except Exception:
    pass

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


def main():
    root = tk.Tk()
    ProDiffTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
