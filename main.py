from utils import Alogger

from tkinter import *
import ctypes
import os

import model
import pages

# Must be called before Tk() is created for Windows taskbar icon to take effect
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('library.app.1.0')

alogger = Alogger("main")


def begin_GUI(session_obj):
    root = Tk()
    root.title("Library")
    root.minsize(width=400,height=500)
    root.geometry("800x650")

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
    if os.path.exists(icon_path):
        root.iconbitmap(default=icon_path)

    pages.main_page(root, session_obj)

    alogger.debug("The GUI initiated")

    return root


def main():
    session_obj = model.init()
    root = begin_GUI(session_obj)
    root.mainloop()

def before_exit():
    alogger.debug("The App closing")


if __name__ == "__main__":
    main()
    before_exit()