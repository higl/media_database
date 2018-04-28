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
import eac.encode as eace
import eac.compare as eacc

class Application(tk.Tk):
    
    def __init__(self):
        tk.Tk.__init__(self)
        self.last = None
        self.historyWindow = None
        self.infoWindow = None
        self.history = []
        self.media_database = None
        self.selectionList = []
        self.grid()
        self.createWidgets()
        self.bindActions()
        self.protocol("WM_DELETE_WINDOW", self.onClose)
        
    def createWidgets(self):
    
        #menu creation
        menubar = tk.Menu(self)

        # create a pulldown menu, and add it to the menu bar
        toolmenu = tk.Menu(menubar, tearoff=0)
        toolmenu.add_command(label="Statistics", command=self.statistics_window)
        toolmenu.add_command(label="Encode", command=self.encode_window)
        toolmenu.add_command(label="Compare", command=self.compare_window)
        toolmenu.add_separator()
        menubar.add_cascade(label="Tools", menu=toolmenu)

        # display the menu
        self.config(menu=menubar)

        #main window widgets
        for i in range(0,50):
            self.rowconfigure(i,weight=1)
            self.columnconfigure(i,weight=1)
        
 
        options = {'sticky':'NSEW','padx':3,'pady':3}
        
        inputr = 0
        inputc = 0
        #input section
        self.filepath = tk.Entry(self)
        self.filepath.grid(row=inputr+0,column=inputc+0,columnspan=15,**options)
        self.loadButton = tk.Button(self,text='Load')
        self.loadButton.grid(row=inputr+0,column=inputc+15,**options)
        self.saveButton = tk.Button(self,text='Save')
        self.saveButton.grid(row=inputr+0,column=inputc+17,**options)
        
        toolr = 1
        toolc = 17
        #tool section
        self.randomButton = tk.Button(self, text='Random')
        self.randomButton.grid(row=toolr+0,column=toolc+0,**options)
        self.deleteButton = tk.Button(self, text='Delete')
        self.deleteButton.grid(row=toolr+1,column=toolc+0,**options)
        self.historyButton = tk.Button(self, text='History')
        self.historyButton.grid(row=toolr+2,column=toolc+0,**options)
        self.linkButton = tk.Button(self, text='Link')
        self.linkButton.grid(row=toolr+3,column=toolc+0,**options)
        self.singleMode = tk.IntVar()
        self.singleBox = tk.Checkbutton(self,text='single',variable=self.singleMode)
        self.singleBox.grid(row=toolr+4,column=toolc+0,**options)
        self.selectionMode = tk.IntVar()
        self.selectionBox = tk.Checkbutton(self,text='selected',variable=self.selectionMode)
        self.selectionBox.grid(row=toolr+5,column=toolc+0,**options)
        
        dbr = 1
        dbc = 0
        #database        
        self.dataBase = tk.Listbox(self)
        self.dataBase.grid(row=dbr+0, column=dbc+0, rowspan=9,columnspan=16,**options)
        scrollbar = tk.Scrollbar()
        scrollbar.grid(row=dbr+0,column=dbc+16,rowspan=9,sticky = 'NSW', padx=3)
        scrollbar.config(command=self.dataBase.yview)
        
        btoolr = 10
        btoolc = 0
        #2. tool section below database        
        self.infobox = InfoFrame(master=self)
        self.infobox.grid(row=btoolr+0,column=btoolc+0,rowspan=6,columnspan=12,**options)
        
        self.selector = SelectorFrame(master=self)
        self.selector.grid(row=btoolr+0,column=btoolc+12,rowspan=6,columnspan=6,**options)

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
        
    def updateInfoBox(self,event):
        e = self.getSelected()
        self.infobox.update(entry=e)
        
    def load(self,event):
        self.dataBase.insert(tk.END,self.filepath.get())
        if self.media_database != None and not self.media_database.saved:
            msg = "Current database is not saved yet! \n Do you want to save before loading a new one?"
            if tkMessageBox.askyesno("Load", msg):
                self.media_database.save()
                
        self.media_database = mdb.media_database(self.filepath.get())
        self.dataBase.delete(0,tk.END)
        self.selectionList = self.media_database.get_selection()
        for i in self.selectionList:
            self.dataBase.insert(tk.END,i)
        self.selector.update()
        
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
        if self.selectionMode.get():
            self.last = self.media_database.get_random_entry(single=self.singleMode.get(),selection=self.selectionList)
        else:
            self.last = self.media_database.get_random_entry(single=self.singleMode.get())
        self.infobox.update(entry=self.last)
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
    
    def statistics_window(self):
        attrib = self.media_database.get_attrib_stat()
        count = self.media_database.get_entry_count()
        StatisticsWindow(self,attrib,count)
    
    def encode_window(self):
        EncodeWindow(self)

    def compare_window(self):
        CompareWindow(self)
        
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
        if self.media_database == None:
            return
        else:
            self.selectionList = self.media_database.get_selection(**args)
            for i in self.selectionList:
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
                self.history.remove(self.infoWindow.entry)
                if self.historyWindow != None:
                    self.historyWindow.fillBox()
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
        if master == None or master.media_database == None:
            self.attribs = ['attribute 1','attribute 2','attribute 3','attribute 4']
        else:
            self.attribs = self.master.media_database.alist.keys()
            self.attribs.append('-')
            if len(self.attribs) < 4:
                att = ['-','-','-','-']
                att[:len(self.attribs)-1] = self.attribs[:]
                
        self.LabelList = []
        self.EntryList = []
        self.VarList = []
        self.createWidgets()
        
    def createWidgets(self):
        options = {'sticky':'NSEW','padx':3,'pady':3}
        self.selectorHead = tk.Label(self,text='Selection')
        self.selectorHead.grid(row=0,column=0,columnspan=2,**options)
        self.applyButton = tk.Button(self,text='Apply Selection')
        self.applyButton.grid(row=5,column=0,columnspan=2,**options)
        self.createSelectors()
        
    def createSelectors(self):
        options = {'sticky':'NSEW','padx':3,'pady':3}
        for i in range(4):            
            newVar = tk.StringVar(self)
            newVar.set(self.attribs[i])
            newLabel = tk.OptionMenu(self,newVar,*self.attribs)
            newLabel.grid(row=i+1,column=0,**options)
            newEntry = tk.Entry(self)
            newEntry.grid(row=i+1,column=1,**options)
            self.LabelList.append(newLabel)
            self.EntryList.append(newEntry)
            self.VarList.append(newVar)
        
    def getArgs(self):
        args = {}
        for e,i in enumerate(self.LabelList):
            var = self.VarList[e].get()
            uString = self.EntryList[e].get()
            uString = updateString(uString)
            if var == '-' or len(uString) == 0:
                continue
            args[self.VarList[e].get()] = uString
        return args
    
    def update(self):
        self.clearLists()
        if self.master == None or self.master.media_database == None:
            self.attribs = ['attribute 1','attribute 2','attribute 3','attribute 4']
        else:    
            self.attribs = self.master.media_database.alist.keys()
            self.attribs.append('-')
            if len(self.attribs) < 4:
                att = ['-','-','-','-']
                att[:len(self.attribs)-1] = self.attribs[:]
                
        self.LabelList = []
        self.EntryList = []
        self.VarList = []
        self.createSelectors()

    def clearLists(self):
        for l in self.LabelList:
            l.destroy()
        for l in self.EntryList:
            l.destroy()
        
