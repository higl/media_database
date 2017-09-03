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

class dirlist:
    import os
    import cpickle
    
    parent = ''
    dlist = []
    p_style = ''
    v_style = ''
    m_style = ''
    e_style = ''
    
    
    
    def __init__(d,p_style = 'first',v_style = 'random',m_style = 'random',e_style = 'first'):
        cwd = os.getcwd()
        
        for i in os.listdir(cwd):
            if os.path.spli()[1] == self.get_filename(d):
                self._load_(i)
                return
        
        self.p_style = p_style
        self.v_style = v_style
        self.m_style = m_style
        self.e_style = e_style
        self.dlist = os.listdir(d)
        self.parent = d
        return
    
    def _load_(d):
        
    def save():
        
    def execute_random(d):    
        #TODO replace os.system by something safer like subprocess
        file_not_found = True
        continue_search = False
        while file_not_found:
            if continue_search or os.path.isdir(d):
                ls = os.listdir(d)
                if len(ls) == 0:
                    raise EmptyFolderException('please delete')
                d = quote_args([d + random.choice()])
                continue_search = False
            elif:
                f = self.determine_exec_file(os.path.split(d)[0])
                if f == '':
                    continue_search = True
                else:
                    filepath = f
                    file_not_found = False
                    
        if os.name == 'nt':
            os.system("start "+filepath)
        elif os.name == 'posix':
            os.system("xdg-open "+filepath)
        
    def determine_exec_file(d):
        ls = [d + i for i in os.listdir(d)]
        
        folder = False
        picture = False
        video = False
        ex = False
        music = False
        
        pf = []
        vf = []
        mf = []
        ef = []
        
        accepted_picture_formats = ('.png', '.jpg', '.jpeg','.tiff','.bmp')
        accepted_video_formats = ('.avi', '.mp4', '.flv','.m4v','.wmv','.mpeg','.mkv','.mov','.rm','.mpg')
        accepted_music_formats = ('.mp3', '.wma', '.flac','.ogg')
        accepted_execs = ('.exe','.jar')
        
        for i in ls:
            if os.path.isdir(i):
                folder = True
            elif i.lower().endswith(accepted_picture_formats):
                picture = True
                if self.p_style = 'first' and len(pf) == 0:
                    pf = [i]
                elif self.p_style = 'last':
                    pf = [i]
                elif self.p_style = 'random'
                    pf.append(i)
            elif i.lower().endswith(accepted_video_formats):
                video = True
                if self.v_style = 'first' and len(vf) == 0:
                    vf = [i]
                elif self.v_style = 'last':
                    vf = [i]
                elif self.v_style = 'random'
                    vf.append(i)
            elif i.lower().endswith(accepted_music_formats):
                music = True
                if self.m_style = 'first' and len(mf) == 0:
                    mf = [i]
                elif self.m_style = 'last':
                    mf = [i]
                elif self.m_style = 'random'
                    mf.append(i)
            elif i.lower().endswith(accepted_execs):
                ex = True
                if self.e_style = 'first' and len(ef) == 0:
                    ef = [i]
                elif self.e_style = 'last':
                    ef = [i]
                elif self.e_style = 'random'
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


d = '/home/johann/Dropbox/To Read/'
execute_random(d)
