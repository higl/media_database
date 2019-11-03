import os
import random
import sys
import sqlite3
from media_entry import *
import pickle
from time import time
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
    #//TODO convert strings into raw strings
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
        
        if os.path.isfile(d):
            self.connection = sqlite3.connect(d)
            self.connection.execute("PRAGMA foreign_keys = 1")

            if not self._check_db_(self.connection):
                raise Exception("""
                the database is not consistent with the current code version!
                maybe you are trying to connect to an older version, where no
                conversion method has been implemented or you are connecting to
                a database that is not a media database at all.
                """)
        else:
            self.connection = self._create_db_(d)
            self.fill()
        self.parent = os.path.normpath(parent)
        
        if os.path.getmtime(parent) > os.path.getmtime(d) or force_update:
            self.update()
        return
        
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
             style integer, 
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
        c.execute('''CREATE TABLE VideoEntries
            (mediaID integer, 
             actorMediaID integer, 
             tagMediaID integer, 
             genreMediaID integer,
             length real,
             FOREIGN KEY(mediaID) REFERENCES MediaEntries(mediaID))
            ''')
        c.execute('''CREATE TABLE MusicEntries
            (mediaID integer, 
             artistMediaID integer, 
             tagMediaID integer, 
             genreMediaID integer,
             ntracks integer,
             FOREIGN KEY(mediaID) REFERENCES MediaEntries(mediaID))
            ''')
        c.execute('''CREATE TABLE PictureEntries
            (mediaID integer, 
             tagMediaID integer,
             npics integer,
             FOREIGN KEY(mediaID) REFERENCES MediaEntries(mediaID))
            ''')
        c.execute('''CREATE TABLE ExecutableEntries
            (mediaID integer, 
             tagMediaID integer,
             FOREIGN KEY(mediaID) REFERENCES MediaEntries(mediaID))
            ''')
        
        # Tables and Indizes for each attribute
        c.execute('''CREATE TABLE Actor
            (actorID integer primary key, 
             name text)
            ''')
        c.execute('''CREATE UNIQUE INDEX actorName
            ON Actor(name);
            ''')          
        c.execute('''CREATE TABLE Artist
            (artistID integer primary key, 
             name text)
            ''')
        c.execute('''CREATE UNIQUE INDEX artistName
            ON Artist(name);
            ''')          
        c.execute('''CREATE TABLE Tag
            (tagID integer primary key, 
             name text)
            ''')
        c.execute('''CREATE UNIQUE INDEX tagName
            ON Tag(name);
            ''')          
        c.execute('''CREATE TABLE Genre
            (genreID integer primary key, 
             name text)
            ''')
        c.execute('''CREATE UNIQUE INDEX genreName
            ON Genre(name);
            ''')          
                  
        # Join Tables
        c.execute('''CREATE TABLE GenreMedia
            (genreMediaID integer, 
             genreID integer,
             FOREIGN KEY(genreMediaID) REFERENCES MediaEntries(mediaID),
             FOREIGN KEY(genreID) REFERENCES Genre(genreID))
            ''')
        c.execute('''CREATE TABLE ActorMedia
            (actorMediaID integer, 
             actorID integer,
             FOREIGN KEY(actorMediaID) REFERENCES MediaEntries(mediaID),
             FOREIGN KEY(actorID) REFERENCES Actor(actorID))
            ''')
        c.execute('''CREATE TABLE ArtistMedia
            (artistMediaID integer, 
             artistID integer,
             FOREIGN KEY(artistMediaID) REFERENCES MediaEntries(mediaID),
             FOREIGN KEY(artistID) REFERENCES Artist(artistID))
            ''')
        c.execute('''CREATE TABLE TagMedia
            (tagMediaID integer, 
             tagID integer,
             FOREIGN KEY(tagMediaID) REFERENCES MediaEntries(mediaID),
             FOREIGN KEY(tagID) REFERENCES Tag(tagID))
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
                    'VideoEntries',
                    'PictureEntries',
                    'MusicEntries',
                    'ExecutableEntriesEntries',
                    'Actor',
                    'Artist',
                    'Tag',
                    'Genre',
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
                name)
        
        return not curs.fetchone() == None
        
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

    def add_entry(self,new_entry,*args,**kwargs):
        """
            This function adds an media_entry to the database.
            
            If a media entry with the same path 
            already exists, nothing happens, i.e. we assume 
            that the current entry in the db is favoured over 
            the external new entry.  
            If the existing entry should be overwritten by 
            the external entry, then update_entry should be used.  
        """
        # the new logic requires that path is a relative path on top of parent
        # \\TODO this needs to be enforced in the rest of the code as well!
        path = new_entry.path
        typ = new_entry.type
        style = new_entry.style
        played = int(new_entry.played)
        attribs = new_entry.attribs
        
        #supported attribs gives the Attrib table 
        #and the corresponding Joining table
        supported_attribs = {
                    'actors': ['Actor','ActorMedia'],
                    'artist': ['Artist','ArtistMedia'],
                    'genre': ['Genre','GenreMedia'],
                    'tags': ['Tag','TagMedia'],
                    'ntracks': [] ,
                    'npics': [],
                    'length': [],
                    }
                    
        #supported types gives the Type table
        #and the corresponding number of common attrib columns
        #and the corresponding specific attrib columns
        supported_types = {
                    'exec': ['ExecutableEntries',1,[]],
                    'video': ['VideoEntries',3,['length']],
                    'music': ['MusicEntries',2,['ntracks']],
                    'picture': ['PictureEntries',1,['npics']]
                    }
        
        if typ not in supported_types:
            raise NotImplementedError
        if any([k not in supported_attribs for k in attribs]):
            raise NotImplementedError
        
        curs = self.connection.cursor()
        # create the entry in the main MediaEntryDB:
        try:
            curs.execute("""INSERT INTO MediaEntries VALUES 
                      (null,?,?,?,?)""",
                      (path,typ,style,played))
        except sqlite3.IntegrityError:
            return
        
        mediaid = curs.lastrowid
        
        # create the entry in the type DB
        querry = "INSERT INTO {} VALUES (?".format(supported_types[typ][0])
        querry = querry + ',?' * supported_types[typ][1] 
        querry = querry + ',?' * len(supported_types[typ][2])
        querry = querry + ');'
        params = [mediaid]*(supported_types[typ][1]+1)
        for a in supported_types[typ][2]:
            params.append(attribs[a])
        
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
                    curs.execute(querry,[e])
                    attribID = curs.lastrowid
                except sqlite3.IntegrityError:
                    querry = "SELECT ROWID FROM {} WHERE name=? ;".format(supported_attribs[a][0])
                    params = e
                    curs.execute(querry,[e])
                    attribID = curs.fetchone()[0]
                # create the entries in the corresponding JOIN Tables
                querry = "INSERT INTO {} VALUES (?,?) ;".format(supported_attribs[a][1])
                params = [mediaid,attribID] 
                curs.execute(querry,params)
        self.connection.commit()
        curs.close()
        return
        
    def delete_entry(self,entry):
        """
            remove a media entry from the database
        """
        
        supported_types = {
                   'exec': ['ExecutableEntries'],
                   'video': ['VideoEntries'],
                   'music': ['MusicEntries'],
                   'picture': ['PictureEntries'],
                   }
        
        join_tables = [
                ['GenreMedia','genreMediaID'],
                ['ActorMedia','actorMediaID'],
                ['ArtistMedia','artistMediaID'],
                ['TagMedia','tagMediaID'],
                ]
        
        curs = self.connection.cursor()
        #we use foreign keys to keep the tables consistend 
        #therefore we need to delete entries bottom up, starting with
        #the attrib join tables
        
        #get the identifier ID:
        querry = "SELECT ROWID FROM MediaEntries WHERE path = ? ;"
        path = [entry.path]
        curs.execute(querry,path)
        mediaID = curs.fetchone()[0]
        
        #delete entries from join_tables
        for t in join_tables:
            querry = "DELETE FROM {} WHERE {} = ? ;".format(t[0],t[1])
            curs.execute(querry,mediaID)
        
        #delete entry from media type db:
        table = supported_types[entry.type][0]
        querry = "DELETE FROM {} WHERE mediaID = ? ;".format(table)
        curs.execute(querry,mediaID)
        
        #finially we can delete the entry from the main db:
        querry = "DELETE FROM MediaEntries WHERE mediaID = ? ;"
        curs.execute(querry,mediaID)
        
        self.connection.commit()
        curs.close()
        return
    
    def clean_attrib_dbs(self):
        """
            remove entries in the attribute tables that are not used by any
            of the media entries
            - this might get very slow depending on the amount of attributes in the 
            various tables 
        """
        attrib_tables = [
                    'Actor',
                    'Artist',
                    'Genre',
                    'Tag',
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
                    curs.execute(querry,n)
                except sqlite3.IntegrityError:
                    pass
        self.connection.commit()
        curs.close()
        return
        
    def update_entry(self,entry):
            
    def get_random_entry(self,single=False,selection=None):
        """
            \TODO this needs to be reimplemented for sql
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
            \TODO this needs to be reimplemented for sql
            fills all the media entries in directory d into the media database
        """
        self.dlist = self.find_media_entries(d,ty)
        for d in self.dlist:
            for a in d.attrib.keys():
                if not a in self.alist:
                    self.alist[a] = 1
                else:
                    self.alist[a] = self.alist[a] + 1
        self.saved = False
    
    def update(self,d,ty='unknown'):
        """
            \TODO this needs to be reimplemented for sql
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
            \TODO this needs to be reimplemented for sql
            search for all folder/files in the directory d.
            It will create a media entry for each folder/file it finds.
            ty specifies the type of media entries that will be created
            if ty == unknown, the type of each media entry will be determined separately
        """
        res = []
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

            res.append(new_entry)
        return res
        
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
        
    
        

        
    def change_style(self):
        """
            \TODO this needs to be reimplemented for sql
            changes the execution style for a specific media entry type
            //TODO this has to be done for every element of the respective type
        """
        return None
        
    def get_selection(self,*args,**kwargs):
        """
            \TODO this needs to be reimplemented for sql
            filters all media entries. Uses the match_selection function of the entries
        """
        return None
        
    def get_entry(self,name):
        """
           \TODO this needs to be reimplemented for sql
            searches for a media entry by its hash
        """
        return None
    
    def find_entry(self,dstring):
        """
            \TODO this needs to be reimplemented for sql
            searches for a media entry by its display string
        """        
        return None
        
    def get_attrib_stat(self):
        """
            \TODO this needs to be reimplemented for sql
            returns statistics about the attributes 
            used in all the media entries of the database
        """        
        return None
    
    def get_entry_count(self):
        """
            \TODO this needs to be reimplemented for sql
            how many media entries do we have?
        """
        return None