class InfoFrame(tk.Frame):
  
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.LabelList = []
        self.EntryList = [] 
        self.entry = None
        self.grid()
        self.createWidgets()
        self.update()
        
    def createWidgets(self):
        options = {'sticky':'NSEW','padx':3,'pady':3}        
        self.selectorHead = tk.Label(self,text='InfoBox')
        self.selectorHead.grid(row=0,column=0,columnspan=2,**options)
        self.showButton = tk.Button(self,text='Show Infopage')
        self.showButton.grid(row=6,column=0,columnspan=2,**options)
        self.showButton.bind("<Button-1>", self.displayInfo)
        
        self.pLabel = tk.Label(self,text='Name: ')
        self.pLabel.grid(row=1,column=0,**options)
        self.pEntry = tk.Label(self,text='')
        self.pEntry.grid(row=1,column=1,**options)        
        
        
    def update(self,entry=None):
        options = {'sticky':'NSEW','padx':3,'pady':3}         
        self.entry = entry
        if entry == None:
            #create an empty entry that fills all the space we might need
            r = 2
            for i in range(3):
                nLabel = tk.Label(self,text='Info '+str(2*i+1))
                nLabel.grid(row=r,column=0)
                self.LabelList.append(nLabel)
                
                nEntry = tk.Entry(self)
                nEntry.grid(row=r,column=1,columnspan=5,**options)
                self.EntryList.append(nEntry)


                nLabel = tk.Label(self,text='Info '+str(2*i+2))
                nLabel.grid(row=r,column=7)
                self.LabelList.append(nLabel)
                
                nEntry = tk.Entry(self)
                nEntry.grid(row=r,column=8,columnspan=5,**options)
                self.EntryList.append(nEntry)

                r = r+1
                if r > 4:
                    break
        else:
            e = entry           
            self.pEntry.config(text=e.get_display_string())
            self.clearLists()
            self.LabelList = []
            self.EntryList = []
            
            nentry = len(e.attrib.keys())
            if nentry <= 6:
                r = 2
                c = 0                        
                for i in e.attrib.keys():
                    nLabel = tk.Label(self,text=i)
                    nLabel.grid(row=r,column=c)
                    self.LabelList.append(nLabel)
                    
                    eString = displayString(e.attrib[i])
                    nEntry = tk.Entry(self)
                    nEntry.insert(0,eString)
                    nEntry.grid(row=r,column=c+1,columnspan=5,**options)
                    self.EntryList.append(nEntry)
                    r = r+1
                    if r > 4:
                        r = 2
                        c = c+6
                        if c >= 12:
                            break
            else:
                #here make dropdownmenues instat of labels and bind and updatentry to it 
                self.VarList = []
                r = 2
                c = 0
                for i in e.attrib.keys():            
                    newVar = tk.StringVar(self)
                    newVar.set(i)
                    newLabel = tk.OptionMenu(self,newVar,*e.attrib.keys(),command=self.updateEntry)
                    newLabel.grid(row=r,column=c,**options)
                    
                    eString = displayString(e.attrib[i])
                    newEntry = tk.Entry(self)
                    newEntry.insert(0,eString)                
                    newEntry.grid(row=r,column=c+1,columnspan=5,**options)
                    self.LabelList.append(newLabel)
                    self.EntryList.append(newEntry)
                    self.VarList.append(newVar)
                    r = r+1
                    if r > 4:
                        r = 2
                        c = c+6
                        if c >= 12:
                            break

    def updateEntry(self,event):
        w = event.widget
        i = self.LabelList.index(w)
        self.EntryList[i].delete(0,tk.END)
        a = self.VarList[i].get()
        eString = displayString(self.entry.attrib[a])
        self.EntryList[i].insert(0,eString)
        
    def clearLists(self):
        for l in self.LabelList:
            l.destroy()
        for l in self.EntryList:
            l.destroy()
        self.VarList = []
                
        
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
        for i in range(0,50):
            self.rowconfigure(i,weight=1)
            self.columnconfigure(i,weight=1)
        self.historyList = tk.Listbox(self)
        self.historyList.grid(row=0,column=0,rowspan=20,columnspan=3,sticky='NSEW',padx=3,pady=3)
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=0,column=3,rowspan=20,sticky='NSW')
        scrollbar.config(command=self.historyList.yview)   
        self.historyList.config(yscrollcommand=scrollbar.set)
        self.historyList.bind("<Double-Button-1>", self.displayInfo)
        self.closeButton = tk.Button(self,text='close')
        self.closeButton.grid(row=21,column=1,columnspan=1,sticky = 'NSEW',padx=3,pady=3)
        self.closeButton.bind("<Button-1>", self.close)

    def close(self,event):
        self.destroy()
        
    def fillBox(self):
        self.historyList.delete(0,tk.END)
        for i in self.history:
            self.historyList.insert(0,i.get_display_string())
    
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
        self.updateButton.bind("<Button-1>", self.updateEntryEvent)
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
        if self.changedInfo():
            if tkMessageBox.askokcancel("Update Info","Entries have been updated. Do you want to save first?"):
                self.updateEntry()
        if entry != None:
            self.entry = entry
        self.fillInfo()
    
    def updateEntryEvent(self,event):
        self.updateEntry()
        
    def updateEntry(self):
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
        if tkMessageBox.askokcancel("Delete", 
            "This will erase " + self.entry.get_display_string() + " from the harddisk! Continue?"):
            self.entry.delete()
            self.status = 'deleted'
        else:
            return
    
    def changedInfo(self):
        attrib = {}
        for e,i in enumerate(self.LabelList):
            uString = self.EntryList[e].get()
            uString = updateString(uString)
            attrib[i.cget('text')] = uString
            if len(uString) == 0:
                continue
        return not self.entry.match_selection(**attrib)
        
 
    def checkStatus(self):
        return self.status
    
    def close(self,event):
        self.destroy()
    
    def link(self,event):
        print 'zelda is not link'

