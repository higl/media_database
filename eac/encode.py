import os
import subprocess
import tempfile

vformats = ('.avi', '.mp4', '.flv','.m4v','.wmv','.mpeg','.mkv','.mov','.rm','.mpg','.MP4')

def encode(inpath,outpath,inpath_is_file=False,quality='low',encoder='ffmpeg',processes=1,audio='mp4',override=False,options=None):
    """
        encodes videos with some predefined quality preset
        
        parameters:
            inpath: filepath or folder of the input 
            outpath: folder of the output
        
        keywords:
            inpath_is_file: is the input a single video file?
            quality: video quality preset, defaults to 'low'
            audio: audio quality preset, defaults to 'mp4'
            encoder: which encoder do we want to use, defaults to 'ffmpeg' ( = only one supported at the moment)
            processes: how many processes do we want to run
            override: if true we will override the output file if it already exists
            options: additional options to the encoder
    #\\TODO acceptedformats
    #\\TODO only do those files that are not already done
    """
    if not inpath_is_file:
        f = findFiles(inpath,formats=vformats)
    else:
        f = [inpath]
    
    #\\TODO clean that up and make it useable
    video_quality_presets = {
        'low': ['-c:v', 'mpeg4', '-sws_flags', 'bilinear', '-vf', 'scale=640:-1', '-qmin', '6', '-qmax', '9','-r', '30'],
        '320x640': ['-c:v', 'mpeg4', '-sws_flags', 'bilinear', '-vf', 'scale=320:640', '-qmin', '6', '-qmax', '9'],
        'qcif': ['-c:v', 'mpeg4', '-sws_flags', 'bilinear', '-vf', 'scale=72:144', '-qmin', '6', '-qmax', '9']
    }
    audio_presets = {
        'mp4': ['-c:a', 'libmp3lame', '-ab', '128000', '-copyts', '-q:a', '5', '-ac', '2', '-ar', '44100', '-async', '3']
    }
    for infile in f:
        if len(infile)>260:
            raise ValueError('input file path is too long')
        else:
            inp = infile
        if override:
            ffmpegopts =  ['-y','-i', inp]
        else:
            ffmpegopts =  ['-n','-i', inp]    
        
        if isinstance(quality,list):
            ffmpegopts += quality
        else:
            ffmpegopts += video_quality_presets[quality]
        
        ffmpegopts += audio_presets[audio]
        
        if processes:
            ffmpegopts += ['-threads', str(processes)]
        
        if options != None:
            for i in options:
                ffmpegopts.append(str(i))
        
        output = os.path.split(inp)[-1]
        output = rreplace(output,output.split('.')[-1],'mp4',1)
        output = outpath + "\\" + output
        if override:
            i = 1
            while os.path.isfile(output):
                output = os.path.splitext(outpath + "\\" +os.path.split(inp)[-1])[0] + '_' + str(i) + os.path.splitext(output)[1]
                i += 1
            
        ffmpegopts += [output]
        
        encodercall = {
                       'ffmpeg': ['ffmpeg'] + ffmpegopts,
                      }
        with tempfile.TemporaryFile() as stdout:
            try:
                subprocess.check_call(encodercall[encoder])
            except subprocess.CalledProcessError as e:
                pass
        
        if inpath_is_file:
            return output

def merge_videos(input,outpath,filename=None,override=True,remove=False,encoder='ffmpeg'):
    """
        merges video files into a single file
        does NOT reencode but just puts them together !
        
        parameters:
            input: a list of input filepaths
            outpath: the output folder
        keywords:    
            filename: the name of the merged video, if not set the filename will be
                      determined from the first entry in input
            override: if true we will override the output file if it already exists
            remove: if true we will delete the input files after the merge
            encoder: which encoder do we want to use, defaults to 'ffmpeg' ( = only one supported at the moment)
    """
    inpath = os.path.dirname(input[0])
    
    if filename != None:
        output = outpath+'\\'+filename
        if os.path.isfile(output) and not override:
            raise Exception
    else:
        output = os.path.split(input[0])[-1]
        output = os.path.splitext(output)[0] + '_all' + os.path.splitext(output)[1]
        output = outpath + "\\" + output
        if override:
            i = 1
            while os.path.isfile(output):
                output = os.path.splitext(outpath + "\\" +os.path.split(input[0])[-1])[0] + '_all_' + str(i) + os.path.splitext(output)[1]
                i += 1    
    
    mergelist = inpath+'\\merge.txt'
    
    with open(mergelist,'w') as file:
        for i in input:
            file.write("file \'" + i + "\'\n")
        
    if override:
        ffmpegopts =  ['-y','-f','concat','-safe', '0','-i', mergelist, '-c', 'copy']
    else:
        ffmpegopts =  ['-n','-f','concat','-safe', '0','-i', mergelist, '-c', 'copy']    
    
    ffmpegopts += [output]
    
    encodercall = {
                   'ffmpeg': ['ffmpeg'] + ffmpegopts,
                  }
    with tempfile.TemporaryFile() as stdout:
        try:
            subprocess.check_call(encodercall[encoder])
            os.remove(mergelist)
        except subprocess.CalledProcessError as e:
            os.remove(mergelist)
            pass
            
    if remove:
        for i in input:
            os.remove(i)
      
    return output


def cut_video(input,outpath,start,length,filename=None,override=True,encoder='ffmpeg'):
    """
        cut a part out of a video file 
        does NOT reencode but just picks it out!
        
        parameters:
            input: the input file
            outpath: the output folder
            start: the start point of the cut in seconds
            lenght: the length of the cut in seconds 
        keywords:    
            filename: the name of the merged video, if not set the filename will be
                      determined from the input
            override: if true we will override the output file if it already exists
            encoder: which encoder do we want to use, defaults to 'ffmpeg' ( = only one supported at the moment)
    """    
    if filename != None:
        output = outpath+'\\'+filename
        if os.path.isfile(output) and not override:
            raise Exception
    else:
        output = os.path.split(input)[-1]
        output = outpath + "\\" + output
        if override:
            i = 1
            while os.path.isfile(output):
                output = os.path.splitext(outpath + "\\" +os.path.split(input)[-1])[0] + '_' + str(i) + os.path.splitext(output)[1]
                i += 1    
            
    if override:
        ffmpegopts =  ['-y','-ss', '%.3f' %start ,'-i', input, '-c', 'copy']
    else:
        ffmpegopts =  ['-n','-ss', '%.3f' %start ,'-i', input, '-c', 'copy']    
    
    if length > 0:
        ffmpegopts += ['-t','%.3f' %length]
        
    ffmpegopts += [output]
    
    encodercall = {
                   'ffmpeg': ['ffmpeg'] + ffmpegopts,
                  }
    with tempfile.TemporaryFile() as stdout:
        try:
            subprocess.check_call(encodercall[encoder])
        except subprocess.CalledProcessError as e:
            pass
      
    return output    

    
def findFiles(path,formats=()):
    """
        find all video files in path that have the specified formats
    """
    list = []
    if os.path.isdir(path):         
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                if len(formats) == 0:
                    list.append(os.path.join(root, name))
                elif name.endswith(formats):
                    list.append(os.path.join(root, name))
    return list
    
def rreplace(s,old,new,number):
    """
        replace the first 'number' appearances (from the right) of string 'old' with 'new'
    """
    li = s.rsplit(old, number)
    return new.join(li)