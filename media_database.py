import os
import random
import sys
from media_entry import *
import pickle
from time import time
mswindows = (sys.platform == "win32")

if mswindows:
    from subprocess import list2cmdline
    quote_args = list2cmdline
else:
    # POSIX
    from pipes import quote

    def quote_args(seq):
        return ' '.join(quote(arg) for arg in seq)

class media_database:
    """
        a media_database stores, media_entries. 
        It can save and load it from disk, 
        search through it and provide information
        needed to display the media entries properly 
    """
    import os
    import pickle
    #//TODO convert strings into raw strings
    #//TODO make dlist a numpy array and then use the masking function for the reduced "unplayed" list in get_random_entry
    
    
    def __init__(self,d,p_style = 'first',v_style = 'random',m_style = 'random',e_style = 'first',force_update=False):
        self.parent = d
        self.hash = hash(d)
        
        cwd = os.getcwd()        
        for i in os.listdir(cwd):
            if os.path.split(i)[1] == str(self.hash)+'.pkl':
                self._load_(i)
                if os.path.getmtime(d) > self.mtime or force_update:
                    self.update(d)
                return
        
        self.p_style = p_style
        self.v_style = v_style
        self.m_style = m_style
        self.e_style = e_style
        self.dlist = []
        self.alist = {}
        self.fill(d)
        self.mtime = time()
        self.saved = False
        return
    
    def _load_(self,d):
        """
            load a media database from filepath d
            \\TODO introduce versioning here
        """
        with open(d, 'rb') as input:
            db = pickle.load(input)
            self.dlist = db['dlist']
            self.alist = db['alist']
            self.p_style = db['pstyle']
            self.m_style = db['mstyle']
            self.v_style = db['vstyle']
            self.e_style = db['estyle']
            self.mtime = db['mtime']
        self.saved = True
            
    def save(self):
        """
            save the media database to disk via pickle
            uses its own hash as the filename
        """
        self.saved = True
        out = {}
        out['dlist']=self.dlist
        out['alist']=self.alist
        out['pstyle']=self.p_style
        out['vstyle']=self.v_style
        out['mstyle']=self.m_style
        out['estyle']=self.e_style
        out['mtime']=self.mtime
        with open(str(self.hash)+'.pkl', 'wb') as output:
            pickle.dump(out, output, pickle.HIGHEST_PROTOCOL)
            
    def get_random_entry(self,single=False,selection=None):
        """
            gives back a random entry.

            If single=True it will make sure that items are not repeated,
            until every item has been selected once before 

            slection mode does not add to single mode
        """
        if selection != None:
            return self.find_entry(random.choice(selection))
        else: 
            elist = self.dlist            
            if single:
                mask = [i.played for i in elist]
                m = [i for (i,v) in zip(elist,mask) if not v]
                if len(m) == 0:
                    print('Congrats you\'ve seen it all')
                    for i in elist:
                        i.set_played(False)
                    m = elist
                return random.choice(m)
            else:
                return random.choice(elist)
        
    
    def fill(self,d,ty='unknown'):
        """
            fills all the media entries in directory d into the media database
        """
        self.dlist = self.find_media_entries(d,ty)
        for d in self.dlist:
            for a in d.attrib.keys():
                if not a in self.alist:
                    self.alist[a] = 1
                else:
                    self.alist[a] = self.alist[a] + 1
        saved = False
    
    def update(self,d,ty='unknown'):
        """
            if new media entries are created or old ones are deleted from disk,
            the media database will usually not react to it
            
            update searches the directory d and compares the media entries in it 
            with all the media entries. 
            Removes those that are not there anymore and
            adds those that are missing in the current list 
        """
        inlist = self.find_media_entries(d,ty)
        curlist = list(self.dlist)
        for i in inlist:
            found = False
            for j in curlist:
                if i == j:
                    found = True
                    curlist.remove(j)
                    break
            if not found:
                self.add_entry(i)
                
        if len(curlist) > 0:
            for i in curlist:
                self.delete_entry(i)
        
        self.saved = False
        
    def find_media_entries(self,d,ty):
        """
            search for all folder/files in the directory d.
            It will create a media entry for each folder/file it finds.
            ty specifies the type of media entries that will be created
            if ty == unknown, the type of each media entry will be determined separately
        """
        res = []
        for i in os.listdir(d):
            path = d + '/' + i 
            if ty == 'unknown':
                t = self.determine_media_type(path)
            else:
                t = ty
                
            if t == 'video':
                new_entry = video_entry(path,style = self.v_style)
            elif t == 'music':
                new_entry = music_entry(path,style = self.m_style)
            elif t == 'exec':
                new_entry = executable_entry(path,style = self.e_style)
            elif t == 'picture':
                new_entry = picture_entry(path,style = self.p_style)
            else:
                new_entry = media_entry(path)

            res.append(new_entry)
        return res
        
    def determine_media_type(self,i):
        """
            This function takes a path as an input and then searches through all the files associated with that path (recursively!).
            Depending on the file extensions found, it will decide which type of media should be associated with that path.
            
            The decision has the following priority when several media types are found:
                executable - video - music - picture 
                
            if no media type is found it will return 'unknown'
            
            \\TODO redo with os.walk
        """
        accepted_video_formats = ('.avi', '.mp4', '.flv','.m4v','.wmv','.mpeg','.mkv','.mov','.rm','.mpg')
        accepted_music_formats = ('.mp3', '.wma', '.flac','.ogg')
        accepted_execs = ('.exe','.jar')
        accepted_picture_formats = ('.png', '.jpg', '.jpeg','.tiff','.bmp')
        picture = False
        video = False
        ex = False
        music = False
        
        folderList = []
        if os.path.isdir(i):
            folderList = [i]
        elif i.lower().endswith(accepted_picture_formats):
            picture = True
        elif i.lower().endswith(accepted_video_formats):
            video = True
        elif i.lower().endswith(accepted_music_formats):
            music = True
        elif i.lower().endswith(accepted_execs):
            ex = True
        while len(folderList)>0:
            ls = os.listdir(folderList[0])
            for i in ls:
                p = folderList[0] + '/' + i
                if os.path.isdir(p):
                    folderList.append(p)
                elif i.lower().endswith(accepted_picture_formats):
                    picture = True
                elif i.lower().endswith(accepted_video_formats):
                    video = True
                elif i.lower().endswith(accepted_music_formats):
                    music = True
                elif i.lower().endswith(accepted_execs):
                    ex = True
            folderList.pop(0)

        if ex:
            return 'exec'
        elif video:
            return 'video'
        elif music:
            return 'music'
        elif picture:
            return 'picture'
        else:
            return 'unknown'
    
        
    def add_entry(self,new_entry,*args,**kwargs):
        """
            This function adds an media_entry to the database.
            
            It first determines the appropriate media type and creates the media_entry 
            if also checks if the same entry already exists. In that case the new media_entry is not added. 
        """
        
        self.dlist.append(new_entry)

        for a in new_entry.attrib.keys():
            if not a in self.alist:
                self.alist[a] = 1
            else:
                self.alist[a] = self.alist[a] + 1
        
        self.saved = False
        self.mtime = time()

        
    def delete_entry(self,entry):
        """
            remove a media entry from the database
        """
        self.dlist.remove(entry)
        for a in entry.attrib.keys():
            self.alist[a] = self.alist[a] - 1
            if self.alist[a] <= 0:
                self.alist.pop(a)
        
        self.saved = False
        self.mtime = time()
        
        
    def change_style(self):
        """
            changes the execution style for a specific media entry type
            //TODO this has to be done for every element of the respective type
        """
        print 'done'
        
    def get_selection(self,*args,**kwargs):
        """
            filters all media entries. Uses the match_selection function of the entries
        """
        l = []
        for i in self.dlist:
            if i.match_selection(*args,**kwargs):
                l.append(i.get_display_string())
        return l
        
    def get_entry(self,name):
        """
            searches for a media entry by its hash
        """
        # \\TODO is this used?
        hash = hash(name)
        for i in dlist:
            if i.hash() == hash:
                return i
        
        return None
    
    def find_entry(self,dstring):
        """
            searches for a media entry by its display string
        """
        for i in self.dlist:
            if i.get_display_string() == dstring:
                return i
        
        return None
        
    def get_attrib_stat(self):
        """
            returns statistics about the attributes 
            used in all the media entries of the database
        """
        attrib = {'Type':{'undefined':0}}
        empty = 0
        for i in self.dlist:
            if attrib['Type'].has_key(i.type):
                attrib['Type'][i.type] += 1
            else: 
                attrib['Type'][i.type] = 1
                
            entryattrib = i.attrib
            ekeys = entryattrib.keys()
            for j in ekeys:
                if not attrib.has_key(j):
                    attrib[j] = {'undefined':empty}
                    if len(entryattrib[j]) == 0:
                        attrib[j]['undefined'] += 1
                    else:    
                        for k in entryattrib[j]:
                            attrib[j][k] = 1
                elif len(entryattrib[j]) == 0:
                    attrib[j]['undefined'] += 1
                else:    
                    for k in entryattrib[j]:
                        if attrib[j].has_key(k):
                            attrib[j][k] += 1
                        else:
                            attrib[j][k] = 1
            for j in attrib.keys():
                if j != 'Type' and not entryattrib.has_key(j):
                    attrib[j]['undefined'] += 1
                    
            empty += 1
        
        return attrib
    
    def get_entry_count(self):
        """
            how many media entries do we have?
        """
        return len(self.dlist)