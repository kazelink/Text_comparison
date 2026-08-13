import ctypes
import tkinter as tk

from app import ProDiffTool

for _call in (lambda: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                  'mycompany.prodifftool.1.0'),
              lambda: ctypes.windll.shcore.SetProcessDpiAwareness(1)):
    try:
        _call()
    except Exception:
        pass


def main():
    root = tk.Tk()
    ProDiffTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
