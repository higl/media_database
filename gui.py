import tkinter as tk
import tkinter.messagebox as tkMessageBox
import tkinter.filedialog as tkFileDialog
import media_database as mdb
import media_entry as me
import threading
import eac.encode as eace
import eac.compare as eacc
import pickle
import os
import numpy as np
import mdb_util
import stat
import sys
import shutil
encoding = sys.getfilesystemencoding()

class Application(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)
        self.last = None
        self.historyWindow = None
        self.infoWindow = None
        self.history = []
        self.media_database = None
        self.selectionList = []

        height = self.winfo_screenheight()
        self.call('tk', 'scaling', height/1080)

        self.grid()
        self.createWidgets()
        self.bindActions()
        self.protocol("WM_DELETE_WINDOW", self.onClose)

    def createWidgets(self):
        """
            creates all the widgets of the main window and places them in the grid

            in the codebase the widgets are separated in
                menu
                input
                primary tools
                database
                secondary tools
            which each have their own block in the grid
        """
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
        #self.linkButton = tk.Button(self, text='Link')
        #self.linkButton.grid(row=toolr+3,column=toolc+0,**options)
        self.forceUpdate = tk.IntVar()
        self.forceBox = tk.Checkbutton(self,
                                       text='force update',
                                       variable=self.forceUpdate)
        self.forceBox.grid(row=toolr+3,column=toolc+0,**options)
        self.loadExternal = tk.IntVar()
        self.loadExternalBox = tk.Checkbutton(self,
                                              text='load external',
                                              variable=self.loadExternal)
        self.loadExternalBox.grid(row=toolr+4,column=toolc+0,**options)
        self.legacyLoad = tk.IntVar()
        self.legacyLoadBox = tk.Checkbutton(self,
                                              text='legacy load',
                                              variable=self.legacyLoad)
        self.legacyLoadBox.grid(row=toolr+5,column=toolc+0,**options)
        self.singleMode = tk.IntVar()
        self.singleBox = tk.Checkbutton(self,text='single',variable=self.singleMode)
        self.singleBox.grid(row=toolr+6,column=toolc+0,**options)
        self.selectionMode = tk.IntVar()
        self.selectionBox = tk.Checkbutton(self,text='selected',variable=self.selectionMode)
        self.selectionBox.grid(row=toolr+7,column=toolc+0,**options)

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
        """
            binds the actions to the widgets that have functionality
        """
        self.loadButton.bind("<Button-1>", self.load)
        self.saveButton.bind("<Button-1>", self.save)
        #self.linkButton.bind("<Button-1>", self.linkFile)
        self.deleteButton.bind("<Button-1>", self.deleteFile)
        self.randomButton.bind("<Button-1>", self.randomFile)
        self.historyButton.bind("<Button-1>", self.displayHistory)
        self.selector.applyButton.bind("<Button-1>", self.displaySelection)
        self.dataBase.bind("<Double-Button-1>", self.displayInfo)
        self.dataBase.bind("<<ListboxSelect>>",self.updateInfoBox)

    def updateInfoBox(self,event):
        """
            updates the infobox with the currently selected media entry
        """
        e = self.getSelected()
        self.infobox.update(entry=e)

    def load(self,event):
        """
            load a database
        """
        path = self.filepath.get()

        if os.path.isfile(path):
            msg = "Select the parent directory of this database."
            parent = tkFileDialog.askdirectory(title=msg,initialdir= "./")
        elif os.path.isdir(path):
            if self.loadExternal.get():
                msg = 'Select the database.'
                parent = path
                path = tkFileDialog.askfile(title = msg,initialdir= "./")
            else:
                parent = path
                path = os.path.join(path,'mediadb.db')

        # legacy load will convert an old pickle file into the given database.
        # if the given database already agrees with the expected database structure
        # then legacy load will try to extend the given database with the data from
        # the pickle file
        self.media_database = mdb.media_database_sql(path,
                                                 parent,
                                                 force_update=self.forceUpdate.get(),
                                                 legacy_load=self.legacyLoad.get()
                                                )

        self.dataBase.delete(0,tk.END)
        self.selectionList = self.media_database.get_selection()
        for i in self.selectionList:
            self.dataBase.insert(tk.END,i)
        self.selector.update()

    def save(self,event):
        """
            save the database
        """

    def linkFile(self,event):
        id = self.dataBase.get(tk.ACTIVE)
        try:
            entry = self.media_database.find_entry(id)
            #open dialog to find destination of link
        #    os.link()
        except:
            print("error")
            #open dialog with file not found

    def deleteFile(self,event):
        """
            delete a database entry from disk
        """
        e = self.getSelected()
        if e != None and tkMessageBox.askokcancel("Delete",
            "This will erase " + e.get_display_string() + " from the harddisk! Continue?"):
            e.delete()
            self.media_database.delete_entry(e)

    def randomFile(self,event):
        """
            execute a random file from the database. If selectionList = True,
            only the currently selected elements from the database will be considered
        """
        if self.selectionMode.get():
            self.last = self.media_database.get_random_entry(selection=self.selectionList)
        else:
            singleMode = self.singleMode.get()
            self.last = self.media_database.get_random_entry(single=singleMode)
            if singleMode and self.last != None:
                self.last.set_played(True)
                self.media_database.update_entry(self.last)

        if self.last == None:
            print('WARNING: the selection was empty')
            return
        self.infobox.update(entry=self.last)
        self.history.append(self.last)
        if self.historyWindow != None:
            self.historyWindow.fillBox()
        t = threading.Thread(target=self.last.execute)
        t.setDaemon(True)
        t.start()

    def displayHistory(self,event):
        """
            show the history of executed files
        """
        if self.historyWindow != None:
            self.historyWindow.destroy()
            self.historyWindow = None
        else:
            self.historyWindow = HistoryWindow(self,self.history)
            self.after(50,self.checkHistoryWindow)


    def displayInfo(self,event):
        """
            display an info window
        """

        e = self.getSelected()
        if e != None:
            self.createInfoWindow(e)

    def statistics_window(self):
        """
            show statistics window
        """
        attrib = self.media_database.get_attrib_stat()
        count = self.media_database.get_entry_count()
        StatisticsWindow(self,attrib,count)

    def encode_window(self):
        """
            show encode window
        """
        EncodeWindow(self)

    def compare_window(self):
        """
            show compare window
        """
        CompareWindow(self)

    def getSelected(self):
        """
            returns the currently selected database entry
        """

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
        """
            show info window
        """
        if self.infoWindow != None:
            self.checkInfoStatus(cont=False)
            self.infoWindow.updateWindow(e)
        else:
            self.infoWindow = InfoWindow(self,e)
            self.after(50,self.checkInfoStatus)

    def displaySelection(self,event):
        """
            event to handle filtering of database entries
        """
        self.fillSelection()

    def fillSelection(self):
        """
            only show filtered database entries
        """
        args = self.selector.getArgs()

        self.dataBase.delete(0,tk.END)
        if self.media_database == None:
            return
        else:
            self.selectionList = self.media_database.get_selection(**args)
            for i in self.selectionList:
                self.dataBase.insert(tk.END,i)

    def checkHistoryWindow(self):
        """
            check status of history window.
            If it does not exist anymore, remove it from the main window
        """
        try:
            if self.historyWindow != None:
                self.historyWindow.state()
                self.after(50,self.checkHistoryWindow)
        except tk.TclError:
            self.historyWindow = None


    def checkInfoStatus(self,cont=True):
        """
            check status of info window
            - If the window does not exist anymore, remove it from the main window
            - if a media entry has been updated or deleted,
            update the list and mark the database as changed
            - if the media entry has been played, add it to the history
        """
        try:
            self.infoWindow.state()
            s = self.infoWindow.checkStatus()
            if s == 'normal':
                pass
            elif s == 'update':
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
            elif s == 'played':
                self.history.append(self.infoWindow.entry)
                if self.historyWindow != None:
                    self.historyWindow.fillBox()
                self.infoWindow.resetStatus()
            if cont:
                self.after(50,self.checkInfoStatus)
        except tk.TclError:
            self.infoWindow = None

    def onClose(self):
        """
            clean up before closing the app.
        """
        self.destroy()

