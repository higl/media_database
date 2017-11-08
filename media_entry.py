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
        
class media_entry:
    path = ''
    filepath = []
    style = ''
    type = ''
    hash = ''
    accepted_format = ()
    played = False
    
    """ 
        //TODO move attributes to a dictionary ?
    """
    def __init__(self,path, type='unknown',style='random',format=()):
        self.path = path
        self.type = type
        self.style = style
        self.played = False
        self.accepted_format = format
        self.filepath = self._determine_files_(self.path,self.style,self.accepted_format)
        self.hash = hash(self.path)
    
    def __eq__(self,other):
        return self.hash == other.hash
        
    def _determine_files_(self,path,style,format):
        """
        \\TODO redo this with the os.walk() function
        """
        fileList = []        
        folderList = []
        if os.path.isdir(path):
            folderList = [path]
        elif len(format)==0 or path.lower().endswith(format):
            fileList.append(path)
            return fileList
        else:
            return ['']
            #raise NoExecutableFileFoundException
            
        while len(folderList)>0:
            ls = os.listdir(folderList[0])
            for i in ls:
                p = folderList[0] + '/' + i
                if os.path.isdir(p):
                    folderList.append(p)
                elif len(format)==0 or p.lower().endswith(format):
                    fileList.append(p)
                    if style=='first':
                        return fileList
          
            folderList.pop(0)
        
        if len(fileList)==0:
            return ['']
            #raise NoExecutableFileFoundException
        elif style=='last':
            return [fileList[-1]]
        else:
            return fileList

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
        if self.style == 'first':
            return self.filepath[0]
        elif self.style == 'last':
            return self.filepath[-1]
        elif self.style == 'random':
            return random.choice(self.filepath)
            
    def equal(self,m):
        return m.get_hash == self.get_hash
        
    def find_first(self,path):
         'found'
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
    
    def execute(self,filepath='unknown',singleMode=False):   
        #TODO replace os.system by something safer like subprocess
        
        if filepath == 'unknown':
            filepath = self.get_filepath()  
        else:
            try:
                self.filepath.index(filepath)
            except Exception:
                print Exception
                return
         
        if os.name == 'nt':
            filepath = '"' + filepath + '"'
            os.system(filepath)
        elif os.name == 'posix':
            #filepath = self.parent+'/'+filepath
            specialchars = [' ', '(', ')']
            for i in specialchars:
                filepath = filepath.replace(i,'\\'+i)
            os.system("xdg-open "+filepath)
        
        if singleMode:    
            self.set_played(True)

    def set_played(self,played):
        self.played = played
            
    
    def delete(self):
        if os.path.isdir(self.path):
            for root, dirs, files in os.walk(self.path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

            os.rmdir(self.path)
        else:
            os.remove(self.path)
                
class video_entry(media_entry):
    tags = []
    actors = []
    genre = ''
    accepted_video_formats = ('.avi', '.mp4', '.flv','.m4v','.wmv','.mpeg','.mkv','.mov','.rm','.mpg')
        
    def __init__(self,path, tags=[], actors=[], genre='unknown',style='first'):
        media_entry.__init__(self,path,type='video',format=self.accepted_video_formats)
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
        media_entry.__init__(self,path,type='music',format=self.accepted_music_formats)
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