import os
import random
import sys
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
        
    def execute_random(self):    
        #TODO replace os.system by something safer like subprocess
        
        random_medium = random.choice(self.dlist)
        filepath = random_medium.get_filepath()  
        if os.name == 'nt':
            os.system("start "+filepath)
        elif os.name == 'posix':
            #filepath = self.parent+'/'+filepath
            specialchars = [' ', '(', ')']
            for i in specialchars:
                filepath = filepath.replace(i,'\\'+i)
            os.system("xdg-open "+filepath)
        
    
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
            print t
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
        print folderList, i
        while len(folderList)>0:
            ls = os.listdir(folderList[0])
            print folderList
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
        
class media_entry:
    import os
    path = ''
    filepath = ''
    style = ''
    type = ''
    hash = ''
    
    """ 
        //TODO move attributes to a dictionary ?
    """
    def __init__(self,path, type='unknown',style='random'):
        self.path = path
        self.type = type
        self.style = style
        if self.style == 'first':
            filepath = find_first(self.path)
        elif self.style == 'last':
            filepath = find_first(self.path)
        elif self.style == 'random':
            filepath = ''
        else:
            filepath = ''
        self.hash = hash(self.path)
        
    def get_path(self):
        return self.path

    def get_display_string(self):
        return os.path.split(self.path)[1]
        
    def get_type(self):
        return self.type

    def get_hash(self):
        return self.hash

    def get_filepath(self):
        #//TODO redo this function in the same manner as determine_media_type with the recurive order search. For styles fist, last, etc. self.filepath has to be set and in the next this will be returned  or even save arrays for random access in media_entry
        d = self.path
        print d
        file_not_found = True
        continue_search = False
        while file_not_found:
            if continue_search or os.path.isdir(d):
                ls = os.listdir(d)
                if len(ls) == 0:
                    raise EmptyFolderException('please delete')
                d = quote_args([d + random.choice(ls)])
                continue_search = False
            else:
                f = self.determine_exec_file(os.path.split(d)[0])
                if f == '':
                    continue_search = True
                else:
                    filepath = f
                    file_not_found = False
        
        if self.style == 'random':
            return find_random()
        else:
            return self.filepath

            
    def determine_exec_file(self,d,extensions='all'): 
        ls = [d + i for i in os.listdir(d)]
        print d, ls
        folder = False
        picture = False
        video = False
        ex = False
        music = False
        
        pf = []
        vf = []
        mf = []
        ef = []
        

        accepted_video_formats = ('.avi', '.mp4', '.flv','.m4v','.wmv','.mpeg','.mkv','.mov','.rm','.mpg')
        
        for i in ls:
            if os.path.isdir(i):
                folder = True
            elif i.lower().endswith(accepted_picture_formats):
                picture = True
                if self.p_style == 'first' and len(pf) == 0:
                    pf = [i]
                elif self.p_style == 'last':
                    pf = [i]
                elif self.p_style == 'random':
                    pf.append(i)
            elif i.lower().endswith(accepted_video_formats):
                video = True
                if self.v_style == 'first' and len(vf) == 0:
                    vf = [i]
                elif self.v_style == 'last':
                    vf = [i]
                elif self.v_style == 'random':
                    vf.append(i)
            elif i.lower().endswith(accepted_music_formats):
                music = True
                if self.m_style == 'first' and len(mf) == 0:
                    mf = [i]
                elif self.m_style == 'last':
                    mf = [i]
                elif self.m_style == 'random':
                    mf.append(i)
            elif i.lower().endswith(accepted_execs):
                ex = True
                if self.e_style == 'first' and len(ef) == 0:
                    ef = [i]
                elif self.e_style == 'last':
                    ef = [i]
                elif self.e_style == 'random':
                    ef.append(i)
                

        if ex:
            return random.choice(ef)
        elif video:
            return random.choice(vf)
        elif music:
            return random.choice(mf)
        elif picture:
            return random.choice(pf)
        elif folder:
            return ''
        else:
            raise StrangeFolderException('Don\'t know what to do with ', d)
            
    def find_first(self,path):
        print 'found'
    def find_last(self,path):
        print 'found'        
    def find_random(self,path):
        print 'found'
    def match_selection(self,type=''):
        """
        \\TODO make this more general with a dictionary of attributes
        """
        if type == '' or self.type == type:
            return True
        else: 
            return False
        
class video_entry(media_entry):
    tags = []
    actors = []
    genre = ''
    accepted_video_formats = ('.avi', '.mp4', '.flv','.m4v','.wmv','.mpeg','.mkv','.mov','.rm','.mpg')
        
    def __init__(self,path, tags=[], actors=[], genre='unknown',style='first'):
        media_entry.__init__(self,path,type='video')
        self.tags = tags
        self.actors = actors
        self.genre = genre
    
    def get_genre(self):
        return self.genre
    
    def get_tags(self):
        return self.tags
        
    def get_actors(self):
        return self.actors
    
    def has_tag(self,tag):
        tag_str = str(tag)
        tag_str = tag_str.lower()
        if tag_str in self.tags.lower():
            return True
        else: 
            return False
    
    def has_actor(self,actor):
        """
            \\TODO account for partial matches, e.g. 'Tom Cruise' should be triggered by 'tom' 'cruise' or 'tom cruise'
        """
        actor_str = str(actor)
        actor_str = actor_str.lower()
        if actor_str in self.actor.lower():
            return True
        else: 
            return False    
            
    def is_genre(self,genre):
        genre = str(genre).lower()
        return self.genre.lower() == genre 
    
    def determine_exec_file(self,d):
        return media_entry.determine_exec_file(self,d,extensions=self.accepted_video_formats)
    
    def match_selection(self,type = 'unknown', tags = [], actor = [], genre = ''):
        if type != 'unknown' and not media_entry.match_selection(type):
            return False
        elif genre != '' and not is_genre(genre):
            return False
        elif len(tags) > 0 and not has_tag(tag):
            return False
        elif len(actor) > 0 and not has_actor(actor):
            return False
        else:
            return True
    
class music_entry(media_entry):
    accepted_music_formats = ('.mp3', '.wma', '.flac','.ogg')
    tags = []
    artist = []
    genre = []
    
    def __init__(self,path, tags=[], artist=[], genre=['unknown'],style='random'):
        media_entry.__init__(self,path,type='video')
        self.tags = tags
        self.artist = artist
        self.genre = genre
    
    def get_genre(self):
        return self.genre
    
    def get_tags(self):
        return self.tags
        
    def get_artist(self):
        return self.artist
    
    def has_tag(self,tag):
        tag_str = str(tag)
        tag_str = tag_str.lower()
        if tag_str in self.tags.lower():
            return True
        else: 
            return False
    
    def has_artist(self,artist):
        """
            \\TODO account for partial matches, e.g. 'Tom Cruise' should be triggered by 'tom' 'cruise' or 'tom cruise' 
        """
        actor_str = str(actor)
        actor_str = actor_str.lower()
        if actor_str in self.actor.lower():
            return True
        else: 
            return False    
            
    def is_genre(self,genre):
        genre = str(genre).lower()
        return self.genre.lower() == genre
    
    
class picture_entry(media_entry):
    accepted_picture_formats = ('.png', '.jpg', '.jpeg','.tiff','.bmp')   

class executable_entry(media_entry):
    accepted_execs = ('.exe','.jar')
    
#d = '/home/johann/Dropbox/To Read/'

#execute_random(d)