class SelectorFrame(tk.Frame):
    """
        a selector frame shows different options to filter the database
        it automatically determines these options from the database
    """
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.grid()
        if master == None or master.media_database == None:
            self.attribs = ['attribute 1','attribute 2','attribute 3','attribute 4']
        else:
            self.attribs = self.master.media_database.get_attribute_list(                   common=True,
                               special=True,
                               global_atr=True
                            )
            if len(self.attribs) < 4:
                att = ['-','-','-','-']
                att[:len(self.attribs)-1] = self.attribs[:]
                self.attribs = att

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
        """
            returns the currently selected arguments
            and the respective entries in the text fields
        """
        args = {}
        for e,i in enumerate(self.LabelList):
            var = self.VarList[e].get()
            uString = self.EntryList[e].get()
            #uString = mdb_util.updateString(uString)
            if var == '-' or len(uString) == 0:
                continue
            args[var] = uString
        return args

    def update(self):
        """
            gets the list of possible selector arguments from the current media database
            and updates the display within in the frame
        """
        self.clearLists()
        if self.master == None or self.master.media_database == None:
            self.attribs = ['attribute 1','attribute 2','attribute 3','attribute 4']
        else:
            self.attribs = self.master.media_database.get_attribute_list(
                            common=True,
                            special=True,
                            global_atr=True
                           )
            self.attribs.append('-')
            if len(self.attribs) < 4:
                att = ['-','-','-','-']
                att[:len(self.attribs)-1] = self.attribs[:]
                self.attribs = att

        self.LabelList = []
        self.EntryList = []
        self.VarList = []
        self.createSelectors()

    def clearLists(self):
        """
            destroy the old entries of the frame
        """
        for l in self.LabelList:
            l.destroy()
        for l in self.EntryList:
            l.destroy()

class InfoFrame(tk.Frame):
    """
        InfoFrame shows the info of the currently selected
        database element within the main window
    """
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
        """
            update the info with a new entry
            or removes the old one if no entry is submitted

            entry infos are displayed according to their attributes,
            whereas the elements are placed automatically
        """
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

            nentry = len(list(e.attrib.keys()))
            if nentry <= 6:
                r = 2
                c = 0
                for i in list(e.attrib.keys()):
                    nLabel = tk.Label(self,text=i)
                    nLabel.grid(row=r,column=c)
                    self.LabelList.append(nLabel)

                    slist = [str(w) for w in e.attrib[i]]
                    eString = mdb_util.displayString(slist)
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
                for i in list(e.attrib.keys()):
                    newVar = tk.StringVar(self)
                    newVar.set(i)
                    newLabel = tk.OptionMenu(self,newVar,*list(e.attrib.keys()),command=self.updateEntry)
                    newLabel.grid(row=r,column=c,**options)

                    slist = [str(w) for w in e.attrib[i]]
                    eString = mdb_util.displayString(slist)
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
        """
            update the current entry - not used
        """
        w = event.widget
        i = self.LabelList.index(w)
        self.EntryList[i].delete(0,tk.END)
        a = self.VarList[i].get()
        slist = [str(w) for w in self.entry.attrib[i]]
        eString = mdb_util.displayString(slist)
        self.EntryList[i].insert(0,eString)

    def clearLists(self):
        for l in self.LabelList:
            l.destroy()
        for l in self.EntryList:
            l.destroy()
        self.VarList = []


    def displayInfo(self,event):
        """
            open a separate info window with extra info
        """
        if self.entry == None:
            e = self.master.getSelected()
        else:
            e = self.entry

        if e != None:
            self.master.createInfoWindow(e)


