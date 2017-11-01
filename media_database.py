import os
import random
import sys
from media_entry import *
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
    parent = ''
    #//TODO make dlist a numpy array and then use the masking function for the reduced "unplayed" list in get_random_entry
    dlist = []
    p_style = ''
    v_style = ''
    m_style = ''
    e_style = ''
    saved = False
    
    
    def __init__(self,d,p_style = 'first',v_style = 'random',m_style = 'random',e_style = 'first'):
        cwd = os.getcwd()
        
        for i in os.listdir(cwd):
            if os.path.split(i)[1] == d:
                self._load_(i)
                return
        
        self.p_style = p_style
        self.v_style = v_style
        self.m_style = m_style
        self.e_style = e_style
        self.fill(d)
        self.parent = d
        self.saved = False
        return
    
    def _load_(self,d):
        if already_exists:
            self.saved = True
        
    def save(self):
        self.saved = True
    
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

            self.dlist.append(new_entry)
        saved = False
        
    def determine_media_type(self,i):
        """
            This function takes a path as an input and then searches through all the files associated with that path (recursively!).
            Depending on the file extensions found, it will decide which type of media should be associated with that path.
            
            The decision has the following priority when several media types are found:
                executable - video - music - picture 
                
            if no media type is found it will return 'unknown'
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
            return 'executable'
        elif video:
            return 'video'
        elif music:
            return 'music'
        elif picture:
            return 'picture'
        else:
            return 'unknown'
    
        
    def add_entry(self,d,*args,**kwargs):
        """
            This function adds an media_entry to the database.
            
            It first determines the appropriate media type and creates the media_entry 
            if also checks if the same entry already exists. In that case the new media_entry is not added. 
        """
    
        hash = hash(d)
        for i in self.dlist:
            if i.get_hash() == hash:
                raise TaskNotExecutedException('item already in list')
                return
         
        type = self.determine_media_type(d)

        if type == 'video':
            new_entry = video_entry(i,**kwargs)
        elif type == 'music':
            new_entry = music_entry(i,**kwargs)
        elif type == 'exec':
            new_entry = executable_entry(i,**kwargs)
        elif type == 'picutre':
            new_entry = picture_entry(i,**kwargs)
        else:
            new_entry = media_entry(i,**kwargs)

        self.dlist.append(new_entry)

        self.saved = False

        
    def delete_entry(self,entry,delete_from_disk=False):
        if delete_from_disk:
            self.saved = False    
        
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
        hash = hash(name)
        for i in dlist:
            if i.hash() == hash:
                return i
        
        raise NotAnEntryError