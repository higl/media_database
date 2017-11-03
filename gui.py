# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import Tkinter as tk
import media_database as mdb
import media_entry as me
import threading

class Application(tk.Frame):
    media_database = None
    history = []
    last = None
    historyWindow = None
    
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.createWidgets()
        self.bindActions()
        
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
        self.singleMode = tk.IntVar()
        self.singleBox = tk.Checkbutton(self,text='single',variable=self.singleMode)
        self.singleBox.grid(row=3,column=17)
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
    
    def bindActions(self):
        self.loadButton.bind("<Button-1>", self.load)
        self.saveButton.bind("<Button-1>", self.save)
        self.linkButton.bind("<Button-1>", self.linkFile)
        self.deleteButton.bind("<Button-1>", self.deleteFile)
        self.randomButton.bind("<Button-1>", self.randomFile) 
        self.historyButton.bind("<Button-1>", self.displayHistory) 
        self.selector.applyButton.bind("<Button-1>", self.displaySelection)
        #self.dataBase.bind(
        #self.pack()    
        
    def load(self,event):
        self.dataBase.insert(tk.END,self.filepath.get())
        if self.media_database != None and not self.media_database.saved:
            #open Warning dialog with save option
            print 'bla'
        self.media_database = mdb.media_database(self.filepath.get())
        self.dataBase.delete(0,tk.END)
        for i in self.media_database.get_selection():
            self.dataBase.insert(tk.END,i)
    
    def save(self,event):
        self.media_database.save()
        
    def linkFile(self,event):
        id = self.dataBase.get(tk.ACTIVE)
        try:
            entry = self.media_database.get_entry(id)
            #open dialog to find destination of link
        #    os.link()
        except:
            print "error"
            #open dialog with file not found

    def deleteFile(self,event):
        id = self.dataBase.get(tk.ACTIVE)
        try:
            entry = self.media_database.get_entry(id)
            #open dialog to issue warning about deleting file
            #self.media_database.delete(entry)
        except:
            print "error"
            #open dialog with file not found            

    def randomFile(self,event):
        self.last = self.media_database.get_random_entry(single=self.singleMode.get())
        self.history.append(self.last)  
        if self.historyWindow != None:
            self.historyWindow.fillBox()
        t = threading.Thread(target=self.last.execute,kwargs={'singleMode':self.singleMode.get()})
        t.setDaemon(True)
        t.start() 
        
    def displayHistory(self,event):
        #open dialog with listbox that contains the entries of history + bind actions similar to media_database 
        #( == doubleclick -> dialog for open and delete
        #     singleclick -> infobox )
        #     rightclick -> dropdown with "add Tag or modify or something like that" 
        # )
        #\\TODO: the close button in historyWindow does not set historyWindow = None -> reopeneing takes 2 klicks on history ... one can check if a window was destroyed with 
        #if 'normal' == window.state()
        if self.historyWindow != None:
            self.historyWindow.destroy()
            self.historyWindow = None
        else:
            self.historyWindow = HistoryFrame(self,self.history)
            self.after(50,self.checkHistoryWindow)
            
        
    def displaySelection(self,event):
        args = self.selector.getArgs()
        
        self.dataBase.delete(0,tk.END)
        for i in self.media_database.get_selection(args):
            self.dataBase.insert(tk.END,item)
    
    def checkHistoryWindow(self):
        try:
            if self.historyWindow != None:
                self.historyWindow.state()
                self.after(50,self.checkHistoryWindow)
        except tk.TclError:
            self.historyWindow = None
    

        
        
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

class HistoryFrame(tk.Toplevel):
    def __init__(self,master,history,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.history = history
        self.grid()
        self.createWidgets()
        self.fillBox()
        
    def createWidgets(self):
        self.historyList = tk.Listbox(self)
        self.historyList.grid(row=0,column=0,rowspan=20,columnspan=3)
        self.closeButton = tk.Button(self,text='close')
        self.closeButton.grid(row=21,column=1)
        self.closeButton.bind("<Button-1>", self.close)
    
    def close(self,event):
        self.destroy()
        
    def fillBox(self):
        self.historyList.delete(0,tk.END)
        for i in self.history:
            self.historyList.insert(tk.END,i.get_display_string())
            
        
master = tk.Tk()
app = Application()
app.master.title('Sample application')

master.mainloop()