class StatisticsWindow(tk.Toplevel):
    
    def __init__(self,master,attrib,count,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.attrib = attrib
        self.count = count
        self.grid()
        self.createWidgets()
        self.fillInfo()
        
    def createWidgets(self):
        self.attribList = tk.Listbox(self)
        self.attribList.grid(row=0,column=0,rowspan=20,columnspan=3)
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=0,column=3,rowspan=20,sticky='NSW')
        scrollbar.config(command=self.attribList.yview)   
        self.attribList.config(yscrollcommand=scrollbar.set)
        self.attribList.bind("<<ListboxSelect>>", self.displayStat)


        self.statList = tk.Listbox(self)
        self.statList.grid(row=0,column=4,rowspan=20,columnspan=6)
        scrollbar_stat = tk.Scrollbar(self)
        scrollbar_stat.grid(row=0,column=11,rowspan=20,sticky='NSW')
        scrollbar_stat.config(command=self.statList.yview)   
        self.statList.config(yscrollcommand=scrollbar_stat.set)
        
        self.countLabel = tk.Label(self,text='Entry Count: ' + str(self.count))
        self.countLabel.grid(row=20,column=7,sticky = 'NSEW',padx=3,pady=3)

        self.closeButton = tk.Button(self,text='close')
        self.closeButton.grid(row=20,column=1,columnspan=1,sticky = 'NSEW',padx=3,pady=3)
        self.closeButton.bind("<Button-1>", self.close)

        
    def close(self,event):
        self.destroy()
        
    def fillInfo(self):
        for i in self.attrib.keys():
            self.attribList.insert(tk.END,i)

    def displayStat(self,event):   
        s = self.attribList.curselection()
        s = self.attrib.keys()[s[0]]
        sort = sorted(self.attrib[s].items(), key=lambda x: x[1], reverse=True)
        
        self.statList.delete(0,tk.END)
        for i in sort:
            pad = 25 - len(i[0]) - len(str(i[1]))
            if pad <= 0:
                st = i[0] + str(i[1])
            else:
                st = i[0].ljust(len(i[0])+pad) + str(i[1])

            self.statList.insert(tk.END,st)


