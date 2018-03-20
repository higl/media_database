import os
import subprocess
import tempfile

vformats = ('.avi', '.mp4', '.flv','.m4v','.wmv','.mpeg','.mkv','.mov','.rm','.mpg')

def encode(inpath,outpath,quality='low',encoder='ffmpeg',processes=1,audio='mp4',override=False):
    #\\TODO acceptedformats
    #\\TODO only do those files that are not already done
    f = findFiles(inpath,formats=vformats)
    
    #\\TODO clean that up and make it useable
    video_quality_presets = {
        'low': ['-c:v', 'mpeg4', '-sws_flags', 'bilinear', '-vf', 'scale=640:-1', '-qmin', '6', '-qmax', '9']
    }
    audio_presets = {
        'mp4': ['-c:a', 'libmp3lame', '-ab', '128000', '-copyts', '-q:a', '5', '-ac', '2', '-ar', '44100', '-async', '3']
    }
    if override:
        ffmpegopts =  ['-y','-i', inpath]
    else:
        ffmpegopts =  ['-n','-i', inpath]    
    
    if isinstance(quality,list):
        ffmpegopts += quality
    else:
        ffmpegopts += video_quality_presets[quality]
    
    ffmpegopts += audio_presets[audio]
    
    if processes:
        ffmpegopts += ['-threads', str(processes)]
    
    output = outpath + os.path.split(inpath)[-1]
    if override:
        i = 1
        while os.path.isfile(output):
            output = os.path.splitext(outpath + os.path.split(inpath)[-1])[0] + '_' + str(i) + os.path.splitext(output)[1]
            i += 1
        
    ffmpegopts += [output]
    
    encodercall = {
                   'ffmpeg': ['ffmpeg'] + ffmpegopts,
                  }
    with tempfile.TemporaryFile() as stdout:
        # try:
            subprocess.check_call(encodercall[encoder])
        # except subprocess.CalledProcessError as e:
            # stdout.seek(0)
            # raise e

def findFiles(path,formats=()):
    list = []
    if os.path.isdir(path):         
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                if len(formats) == 0:
                    list.append(os.path.join(root, name))
                elif name.endswith(formats):
                    list.append(os.path.join(root, name))
    return list