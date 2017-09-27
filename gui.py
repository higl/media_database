# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import Tkinter as tk
import media_database as mdb


class Application(tk.Frame):
    media_database = Null
    history = []
    historyFrameActive = False
    last = Null
    
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.createWidgets()
        #self.bindActions()
        
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
    
    def binActions(self):
        self.loadButton.bind("<Button-1>", load)
        self.saveButton.bind("<Button-1>", save)
        self.linkButton.bind("<Button-1>", linkFile)
        self.deleteButton.bind("<Button-1>", deleteFile)
        self.randomButton.bind("<Button-1>", randomFile) 
        self.historyButton.bind("<Button-1>", displayHistory) 
        self.selector.applyButton.bind("<Button-1>", displaySelection)
        self.dataBase.bind(
        self.pack()    
    self.pack()
        
    def load():
        print self.filepath.get()
        if self.media_database != Null and !self.media_database.saved:
            #open Warning dialog with save option
        self.media_database = mdb.media_database(self.filepath.get())
        self.dataBase.delete(0,END)
        for i in self.media_database.get_selection():
            self.dataBase.insert(END,item)
    
    def save():
        self.media_database.save()
        
    def linkFile():
        id = self.dataBase.get(ACTIVE)
        try:
            entry = self.media_database.get_entry(id)
            #open dialog to find destination of link
        #    os.link()
        except:
            #open dialog with file not found

    def deleteFile():
        id = self.dataBase.get(ACTIVE)
        try:
            entry = self.media_database.get_entry(id)
            #open dialog to issue warning about deleting file
            #self.media_database.delete(entry)
        except:
            #open dialog with file not found            

    def randomFile():
        self.last = self.media_database.executeRandom()
        history.append(self.last)
        if historyFrameActive:
            self.historyFrame.append(self.last)        
        
    def displayHistory():
        #open dialog with listbox that contains the entries of history + bind actions similar to media_database 
        #( == doubleclick -> dialog for open and delete
        #     singleclick -> infobox )
        #     rightclick -> dropdown with "add Tag or modify or something like that" 
        # )
        historyFrameActive = True
        
    def displaySelection():
        args = self.selector.getArgs()
        
        self.dataBase.delete(0,END)
        for i in self.media_database.get_selection(args):
            self.dataBase.insert(END,item)
        
       
        
        
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