class HistoryWindow(tk.Toplevel):
    """
        history window is a separate window that lists
        the executed database entries
    """
    def __init__(self,master,history,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.history = history
        self.grid()
        x = master.winfo_rootx()
        y = master.winfo_rooty()
        height = master.winfo_height()
        width = master.winfo_width()
        geom = "+%d+%d" % (x,y+height*1.01)
        self.geometry( geom )
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
        """
            displays the history list in the list box
        """
        self.historyList.delete(0,tk.END)
        for i in self.history:
            self.historyList.insert(0,i.get_display_string())

    def displayInfo(self,event):
        """
            open a Info Window with the selected entry
        """
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
    """
        a separate Info Window
    """
    def __init__(self,master,entry,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.status = 'normal'
        self.entry = entry
        self.grid()
        x = master.winfo_rootx()
        y = master.winfo_rooty()
        height = master.winfo_height()
        width = master.winfo_width()
        geom = "+%d+%d" % (x+width*1.01,y+height*1.01)
        self.geometry( geom )
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
            creates and fills widgets that display the attributes of the media entry

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
        for i in list(self.entry.attrib.keys()):
            nLabel = tk.Label(self,text=i)
            nLabel.grid(row=r,column=1)
            self.LabelList.append(nLabel)

            slist = [str(w) for w in self.entry.attrib[i]]
            eString = mdb_util.displayString(slist)
            nEntry = tk.Entry(self)
            nEntry.insert(0,eString)
            nEntry.grid(row=r,column=2,columnspan=5)
            self.EntryList.append(nEntry)
            r = r+1


    def clearWindow(self):
        """
            removes all the widgets needed to
            display the current media entry
        """
        list = self.grid_slaves()
        for l in list:
            l.destroy()

    def playFile(self,event):
        """
            execute the media entry in a separate thread
        """
        t = threading.Thread(target=self.entry.execute)
        t.setDaemon(True)
        t.start()
        self.status = 'played'

    def updateWindow(self,entry=None):
        """
            exchange the current media entry with a new one
            checks if the current one has been modified first and warns accordingly
        """
        if self.changedInfo()[0]:
            if tkMessageBox.askokcancel("Update Info","Entries have been updated. Do you want to save first?"):
                self.updateEntry()
        if entry != None:
            self.entry = entry
        self.fillInfo()

    def updateEntryEvent(self,event):
        self.updateEntry()

    def updateEntry(self):
        """
            update the attribute entries in the current media entry
        """

        changed, attrib = self.changedInfo()

        if changed:
            self.entry.update_attrib(**attrib)
            db = self.master.media_database
            db.update_entry(self.entry,update_attrib=True)
            self.status = 'update'

    def delete(self,event):
        """
            delete the current media entry FROM DISK!
        """
        if tkMessageBox.askokcancel("Delete",
            "This will erase " + self.entry.get_display_string() + " from the harddisk! Continue?"):
            self.entry.delete()
            self.status = 'deleted'
        else:
            return

    def changedInfo(self):
        """
            checks if the attribute entries have been
            changed from the stored values
        """
        attrib = {}
        for e,i in enumerate(self.LabelList):
            name = i.cget('text')
            uString = self.EntryList[e].get()
            uString = mdb_util.updateString(uString)
            if len(self.entry.attrib[name])>0:
                ttype = type(self.entry.attrib[name][0])
                uString = [ttype(w) for w in uString]
            attrib[name] = uString
            if len(uString) == 0:
                continue
        match = self.entry.match_selection(ignore_empty=False,
                                           crossmatch=True,**attrib)
        return not match, attrib


    def checkStatus(self):
        return self.status

    def resetStatus(self):
        self.status = 'normal'

    def close(self,event):
        self.destroy()

    def link(self,event):
        print('zelda is not link')

class StatisticsWindow(tk.Toplevel):
    """
        A window that displays a selection of Statistics about
        the attributes of the current media database
    """

    def __init__(self,master,attrib,count,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.attrib = attrib
        self.count = count
        self.grid()
        x = master.winfo_rootx()
        y = master.winfo_rooty()
        height = master.winfo_height()
        width = master.winfo_width()
        geom = "+%d+%d" % (x+width*1.01,y)
        self.geometry( geom )
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


        self.statList = tk.Listbox(self,width=25)
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
        """
            Fills the list of attributes in the selection box
        """
        for i in list(self.attrib.keys()):
            self.attribList.insert(tk.END,i)

    def displayStat(self,event):
        """
            Displays the statistics about the currently selected attribute
        """
        s = self.attribList.curselection()
        s = list(self.attrib.keys())[s[0]]
        results = self.attrib[s]

        self.statList.delete(0,tk.END)
        for i in results:
            self.statList.insert(tk.END,'{:<25}{:>5}'.format(i[0],str(i[1])))


class EncodeWindow(tk.Toplevel):
    """
        A window that allow to encode video files in a folder and store them in a different folder.

    """
    def __init__(self,master,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.ready = False
        self.thread = None
        self.result = {}
        self.grid()
        x = master.winfo_rootx()
        y = master.winfo_rooty()
        height = master.winfo_height()
        width = master.winfo_width()
        geom = "+%d+%d" % (x+width*1.01,y)
        self.geometry( geom )
        self.createWidgets()
        self.abort = False
        self.protocol("WM_DELETE_WINDOW", self.onClose)

    def createWidgets(self):
        options = {'sticky':'NSEW','padx':3,'pady':3}


        self.error = tk.StringVar()
        self.errorLabel = tk.Label(self,textvariable=self.error)
        self.errorLabel.grid(row=0,column=0,columnspan=8,**options)

        #input, output
        rio = 1
        cio = 0

        self.inputLabel = tk.Label(self,text='Input')
        self.inputLabel.grid(row=rio,column=cio,columnspan=3,**options)
        self.inputPath = tk.Entry(self)
        self.inputPath.grid(row=rio+1,column=cio,columnspan=3,**options)
        self.outputLabel = tk.Label(self,text='Output')
        self.outputLabel.grid(row=rio,column=cio+3,columnspan=3,**options)
        self.outputPath = tk.Entry(self)
        self.outputPath.grid(row=rio+1,column=cio+3,columnspan=3,**options)

        self.inputList = tk.Listbox(self)
        self.inputList.grid(row=rio+2,column=cio,rowspan=20,columnspan=2,**options)
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=rio+2,column=cio+2,rowspan=20,sticky='NSW')
        scrollbar.config(command=self.inputList.yview)
        self.inputList.config(yscrollcommand=scrollbar.set)

        self.outputList = tk.Listbox(self,selectmode=tk.MULTIPLE)
        self.outputList.grid(row=rio+2,column=cio+3,rowspan=20,columnspan=2,**options)
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=rio+2,column=cio+3+2,rowspan=20,sticky='NSW')
        scrollbar.config(command=self.outputList.yview)
        self.outputList.config(yscrollcommand=scrollbar.set)


        self.checkpButton = tk.Button(self,text='Check Paths')
        self.checkpButton.grid(row=rio+23,column=cio,columnspan=2,**options)
        self.checkpButton.bind("<Button-1>", self.check_paths)

        self.compareButton = tk.Button(self,text='Encode')
        self.compareButton.grid(row=rio+23,column=cio+3, columnspan=2,**options)
        self.compareButton.bind("<Button-1>", self.encode)

        self.checkeButton = tk.Button(self,text='Check Encode')
        self.checkeButton.grid(row=rio+24,column=cio,columnspan=2,**options)
        self.checkeButton.bind("<Button-1>", self.check_encode)

        self.finalizeButton = tk.Button(self,text='Finalize All')
        self.finalizeButton.grid(row=rio+24,column=cio+3, columnspan=2,**options)
        self.finalizeButton.bind("<Button-1>", self.finalize_all)


        #options block
        orow = 1
        ocol = 7

        self.optionLabel = tk.Label(self,text='Options:')
        self.optionLabel.grid(row=orow,column=ocol,columnspan=2,**options)

        self.encoderLabel = tk.Label(self,text='encoder')
        self.encoderLabel.grid(row=orow+1,column=ocol,columnspan=1,**options)
        self.encoderEntry = tk.Entry(self)
        self.encoderEntry.grid(row=orow+1,column=ocol+1,columnspan=1,**options)
        self.encoderEntry.insert(tk.END,'ffmpeg')

        self.qualityLabel = tk.Label(self,text='quality')
        self.qualityLabel.grid(row=orow+2,column=ocol,columnspan=1,**options)
        self.qualityEntry = tk.Entry(self)
        self.qualityEntry.grid(row=orow+2,column=ocol+1,columnspan=1,**options)
        self.qualityEntry.insert(tk.END,'low')

        self.procLabel = tk.Label(self,text='processors')
        self.procLabel.grid(row=orow+3,column=ocol,columnspan=1,**options)
        self.procEntry = tk.Entry(self)
        self.procEntry.grid(row=orow+4,column=ocol+1,columnspan=1,**options)
        self.procEntry.insert(0,'4')

        self.override = tk.IntVar()
        self.overrideBox = tk.Checkbutton(self,text='override',variable=self.override)
        self.overrideBox.grid(row=orow+4,column=ocol,columnspan=2,**options)

        self.extend = tk.IntVar()
        self.extendBox = tk.Checkbutton(self,text='extend filenames',variable=self.extend)
        self.extendBox.grid(row=orow+5,column=ocol,columnspan=2,**options)
        self.extendBox.select()

        self.abortButton = tk.Button(self,text='Abort')
        self.abortButton.grid(row=orow+6,column=ocol, columnspan=2,**options)
        self.abortButton.bind("<Button-1>", self.abort_thread)

        self.emptyButton = tk.Button(self,text='Rm empty folders')
        self.emptyButton.grid(row=orow+7,column=ocol, columnspan=2,**options)
        self.emptyButton.bind("<Button-1>", self.rm_empty_folders)

        self.mergeButton = tk.Button(self,text='Merge Output Videos')
        self.mergeButton.grid(row=orow+8,column=ocol, columnspan=2,**options)
        self.mergeButton.bind("<Button-1>", self.merge_videos)

        self.closeButton = tk.Button(self,text='Close')
        self.closeButton.grid(row=orow+24,column=ocol, columnspan=2,**options)
        self.closeButton.bind("<Button-1>", self.close)


    def close(self,event):
        self.destroy()

    def merge_videos(self,event):
        """
            merge the selected video files from the output
            list into a single file
        """
        selected = self.getSelected(list=self.outputList)
        encoder = self.encoderEntry.get()

        notfound = np.ones(len(selected))
        for i in list(self.result.keys()):
            for e,j in enumerate(selected):
                if j == self.result[i]:
                    notfound[e] = 0

        if any(notfound):
            out = eace.merge_videos(selected,self.outp,remove=True,encoder=encoder)
        else:
            self.error.set('WARNING: Not finalized files selected, please delete merged files manually')
            out = eace.merge_videos(selected,self.outp,remove=False,encoder=encoder)

        self.outputList.insert(tk.END,out)

    def rm_empty_folders(self,event):
        """
            removes alls empty folders in the input and output directories
        """
        mdb_util.rm_empty_folders(self.inp)
        mdb_util.rm_empty_folders(self.outp)

    def check_paths(self,event):
        self.update(load=True)

    def update(self,load=False,remove=None):
        """
            finds all video files in the input and output directories
            and displays them in the respective list boxes

            also loads a result file that matches original to encoded
            video files from previous runs on the same directories
        """
        self.inp = os.path.normpath(self.inputPath.get())
        self.outp = os.path.normpath(self.outputPath.get())

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

        self.resultfile = str(hash(self.inp) + hash(self.outp))+'.encode'

        if load:
            if os.path.isfile(self.resultfile) and not self.override.get():
                with open(self.resultfile, 'rb') as input:
                    self.result = pickle.load(input)
            else:
                self.result = {}
        if remove != None:
            self.result.pop(remove)
            with open(self.resultfile, 'wb') as output:
                pickle.dump(self.result, output, pickle.HIGHEST_PROTOCOL)

        self.ready = True
        self.error.set('')


    def check_encode(self,event):
        """
            open a new window that allows you to check the outcome of the encoding

            it either uses the selected video or the next video file in the result dictionary
        """
        s = self.getSelected(list=self.inputList)
        if len(s) > 0:
            for i in s:
                if i in self.result:
                    self.CheckWindow = CheckWindow(i,self.result[i],result=self.result,master=self)
                    return
            self.error.set('cannot check result for this entry (no result available)')
        else:
            #we take the first element in the input listbox
            if len(list(self.result.keys())) > 0:
                s = list(self.result.keys())[0]
                self.CheckWindow = CheckWindow(s,self.result[s],result=self.result,master=self)
            else:
                self.error.set('cannot check result (no results available')

    def getSelected(self,list=None):
        """
            return all selected elements of a listbox
        """
        if list != None:
            s = list.curselection()
        else:
            return []
        value = []
        for i in s:
            value.append(list.get(i))
        return value

    def finalize_all(self,event):
        """
            finalizes all encoded videos in the result dictionary.
            this means:
                we compare the file sizes of original and encoded video.
                We will select the smaller one and move it to the output folder.
                The remaining file will be deleted from disk.
        """
        if tkMessageBox.askokcancel("Do you really want to finalize all results?"):
            for i in list(self.result.keys()):
                if os.path.getsize(i) > os.path.getsize(self.result[i]):
                    try:
                        os.remove(i)
                    except:
                        os.chmod(i, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO)
                        os.remove(i)
                else:
                    os.remove(self.result[i])
                    try:
                        shutil.move(i,self.result[i])
                    except:
                        os.chmod(i, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO)
                        shutil.move(i,self.result[i])

                self.result.pop(i)

            with open(self.resultfile, 'wb') as output:
                pickle.dump(self.result, output, pickle.HIGHEST_PROTOCOL)
            self.update()
        else:
            return


    def encode(self,event):
        """
            the event handler that creates a thread to start encoding
        """
        if self.thread != None and self.thread.is_alive():
            return
        else:
            if self.ready:
                self.error.set('')
                kwargs = {}
                kwargs['encoder'] = self.encoderEntry.get()
                kwargs['quality'] = self.qualityEntry.get()
                kwargs['processes'] = self.procEntry.get()
                kwargs['override'] = self.extend.get()

                self.thread = eace.encode_thread(
                                self.infiles,self.outp,
                                self.result,self.resultfile,
                                **kwargs
                                )
                self.thread.setDaemon(True)
                self.thread.start()
                self.after(1000,self.checkEncodeThread)
                return
            else:
                self.error.set(
                    'first check the given input and output folder'
                    )
                return

    def checkEncodeThread(self):
        """
            check status of encode thread.
            updates the local copy of the thread results if necessary
        """
        if self.thread is not None and self.thread.is_alive():
            self.thread.self_lock.acquire()
            if self.thread.update:
                self.result = self.thread.result
                self.thread.update = False
            self.thread.self_lock.release()
            self.after(1000,self.checkEncodeThread)
        else:
            return

    def abort_thread(self,event):
        """
            checks if an encoding thread is running and if so, sends a signal
            to it that forces it to abort after the next encode finishes
        """
        if self.thread != None and self.thread.is_alive():
            self.thread.self_lock.acquire()
            self.thread.abort = True
            self.thread.self_lock.release()
        return

    def onClose(self):
        """
            make sure that we do not close this window with a running encode thread.
            wait for it to abort first
        """
        if self.thread != None and self.thread.is_alive():
            self.abort = True
            self.thread.join()
            self.destroy()
        else:
            self.destroy()
        return

class CheckWindow(tk.Toplevel):
    """
        a window that allows to compare two video files
        and take further actions (keep one or the other, manipulate result)
    """
    def __init__(self,input,output,master=None,result=None,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.input = input
        self.inputE = me.video_entry(input)
        self.output = output
        self.outputE = me.video_entry(output)
        self.grid()
        x = master.winfo_rootx()
        y = master.winfo_rooty()
        height = master.winfo_height()
        geom = "+%d+%d" % (x,y+height)
        self.geometry( geom )
        self.createWidgets()

    def createWidgets(self):
        #menu creation
        menubar = tk.Menu(self)

        # create a pulldown menu, and add it to the menu bar
        toolmenu = tk.Menu(menubar, tearoff=0)
        toolmenu.add_command(label="Cut", command=self.cutWindow)
        toolmenu.add_separator()
        menubar.add_cascade(label="Tools", menu=toolmenu)

        # display the menu
        self.config(menu=menubar)


        options = {'sticky':'NSEW','padx':3,'pady':3}

        self.watchqButton = tk.Button(self,text='Watch Input')
        self.watchqButton.grid(row=0,column=0,columnspan=2,**options)
        self.watchqButton.bind("<Button-1>", self.watchInput)

        self.watchsButton = tk.Button(self,text='Watch Output')
        self.watchsButton.grid(row=0,column=3,columnspan=2,**options)
        self.watchsButton.bind("<Button-1>", self.watchOutput)


        self.rejectButton = tk.Button(self,text='Reject')
        self.rejectButton.grid(row=1,column=0,columnspan=2,**options)
        self.rejectButton.bind("<Button-1>", self.reject)

        self.finalizeButton = tk.Button(self,text='Finalize')
        self.finalizeButton.grid(row=1,column=3,columnspan=2,**options)
        self.finalizeButton.bind("<Button-1>", self.finalize)

    def cutWindow(self):
        """
            opens a window to cut the output video into smaller pieces
        """
        CutWindow(self.input,self.output,master=self.master)

    def watchInput(self,event):
        """
            watch the input video (opens a separate thread)
        """
        t = threading.Thread(target=self.inputE.execute)
        t.setDaemon(True)
        t.start()

    def watchOutput(self,event):
        """
            watch the output video (opens a separate thread)
        """
        t = threading.Thread(target=self.outputE.execute)
        t.setDaemon(True)
        t.start()

    def reject(self,event):
        """
            we reject the produced output -> delete the output and remove the entry from the result dictionary
        """
        if tkMessageBox.askokcancel("Delete",
            "This will erase " + self.outputE.get_display_string() + " from the harddisk! Continue?"):
            os.remove(self.output)
            self.master.update(remove = self.input)
            self.destroy()
        else:
            return

    def finalize(self,event):
        """
            we finalize produced output:
                we compare the file sizes of original and encoded video.
                We will select the smaller one and move it to the output folder.
                The remaining file will be deleted from disk.
        """
        if tkMessageBox.askokcancel("Finalize","Do you want to finalize "+ self.input+ " ?"):
            if os.path.getsize(self.input) > os.path.getsize(self.output):
                try:
                    os.remove(self.input)
                except:
                    os.chmod(self.input, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO)
                    os.remove(self.input)
            else:
                os.remove(self.output)
                try:
                    shutil.move(self.input,self.output)
                except:
                    os.chmod(self.input, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO)
                    shutil.move(self.input,self.output)

            self.master.update(remove = self.input)
            self.destroy()
        else:
            return

class CutWindow(tk.Toplevel):
    """
        window that allows to cut a video into smaller pieces
    """
    def __init__(self,input,output,master=None,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.input = input
        self.output = output
        self.grid()
        x = master.winfo_rootx()
        y = master.winfo_rooty()
        height = master.winfo_height()
        geom = "+%d+%d" % (x,y+height)
        self.geometry( geom )
        self.createWidgets()

    def createWidgets(self):
        options = {'sticky':'NSEW','padx':3,'pady':3}

        self.hLabel = tk.Label(self,text='h')
        self.hLabel.grid(row=0,column=0,columnspan=1,**options)
        self.mLabel = tk.Label(self,text='m')
        self.mLabel.grid(row=0,column=1,columnspan=1,**options)
        self.sLabel = tk.Label(self,text='s')
        self.sLabel.grid(row=0,column=2,columnspan=1,**options)

        self.cutList = []
        self.cutList.append(CutElement(self))
        self.cutList[-1].grid(row=len(self.cutList)+1,column=0,columnspan=4,rowspan=1,**options)


        self.addButton = tk.Button(self,text='Add Cut')
        self.addButton.grid(row=0,column=4,columnspan=2,**options)
        self.addButton.bind("<Button-1>", self.addCutElement)

        self.removeButton = tk.Button(self,text='Remove Cut')
        self.removeButton.grid(row=1,column=4,columnspan=2,**options)
        self.removeButton.bind("<Button-1>", self.removeCutElement)

        self.cutButton = tk.Button(self,text='Cut')
        self.cutButton.grid(row=2,column=4,columnspan=2,**options)
        self.cutButton.bind("<Button-1>", self.cut)


    def cut(self,event):
        """
            does the cutting
        """
        cuts = np.zeros(len(self.cutList)+1)
        length = np.zeros(len(self.cutList))

        for e,i in enumerate(self.cutList):
            cuts[e+1] = i.getSeconds()
            length[e] = cuts[e+1] - cuts[e]
        for e,i in enumerate(length):
            eace.cut_video(self.output,os.path.dirname(self.output),cuts[e],i,override=True)

        eace.cut_video(self.output,os.path.dirname(self.output),cuts[-1],0,override=True)

    def addCutElement(self,event):
        """
            adds another empty cut point to the window. This allows to cut the video in one more place
        """
        options = {'sticky':'NSEW','padx':3,'pady':3}
        self.cutList.append(CutElement(self))
        self.cutList[-1].grid(row=len(self.cutList)+1,column=0,columnspan=4,rowspan=1,**options)

    def removeCutElement(self,event):
        """
            removes a cut point from the window.
        """
        self.cutList.pop().destroy()

class CutElement(tk.Frame):
    """
        a cut element allows to enter the timestamp of a cut point for the cutwindow
    """
    def __init__(self,master):
        tk.Frame.__init__(self,master)
        self.grid()
        self.createWidgets()

    def createWidgets(self):
        options = {'sticky':'NSEW','padx':3,'pady':3}

        self.hEntry = tk.Entry(self)
        self.hEntry.grid(row=0,column=0,columnspan=1,**options)
        self.hEntry.insert(0,'0')
        self.mEntry = tk.Entry(self)
        self.mEntry.grid(row=0,column=1,columnspan=1,**options)
        self.mEntry.insert(0,'0')
        self.sEntry = tk.Entry(self)
        self.sEntry.grid(row=0,column=2,columnspan=1,**options)
        self.sEntry.insert(0,'0')

    def getSeconds(self):
        """
            returns the timestamp of the cut in seconds
        """
        h = self.hEntry.get()
        m = self.mEntry.get()
        s = self.sEntry.get()

        try:
            sec = int(h) * 3600
            sec = sec + int(m) * 60
            sec = sec + float(s)
            sec = round(sec,3)
            return sec
        except:
            return None

class CompareWindow(tk.Toplevel):
    """
        The CompareWindow allows to find duplicate videos,
        by creating a fingerprint file of each video file
        and then comparing these, using the eac module
    """
    def __init__(self,master,*args,**kwargs):
        tk.Toplevel.__init__(self,master=master,*args,**kwargs)
        self.ready = False
        self.thread = None
        self.abort = False
        self.grid()
        x = master.winfo_rootx()
        y = master.winfo_rooty()
        height = master.winfo_height()
        width = master.winfo_width()
        geom = "+%d+%d" % (x+width*1.01,y)
        self.geometry( geom )
        self.createWidgets()
        self.protocol("WM_DELETE_WINDOW", self.onClose)

    def createWidgets(self):
        options = {'sticky':'NSEW','padx':3,'pady':3}


        self.error = tk.StringVar()
        self.errorLabel = tk.Label(self,textvariable=self.error)
        self.errorLabel.grid(row=0,column=0,columnspan=8,**options)

        #input, output
        rio = 1
        cio = 0

        self.inputLabel = tk.Label(self,text='Querry')
        self.inputLabel.grid(row=rio,column=cio,columnspan=3,**options)
        self.inputPath = tk.Entry(self)
        self.inputPath.grid(row=rio+1,column=cio,columnspan=3,**options)
        self.outputLabel = tk.Label(self,text='Source')
        self.outputLabel.grid(row=rio,column=cio+3,columnspan=3,**options)
        self.outputPath = tk.Entry(self)
        self.outputPath.grid(row=rio+1,column=cio+3,columnspan=3,**options)

        self.querrysource = tk.IntVar()
        self.qsBox = tk.Checkbutton(self,text='Querry = Source',variable=self.querrysource,command=self.enable_disable)
        self.qsBox.grid(row=rio+2,column=cio,**options)

        self.sourcedb = tk.IntVar()
        self.sdbBox = tk.Checkbutton(self,text='Source = media db',variable=self.sourcedb,command=self.enable_disable)
        self.sdbBox.grid(row=rio+2,column=cio+3,**options)

        self.inputList = tk.Listbox(self)
        self.inputList.grid(row=rio+3,column=cio,rowspan=20,columnspan=2,**options)
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=rio+3,column=cio+2,rowspan=20,sticky='NSW')
        scrollbar.config(command=self.inputList.yview)
        self.inputList.config(yscrollcommand=scrollbar.set)

        self.outputList = tk.Listbox(self)
        self.outputList.grid(row=rio+3,column=cio+3,rowspan=20,columnspan=2,**options)
        scrollbar = tk.Scrollbar(self)
        scrollbar.grid(row=rio+3,column=cio+3+2,rowspan=20,sticky='NSW')
        scrollbar.config(command=self.outputList.yview)
        self.outputList.config(yscrollcommand=scrollbar.set)


        self.checkButton = tk.Button(self,text='Check')
        self.checkButton.grid(row=rio+23,column=cio,columnspan=2,**options)
        self.checkButton.bind("<Button-1>", self.check)

        self.compareButton = tk.Button(self,text='Compare')
        self.compareButton.grid(row=rio+23,column=cio+3, columnspan=2,**options)
        self.compareButton.bind("<Button-1>", self.compare)

        #options block
        orow = 1
        ocol = 7

        self.optionLabel = tk.Label(self,text='Options:')
        self.optionLabel.grid(row=orow,column=ocol,columnspan=2,**options)

        self.fpsLabel = tk.Label(self,text='nfps')
        self.fpsLabel.grid(row=orow+1,column=ocol,columnspan=1,**options)
        self.fpsEntry = tk.Entry(self)
        self.fpsEntry.grid(row=orow+1,column=ocol+1,columnspan=1,**options)
        self.fpsEntry.insert(tk.END,'3')

        self.nsecLabel = tk.Label(self,text='nseconds')
        self.nsecLabel.grid(row=orow+2,column=ocol,columnspan=1,**options)
        self.nsecEntry = tk.Entry(self)
        self.nsecEntry.grid(row=orow+2,column=ocol+1,columnspan=1,**options)
        self.nsecEntry.insert(tk.END,'60')

        self.qualityLabel = tk.Label(self,text='quality')
        self.qualityLabel.grid(row=orow+3,column=ocol,columnspan=1,**options)
        self.qualityEntry = tk.Entry(self)
        self.qualityEntry.grid(row=orow+3,column=ocol+1,columnspan=1,**options)
        self.qualityEntry.insert(tk.END,'320x640')

        self.procLabel = tk.Label(self,text='processors')
        self.procLabel.grid(row=orow+4,column=ocol,columnspan=1,**options)
        self.procEntry = tk.Entry(self)
        self.procEntry.grid(row=orow+4,column=ocol+1,columnspan=1,**options)
        self.procEntry.insert(tk.END,'1')

        self.crossCheck = tk.IntVar()
        self.crossCheckBox = tk.Checkbutton(self,text='cross check',variable=self.crossCheck)
        self.crossCheckBox.grid(row=orow+5,column=ocol,columnspan=2,**options)

        self.override = tk.IntVar()
        self.overrideBox = tk.Checkbutton(self,text='override',variable=self.override)
        self.overrideBox.grid(row=orow+6,column=ocol,columnspan=2,**options)

        self.pmode = tk.IntVar()
        self.pmodeBox = tk.Checkbutton(self,text='picture mode',variable=self.pmode)
        self.pmodeBox.grid(row=orow+7,column=ocol,columnspan=2,**options)

        self.renameascii = tk.IntVar()
        self.renameasciiBox = tk.Checkbutton(self,text='rename to ascii',variable=self.renameascii)
        self.renameasciiBox.grid(row=orow+8,column=ocol,columnspan=2,**options)

        self.abortButton = tk.Button(self,text='Abort')
        self.abortButton.grid(row=orow+23,column=ocol, columnspan=2,**options)
        self.abortButton.bind("<Button-1>", self.abort_thread)

        # result block
        rrow = 25
        rcol = 0

        self.resultLabel = tk.Label(self,text='Results:')
        self.resultLabel.grid(row=rrow,column=rcol,columnspan=1,**options)

        self.resultCounter = tk.StringVar()
        self.resultCountLabel = tk.Label(self,textvariable=self.resultCounter)
        self.resultCountLabel.grid(row=rrow+1,column=rcol,columnspan=1,**options)

        self.rquerryLabel = tk.Label(self,text='Querry path')
        self.rquerryLabel.grid(row=rrow+2,column=rcol,columnspan=2,**options)

        self.rinfoLabel = tk.Label(self,text='# or min / max(Score)')
        self.rinfoLabel.grid(row=rrow+2,column=rcol+3,columnspan=1,**options)

        self.rsourceLabel = tk.Label(self,text='Source path')
        self.rsourceLabel.grid(row=rrow+2,column=rcol+4,columnspan=2,**options)

        # create scrolled canvas

        vscrollbar = AutoScrollbar(self)
        vscrollbar.grid(row=rrow+3, column=rcol+6,rowspan=10, sticky='NSW')
        hscrollbar = AutoScrollbar(self, orient=tk.HORIZONTAL)
        hscrollbar.grid(row=rrow+14, column=rcol,columnspan=10, sticky='NSW')

        self.resultCanvas = tk.Canvas(self, yscrollcommand=vscrollbar.set, xscrollcommand=hscrollbar.set)
        self.resultCanvas.grid(row=rrow+3, column=rcol,rowspan=10,columnspan=5, **options)

        vscrollbar.config(command=self.resultCanvas.yview)
        hscrollbar.config(command=self.resultCanvas.xview)

        # make the canvas expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # create canvas contents
        self.resultframe = resultFrame(master=self.resultCanvas)
        self.resultframe.rowconfigure(1, weight=1)
        self.resultframe.columnconfigure(1, weight=1)

        self.resultCanvas.create_window(0, 0, anchor='nw', window=self.resultframe)
        self.resultframe.update_idletasks()
        self.resultCanvas.config(scrollregion=self.resultCanvas.bbox("all"))

        #result options block
        rorow = rrow
        rocol = rcol + 7

        self.optionLabel = tk.Label(self,text='Options:')
        self.optionLabel.grid(row=rorow,column=rocol,columnspan=2,**options)

        self.minScoreLabel = tk.Label(self,text='score min')
        self.minScoreLabel.grid(row=rorow+1,column=rocol,columnspan=1,**options)
        self.minScoreEntry = tk.Entry(self)
        self.minScoreEntry.grid(row=rorow+1,column=rocol+1,columnspan=1,**options)
        self.minScoreEntry.insert(tk.END,'90')

        self.maxScoreLabel = tk.Label(self,text='score max')
        self.maxScoreLabel.grid(row=rorow+2,column=rocol,columnspan=1,**options)
        self.maxScoreEntry = tk.Entry(self)
        self.maxScoreEntry.grid(row=rorow+2,column=rocol+1,columnspan=1,**options)
        self.maxScoreEntry.insert(tk.END,'100')

        self.minEntryLabel = tk.Label(self,text='# matches')
        self.minEntryLabel.grid(row=rorow+3,column=rocol,columnspan=1,**options)
        self.minEntry = tk.Entry(self)
        self.minEntry.grid(row=rorow+3,column=rocol+1,columnspan=1,**options)
        self.minEntry.insert(tk.END,'1')

        self.ignoreSelf = tk.IntVar()
        self.ignoreSelfBox = tk.Checkbutton(self,text='ignore self match',variable=self.ignoreSelf)
        self.ignoreSelfBox.grid(row=rorow+4,column=rocol,columnspan=2,**options)

        self.updateButton = tk.Button(self,text='update result')
        self.updateButton.grid(row = rorow+5,column=rocol,columnspan=2,**options)
        self.updateButton.bind("<Button-1>", self.update_result)

        self.addButton = tk.Button(self,text='add to db')
        self.addButton.grid(row = rorow+6,column=rocol,columnspan=2,**options)
        self.addButton.bind("<Button-1>", self.add_result)

        self.closeButton = tk.Button(self,text='Close')
        self.closeButton.grid(row=rorow+23,column=rocol, columnspan=2,**options)
        self.closeButton.bind("<Button-1>", self.close)

    def enable_disable(self):
        """
            enables or disables the output entry field,
            based on the options set
        """
        if self.sourcedb.get() or self.querrysource.get():
            self.outputPath.config(state='disabled')
        else:
            self.outputPath.config(state='normal')

    def close(self,event):
        self.destroy()

    def check(self,event):
        """
            checks the input and output folders for all video files
            and displays them in the respective listboxes
        """
        self.inp = os.path.normpath(self.inputPath.get())
        if self.querrysource.get():
            self.outp = self.inp
        elif self.sourcedb.get():
            self.outp = os.path.normpath(self.master.media_database.parent)
        else:
            self.outp = os.path.normpath(self.outputPath.get())

        if not os.path.isdir(self.inp) or not os.path.isdir(self.outp):
            self.ready = False
            self.error.set('Input and Output have to be folders')
            return

        if self.pmode.get():
            self.infiles  = eace.findFiles(self.inp,formats=eace.pformats,return_root=True)
            self.outfiles = eace.findFiles(self.outp,formats=eace.pformats,return_root=True)
        else:
            self.infiles  = eace.findFiles(self.inp,formats=eace.vformats)
            self.outfiles = eace.findFiles(self.outp,formats=eace.vformats)

        if self.renameascii.get():
            self.infiles = mdb_util.rename_to_ascii(self.infiles,recursive=self.pmode.get())
            self.outfiles = mdb_util.rename_to_ascii(self.outfiles,recursive=self.pmode.get())
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


    def compare(self,event):
        """
            event to start a thread that compares video files
        """
        if self.thread != None and self.thread.is_alive():
            return
        else:
            if self.ready:
                self.error.set('')
                kwargs = {}
                kwargs['quality'] = self.qualityEntry.get()
                kwargs['proc'] = self.procEntry.get()
                kwargs['fps'] = int(self.fpsEntry.get())
                kwargs['nsec'] = int(self.nsecEntry.get())
                kwargs['override'] = self.override.get()
                kwargs['querrysource'] = self.querrysource.get()
                kwargs['pmode'] = self.pmode.get()
                kwargs['crosscheck'] = self.crossCheck.get()
                res_file = str(hash(self.inp) + hash(self.outp))
                self.result = {}
                self.thread = eacc.compare_thread(
                                self.infiles,self.outfiles,
                                self.result,res_file,
                                **kwargs
                                )
                self.thread.setDaemon(True)
                self.thread.start()
                self.after(1000,self.checkCompareThread)
                return
            else:
                self.error.set(
                    'first check the given input and output folder'
                    )
                return

    def checkCompareThread(self):
        """
            check status of encode thread.
            updates the local copy of the thread results if necessary
        """
        if self.thread is not None and self.thread.is_alive():
            self.thread.self_lock.acquire()
            if self.thread.update:
                self.result = self.thread.result
                self.error.set(self.thread.message)
                self.thread.update = False
            self.thread.self_lock.release()
            self.after(1000,self.checkCompareThread)
        else:
            return

    def abort_thread(self,event):
        """
            checks if an encoding thread is running and if so, sends a signal
            to it that forces it to abort after the next encode finishes
        """
        if self.thread != None and self.thread.is_alive():
            self.thread.self_lock.acquire()
            self.thread.abort = True
            self.error.set(self.thread.message + '- abort requested')
            self.thread.self_lock.release()
        return

    def update_result(self,event):
        """
            display the results.
            Only shows results with a probability score between vmin and vmax
        """
        vmin = float(self.minScoreEntry.get())
        vmax = float(self.maxScoreEntry.get())
        nmin = float(self.minEntry.get())
        self.resultframe.update_widgets(self.result,
                vmin=vmin,vmax=vmax,nmin=nmin,
                ignoreSelf=self.ignoreSelf.get(),pmode=self.pmode.get())
        self.resultframe.update_idletasks()
        self.resultCanvas.config(scrollregion=self.resultCanvas.bbox("all"))


    def add_result(self,event):
        """
            when we compare with the current media database
            of the main window, then we can also create media entries from  the result files
            (hopefully clean of duplicates after we checked them) and add them to the media database

            this also includes moving the physical file on disk to the media database folder
        """
        if not self.sourcedb.get():
            self.error.set('results can only be added to the database, if they are compared to a database from the main window')
            return
        parent = os.path.normcase(self.master.media_database.parent)
        if self.inp in parent:
            self.error.set('the database cannot be part of the querry')
            return

        if tkMessageBox.askokcancel("Add to DB",
            "Do you really want to add all of the current result to the database? Any duplicate in there will also be copied!" ):

            for i in list(self.result.keys()):
                self.move_to_db(i,self.master.media_database)
                self.result.pop(i)

            res_file = str(hash(self.inp) + hash(self.outp))
            res_file = res_file + '.res'
            with open(res_file, 'wb') as output:
                pickle.dump(self.result, output, pickle.HIGHEST_PROTOCOL)

        else:
            return

    def move_to_db(self,fi,db):
        """
            does the physical data transfer from the output folder to the media database folder
            has to take care of too long filenames
        """
        pmode = self.pmode.get()

        destination = db.parent
        pmode = self.pmode.get()
        f = os.path.split(fi)[-1]
        desc = fi+'.dscr'

        destination = mdb_util.ensureUnicode(destination)
        f = mdb_util.ensureUnicode(f)
        desc = mdb_util.ensureUnicode(desc)

        if pmode:
            path = os.path.join(destination,f)
            if len(path) > 210:
                path = os.path.join(destination,f[0:210-len(f)-2-len(destination)])
                path = path.rstrip()
        else:
            path = os.path.join(destination,os.path.splitext(f)[0])
            path = path.rstrip()
            if len(os.path.join(path,f)) > 250:
                path = os.path.join(destination,os.path.splitext(f)[0][0:250-len(f)-2-len(destination)])
                path = path.rstrip()

        i = 0
        opath = path
        while os.path.isdir(path):
            path = opath + '_' + str(str(i),encoding)
            i = i+1

        if pmode:
            shutil.move(fi,path)
            e = me.picture_entry(path)
        else:
            os.mkdir(path)
            shutil.move(fi,os.path.join(path,f))
            shutil.move(desc,os.path.join(path,os.path.split(desc)[-1]))
            e = me.video_entry(path)
        db.add_entry(e)

    def onClose(self):
        """
            we don't want to close this window with a running compare thread.
            If it is, send an abort signal and wait for it to die.
        """
        if self.thread != None and self.thread.is_alive():
            self.abort = True
            self.thread.join()
            self.destroy()
        else:
            self.destroy()

class resultFrame(tk.Frame):
    """
        the structure that allows to display the results
        of the compare window in a flexible way
    """
    def __init__(self,master=None):
        tk.Frame.__init__(self,master)
        self.resultList = []
        self.grid()
        self.vmin = 0
        self.vmax = 0
        self.nmin = 0
        self.ignore = False

    def update_widgets(self,result,vmin=0,vmax=0,nmin=0,ignoreSelf=None,pmode=False):
        """
            select the results that have a probability score between vmin and vmax and display them
        """
        self.clearLists()
        if vmin > 0:
            self.vmin = vmin
        if vmax > 0:
            self.vmax = vmax
        if nmin > 0:
            self.nmin = nmin
        if ignoreSelf != None:
            self.ignore = ignoreSelf
        row = 0
        if pmode:
            scoreindex = 4
        else:
            scoreindex = 6

        for i in sorted(result.keys()):
            for j in result[i]:
                if j[1].shape[1]>0:
                    if self.ignore and i==j[0]:
                        continue
                    elif pmode:
                        nmatch = 0
                        for l in range(j[1].shape[1]):
                            nmatch = nmatch + j[1][1,l]-j[1][0,l] + 1
                        if nmatch < nmin:
                            continue
                    else:
                        nmatch = 0.0
                        for l in range(j[1].shape[1]):
                            nmatch = nmatch + j[1][2,l]-j[1][1,l]
                        nmatch = nmatch / 1000.0 / 60.0 # going back to minutes
                        if nmatch < nmin:
                            continue
                    s = max(j[1][scoreindex,:])

                    if len(j) > 2:
                        revs = max(j[2][scoreindex,:])
                        s = max([s,revs])

                    if s >= self.vmin and s <= self.vmax:
                        try:
                            self.resultList.append(resultElement(i,j[0],s,nmatch,master=self,result=result,pmode=pmode))
                        except tk.TclError:
                            # the element probably self destructed!
                            continue
                        self.resultList[-1].grid(row=row,column=0,columnspan=5,rowspan=2)
                        row = row+2


    def clearLists(self):
        for l in self.resultList:
            l.destroy()
        self.resultList = []

class resultElement(tk.Frame):
    """
        the display element of a single result entry in the compare window
        includes buttons to watch source and query file,
        and to delete the query file in case it is found to be a dublicate
    """
    def __init__(self,querry,source,score,nmatch,master=None,result=None,pmode=False):
        tk.Frame.__init__(self,master)
        self.querry = querry
        self.source = source
        self.pmode = pmode
        if pmode:
            self.querryE = me.picture_entry(querry)
            self.sourceE = me.picture_entry(source)
        else:
            self.querryE = me.video_entry(querry)
            self.sourceE = me.video_entry(source)
        self.score = score
        self.nmatch = nmatch
        self.result = result
        if self.querryE.filepath == ['']:
            self.result.pop(self.querry)
            self.master.update_widgets(self.result,pmode=self.pmode)
            self.destroy()
        elif self.sourceE.filepath == ['']:
            for e,s in enumerate(self.result[self.querry]):
                if s[0] == self.source:
                    self.result[self.querry].pop(e)
            self.master.update_widgets(self.result,pmode=self.pmode)
            self.destroy()
        self.grid()
        self.createWidgets()

    def createWidgets(self):
        options = {'sticky':'NSEW','padx':3,'pady':3}

        q = os.path.split(self.querry)[-1]
        if len(q) > 30:
            self.querryLabel = tk.Label(self,text=q[:27]+'...',width = 30)
        else:
            self.querryLabel = tk.Label(self,text=q,width = 30)
        self.querryLabel.grid(row=0,column=0,columnspan=2,**options)

        s = os.path.split(self.source)[-1]
        if len(s) > 30:
            self.sourceLabel = tk.Label(self,text=s[:27]+'...',width = 30)
        else:
            self.sourceLabel = tk.Label(self,text=s,width = 30)
        self.sourceLabel.grid(row=0,column=3,columnspan=2,**options)

        self.scoreLabel = tk.Label(self,text='%3.1f / %3.1f' %(self.nmatch, self.score),width = 11)
        self.scoreLabel.grid(row=0,column=2,columnspan=1,**options)

        self.watchqButton = tk.Button(self,text='Watch',width = 5)
        self.watchqButton.grid(row=1,column=0,columnspan=2,**options)
        self.watchqButton.bind("<Button-1>", self.watchQuerry)

        self.watchsButton = tk.Button(self,text='Watch',width = 5)
        self.watchsButton.grid(row=1,column=3,columnspan=2,**options)
        self.watchsButton.bind("<Button-1>", self.watchSource)


        self.deleteButton = tk.Button(self,text='Delete',width = 5)
        self.deleteButton.grid(row=1,column=2,columnspan=1,**options)
        self.deleteButton.bind("<Button-1>", self.deleteQuerry)

    def watchQuerry(self,event):
        """
            watch the query video
        """
        t = threading.Thread(target=self.querryE.execute)
        t.setDaemon(True)
        t.start()

    def watchSource(self,event):
        """
            watch the source video
        """
        t = threading.Thread(target=self.sourceE.execute)
        t.setDaemon(True)
        t.start()

    def deleteQuerry(self,event):
        """
            delete the query video from disk
        """
        if tkMessageBox.askokcancel("Delete",
            "This will erase " + self.querryE.get_display_string() + " from the harddisk! Continue?"):
            self.querryE.delete()
            self.result.pop(self.querry)
            self.master.update_widgets(self.result,pmode=self.pmode)
            self.destroy()
        else:
            return


class AutoScrollbar(tk.Scrollbar):
    """
     Taken from StockOverFlow:
     A scrollbar that hides itself if it's not needed.
     Only works if you use the grid geometry manager!
    """
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        tk.Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError("cannot use pack with this widget")
    def place(self, **kw):
        raise TclError("cannot use place with this widget")





# app = Application()
# app.title('Sample application')
# app.grid_columnconfigure(0,weight=1)
# app.grid_rowconfigure(0,weight=1)
# app.resizable(True,True)

# app.mainloop()
