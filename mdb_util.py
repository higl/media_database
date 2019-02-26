import os

def rm_empty_folders(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for i in dirs:
            i = os.path.join(root, i)
            try:
                os.rmdir(i)
            except:
                pass