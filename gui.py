# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import Tkinter as tk
import tkMessageBox
import media_database as mdb
import media_entry as me
import threading

class Application(tk.Tk):
    media_database = None
    history = []
    last = None
    historyWindow = None
    infoWindow = None
    
    def __init__(self):
        tk.Tk.__init__(self)
        self.grid()
        self.createWidgets()
        self.bindActions()
        self.protocol("WM_DELETE_WINDOW", self.onClose)
        
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
        self.selector = SelectorFrame(master=self)
        self.selector.grid(row=9,column=16,rowspan=10,columnspan=4)
        self.infobox = InfoFrame(master=self)
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
        self.dataBase.bind("<Double-Button-1>", self.displayInfo)
        self.dataBase.bind("<<ListboxSelect>>",self.updateInfoBox)
        #self.pack()    
    
    def updateInfoBox(self,event):
        e = self.getSelected()
        self.infobox.update(e)
        
    def load(self,event):
        self.dataBase.insert(tk.END,self.filepath.get())
        if self.media_database != None and not self.media_database.saved:
            msg = "Current database is not saved yet! \n Do you want to save before loading a new one?"
            if tkMessageBox.askyesno("Load", msg):
                self.media_database.save()
                
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
        e = self.getSelected()
        if e != None and tkMessageBox.askokcancel("Delete", 
            "This will erase " + e.get_display_string() + " from the harddisk! Continue?"):
            e.delete()
            self.media_database.delete_entry(e)

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
            
    def displayInfo(self,event):
        e = self.getSelected()
        if e != None:
            self.createInfoWindow(e)
        
    def getSelected(self):
        s = self.dataBase.curselection()
        if len(s) == 0:
            tkMessageBox.showinfo(
            "Select File",
            "Please select an entry"
            )
            return None 
        else:
            value = self.dataBase.get(s[0])        
            e = self.media_database.find_entry(value)
            return e
            
    def createInfoWindow(self,e):
        if self.infoWindow != None:
            self.checkInfoStatus(cont=False)
            self.infoWindow.updateWindow(e)
        else:
            self.infoWindow = InfoWindow(self,e)
            self.after(50,self.checkInfoStatus)
    
    def displaySelection(self,event):
        self.fillSelection()
     
    def fillSelection(self):
        args = self.selector.getArgs()
        
        self.dataBase.delete(0,tk.END)
        for i in self.media_database.get_selection(**args):
            self.dataBase.insert(tk.END,i)
            
    def checkHistoryWindow(self):
        try:
            if self.historyWindow != None:
                self.historyWindow.state()
                self.after(50,self.checkHistoryWindow)
        except tk.TclError:
            self.historyWindow = None
    

    def checkInfoStatus(self,cont=True):
        try:
            self.infoWindow.state()
            s = self.infoWindow.checkStatus()
            if s == 'normal':
                pass 
            elif s == 'update':
                self.media_database.saved = False
                self.infoWindow.status = 'normal'
            elif s == 'deleted':
                self.media_database.delete_entry(self.infoWindow.entry)
                self.infoWindow.destroy()
                self.infoWindow = None
                self.fillSelection()
                cont = False
            if cont:
                self.after(50,self.checkInfoStatus)
        except tk.TclError:
            self.infoWindow = None

    def onClose(self):
        if self.media_database != None and not self.media_database.saved:
            msg = "Current database is not saved. \n Do you want to save before closing?"    
            if tkMessageBox.askyesno("Exit", msg):
                self.media_database.save()
                self.destroy()
            else:
                self.destroy()
        else:
            self.destroy()
    
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
        self.tagLabel = tk.Label(self,text='Tag')
        self.tagLabel.grid(row=2,column=0)
        self.tagEntry = tk.Entry(self)
        self.tagEntry.grid(row=2,column=1)
        self.genreLabel = tk.Label(self,text='Genre')
        self.genreLabel.grid(row=3,column=0)
        self.genreEntry = tk.Entry(self)
        self.genreEntry.grid(row=3,column=1)
        self.applyButton = tk.Button(self,text='Apply Selection')
        self.applyButton.grid(row=4,column=0,columnspan=2)
    
    def getArgs(self):
        args = {}
        args['actors'] = updateString(self.actorEntry.get())
        args['tags'] = updateString(self.tagEntry.get())
        args['genre'] = self.genreEntry.get()
        return args
        
