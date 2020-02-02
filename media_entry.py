import os
import random
import sys
import cv2
mswindows = (sys.platform == "win32")
from mdb_util import ensureStringList, ensureList, makeAttribList 

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
        A media entry stores information about a media file or
        a folder containing a certain type of media
    """
    def __init__(self,path, type='unknown',style='random', played=False, format=()):
        self.path = path 
        self.type = type
        self.style = style
        self.played = played
        self.accepted_format = format
        self.filepath = self._determine_files_(self.path,self.style,self.accepted_format)
        self.hash = hash(self.path)
        self.attrib = {}
    
    def __eq__(self,other):
        if type(other) is type(self):
            return self.hash == other.hash
        else: 
            return False
    
    def __ne__(self,other):
        return not self.__eq__(other)
    
    def _determine_files_(self,path,style,format):
        """
            get all the media files inside of path that
            fit the style of the media entry. 
            Selection is done over a predefined set of
            file endings associated with each media type 
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
            
        fileList = sorted(fileList)
        if len(fileList)==0:
            return ['']
            #raise NoExecutableFileFoundException
        elif style=='last':
            return [fileList[-1]]
        else:
            return sorted(fileList)
    
    def add_attrib(self,**kwargs):
        """
            This will save any kwarg to the attrib dictionary of the media_entry.
            If the attrib entry already exists, it will be skipped.
            
            We can add attrib entries with any datatype here, but we should 
            make sure that they are consistend 
        """
        keys = kwargs.keys()
        for i in keys:
            if not self.attrib.has_key(i):
                self.attrib[i] = makeAttribList(kwargs[i])
    
    def update_attrib(self,**kwargs):
        """
            This will update any kwarg in the attrib dictionary of the media_entry.
            If the attrib entry does not exist, it will be skipped.
        """    
        keys = kwargs.keys()
        for i in keys:
            if self.attrib.has_key(i):
                update = makeAttribList(kwargs[i])
                ttype = type(self.attrib[i][0])
                if ttype in (str,unicode):
                    ttype = basestring
                if not isinstance(update[0],ttype):
                    msg = """Update to {} is of type {}, 
                            but should be type {}""".format(
                            i,type(update[0]),type(self.attrib[i][0])
                            )
                    raise TypeError(msg)
                self.attrib[i] = makeAttribList(kwargs[i])
                    
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
        """
            return a filepath (to be executed?) of the media files in the media entry.
            if several files are present, selection will depend on the style settings. 
        //TODO redo this function in the same manner as determine_media_type with the recurive order search. For styles fist, last, etc. self.filepath has to be set and in the next this will be returned  or even save arrays for random access in media_entry
        """
        if self.style == 'first':
            return self.filepath[0]
        elif self.style == 'last':
            return self.filepath[-1]
        elif self.style == 'random':
            return random.choice(self.filepath)
            

    def match_selection(self,type='',style='',name='',case_sensitive=False,**kwargs):
        """
            checks if the media entry matches a filter, 
            based on type, style, name and attributes 
        \\TODO check if this works
        \\TODO add type consideration in the matching process
        """
        if not type == '' and not self.type == type:
            return False
        elif not style == '' and not self.style == style: 
            return False
        elif not name == '' and not name in self.path: 
            return False
        
        keys = kwargs.keys()
        for i in keys:
            if self.attrib.has_key(i):
                args = makeAttribList(kwargs[i])
                    
                match = [False for j in args]
                
                for e,j in enumerate(args):
                    if case_sensitive:
                        match[e] = any(j in k for k in self.attrib[i])
                    else:
                        match[e] = any(j.lower() in k.lower() for k in self.attrib[i])
                            
                if not all(match):
                    return False
            else:
                return False
        return True

        
    def execute(self,filepath='unknown',singleMode=False):   
        """
            play a media file
        //TODO replace os.system by something safer like subprocess
        """
        
        if filepath == 'unknown':
            filepath = self.get_filepath()  
        else:
            try:
                self.filepath.index(filepath)
            except Exception:
                print Exception
                return
         
        if os.name == 'nt':
            filepath = os.path.normpath(filepath)
            os.startfile(filepath)
        elif os.name == 'posix':
            #filepath = self.parent+'/'+filepath
            specialchars = [' ', '(', ')']
            for i in specialchars:
                filepath = filepath.replace(i,'\\'+i)
            os.system("xdg-open "+filepath)
        
        if singleMode:    
            self.set_played(True)

    def set_played(self,played):
        """
            mark if a media entry has been played before
        """
        self.played = played
            
    
    def delete(self):
        """
            delete a media entry from disk
        """
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
    """
        a media entry containing video files
    """
    import cv2
    accepted_video_formats = ('.avi', '.mp4', '.flv','.m4v','.wmv','.mpeg','.mkv','.mov','.rm','.mpg','.MP4')
        
    def __init__(self,
                path, 
                tags=[], 
                actors=[], 
                genre='unknown',
                style='first',
                **kwargs):
        media_entry.__init__(self,
                            path,
                            type='video',
                            format=self.accepted_video_formats,
                            style=style,
                            **kwargs)
        self.attrib['tags'] = ensureStringList(tags)
        self.attrib['actors'] = ensureStringList(actors)
        self.attrib['genre'] = ensureStringList(genre)
        length = 0.0
        for f in self.filepath:
            v=cv2.VideoCapture(f)
            v.set(cv2.CAP_PROP_POS_AVI_RATIO,1)
            length = length + v.get(cv2.CAP_PROP_POS_MSEC)
        self.attrib['length'] = makeAttribList(length / 1000.0)
    
class music_entry(media_entry):
    """
        a media entry containing music files
    """
    accepted_music_formats = ('.mp3', '.wma', '.flac','.ogg')
    
    def __init__(self,
                path, 
                tags=[], 
                artist=[], 
                genre=['unknown'],
                style='random',
                **kwargs
                ):
        
        media_entry.__init__(self,
                            path,
                            type='music',
                            format=self.accepted_music_formats,
                            style=style,
                            **kwargs)
        self.attrib['tags'] = ensureStringList(tags)
        self.attrib['artist'] = ensureStringList(artist)
        self.attrib['genre'] = ensureStringList(genre)
        self.attrib['ntacks'] = makeAttribList(len(self.filepath))
        
    
class picture_entry(media_entry):
    """
        a media entry containing picture files
    """
    accepted_picture_formats = ('.png', '.jpg', '.jpeg','.tiff','.bmp','.JPG','.JPEG')   
    
    def __init__(self,path, tags=[],style='first',**kwargs):
        media_entry.__init__(self,
                            path,
                            type='picture',
                            format=self.accepted_picture_formats,
                            style=style,
                            **kwargs)
        self.attrib['tags'] = ensureStringList(tags)
        self.attrib['npics'] = makeAttribList(len(self.filepath))
    
    
class executable_entry(media_entry):
    """
        a media entry containing executables
    """
    accepted_exe_formats = ('.exe','.jar')
    
    def __init__(self,path, tags=[],style='first',**kwargs):
        media_entry.__init__(self,
                            path,
                            type='exec',
                            format=self.accepted_exe_formats,
                            style=style,
                            **kwargs)
        self.attrib['tags'] = ensureStringList(tags)