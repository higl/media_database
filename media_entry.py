import os
import random
import sys
import cv2
mswindows = (sys.platform == "win32")
encoding = sys.getfilesystemencoding()
from mdb_util import *

if mswindows:
    from subprocess import list2cmdline
    quote_args = list2cmdline
else:
    # POSIX
    from pipes import quote

    def quote_args(seq):
        return ' '.join(quote(arg) for arg in seq)

entry_version = u'0.1' 

class media_entry:
    """ 
        A media entry stores information about a media file or
        a folder containing a certain type of media
    """
    def __init__(self,path, type='unknown',style='random', played=False, format=()):
        self.version = entry_version
        self.path = ensureUnicode(path) 
        self.type = ensureUnicode(type)
        self.style = ensureUnicode(style)
        self.played = played
        self.accepted_format = format
        self.filepath = self._determine_files_(self.path,self.accepted_format)
        self.hash = hash(self.path)
        self.attrib = {}
    
    def __eq__(self,other):
        if type(other) is type(self):
            return self.hash == other.hash
        else: 
            return False
    
    def __ne__(self,other):
        return not self.__eq__(other)
    
    def _determine_files_(self,path,format):
        """ 
            if path is a folder, we will
            get all the media files inside of path that
            fit the allowed formats of the media entry. 
            
            if path is a file we will return its path instead 
            
        """
        if os.path.isfile(path):
            if path.lower().endswith(format):
                return [path]
            else:
                print 'Warning: No executable file was found'
                return [u'']
                
        fileList = []        
        for root,folder,files in os.walk(path):
            for f in files:
                if f.lower().endswith(format):
                    fi = os.path.join(root,f)
                    fi = os.path.normpath(fi)
                    fi = os.path.normcase(fi)
                    fileList.append(fi)
            
        fileList = sorted(fileList)
        if len(fileList)==0:
            print 'Warning: No executable file was found'
            return [u'']
            #raise NoExecutableFileFoundException
        else:
            return fileList
    
    def add_attrib(self,**kwargs):
        """
            deprectiated. use the update_attrib function with override=False instead 
        """
        if 'override' in kwargs:
            self.update_attrib(**kwargs)
        else:
            self.update_attrib(override=False,**kwargs)
                
    
    def update_attrib(self,override=True,**kwargs):
        """
            This will update any kwarg in the attrib dictionary of the media_entry.
            If the attrib entry does not exist, it will be created.
            
            In case we want to use this function to create new attribs but 
            don't want to override existing ones, we can use override=False.
            
            We raise an error when the datatype of the update 
            does not match the old datatype. This does not 
            work if the old entry is an empty list. In this 
            case the datatype of the update will be excepted anyway.
            The same is true for emptying the attribute list
        """    
        keys = kwargs.keys()
        for i in keys:
            if self.attrib.has_key(i):
                if override:
                    update = makeAttribList(kwargs[i])
                    if len(self.attrib[i]) > 0 and len(update) > 0:
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
            else:
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
        """
        if not type == '' and not self.type == type:
            return False
        elif not style == '' and not self.style == style: 
            return False
        elif not name == '' and not name in self.path: 
            return False
        
        keys = kwargs.keys()
                
        for i in keys:
            args = makeAttribList(kwargs[i])
            #filter empty args 
            if len(args) == 0:
                continue
            if self.attrib.has_key(i):
                orig = self.attrib[i]
                
                # len(args) > 0 at this point !
                if len(orig) == 0:
                    return False
                else:
                    #we overloaded the type function here,
                    #so we need to use object.__class__ instead
                    ttype = orig[0].__class__
                
                if ttype in (str,unicode):
                    ttype = basestring
                if not all([isinstance(w,ttype) for w in args]):
                    print 'type mismatch in match_selection'
                    return False
                if ttype in (str,unicode) and not case_sensitive:
                    orig = [w.lower for w in orig]
                    args = [w.lower for w in args]
                    
                match = [w in orig for w in args]
                            
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
        
        print filepath          
        if filepath == 'unknown':
            filepath = self.get_filepath()  
        else:
            try:
                self.filepath.index(filepath)
            except Exception:
                print Exception
                return
        print filepath          
       
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
            try:
                f = f.encode(encoding)
                v=cv2.VideoCapture(f)
                v.set(cv2.CAP_PROP_POS_AVI_RATIO,1)
                length = length + v.get(cv2.CAP_PROP_POS_MSEC)
            except:
                pass 
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
        
def convert_to_new_version(entry):
    """ We might save media entries in some form, e.g. as pickles. If we want 
    to load them and include them in a program that uses a most recent version of the media entry library
    then we might run into conflicts. 
    
    In order to always work with the most recent media entry version it is best practice 
    to pass all stored entries through this function after they've been loaded. 
    """
    
    try:
        version = entry.version
    except:
        version = u'0.0' #the first version did not have a version label yet
    
    if version == entry_version:
        return entry
        #return media_entry(entry.path,type=entry.type,style=entry.style,played=entry.played, format=entry.accepted_format)
    elif version == u'0.0':
        supported_types = {
            'exec': executable_entry,
            'video': video_entry,
            'music': music_entry,
            'picture': picture_entry,
            'unknown': media_entry, 
            }
        try:
            generator = supported_types[entry.type]
        except KeyError:
            print 'cannot create a new entry for type {}'.format(entry.type)
            return None
        kwargs = {}
        kwargs['style'] = entry.style
        kwargs['played'] = entry.played
        path = entry.path
        new_entry = generator(path, **kwargs)
        new_entry.update_attrib(**entry.attrib)
        return new_entry        
    else:
        raise NotImplementedError("""
                      I do not know how to convert from version "{}" 
                      to the current version "{}"'
                      """.format(version,entry_version)) 
    
    
    
    