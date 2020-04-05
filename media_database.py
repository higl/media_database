import os
import random
import sys
encoding = sys.getfilesystemencoding()
import sqlite3
import cv2
from media_entry import *
from mdb_util import *
import pickle
from time import time
import numpy as np
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
    """
        a media_database stores, media_entries. 
        It can save and load it from disk, 
        search through it and provide information
        needed to display the media entries properly 
    """
    import os
    import pickle
    #//TODO convert strings into unicode strings
    #//TODO make dlist a numpy array and then use the masking function for the reduced "unplayed" list in get_random_entry
    
    
    def __init__(self,d,p_style = 'first',v_style = 'random',m_style = 'random',e_style = 'first',force_update=False):
        self.parent = d
        self.hash = hash(d)
        
        cwd = os.getcwd()        
        for i in os.listdir(cwd):
            if os.path.split(i)[1] == str(self.hash)+'.pkl':
                self._load_(i)
                if os.path.getmtime(d) > self.mtime or force_update:
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
        """
            load a media database from filepath d
            \\TODO introduce versioning here
        """
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
        """
            save the media database to disk via pickle
            uses its own hash as the filename
        """
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
            
    def get_random_entry(self,single=False,selection=None):
        """
            gives back a random entry.

            If single=True it will make sure that items are not repeated,
            until every item has been selected once before 

            slection mode does not add to single mode
        """
        if selection != None:
            return self.find_entry(random.choice(selection))
        else: 
            elist = self.dlist            
            if single:
                mask = [i.played for i in elist]
                m = [i for (i,v) in zip(elist,mask) if not v]
                if len(m) == 0:
                    print('Congrats you\'ve seen it all')
                    for i in elist:
                        i.set_played(False)
                    m = elist
                return random.choice(m)
            else:
                return random.choice(elist)
        
    
    def fill(self,d,ty='unknown'):
        """
            fills all the media entries in directory d into the media database
        """
        self.dlist = self.find_media_entries(d,ty)
        for d in self.dlist:
            for a in d.attrib.keys():
                if not a in self.alist:
                    self.alist[a] = 1
                else:
                    self.alist[a] = self.alist[a] + 1
        saved = False
    
    def update(self,d,ty='unknown'):
        """
            if new media entries are created or old ones are deleted from disk,
            the media database will usually not react to it
            
            update searches the directory d and compares the media entries in it 
            with all the media entries. 
            Removes those that are not there anymore and
            adds those that are missing in the current list 
        """
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
        """
            search for all folder/files in the directory d.
            It will create a media entry for each folder/file it finds.
            ty specifies the type of media entries that will be created
            if ty == unknown, the type of each media entry will be determined separately
        """
        res = []
        for i in os.listdir(d):
            path = os.path.join(d,i)
            
            # skip the db file itself
            if path == self.db_path:
                continue 
            
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

        
    def delete_entry(self,entry):
        """
            remove a media entry from the database
        """
        self.dlist.remove(entry)
        for a in entry.attrib.keys():
            self.alist[a] = self.alist[a] - 1
            if self.alist[a] <= 0:
                self.alist.pop(a)
        
        self.saved = False
        self.mtime = time()
        
        
    def change_style(self):
        """
            changes the execution style for a specific media entry type
            //TODO this has to be done for every element of the respective type
        """
        print 'done'
        
    def get_selection(self,*args,**kwargs):
        """
            filters all media entries. Uses the match_selection function of the entries
        """
        l = []
        for i in self.dlist:
            if i.match_selection(*args,**kwargs):
                l.append(i.get_display_string())
        return l
        
    def get_entry(self,name):
        """
            searches for a media entry by its hash
        """
        # \\TODO is this used?
        hash = hash(name)
        for i in dlist:
            if i.hash() == hash:
                return i
        
        return None
    
    def find_entry(self,dstring):
        """
            searches for a media entry by its display string
        """
        for i in self.dlist:
            if i.get_display_string() == dstring:
                return i
        
        return None
        
    def get_attrib_stat(self):
        """
            returns statistics about the attributes 
            used in all the media entries of the database
        """
        attrib = {'Type':{'undefined':0}}
        empty = 0
        for i in self.dlist:
            if attrib['Type'].has_key(i.type):
                attrib['Type'][i.type] += 1
            else: 
                attrib['Type'][i.type] = 1
                
            entryattrib = i.attrib
            ekeys = entryattrib.keys()
            for j in ekeys:
                if not attrib.has_key(j):
                    attrib[j] = {'undefined':empty}
                    if len(entryattrib[j]) == 0:
                        attrib[j]['undefined'] += 1
                    else:    
                        for k in entryattrib[j]:
                            attrib[j][k] = 1
                elif len(entryattrib[j]) == 0:
                    attrib[j]['undefined'] += 1
                else:    
                    for k in entryattrib[j]:
                        if attrib[j].has_key(k):
                            attrib[j][k] += 1
                        else:
                            attrib[j][k] = 1
            for j in attrib.keys():
                if j != 'Type' and not entryattrib.has_key(j):
                    attrib[j]['undefined'] += 1
                    
            empty += 1
        
        return attrib
    
    def get_entry_count(self):
        """
            how many media entries do we have?
        """
        return len(self.dlist)
        
