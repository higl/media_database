import os
import sys
import shutil
encoding = sys.getfilesystemencoding()

def rm_empty_folders(path):
    """
        remove all empty folders in path
    """
    for root, dirs, files in os.walk(path, topdown=False):
        for i in dirs:
            i = os.path.join(root, i)
            try:
                os.rmdir(i)
            except:
                pass

def updateString(s):
    """
        takes a string and splits it up into single attributes (separeted by comma),
        that can be added to a media entry
    """
    tmpstr = s.split(',')
    tmpstr = list([x.lstrip() for x in tmpstr])
    tmpstr = list([x.rstrip() for x in tmpstr])
    tmpstr = [x for x in tmpstr if x != '']
    return tmpstr

def displayString(s):
    """
        takes a list of strings (typically all the attributes of a media entry)
        and combines them into a nice string to display them
    """
    tmpstr = ''
    for i in s:
        tmpstr = tmpstr + ' , ' + i

    tmpstr = tmpstr.lstrip(' , ')
    tmpstr = tmpstr.rstrip(' , ')
    return tmpstr

def ensureList(lis):
    if not isinstance(lis,list):
        lis = [lis]
    return lis

def ensureStringList(lis):
    lis = ensureList(lis)
    lis = [ensureUnicode(i) for i in lis]
    return lis

def makeAttribList(lis):
    lis = ensureList(lis)
    if len(lis) == 0:
        return lis
    ttype = type(lis[0])
    #handling of strings:
    if ttype in (str,str):
        lis = ensureStringList(lis) # this converts to unicode
        ttype = str
    if not all([isinstance(i,ttype) for i in lis]):
        raise TypeError('Entries in Attribute Lists all need to have the same datatype!')

    return lis

#not needed for python 3!
def ensureUnicode(string):
    if type(string) == str:
        return string
    else:
        return str(string,encoding)


def rename_to_ascii(filelist,recursive=False):
    filelist = ensureStringList(filelist)
    for f in filelist:
        #WARNING: this potentially moves/creates large unwanted directory #structures if there are unicode characters in the path until we #reach the file we are interested in, which is usually the last #segment of the path, but does not have to be there
        ascii = f.encode('ascii',errors='ignore').decode(encoding)
        if ascii != f:
            shutil.move(f,ascii)
            f = ascii
        if os.path.isdir(f) and recursive:
            for root, dirs, files in os.walk(ascii, topdown=True):
                #os.walk allows to modify the dirs array in place to
                #and then only uses the remaining/changed values further
                #down the tree
                for d in dirs:
                    ascii = d.encode('ascii',errors='ignore').decode(encoding)
                    if ascii != d:
                        shutil.move(os.path.join(root, d),os.path.join(root, ascii))
                        d = ascii

                for name in files:
                    ascii = name.encode('ascii',errors='ignore').decode(encoding)
                    if ascii != name:
                        shutil.move(os.path.join(root, name),os.path.join(root, ascii))
                        name = ascii
    return filelist
