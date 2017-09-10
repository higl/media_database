# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import Tkinter as tk

class Application(tk.Frame):
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.createWidgets()
        
    def createWidgets(self):
        top = self.winfo_toplevel()
        # for i in range(0,50):
            # top.rowconfigure(i,weight=1)
            # top.columnconfigure(i,weight=1)
   #     self.quitButton = tk.Button(self, text='Quit',command=self.quit)
    #    self.quitButton.grid(column=1,columnspan=3)
        
        self.filepath = tk.Entry(self)
        self.filepath.grid(row=2,column=0,columnspan=15)
        self.loadButton = tk.Button(self,text='Load')
        self.loadButton.grid(row=2,column=15)
        self.saveButton = tk.Button(self,text='Save')
        self.saveButton.grid(row=2,column=16)
        self.randomButton = tk.Button(self, text='Random')
        self.randomButton.grid(row=3,column=16)
        self.deleteButton = tk.Button(self, text='Delete')
        self.deleteButton.grid(row=4,column=16)
        self.historyButton = tk.Button(self, text='History')
        self.historyButton.grid(row=6,column=16)
        self.linkButton = tk.Button(self, text='Link')
        self.linkButton.grid(row=5,column=16)
        self.dataBase = tk.Listbox(self)
        self.dataBase.grid(row=3, column=0, rowspan=9,columnspan=16)
        self.selector = SelectorFrame()
        self.selector.grid(row=9,column=16,rowspan=6,columnspan=4)
        self.infobox = InfoFrame()
        self.infobox.grid(row=13,column=0,rowspan=3,columnspan=15)
        
    def executeRandom(self):
        self.labelah = tk.Label(self, text='aaaaah')
        self.labelah.grid(row=3)
        print('aaaaah')
        
        
class SelectorFrame(tk.Frame):
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.createWidgets()
        
    def createWidgets(self):
        self.selectorHead = tk.Label(self,text='Selection')
        self.selectorHead.grid(row=0,column=0,columnspan=2)
        self.actorLabel = tk.Label(self,text='Actor')
        self.actorLabel.grid(row=1,column=0)
        self.actorEntry = tk.Entry(self)
        self.actorEntry.grid(row=1,column=1)
        self.tagLabel = tk.Label(self,text='Actor')
        self.tagLabel.grid(row=2,column=0)
        self.tagEntry = tk.Entry(self)
        self.tagEntry.grid(row=2,column=1)
        self.genreLabel = tk.Label(self,text='Actor')
        self.genreLabel.grid(row=3,column=0)
        self.genreEntry = tk.Entry(self)
        self.genreEntry.grid(row=3,column=1)
        
        self.applyButton = tk.Button(self,text='Apply Selection')
        self.applyButton.grid(row=4,column=0,columnspan=2)



class InfoFrame(tk.Frame):
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.createWidgets()
        
    def createWidgets(self):
        self.selectorHead = tk.Label(self,text='InfoBox')
        self.selectorHead.grid(row=0,column=0,columnspan=2)
        self.actorLabel = tk.Label(self,text='Actor: ')
        self.actorLabel.grid(row=1,column=0)
        self.actorEntry = tk.Label(self,text='Will Smith')
        self.actorEntry.grid(row=1,column=1)
        self.tagLabel = tk.Label(self,text='Tag: ')
        self.tagLabel.grid(row=2,column=0)
        self.tagEntry = tk.Label(self,text='good, oscar')
        self.tagEntry.grid(row=2,column=1)
        self.genreLabel = tk.Label(self,text='Genre: ')
        self.genreLabel.grid(row=1,column=2)
        self.genreEntry = tk.Label(self, text='Horror')
        self.genreEntry.grid(row=1,column=3)
        
        self.applyButton = tk.Button(self,text='Show Infopage')
        self.applyButton.grid(row=4,column=0,columnspan=2)




app = Application()
app.master.title('Sample application')

app.mainloop()