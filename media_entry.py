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
        self.attrib = {}
    
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
    
    def add_attrib(self,**kwargs):
        """
            This will save any kwarg to the attrib dictionary of the media_entry.
            If the attrib entry already exists, it will be skipped.
        """
        keys = kwargs.keys()
        for i in keys:
            if not self.attrib.has_key(i):
                if not isinstance(kwargs[i],basestring):
                    self.attrib[i] = [str(j) for j in kwargs[i]]
                else:
                    self.attrib[i] = [kwargs[i]]
    
    def update_attrib(self,**kwargs):
        """
            This will update any kwarg in the attrib dictionary of the media_entry.
            If the attrib entry does not exist, it will be skipped.
        """    
        keys = kwargs.keys()
        for i in keys:
            if self.attrib.has_key(i):
                if not isinstance(kwargs[i],basestring):
                    self.attrib[i] = [str(j) for j in kwargs[i]]
                else:
                    self.attrib[i] = [kwargs[i]]
                    
    def remove_attrib(self,**kwargs):
        """
            This will remove any kwarg from the attrib dictionary of the media_entry.
            If the attrib entry does not exist, it will be skipped.
        """
        keys = kwargs.keys()
        for i in keys:
            if self.attrib.has_key(i):
                self.attrib.pop(i)
            
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
            

    def match_selection(self,type='',style='',case_sensitive=False,**kwargs):
        """
        \\TODO check if this works
        """
        if not type == '' and not self.type == type:
            return False
        elif not style == '' and not self.style == style: 
            return False
        
        keys = kwargs.keys()
        for i in keys:
            if self.attrib.has_key(i):
                if not isinstance(kwargs[i],basestring):
                    args = kwargs[i]
                else:
                    args = [kwargs[i]]
                    
                match = [False for j in args]
                
                for e,j in enumerate(args):
                    if case_sensitive:
                        match[e] = any(j.lower() in k.lower() for k in self.attrib[i])
                    else:
                        match[e] = any(j in k for k in self.attrib[i])
                            
                if not all(match):
                    return False
            else:
                return False
        return True

        
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
    accepted_video_formats = ('.avi', '.mp4', '.flv','.m4v','.wmv','.mpeg','.mkv','.mov','.rm','.mpg')
        
    def __init__(self,path, tags=[], actors=[], genre='unknown',style='first'):
        media_entry.__init__(self,path,type='video',format=self.accepted_video_formats)
        self.attrib['tags'] = tags
        self.attrib['actors'] = actors
        self.attrib['genre'] = [genre]
    
    
class music_entry(media_entry):
    accepted_music_formats = ('.mp3', '.wma', '.flac','.ogg')
    
    def __init__(self,path, tags=[], artist=[], genre=['unknown'],style='random'):
        media_entry.__init__(self,path,type='music',format=self.accepted_music_formats)
        self.attrib['tags'] = tags
        self.attrib['artist'] = artist
        self.attrib['genre'] = genre
        
    
class picture_entry(media_entry):
    accepted_picture_formats = ('.png', '.jpg', '.jpeg','.tiff','.bmp')   
    
    def __init__(self,path, tags=[],style='first'):
        media_entry.__init__(self,path,type='picture',format=self.accepted_picture_formats)
        self.attrib['tags'] = tags
    
    
class executable_entry(media_entry):
    accepted_exe_formats = ('.exe','.jar')
    
    def __init__(self,path, tags=[],style='first'):
        media_entry.__init__(self,path,type='exec',format=self.accepted_exe_formats)
        self.attrib['tags'] = tags