class InfoFrame(tk.Frame):
    LabelList = []
    EntryList = []
    
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.grid()
        self.createWidgets()
        
    def createWidgets(self):
        self.selectorHead = tk.Label(self,text='InfoBox')
        self.selectorHead.grid(row=0,column=0,columnspan=2)
        self.showButton = tk.Button(self,text='Show Infopage')
        self.showButton.grid(row=4,column=0,columnspan=2)
        self.showButton.bind("<Button-1>", self.displayInfo)
        
        self.pLabel = tk.Label(self,text='Name: ')
        self.pLabel.grid(row=1,column=3)
        self.pEntry = tk.Label(self,text='')
        self.pEntry.grid(row=1,column=4)        
        
        
    def update(self,e):
        self.pEntry.config(text=e.get_display_string())
        self.clearLists()
        r = 2
        self.LabelList = []
        self.EntryList = []
        
        for i in e.attrib.keys():
            nLabel = tk.Label(self,text=i)
            nLabel.grid(row=r,column=1)
            self.LabelList.append(nLabel)
            
            eString = displayString(e.attrib[i])
            nEntry = tk.Entry(self)
            nEntry.insert(0,eString)
            nEntry.grid(row=r,column=2,columnspan=2)
            self.EntryList.append(nEntry)
            r = r+1
            if r >= 4:
                break
    
    def clearLists(self):
        for l in self.LabelList:
            l.destroy()
        for l in self.EntryList:
            l.destroy()
                
        
    def displayInfo(self,event):
        e = self.master.getSelected()
        if e != None:
            self.master.createInfoWindow(e)
            

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
        self.historyList.bind("<Double-Button-1>", self.displayInfo)
        self.closeButton = tk.Button(self,text='close')
        self.closeButton.grid(row=21,column=1)
        self.closeButton.bind("<Button-1>", self.close)
    
    def close(self,event):
        self.destroy()
        
    def fillBox(self):
        self.historyList.delete(0,tk.END)
        for i in self.history:
            self.historyList.insert(tk.END,i.get_display_string())
    
    def displayInfo(self,event):
        s = self.historyList.curselection()
        if len(s) == 0:
            tkMessageBox.showinfo(
            "Select File",
            "Please select an entry to be deleted"
            )
        else:
            value = self.historyList.get(s[0])       
            for i in self.history:
                if i.get_display_string() == value:
                    self.master.createInfoWindow(i)
                    return
        
    
class InfoWindow(tk.Toplevel):
    status = 'normal'
    
    def __init__(self,master,entry,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.status = 'normal'
        self.entry = entry
        self.grid()
        self.createWidgets()
        self.fillInfo()
        
    def createWidgets(self):
        self.historyList = tk.Listbox(self)
        self.historyList.grid(row=0,column=0,rowspan=20,columnspan=3)
        self.closeButton = tk.Button(self,text='close')
        self.closeButton.grid(row=21,column=1)
        self.closeButton.bind("<Button-1>", self.close)
    
    def close(self,event):
        self.destroy()
        
    def fillInfo(self):
        """
            \\TODO make the layout depending on the number of attributes 
                    if there are more than 10 attributes, I would like to have 10 dropdownboxes with all the attributes available ... I guess there will be never more than 10 different attributes updated and if so we should use a different method 
        """
        self.clearWindow()

        self.playButton = tk.Button(self,text='Play')
        self.playButton.grid(row=1,column=7)
        self.playButton.bind("<Button-1>", self.playFile)
        self.linkButton = tk.Button(self,text='Link')
        self.linkButton.grid(row=2,column=7)
        self.linkButton.bind("<Button-1>", self.link)
        self.updateButton = tk.Button(self,text='update entry')
        self.updateButton.grid(row=3,column=7)
        self.updateButton.bind("<Button-1>", self.updateEntry)
        self.deleteButton = tk.Button(self,text='delete from disk')
        self.deleteButton.grid(row=4,column=7)
        self.deleteButton.bind("<Button-1>", self.delete)
        self.closeButton = tk.Button(self,text='close')
        self.closeButton.grid(row=5,column=7)
        self.closeButton.bind("<Button-1>", self.close)

        self.pLabel = tk.Label(self,text='Name: ')
        self.pLabel.grid(row=1,column=3)
        self.pEntry = tk.Label(self,text=self.entry.get_display_string())
        self.pEntry.grid(row=1,column=4)        
        self.sLabel = tk.Label(self,text='media - type: ')
        self.sLabel.grid(row=2,column=3)
        self.sEntry = tk.Entry(self)
        self.sEntry.insert(0,self.entry.get_type())
        self.sEntry.grid(row=2,column=4)

        r = 3
        self.LabelList = []
        self.EntryList = []
        for i in self.entry.attrib.keys():
            nLabel = tk.Label(self,text=i)
            nLabel.grid(row=r,column=1)
            self.LabelList.append(nLabel)
            
            eString = displayString(self.entry.attrib[i])
            nEntry = tk.Entry(self)
            nEntry.insert(0,eString)
            nEntry.grid(row=r,column=2,columnspan=5)
            self.EntryList.append(nEntry)
            r = r+1
            
        
    def clearWindow(self):
        list = self.grid_slaves()
        for l in list:
            l.destroy()
            
    def playFile(self,event):
        t = threading.Thread(target=self.entry.execute)
        t.setDaemon(True)
        t.start() 

    def updateWindow(self,entry=None):
        if entry != None:
            self.entry = entry
        self.fillInfo()
    
    def updateEntry(self,event):
        """
        """
        attrib = {}
        for e,i in enumerate(self.LabelList):
            uString = self.EntryList[e].get()
            uString = updateString(uString)
            attrib[i.cget('text')] = uString
        
        self.entry.update_attrib(**attrib)
        self.status = 'update'
        
    
    def delete(self,event):
        self.entry.delete()
        self.status = 'deleted'
        
    def checkStatus(self):
        return self.status
    
    def close(self,event):
        self.destroy()
    
    def link(self,event):
        print 'zelda is not link'

def updateString(s):
    tmpstr = s.split(',')
    tmpstr = list(map(lambda x: x.lstrip(),tmpstr))
    tmpstr = list(map(lambda x: x.rstrip(),tmpstr)) 
    tmpstr = filter(lambda x: x != '', tmpstr)
    return tmpstr

def displayString(s):
    tmpstr = ''
    for i in s:
        tmpstr = tmpstr + ' , ' + i
    
    tmpstr = tmpstr.lstrip(' , ')    
    tmpstr = tmpstr.rstrip(' , ')
    return tmpstr
    

app = Application()
app.title('Sample application')

app.mainloop()