class EncodeWindow(tk.Toplevel):
    
    def __init__(self,master,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.ready = False
        self.grid()
        self.createWidgets()
        
    def createWidgets(self):
        options = {'sticky':'NSEW','padx':3,'pady':3}      
        
        self.inputPath = tk.Entry(self)
        self.inputPath.grid(row=0,column=0,columnspan=10,**options)
        self.outputPath = tk.Entry(self)
        self.outputPath.grid(row=1,column=0,columnspan=10,**options)
        
        self.checkButton = tk.Button(self,text='Check')
        self.checkButton.grid(row=0,column=11,**options)
        self.checkButton.bind("<Button-1>", self.check)
        
        self.inputList = tk.Listbox(self)
        self.inputList.grid(row=2,column=0,rowspan=20,columnspan=5)
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=2,column=5,rowspan=20,sticky='NSW')
        scrollbar.config(command=self.inputList.yview)   
        self.inputList.config(yscrollcommand=scrollbar.set)
        
        self.outputList = tk.Listbox(self)
        self.outputList.grid(row=2,column=6,rowspan=20,columnspan=5)
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=2,column=11,rowspan=20,sticky='NSW')
        scrollbar.config(command=self.outputList.yview)
        self.outputList.config(yscrollcommand=scrollbar.set)
        
        self.encodeButton = tk.Button(self,text='Encode')
        self.encodeButton.grid(row=22,column=0, columnspan=5,**options)
        self.encodeButton.bind("<Button-1>", self.encode)
        
        self.closeButton = tk.Button(self,text='Close')
        self.closeButton.grid(row=22,column=5, columnspan=5,**options)
        self.closeButton.bind("<Button-1>", self.close)
        
        self.error = tk.StringVar()
        self.errorLabel = tk.Label(self,textvariable=self.error)
        self.errorLabel.grid(row=23,column=0,columnspan=10,sticky = 'NSEW',padx=3,pady=3)

    def close(self,event):
        self.destroy()

    def check(self,event):
        import os
        
        self.inp = self.inputPath.get()
        self.outp = self.outputPath.get()
        
        if not os.path.isdir(self.inp) or not os.path.isdir(self.outp):
            self.ready = False
            self.error.set('Input and Output have to be folders')
            return
        
        infiles  = eace.findFiles(self.inp,formats=eace.vformats)
        outfiles = eace.findFiles(self.outp,formats=eace.vformats)
            
        infiles = sorted(infiles)
        outfiles = sorted(outfiles)
        
        self.inputList.delete(0,tk.END)
        for i in infiles:
            self.inputList.insert(tk.END,i)

        self.outputList.delete(0,tk.END)
        for i in outfiles:
            self.outputList.insert(tk.END,i)
        
        self.ready = True
        self.error.set('')
        
    def encode(self,event):
        if self.ready:
            self.error.set('')
            kargs = {'quality':'low','encoder':'ffmpeg','processes':4,'audio':'mp4','override':False}
            args = (self.inp,self.outp)
            t = threading.Thread(target=eace.encode,kwargs=kargs,args=args)
            t.setDaemon(True)
            t.start()
            #eace.encode(self.inp,self.outp,quality='low',encoder='ffmpeg',processes=1,audio='mp4',override=False)
        else:
            self.error.set('first check the given input and output folder')
            return
        