class media_database_sql:
    """
        \\always commit write operations before the cursor is closed!
        \\always close cursors at end of function 
        
        \\TODO for now the different attributes are hardcoded, in 
        \\order to easily add more attributes it might be worth 
        \\to make the attribute tables somewhat more flexible in the future
        a media_database stores, media_entries. 
        It can save and load it from disk, 
        search through it and provide information
        needed to display the media entries properly 
    """
    import os
    import pickle
    import sqlite3    
    
    def __init__(self,d,parent,p_style = 'first',v_style = 'random',m_style = 'random',e_style = 'first',force_update=False,legacy_load=False):
        """ Initialize a database connection. Create the database first if no other file is given.        
        """       
        
        self.parent = os.path.normpath(ensureUnicode(parent))
        self.parent = os.path.normcase(self.parent)
        self.db_path = os.path.abspath(ensureUnicode(d)) #this allows us to also store the 
                                                         #db in a relative path 
        self.db_path = os.path.normcase(self.db_path)
        
        self.p_style = ensureUnicode(p_style)
        self.v_style = ensureUnicode(v_style)
        self.m_style = ensureUnicode(m_style)
        self.e_style = ensureUnicode(e_style)

        if os.path.isfile(self.db_path):
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = 1")

            if not self._check_db_(self.connection):
                raise Exception("""
                the database is not consistent with the current code version!
                maybe you are trying to connect to an older version, where no
                conversion method has been implemented or you are connecting to
                a database that is not a media database at all.
                """)
        else:
            self.connection = self._create_db_(self.db_path)
            self.fill()
        
        if force_update:
            self.update()
        
        if legacy_load:
            self.hash = hash(parent)
            cwd = os.getcwd()        
            for i in os.listdir(cwd):
                if os.path.split(i)[1] == str(self.hash)+'.pkl':
                    self._convert_pkl_to_sqlite_(i,self.connection)
                    break
        return
        
    def _create_db_(self,d):
        """
            setup a media database and return the connector to it
        """
        connection = sqlite3.connect(d)
        connection.execute("PRAGMA foreign_keys = 1")        

        c = connection.cursor()
        # The main table:
        c.execute('''CREATE TABLE MediaEntries
            (mediaID integer primary key,
             path text, 
             type text, 
             style text, 
             played integer)
            ''')
        c.execute('''CREATE UNIQUE INDEX path
            ON MediaEntries(path);
            ''')          
                  
        # Tables for each media type. We even use the MediaEntries
        # table as our foreign key reference, which is then copied in the
        # columns of common attributes
        # specific type attributes for now need to 
        # come after the common attributes
        # but in the future single media types might have distinctive columns
        # (e.g. last_opened_id in Picture/Music entries) 
        
        
        # We use foreign keys here. From sqlite.org:
        # "Attempting to insert a row into the track table 
        # that does not correspond to any row in the artist 
        # table will fail, as will attempting to delete a row 
        # from the artist table when there exist dependent 
        # rows in the track table There is one exception: 
        # if the foreign key column in the track table is NULL, 
        # then no corresponding entry in the artist table is required."
        c.execute('''CREATE TABLE Type_Video
            (mediaID integer, 
             actorMediaID integer, 
             tagMediaID integer, 
             genreMediaID integer,
             length real,
             FOREIGN KEY(mediaID) REFERENCES MediaEntries(mediaID))
            ''')
        c.execute('''CREATE TABLE Type_Music
            (mediaID integer, 
             artistMediaID integer, 
             tagMediaID integer, 
             genreMediaID integer,
             ntracks integer,
             FOREIGN KEY(mediaID) REFERENCES MediaEntries(mediaID))
            ''')
        c.execute('''CREATE TABLE Type_Picture
            (mediaID integer, 
             tagMediaID integer,
             npics integer,
             FOREIGN KEY(mediaID) REFERENCES MediaEntries(mediaID))
            ''')
        c.execute('''CREATE TABLE Type_Executable
            (mediaID integer, 
             tagMediaID integer,
             FOREIGN KEY(mediaID) REFERENCES MediaEntries(mediaID))
            ''')
        
        # Tables and Indizes for each attribute
        c.execute('''CREATE TABLE Attribute_Actor
            (actorID integer primary key, 
             name text)
            ''')
        c.execute('''CREATE UNIQUE INDEX actorName
            ON Attribute_Actor(name);
            ''')          
        c.execute('''CREATE TABLE Attribute_Artist
            (artistID integer primary key, 
             name text)
            ''')
        c.execute('''CREATE UNIQUE INDEX artistName
            ON Attribute_Artist(name);
            ''')          
        c.execute('''CREATE TABLE Attribute_Tag
            (tagID integer primary key, 
             name text)
            ''')
        c.execute('''CREATE UNIQUE INDEX tagName
            ON Attribute_Tag(name);
            ''')          
        c.execute('''CREATE TABLE Attribute_Genre
            (genreID integer primary key, 
             name text)
            ''')
        c.execute('''CREATE UNIQUE INDEX genreName
            ON Attribute_Genre(name);
            ''')          
                  
        # Join Tables
        c.execute('''CREATE TABLE GenreMedia
            (genreMediaID integer, 
             genreID integer,
             FOREIGN KEY(genreMediaID) REFERENCES MediaEntries(mediaID),
             FOREIGN KEY(genreID) REFERENCES Attribute_Genre(genreID))
            ''')
        c.execute('''CREATE TABLE ActorMedia
            (actorMediaID integer, 
             actorID integer,
             FOREIGN KEY(actorMediaID) REFERENCES MediaEntries(mediaID),
             FOREIGN KEY(actorID) REFERENCES Attribute_Actor(actorID))
            ''')
        c.execute('''CREATE TABLE ArtistMedia
            (artistMediaID integer, 
             artistID integer,
             FOREIGN KEY(artistMediaID) REFERENCES MediaEntries(mediaID),
             FOREIGN KEY(artistID) REFERENCES Attribute_Artist(artistID))
            ''')
        c.execute('''CREATE TABLE TagMedia
            (tagMediaID integer, 
             tagID integer,
             FOREIGN KEY(tagMediaID) REFERENCES MediaEntries(mediaID),
             FOREIGN KEY(tagID) REFERENCES Attribute_Tag(tagID))
            ''')
                  
        connection.commit()
        c.close()
        
        return connection
    
    def _check_db_(self,conn):
        """
            check if the given database connection contains
            all the tables we need 
        """
        tablelist = [
                    'MediaEntries',
                    'Type_Video',
                    'Type_Picture',
                    'Type_Music',
                    'Type_Executable',
                    'Attribute_Actor',
                    'Attribute_Artist',
                    'Attribute_Tag',
                    'Attribute_Genre',
                    'GenreMedia',
                    'TagMedia',
                    'ActorMedia',
                    'ArtistMedia',
                    ]
        curs = conn.cursor()
        checks = [self._table_exists_(curs,t) for t in tablelist]
        curs.close()
        return all(checks)
        
    def _table_exists_(self,curs,name):
        """
            check if a table with name 'name' exists and return True
            if not, return False
        """
        curs.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?;""",
                [name])
        fetch = curs.fetchone()
        return not fetch == None
        
    def _convert_pkl_to_sqlite_(self,d,conn):
        """
            load a media database from filepath d in pickle format
            and add the data to the database we are connected to
        """
        
        with open(d, 'rb') as input:
            db = pickle.load(input)
            dlist = db['dlist']
            alist = db['alist']
            p_style = db['pstyle']
            m_style = db['mstyle']
            v_style = db['vstyle']
            e_style = db['estyle']
            mtime = db['mtime']
        
        self.add_entries(dlist)
        return
            

    def add_entry(self,new_entry,cursor=None,*args,**kwargs):
        """
            This function adds an media_entry to the database.
            
            If a media entry with the same path 
            already exists, nothing happens, i.e. we assume 
            that the current entry in the db is favoured over 
            the external new entry.  
            If the existing entry should be overwritten by 
            the external entry, then update_entry should be used.  
            
            special attributes are restricted to one element!
        """
        path = new_entry.get_display_string()
        if not os.path.exists(os.path.join(self.parent,path)):
            print """
                    ERROR: media database currently 
                    only supports media entries that are
                    located within 0.th level of the parent directory
                  """
            #raise NotImplementedError
        typ = new_entry.type
        style = new_entry.style
        played = int(new_entry.played)
        attribs = new_entry.attrib
        
        #supported attribs gives the Attrib table 
        #and the corresponding Joining table
        supported_attribs = {
                    'actors': ['Attribute_Actor','ActorMedia'],
                    'artist': ['Attribute_Artist','ArtistMedia'],
                    'genre': ['Attribute_Genre','GenreMedia'],
                    'tags': ['Attribute_Tag','TagMedia'],
                    'ntracks': [] ,
                    'npics': [],
                    'length': [],
                    }
                    
        #supported types gives the Type table
        #and the corresponding number of common attrib columns
        #and the corresponding specific attrib columns
        supported_types = {
                    'exec': ['Type_Executable',1,[]],
                    'video': ['Type_Video',3,['length']],
                    'music': ['Type_Music',2,['ntracks']],
                    'picture': ['Type_Picture',1,['npics']],
                    'unknown' : []
                    }
        
        if typ not in supported_types:
            raise NotImplementedError(
                '{} is not in the list of supported types'.format(typ)
                )
        if any([k not in supported_attribs for k in attribs]):
            error = ''
            for k in attribs:
                if k not in supported_attribs:
                    error = ' ' + error + k 
            raise NotImplementedError(
                '{} is not in the list of supported attributes'.format(error)
                )
                
        if cursor == None:
            curs = self.connection.cursor()
        else:
            curs = cursor

        # create the entry in the main MediaEntryDB:
        try:
            curs.execute("""INSERT INTO MediaEntries VALUES 
                      (null,?,?,?,?)""",
                      (path,typ,style,played))
        except sqlite3.IntegrityError:
            return
        
        mediaid = curs.lastrowid
        
        # create the entry in the type DB. Unknown Types have no type DB!
        if not typ == 'unknown':
            querry = "INSERT INTO {} VALUES (?".format(supported_types[typ][0])
            querry = querry + ',?' * supported_types[typ][1] 
            querry = querry + ',?' * len(supported_types[typ][2])
            querry = querry + ');'
            params = [mediaid]*(supported_types[typ][1]+1)
            for a in supported_types[typ][2]:
                params.append(attribs[a][0])
            curs.execute(querry,params)
        
        for a in attribs:
            if len(supported_attribs[a]) != 2:
                continue
            for e in attribs[a]:
                # create the entry in the Attribute DB,
                # \\TODO once we update to python3 we should 
                # \\change this querry to the INSERT ... ON CONFLICT DO ... 
                # \\syntax 
                querry = "INSERT INTO {} VALUES (null,?) ;".format(supported_attribs[a][0])
                try:
                    # e should already be a list
                    curs.execute(querry,[e])
                    attribID = curs.lastrowid
                except sqlite3.IntegrityError:
                    querry = "SELECT ROWID FROM {} WHERE name=? ;".format(supported_attribs[a][0])
                    params = e
                    e = self.sanitize_querry(e)
                    curs.execute(querry,[e])
                    attribID = curs.fetchone()[0]
                # create the entries in the corresponding JOIN Tables
                querry = "INSERT INTO {} VALUES (?,?) ;".format(supported_attribs[a][1])
                params = [mediaid,attribID] 
                curs.execute(querry,params)

        if cursor == None:
            self.connection.commit()
            curs.close()
        return
        
    def delete_entry(self,entry,cursor=None):
        """
            remove a media entry from the database
            
            if the media entry does not exists, this function silently exits
        """
        
        supported_types = {
                   'exec': ['Type_Executable'],
                   'video': ['Type_Video'],
                   'music': ['Type_Music'],
                   'picture': ['Type_Picture'],
                   'unknown': [],
                   }
        
        join_tables = [
                ['GenreMedia','genreMediaID'],
                ['ActorMedia','actorMediaID'],
                ['ArtistMedia','artistMediaID'],
                ['TagMedia','tagMediaID'],
                ]
        
        if cursor == None:
            curs = self.connection.cursor()
        else:
            curs = cursor

        #we use foreign keys to keep the tables consistend 
        #therefore we need to delete entries bottom up, starting with
        #the attrib join tables
        
        #get the identifier ID:
        querry = "SELECT ROWID FROM MediaEntries WHERE path = ? ;"
        path = [self.sanitize_querry(entry.get_display_string())]
        curs.execute(querry,path)
        mediaID = curs.fetchone()
        if mediaID != None:
            mediaID = mediaID[0]
        else: 
            # this entry does not exist in the tables, we silently exit here
            return
        
        #delete entries from join_tables
        for t in join_tables:
            querry = "DELETE FROM {} WHERE {} = ? ;".format(t[0],t[1])
            curs.execute(querry,[mediaID])
        
        if not entry.type == 'unknown':
            #delete entry from media type db:
            table = supported_types[entry.type][0]
            querry = "DELETE FROM {} WHERE mediaID = ? ;".format(table)
            curs.execute(querry,[mediaID])
        
        #finially we can delete the entry from the main db:
        querry = "DELETE FROM MediaEntries WHERE mediaID = ? ;"
        curs.execute(querry,[mediaID])
        
        if cursor == None:
            self.connection.commit()
            curs.close()
        return
    
    def clean_attrib_dbs(self):
        """
            remove entries in the attribute tables that are not used by any
            of the media entries
            - this might get very slow depending on the amount of attributes in the 
            various tables 
            
            /TODO redo this, using the attrib stats, so that we can avoid throwing database errors
        """
        attrib_tables = [
                    'Attribute_Actor',
                    'Attribute_Artist',
                    'Attribute_Genre',
                    'Attribute_Tag',
                    ]
        
        curs = self.connection.cursor()


        for table in attrib_tables:
            #get a list of all attributes in the table
            querry = "SELECT name FROM {}".format(table)
            curs.execute(querry)
            
            names = curs.fetchall()
            for n in names:
                querry = "DELETE FROM {} WHERE name = ?".format(table)
                try:
                    n = self.sanitize_querry(n)
                    curs.execute(querry,n)
                except sqlite3.IntegrityError:
                    pass
        self.connection.commit()
        curs.close()
        return
        
    def update_entry(self,entry,cursor=None,update_attrib=False):
        """
            This function updates a media_entry in the database.
            We always update the main table, but everything 
            in the type and attribute tables is only updated if 
            we use either update_attrib or if we change the type 
            of the entry 
        """
        path = entry.get_display_string()
        if not os.path.exists(os.path.join(self.parent,path)):
            print """
                    ERROR: media database currently 
                    only supports media entries that are
                    located within 0.th level of the parent directory
                  """
            raise NotImplementedError
        typ = entry.type
        style = entry.style
        played = int(entry.played)
        attribs = entry.attrib
        
        #supported attribs gives the Attrib table 
        #and the corresponding Joining table
        supported_attribs = {
                    'actors': ['Attribute_Actor','ActorMedia'],
                    'artist': ['Attribute_Artist','ArtistMedia'],
                    'genre': ['Attribute_Genre','GenreMedia'],
                    'tags': ['Attribute_Tag','TagMedia'],
                    'ntracks': [] ,
                    'npics': [],
                    'length': [],
                    }
                    
        #supported types gives the Type table
        #and the corresponding number of common attrib columns
        #and the corresponding specific attrib columns
        supported_types = {
                    'exec': ['Type_Executable',1,[]],
                    'video': ['Type_Video',3,['length']],
                    'music': ['Type_Music',2,['ntracks']],
                    'picture': ['Type_Picture',1,['npics']]
                    }
        
        if typ not in supported_types:
            raise NotImplementedError
        if any([k not in supported_attribs for k in attribs]):
            raise NotImplementedError
        
        if cursor == None:
            curs = self.connection.cursor()
        else:
            curs = cursor

        # determine if the media type was changed and get the mediaID
        p = self.sanitize_querry(path)
        curs.execute("""SELECT MediaID,type 
                    FROM MediaEntries 
                    WHERE
                        path = ? ;""",
                    [p])
        mediaid,otype = curs.fetchone()
        typechange = otype.__ne__(typ)
                
        # update the entry in the main MediaEntryDB:
        curs.execute("""UPDATE MediaEntries 
                    SET 
                        type = ?,
                        style = ?,
                        played = ?
                    WHERE
                        path = ? ;""",
                  (typ,style,played,p))
        
        
        # delete old entries in the attrib join tables 
        # if we change the type we also change the reference id in 
        # the attrib tables therefore we also need to delete the 
        # entries in the join tables     
        if typechange or update_attrib:
            for a in supported_attribs:
                tables = supported_attribs[a]
                if len(tables) != 2:
                    continue
                idcolumn = tables[1][0].lower() + tables[1][1:] + 'ID'
                
                querry = """
                            DELETE 
                            FROM {} 
                            WHERE {} = ? ;
                        """.format(tables[1],idcolumn)
                params = [mediaid] 
                curs.execute(querry,params)
                
        # update the entry in the type table, 
        # if the type was changed, create a new entry
        # and delete the old one in the respective tables
        if typechange:
            querry = """
                        DELETE 
                        FROM {} 
                        WHERE mediaID = ? ;
                     """.format(supported_types[otype][0])
            params = mediaid
            curs.execute(querry,params)
            
            querry = """
                        INSERT 
                        INTO {} 
                        VALUES (?
                    """.format(supported_types[typ][0])
            querry = querry + ',?' * supported_types[typ][1] 
            querry = querry + ',?' * len(supported_types[typ][2])
            querry = querry + ');'
            params = [mediaid]*(supported_types[typ][1]+1)
            for a in supported_types[typ][2]:
                params.append(attribs[a])
            curs.execute(querry,params)
        
        if typechange or update_attrib:
            for a in attribs:
                if len(supported_attribs[a]) != 2:
                    continue
                for e in attribs[a]:
                    # create the entry in the Attribute DB,
                    # \\TODO once we update to python3 we should 
                    # \\change this querry to the INSERT ... ON CONFLICT DO ... 
                    # \\syntax 
                    querry = "INSERT INTO {} VALUES (null,?) ;".format(supported_attribs[a][0])
                    try:
                        curs.execute(querry,[e])
                        attribID = curs.lastrowid
                    except sqlite3.IntegrityError:
                        querry = "SELECT ROWID FROM {} WHERE name=? ;".format(supported_attribs[a][0])
                        params = e
                        e = self.sanitize_querry(e)
                        curs.execute(querry,[e])
                        attribID = curs.fetchone()[0]
                    # create the entries in the corresponding JOIN Tables
                    querry = """
                                INSERT 
                                INTO {} 
                                VALUES (?,?) ;
                            """.format(supported_attribs[a][1])
                    params = [mediaid,attribID] 
                    curs.execute(querry,params)
        
        if cursor == None:
            self.connection.commit()
            curs.close()
        return    
    
    def create_media_entry_from_db(self,path):
        """
            this database acts as an intermediate layer between
            the media_entry types that are used in the gui and 
            the data saved on disk.
            We therefore need to be able to use the database entries to 
            create media_entries with the same information
            
            we will return the new media_entry instance
        """
        #we handle full paths as well as relative paths 
        #on top of the parent directory here
        #Be aware that the full path still needs to contain the parent path
        #and is only allowed to go 1 level deeper
        
        cwd = os.path.normcase(os.getcwd())
        if os.path.exists(path):
            split = os.path.split(os.path.normcase(path))
            if split[0] == self.parent or cwd == self.parent:
                path = split[1]
            else:
                raise AttributeError('{} is not part of the database'.format(path))
        else:
            join = os.path.join(self.parent,path)
            if not os.path.exists(join):
                raise AttributeError('{} is not part of the database'.format(join))
        
        supported_types = {
            'exec': [executable_entry,['tags']],
            'video': [video_entry,['tags', 'actors', 'genre']],
            'music': [music_entry,['tags', 'artist', 'genre']],
            'picture': [picture_entry,['tags']],
            'unknown': [media_entry, []],
            }

        supported_attribs = {
                    'actors': ['Attribute_Actor','ActorMedia','actorID','actorMediaID'],
                    'artist': ['Attribute_Artist','ArtistMedia','artistID','artistMediaID'],
                    'genre': ['Attribute_Genre','GenreMedia','genreID','genreMediaID'],
                    'tags': ['Attribute_Tag','TagMedia','tagID','tagMediaID'],
                    }
                    
        curs = self.connection.cursor()
        
        #select the rows from the main table and set the 
        #determined attributes
        querry = """SELECT 
                        type,
                        style,
                        played
                    FROM MediaEntries
                    WHERE path = ?"""
        path = self.sanitize_querry(path)
        curs.execute(querry, [path])
        res = curs.fetchone() #paths are unique!
        typ = res[0]
        style = res[1]
        played = bool(res[2])

        #for now there is no need to select any data from the 
        #type tables, because all quantities stored there, are 
        #calculated while entry creation. In the future this might change
        #which is why we give a template for those kind of selects here:
        
        attribs = {}
        for a in supported_types[typ][1]:
            tables = supported_attribs[a]
            querry = """SELECT 
                            {}.name AS name
                        FROM MediaEntries 
                            INNER JOIN {} ON {}.{} = MediaEntries.MediaID
                            INNER JOIN {} ON {}.{} = {}.{} 
                        WHERE path = ?
                    """.format(
                      tables[0],
                      tables[1],
                      tables[1],
                      tables[3],
                      tables[0],
                      tables[1],
                      tables[2],
                      tables[0],
                      tables[2]
                    )

            # path is already sanitized
            curs.execute(querry,[path])
            res = curs.fetchall()
            # we want to avoid adding empty attributes that are 
            # usually not connected with a type here 
            # the creator function takes care of typical attributes
            if len(res) > 0:
                attribs[a] = [i[0] for i in res]
        
        curs.close()
        
        creator = supported_types[typ][0]
        path = os.path.join(self.parent,path)
        # the creator function takes care of type handling
        entry = creator(path,style=style,played=played,**attribs)
        return entry
        
    def get_random_entry(self,single=False,selection=None):
        """
            gives back a random media entry instance, that is created from 
            a random entry in the media table or, if given, from a random
            element of a selection list.

            If single=True it will make sure that items are not repeated,
            until every item has been selected once before 

            selection mode does not add to single mode
        """
        if selection != None:
            if len(selection) == 0:
                return None
            return self.create_media_entry_from_db(random.choice(selection))
        elif single:            
            querry = """
                        SELECT
                            path
                        FROM
                            MediaEntries
                        WHERE played = 0 ;
                    """
        else:
            querry = """
                        SELECT
                            path
                        FROM
                            MediaEntries ;
                    """
        curs = self.connection.cursor()
        curs.execute(querry)
        selection = curs.fetchall()
        
        if len(selection) == 0: 
            if single:
                print('Congrats you\'ve seen it all')
                curs.execute(
                    """UPDATE MediaEntries 
                       SET 
                           played = 0 ;
                    """)
                curs.fetchall()
                curs.execute(querry)
                selection = curs.fetchall()
            else:
                selection = [None]
        curs.close()
        
        return self.create_media_entry_from_db(random.choice(selection)[0])
                
    
    def fill(self,ty='unknown'):
        """
            fills all the media entries in the parent directory into the media database
        """
        
        dlist = self.find_media_entries(self.parent,ty)

        self.add_entries(dlist)
        return
        
    def add_entries(self,elist):
        """
            add several entries
            this is more efficient than adding the entries 
            individually due to a combindes database commit
        """
        curs = self.connection.cursor()

        for e in elist:
            try:
                self.add_entry(e,cursor=curs)
                self.saved = False
            except sqlite3.IntegrityError:
                pass
        self.connection.commit()
        curs.close()
        return

    def delete_entries(self,elist):
        """
            delete several entries
            this is more efficient than adding the entries 
            individually due to a combindes database commit
        """
        curs = self.connection.cursor()

        for e in elist:
            self.delete_entry(e,cursor=curs)
            self.saved = False

        self.connection.commit()
        curs.close()
        return
                
    def update(self,ty='unknown'):
        """
            if new media entries are created or old ones are deleted from disk,
            the media database will usually not react to it
            
            update searches the parent folder and compares the media entries in it 
            with all the media entries. 
            Removes those that are not there anymore and
            adds those that are missing in the database 
        """
        inlist = [unicode(i,encoding) for i in os.listdir(self.parent)]

        curs = self.connection.cursor()
        
        querry = "SELECT path from MediaEntries"
        curs.execute(querry)
        curlist = curs.fetchall()
        curlist = [i[0] for i in curlist]
        
        curlist = sorted(curlist)
        inlist = sorted(inlist)
        
        toadd = []
        todelete = []


        #filter the db file itself 
        for i in inlist:
            if os.path.normcase(os.path.join(self.parent,i)) == self.db_path:
                inlist.remove(i)
        
        #the sorting part here is much faster than with simple filters
        #creating media entries, on the other hand, is very slow...
        offset = 0
        for e,i in enumerate(inlist):
            while curlist[e+offset] < i:
                entry = self.create_empty_entry(curlist[e+offset],'unknown')
                todelete.append(entry)
                offset = offset + 1
            if curlist[e+offset] > i:
                entry = self.create_empty_entry(i,'unknown')
                toadd.append(entry)
                offset = offset - 1

        if len(toadd) > 0:
            self.add_entries(toadd)
        if len(todelete) > 0:
            self.delete_entries(todelete)
            
        self.connection.commit()
        curs.close()
        self.saved = False
        return
        
    def find_media_entries(self,d,ty):
        """
            search for all folder/files in the directory d.
            It will create a media entry for each folder/file it finds.
            ty specifies the type of media entries that will be created
            if ty == unknown, the type of each media entry will be determined separately
        """
        res = []
        for i in os.listdir(d):
            path = os.path.join(d,i)
            # skip the db file itself
            if os.path.normcase(path) == self.db_path:
                continue
            
            res.append(self.create_empty_entry(path,ty))    

        return res
        
    def create_empty_entry(self,path,ty):
        """
            create an empty media entry object for a given path
            typ specifies the type of media entry that will be created
            if typ == unknown, the type of the media entry will be determined first
        """
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
        return new_entry
    
    
    def determine_media_type(self,path):
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
        
        for root,folder,files in os.walk(path):
            for f in files:
                if f.lower().endswith(accepted_picture_formats):
                    picture = True
                elif f.lower().endswith(accepted_video_formats):
                    video = True
                elif f.lower().endswith(accepted_music_formats):
                    music = True
                elif f.lower().endswith(accepted_execs):
                    ex = True

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
        
    
    def find_entry(self,dstring):
        """
            searches for a media entry by its display string
            
            since we now save the display strings in the database, 
            this is just a wrapper for create_media_entry_from_db
        """        
        return self.create_media_entry_from_db(dstring)

    def get_selection(self,*args,**kwargs):
        """
            filters all media entries based on a the kwargs dictionary
            passed to this function 
            
            keywords are filtered into global, common, and special attributes
            
            'global_mode' is a special keyword and can change the behaviour how 
            we combine the querries for each attribute at the end. 
            possible options are 'AND' or 'OR'. The default behaviour is 'AND'
            
            if a keyword does not fit into any of the groups, we will raise an
            error 
            
            we are using LIKE searches here for the string sql statements 
            once we are on python3 and a more recent sqlite version 
            we might want to change this to WHERE instr(*column*,'string') > 0 
            (which is then also case sensitive)
            
            \\TODO update gui to show and enable all possible selection attributes and options of this function. (use get_attribute_list and add another checkbox) 
        """        
        
        #We will have different querries for common and special attributes 
        #therefore we need to sort the selector attributes into those categories
        #we will also separate the 'global_mode' attribute as a special case
        
        try:
            global_mode = kwargs.pop('global_mode')
        except:
            global_mode = 'AND'
        
        curs = self.connection.cursor()
        
        special_attribs = self.get_attribute_list(cursor=curs,common=False,special=True,global_atr=False)
        common_attribs = self.get_attribute_list(cursor=curs,common=True,special=False,global_atr=False)
        global_attribs = self.get_attribute_list(cursor=curs,common=False,special=False,global_atr=True)
        
        global_selector = {}
        special_selector = {}
        common_selector = {}
        
        keys = kwargs.keys()
        for k in keys:
            if k in global_attribs:
                global_selector[k] = kwargs[k]
            elif k in special_attribs:
                special_selector[k] = kwargs[k]
            elif k in common_attribs:
                common_selector[k] = kwargs[k]
            else:
                raise NotImplementedError("""we cannot find the attrib {}. 
                                           The selector is therefore invalid""".format(k))
        
        results = []
        
        #first we make a querry on the global attributes stored in the main media table 
        for atr in global_selector:            
            isstring = self.is_string_attrib(atr,cursor=curs)
            s, mode = self.parse_input(global_selector[atr],like_prep=isstring)            
            if mode == 'GLOBAL':
                    mode = global_mode
            buf = self.execute_selector(curs,self.generate_global_attribute_querry,
                                        atr,s,mode,None,isstring)                
            results.append(buf)
            
            
        #now we search for the special attributes 
        #those are located in the type tables  
        for atr in special_selector:
            tables = self.get_associated_tables(atr,cursor=curs)
            isstring = self.is_string_attrib(atr,cursor=curs)            
            for t in tables:
                s, mode = self.parse_input(special_selector[atr],like_prep=isstring)                
                if mode == 'GLOBAL':
                    mode = global_mode                
                buf = self.execute_selector(curs,self.generate_special_attribute_querry,
                                            atr,s,mode,t,isstring)                    
                results.append(buf)


        #now we search for the common attributes - these are all strings!
        for atr in common_selector:
            s, mode = self.parse_input(common_selector[atr])
            if mode == 'GLOBAL':
                mode = global_mode            
            buf = self.execute_selector(curs,self.generate_common_attribute_querry,
                                        atr,s,mode,None,True)
            results.append(buf)

        if len(results) == 0:
            querry = """
                        SELECT mediaID, path FROM MediaEntries
                     """
            curs.execute(querry)
            res = curs.fetchall()
        elif global_mode == 'OR':
            res = []
            for r in results:
                res += r
        elif global_mode == 'AND':
            res = results[0]
            for check in results[1:]:
                res = filter(lambda x: x in check, res) 
        else:
            raise NotImplementedError('unknown selector mode')
        
        res = [ r[1] for r in res]
        res = sorted(set(res))
        
        curs.close()
        return res 

    def execute_selector(self,cursor,generator,attribute,words,mode,table,isstring):
        """
            execute the logic of the selector based on the mode and attribute type

            cursor: cursor to the database
            generator: generator function for the querry
            attribute: the name of the attribute
            words: list of words 
            mode: the mode of filtering ('AND' or 'OR')
            table: the name of the table (only really needed for special attributes)
            issting: is the attribute a string type?             
        """

        if mode == 'AND' and isstring:
            res = []
            for w in words:
                w = [w]
                querry = generator(attribute,table,w,mode,isstring) 
                cursor.execute(querry)
                res.append(cursor.fetchall())
            
            buf = res[0]
            for check in res[1:]:
                buf = filter(lambda x: x in check, buf)
        else:
            querry = generator(attribute,table,words,mode,isstring) 
            cursor.execute(querry)
            buf = cursor.fetchall()
        
        return buf 

    
    def generate_global_attribute_querry(self,attribute,table,words,mode,isstring):
        """
            create the querry to match with a global attribute 
        """

        querry = """
                    SELECT mediaID, path FROM MediaEntries WHERE
                 """
                
        if isstring:
            if len(words) > 1:
                querry += '\n'.join(['    {} LIKE {!r} {}'.format(attribute,w,mode) for w in words[:-1]])
            querry += '\n    {} LIKE {!r};'.format(attribute,words[-1])
        else:
            operators = []
            numbers = []
            for n in words:
                op,num = self.get_math_operator(n)
                operators.append(op)
                numbers.append(num)
                
            if len(words) > 1:
                querry += '\n'.join(
                    ['    {} {} {} {}'.format(attribute,o,n,mode) 
                        for o,n in zip(operators[:-1],numbers[:-1])
                    ]
                    )
            querry += '\n    {} {} {};'.format(attribute,operators[-1],numbers[-1]) 

        return querry

    def generate_common_attribute_querry(self,attribute,table,words,mode,isstring):
        """
            create the querry to match with a common attribute 

            Example:
            SELECT 
                MediaEntries.mediaID, MediaEntries.path
            FROM 
                MediaEntries 
                INNER JOIN ActorMedia ON ActorMedia.actorMediaID = MediaEntries.mediaID
                INNER JOIN Attribute_Actor ON ActorMedia.actorID = Attribute_Actor.actorID 
            WHERE path = ?
                 
        """              
        join_t = attribute + 'Media'
        attr_t = 'Attribute_' + attribute
        column = attribute.lower() + 'ID'
        join_c = attribute.lower() + 'MediaID'
        querry = """
                    SELECT 
                        MediaEntries.mediaID, MediaEntries.path 
                    FROM MediaEntries
                        INNER JOIN {} ON {}.{} = MediaEntries.mediaID
                        INNER JOIN {} ON {}.{} = {}.{}
                    WHERE
                 """.format(join_t,join_t,join_c,attr_t,join_t,column,attr_t,column)
        if len(words) > 1:    
            querry += '\n'.join(['    name LIKE {!r} {}'.format(w,mode) for w in words[:-1]])
        querry += '\n    name LIKE {!r};'.format(words[-1])
        
        return querry
    
    def generate_special_attribute_querry(self,attribute,table,words,mode,isstring):
        """
            create the querry to match with a special attribute 
        """
        querry = """
                    SELECT 
                        MediaEntries.mediaID, MediaEntries.path 
                    FROM 
                        MediaEntries
                        INNER JOIN {} ON {}.mediaID = MediaEntries.mediaID
                    WHERE
                 """.format(table,table)
                                     
        if isstring:
            if len(words) > 1:
                querry += '\n'.join(['    {} LIKE {!r} {}'.format(attribute,w,mode) for w in words[:-1]])
            querry += '\n    {} LIKE {!r};'.format(attribute,words[-1])
        else:
            operators = []
            numbers = []
            for n in words:
                op,num = self.get_math_operator(n)
                operators.append(op)
                numbers.append(num)
            
            if len(words) > 1:
                querry += '\n'.join(
                    ['    {} {} {} {}'.format(attribute,o,n,mode) 
                        for o,n in zip(operators[:-1],numbers[:-1])
                    ]
                    )
            querry += '\n    {} {} {};'.format(attribute,operators[-1],numbers[-1]) 

        return querry
        
    def parse_input(self,string,like_prep=True):
        """
            separate the input string into its words
            where double quotes can define words with 
            spaces and have to be accounted for
            
            a single quote will convert the rest 
            of the string into a single word
            
            like_prep == True:
                we also used this to sanitize the strings (escape characters)
                and to include '%' at the beginning and end of each word 
                to enable 'LIKE' searches
            
            if the first word is 'AND' or 'OR'
            we will perform the search for this specific 
            attribute in the respective mode. 
            Otherwise we will use the global mode that 
            is used to combine the searches for all attributes
        """
        split = string.split('"')
        
        querry = []
        for s in split[0::2]:
            querry += list(s.split(' '))
        
        if len(split) > 1:
            for s in split[1::2]:
                querry += [s]
        
        if querry[0] == 'AND':
            mode = 'AND'
            querry = querry[1:]
        elif querry[0] == 'OR': 
            mode = 'OR'
            querry = querry[1:]
        else:
            mode = 'GLOBAL'
        
        while True:
            try:
                querry.remove('')
            except:
                break
        
        if like_prep:
            for i,q in enumerate(querry):
                querry[i] = '%'+q+'%'
            
        return querry, mode
    
    def get_math_operator(self,string):
        """
            extract the math operator we need for the sql querry 
            for ints and floats 
        """
        
        if string.startswith(('<=','>=')):
            operator = string[:2]
            try:
                number = string[2:]
            except:
                print """
                      Warning no number associated with this operator. 
                      Do not leave spaces inbetween operator and number in search bar!
                      """
        elif string.startswith(('<','>','=')):
            operator = string[:1]
            try:
                number = string[1:]
            except:
                print """
                      Warning no number associated with this operator. 
                      Do not leave spaces inbetween operator and number in search bar!
                      """
        else:
            operator = '='
            number = string
            
        return operator, number 
    
    def get_type_list(self,cursor=None):
        """returns a list of all media types in the database 
        """
        if cursor == None:
            curs = self.connection.cursor()
        else:
            curs = cursor
        curs.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table';""")
        tables = curs.fetchall()
        
        if cursor == None:
            curs.close()
        
        type_names = []
        for t in tables:
            if t[0].startswith('Type_'):
                type_names.append(t[0][5:])
                
        return type_names
        
    def get_attribute_list(self,typ=None,cursor=None,common=True,special=True,global_atr=True):
        """returns a list of all possible attributes of either the whole database (type==None)
           or of a specific media type (type=="type")
        """
        
        #we have comman attributes and special attributs
        
        if cursor == None:
            curs = self.connection.cursor()
        else:
            curs = cursor
        
        attribs = []
        #global attributes are the column names of the MediaEntries table
        if global_atr:
            for row in curs.execute("pragma table_info('MediaEntries')").fetchall():
                attribs.append(row[1])
                    
        #common attributes can be found over their repective tables
        if common:
            curs.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table';""")
            tables = curs.fetchall()
        
            for t in tables:
                if t[0].startswith('Attribute_'):
                    attribs.append(t[0][10:])
        
        #special attributes can be found in the respective type tables
        if special or typ != None:
            if typ != None:
                typetables = [typ]
            else:
                typetables = self.get_type_list(cursor=curs)        
            if common and typ != None:
                mask = [False]*len(attribs)
            for t in typetables:
                t = 'Type_' + t
                for row in curs.execute("pragma table_info('{}')".format(t)).fetchall():
                    if special and not row[1].endswith('ID'):
                        # we are searching for special attributes
                        attribs.append(row[1])
                    if common and typ != None:
                        # we filter the common attributes that match the Type
                        for i,a in enumerate(attribs):
                            if (row[1].startswith(a.lower())
                                and row[1].endswith('MediaID')):
                                    mask[i] = True
        if common and typ != None:
            attr = [attribs[i] for i in range(len(mask)) if mask[i]]
            attribs = attr + attribs[len(mask):]
            
        if cursor == None:
            curs.close()
        
        return attribs 

    def get_associated_tables(self,attribute,cursor=None):
        """returns a list of all type tables associated with a given attribute 
        """
        
        if cursor == None:
            curs = self.connection.cursor()
        else:
            curs = cursor
        
        tables = []
                
        #special attributes can be found in the respective type tables
        typetables = self.get_type_list(cursor=curs)        
        
        for t in typetables:
            t = 'Type_' + t
            for row in curs.execute("pragma table_info('{}')".format(t)).fetchall():
                if ( row[1] == attribute or
                     (row[1].endswith('ID') and 
                      row[1].startswith(attribute.lower()))
                    ):
                    tables.append(t)

        
        if cursor == None:
            curs.close()
        
        return tables 

    def is_string_attrib(self,attribute,cursor=None):
        """determine if a attribute column is defined with a string data type
           
           this only makes sense for special attributes since common attributes are 
           always defined as strings! - We might want to lift this restriction in the future, 
                                        but currently I don't see a usable case for common (=many to many relationship)
                                        integer/float attributes 
        """
        
        if cursor == None:
            curs = self.connection.cursor()
        else:
            curs = cursor
                        
        #special attributes can be found in the respective type tables
        typetables = self.get_type_list(cursor=curs)        
        
        isstring = False
        for t in typetables:
            t = 'Type_' + t
            for row in curs.execute("pragma table_info('{}')".format(t)).fetchall():
                if row[1] == attribute and row[2] == 'text':
                    isstring = True
                    break
        # also check the main MediaEntries table!
        for row in curs.execute("pragma table_info('MediaEntries')").fetchall():
                if row[1] == attribute and row[2] == 'text':
                    isstring = True
                    break
                    
        if cursor == None:
            curs.close()
        
        return isstring
    
    def get_attrib_stat(self):
        """
            \TODO this needs to be reimplemented for sql
            returns statistics about the attributes 
            used in all the media entries of the database
        """
        curs = self.connection.cursor()
        stat = {}
        
        special_attribs = self.get_attribute_list(cursor=curs,common=False,special=True,global_atr=False)
        common_attribs = self.get_attribute_list(cursor=curs,common=True,special=False,global_atr=False)
        global_attribs = self.get_attribute_list(cursor=curs,common=False,special=False,global_atr=True)
        
        #global attribs are all in the MediaEntries table
        global_attribs.remove('path')   #unique attribute, no need for stats
        global_attribs.remove('mediaID')#unique attribute, no need for stats

        querry = """ SELECT """
        if len(global_attribs) > 1:
            querry += '\n'.join([' {}, '.format(attribute) for attribute in global_attribs[:-1]])
        querry += '{} \n'.format(global_attribs[-1])
        querry += """FROM MediaEntries ;"""
        
        curs.execute(querry)
        res = curs.fetchall()
        for i,attribute in enumerate(global_attribs):
            isstring = self.is_string_attrib(attribute)   
            buf = [r[i] for r in res]
            stat[attribute] = self.querry_statistics(buf,isstring)
         
        #special attributes 
        for attribute in special_attribs:
            isstring = self.is_string_attrib(attribute)
            tables = self.get_associated_tables(attribute,cursor=curs)
            for t in tables:
                querry = """ SELECT {} FROM {};""".format(attribute,t)
                curs.execute(querry)
                res = curs.fetchall()
                buf = [r[0] for r in res]
                stat[attribute] = self.querry_statistics(buf,isstring)

        #common attributes 
        for attribute in common_attribs:
            isstring = True
            attr_t = 'Attribute_' + attribute  
            join_t = attribute + 'Media'
            column = attribute.lower() + 'ID'
            querry = """
                    SELECT 
                        name 
                    FROM {}
                        INNER JOIN {} ON {}.{} = {}.{}
                    """.format(join_t,attr_t,join_t,column,attr_t,column)
            curs.execute(querry)
            res = curs.fetchall()
            buf = [r[0] for r in res]
            stat[attribute] = self.querry_statistics(buf,isstring)
        
        curs.close()
        return stat

    def querry_statistics(self,buf,isstring):
        """
           Analyse the result of a querry and return some statistics about it
        """
        result = {}
        if len(buf) == 0:
            return result
            
        if isstring:
            unique = set(buf)
            for u in unique:
                result[u] = buf.count(u)
        else:
            array = np.array(buf)
            max = np.max(array)
            min = np.min(array)
            if (max == 1 and min == 0) or (min == max and min in [0,1]): #we assume this is boolean
                result['True'] = np.sum(array)
                result['False'] = len(array) - result['True']
            else:
                bins = np.linspace(min, max+1, 11,dtype=array.dtype)
                digitized = np.digitize(array, bins)
                for e in np.arange(1,11):
                    str = '{:.1g} - {:.1g}'.format(bins[e-1],bins[e])
                    result[str] = len(array[digitized == e])
            
        return result
        
        
    def get_entry_count(self):
        """
            how many media entries do we have?
        """
        curs = self.connection.cursor()
        
        querry = "SELECT mediaID from MediaEntries"
        curs.execute(querry)
        curlist = curs.fetchall()
        ncount = len(curlist)
        
        curs.close()
        
        return ncount
    
    def sanitize_querry(self,path):
        """ replace special chars in sql querries with the appropriate escape characters
        """
        
        #chars = [u"'"]
        
        #for c in chars:
        #    path = path.replace(u"\\"+c,c) # protection from 'double sanitize'
        #    path = path.replace(c,u"\\"+c)
            
        return path