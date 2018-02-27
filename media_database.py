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
    import os
    import pickle
    #//TODO convert strings into raw strings
    #//TODO make dlist a numpy array and then use the masking function for the reduced "unplayed" list in get_random_entry
    
    
    def __init__(self,d,p_style = 'first',v_style = 'random',m_style = 'random',e_style = 'first'):
        self.parent = d
        self.hash = hash(d)
        
        cwd = os.getcwd()        
        for i in os.listdir(cwd):
            if os.path.split(i)[1] == str(self.hash)+'.pkl':
                self._load_(i)
                if os.path.getmtime(d) > self.mtime:
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
            
    def get_random_entry(self,single=False):
        if single:
            mask = [i.played for i in self.dlist]
            m = [i for (i,v) in zip(self.dlist,mask) if not v]
            if len(m) == 0:
                print('Congrats you\'ve seen it all')
                for i in self.dlist:
                    i.set_played(False)
                m = self.dlist
            return random.choice(m)
        else:
            return random.choice(self.dlist)
        
    
    def fill(self,d,ty='unknown'):
        self.dlist = self.find_media_entries(d,ty)
        for d in self.dlist:
            for a in d.attrib.keys():
                if not a in self.alist:
                    self.alist[a] = 1
                else:
                    self.alist[a] = self.alist[a] + 1
        saved = False
    
    def update(self,d,ty='unknown'):
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

        
    def delete_entry(self,entry,delete_from_disk=False):
        self.dlist.remove(entry)
        for a in entry.attrib.keys():
            self.alist[a] = self.alist[a] - 1
            if self.alist[a] <= 0:
                self.alist.pop(a)
        
        self.saved = False
        self.mtime = time()
        
        
    def change_style(self):
        """
            //TODO this has to be done for every element of the respective type
        """
        print 'done'
        
    def get_selection(self,*args,**kwargs):
        l = []
        for i in self.dlist:
            if i.match_selection(*args,**kwargs):
                l.append(i.get_display_string())
        return l
        
    def get_entry(self,name):
        # \\TODO is this used?
        hash = hash(name)
        for i in dlist:
            if i.hash() == hash:
                return i
        
        return None
    
    def find_entry(self,dstring):
        for i in self.dlist:
            if i.get_display_string() == dstring:
                return i
        
        return None
        
    def get_attrib_stat(self):
        attrib = {}
        for i in self.dlist:
            entryattrib = i.attrib
            ekeys = entryattrib.keys()
            for j in ekeys:
                if not attrib.has_key(j):
                    attrib[j] = {}
                    for k in entryattrib[j]:
                        attrib[j][k] = 1
                else:
                    for k in entryattrib[j]:
                        if attrib[j].has_key(k):
                            attrib[j][k] += 1
                        else:
                            attrib[j][k] = 1
        
        return attrib
                