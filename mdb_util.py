import os

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
    tmpstr = list(map(lambda x: x.lstrip(),tmpstr))
    tmpstr = list(map(lambda x: x.rstrip(),tmpstr)) 
    tmpstr = filter(lambda x: x != '', tmpstr)
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
    lis = [str(i) for i in lis]
    return lis

def makeAttribList(lis):
    lis = ensureList(lis)
    if len(lis) == 0:
        return lis
    ttype = type(lis[0])
    #handling of strings:
    if ttype in (str,unicode):
        ttype = basestring
    if not all([isinstance(i,ttype) for i in lis]):
        raise TypeError('Entries in Attribute Lists all need to have the same datatype!')
    
    return lis