class CompareWindow(tk.Toplevel):
    
    def __init__(self,master,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.ready = False
        self.grid()
        self.createWidgets()
        
    def createWidgets(self):
        options = {'sticky':'NSEW','padx':3,'pady':3}      
        
        self.inputPath = tk.Entry(self)
        self.inputPath.grid(row=0,column=0,columnspan=10,**options)
        self.outputPath = tk.Entry(self)
        self.outputPath.grid(row=1,column=0,columnspan=10,**options)
        
        self.checkButton = tk.Button(self,text='Check')
        self.checkButton.grid(row=0,column=11,**options)
        self.checkButton.bind("<Button-1>", self.check)
        
        self.inputList = tk.Listbox(self)
        self.inputList.grid(row=2,column=0,rowspan=20,columnspan=5)
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=2,column=5,rowspan=20,sticky='NSW')
        scrollbar.config(command=self.inputList.yview)   
        self.inputList.config(yscrollcommand=scrollbar.set)
        
        self.outputList = tk.Listbox(self)
        self.outputList.grid(row=2,column=6,rowspan=20,columnspan=5)
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=2,column=11,rowspan=20,sticky='NSW')
        scrollbar.config(command=self.outputList.yview)
        self.outputList.config(yscrollcommand=scrollbar.set)
        
        self.compareButton = tk.Button(self,text='Compare')
        self.compareButton.grid(row=22,column=0, columnspan=5,**options)
        self.compareButton.bind("<Button-1>", self.encode)
        
        self.closeButton = tk.Button(self,text='Close')
        self.closeButton.grid(row=22,column=5, columnspan=5,**options)
        self.closeButton.bind("<Button-1>", self.close)
        
        self.error = tk.StringVar()
        self.errorLabel = tk.Label(self,textvariable=self.error)
        self.errorLabel.grid(row=23,column=0,columnspan=10,sticky = 'NSEW',padx=3,pady=3)

    def close(self,event):
        self.destroy()

    def check(self,event):
        import os
        
        self.inp = self.inputPath.get()
        self.outp = self.outputPath.get()
        
        if not os.path.isdir(self.inp) or not os.path.isdir(self.outp):
            self.ready = False
            self.error.set('Input and Output have to be folders')
            return
        
        self.infiles  = eace.findFiles(self.inp,formats=eace.vformats)
        self.outfiles = eace.findFiles(self.outp,formats=eace.vformats)
            
        self.infiles = sorted(self.infiles)
        self.outfiles = sorted(self.outfiles)
        
        self.inputList.delete(0,tk.END)
        for i in self.infiles:
            self.inputList.insert(tk.END,i)

        self.outputList.delete(0,tk.END)
        for i in self.outfiles:
            self.outputList.insert(tk.END,i)
        
        self.ready = True
        self.error.set('')
        
    def encode(self,event):
        if self.ready:
            self.error.set('')
            self.infingerprints = []
            self.outfingerprints = []
            for i in self.infiles:
                self.infingerprints.append(eacc.get_video_descriptor(i))
            
            for i in self.outfiles:
                self.outfingerprints.append(eacc.get_video_descriptor(i))
                
            for i in self.infingerprints:
                for j in self.outfingerprints:
                    print eacc.compare_clips(i,j)
        else:
            self.error.set('first check the given input and output folder')
            return    
        
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
app.grid_columnconfigure(0,weight=1)
app.grid_rowconfigure(0,weight=1)
app.resizable(True,True)

app.mainloop()
