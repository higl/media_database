import Tkinter as tk
import gui

if __name__ == '__main__':
    app = gui.Application()
    app.title('Sample application')
    app.grid_columnconfigure(0,weight=1)
    app.grid_rowconfigure(0,weight=1)
    app.resizable(True,True)

    app.mainloop()
