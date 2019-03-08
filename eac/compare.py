import cv2
import subprocess
import tempfile
import numpy as np
import scipy.spatial
import os


# Video transformation
def get_video_descriptor(video,nfps=3,quality='320x640',nkey=180,processes=1):
    """
        compute the fingerprint file of a video file. 
    """
    import encode
    
    N_opts = {'320x640':320,'qcif':72}
    try:
        N = N_opts[quality]
        M = 2*N
    except:
        print 'Erro: not a valid quality option for the encoding'
        return
    #change resolution to MxN with N=2xM (ffmpeg option is -s 2*NxN) 
    outpath = tempfile.mkdtemp()
    output = outpath + "\\" + os.path.split(video)[-1]
    output = rreplace(output,output.split('.')[-1],'mp4',1)
    encode.encode(video,outpath,inpath_is_file=True,quality=quality,processes=processes,options=['-r', nfps])
    
    fr,gfr,ts,te = get_keyframes(output,nkey,M=M,N=N,nfps=nfps)
    
    for root, dirs, files in os.walk(outpath, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(outpath)
    
    return get_fingerprints(fr,gfr,ts,te)
    

def get_keyframes(video,nkey,N=320,M=640,nfps=10):
    """
        compute the keyframes of a video files
        
        keyframes are averaged frames over a specific length 
        we then extend the keyframe with a flipped version of itself, to prevent rotation attacks
        we also need keyframes in grey color for a better contrast
    """
    v = cv2.VideoCapture(video)
    
    keyframes = []
    graykeyframes = []
    nframes = 1
    key = np.zeros([M,N,3],dtype='uint32')
    gray = np.zeros([M,N],dtype='uint32')
    
    
    while(v.isOpened()):
        ret, frame = v.read()
    
        if frame is None:
            keyframes.append((key/nkey).astype('uint8'))
            graykeyframes.append((gray/nkey).astype('uint8'))
            break
        else:
            key = key + frame
            gray = gray + cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        
        if nframes == nkey:
            keyframes.append((key/nkey).astype('uint8'))
            graykeyframes.append((gray/nkey).astype('uint8'))
            nframes = 1
            key = np.zeros([M,N,3],dtype='uint32')
            gray = np.zeros([M,N],dtype='uint32')
        else:
            nframes = nframes + 1
        if cv2.waitKey(nfps) & 0xFF == ord('q'):
            break    
    
    #tstart and tend hold the timestamps of the keyframes in milliseconds
    tstart = [j * nkey/(1.0*nfps) * 1000.0 for j in range(len(keyframes))]
    tend = [j * nkey/(1.0*nfps) * 1000.0 for j in range(1,len(keyframes))]
    # nframes is the number of frames in the last keyframe. We use this to determine the endpoint of the movie.
    tend.append(((len(keyframes)-1)*nkey+nframes)/(1.0*nfps)*1000.0)
    
    #now flip the right side of the grey image and combine the original image with the flipped one to a MxM image
    flipgrey = [cv2.flip(i,0) for i in graykeyframes]
    #fliprgb = [cv2.flip(i,0) for i in keyframes]
    
    #kframes = np.zeros([len(keyframes),2*N,M,3],dtype='uint8')
    gkframes = np.zeros([len(graykeyframes),M,2*N],dtype='uint8')
    
    #for i,f in enumerate(keyframes):
    #    kframes[i,:N,:,:] = f
    #    kframes[i,N:,:,:] = fliprgb[i]
        
    for i,f in enumerate(graykeyframes):
        gkframes[i,:,:N] = f
        gkframes[i,:,N:] = flipgrey[i]

    return keyframes,gkframes,tstart,tend
    
    
# Create fingerprints
def get_fingerprints(kframes,gkframes,tstart,tend,thrs=0.5,nfeatures=400,nlevels=15):
    """
        get all the fingerprints of a keyframe.
        
        we have three different fingerprints:
            1. a thumbnail image for a quick pixel by pixel comparison
            2. a color histogram of all the pixels
            3. keypoints associated with edges on the image, 
               computed from intensity gradients (grey keyframe) 
    """
    fprin = {'thumb': [],'cc': [],'orb': [],'tstart': [],'tend': []}
    orbfunc = cv2.ORB_create(nfeatures=nfeatures,nlevels=nlevels)
    
    for i,f in enumerate(kframes):
        ### 1. Fingerprint 
        th = thumbnail(gkframes[i])
        ### 2. Fingerprint
        cc = color_correlation(f)
        ### 3. Fingerprint (local)
        orb = orb_detection(gkframes[i],orb=orbfunc)
        ### compare fingerprints to the previous fingerprint and discard too similar ones
        if i > 0:
            sim = compare_frame([th,cc,orb[1]],[prev_th,prev_cc,prev_orb])
            if sim <= thrs:
                fprin['thumb'].append(th)
                fprin['cc'].append(cc)
                fprin['orb'].append(orb[1])
                fprin['tstart'].append(tstart[i])
                fprin['tend'].append(tend[i])
                prev_th = th
                prev_cc = cc
                prev_orb = orb[1]
                norb = len(orb[0])
            else:
                #discard the keyframe with less orb points. Update the timestamps accordingly
                if len(orb[0]) > norb:
                    fprin['thumb'][-1] = th
                    fprin['cc'][-1] = cc
                    fprin['orb'][-1] = orb[1]
                    fprin['tend'][-1] = tend[i]
                    prev_th = th
                    prev_cc = cc
                    prev_orb = orb[1]
                    norb = len(orb[0])
                else:
                    fprin['tend'][-1] = tend[i]
        else:
            fprin['thumb'].append(th)
            fprin['cc'].append(cc)
            fprin['orb'].append(orb[1])
            fprin['tstart'].append(tstart[i])
            fprin['tend'].append(tend[i])
            prev_th = th
            prev_cc = cc
            prev_orb = orb[1]
            norb = len(orb[0]) 
    fprin['nframes'] = len(fprin['thumb'])      
    return fprin

def get_picture_descriptor(pictures,quality='320x640',interp=cv2.INTER_AREA):
    """
        get a single decriptor file for a picture folder. 
        All pictures in there will be used as "keyframes" 
        and can later be compared with the same algorithm as the video comparison.
        This way we can compare picture folders, 
        rather than comparing each picture with every other, 
        which potentially is very time consuming.
        
        paramters:
            pictures: a list of picture files that should be used for the descriptor
        keywords:
            quality: sets the size of the image from which the fingerprints are computed
            interp: which interpolation method should be used. Defaults to inter_area
    """
    
    orbfunc = cv2.ORB_create(nfeatures=400,nlevels=15)
    
    N_opts = {'320x640':320,'qcif':72}
    try:
        N = N_opts[quality]
        M = 2*N
    except:
        print 'Erro: not a valid quality option for the encoding'
        return
    
    #define the decriptor dictionary
    desc = {'thumb': [],'cc': [],'orb': [],'nframes': len(pictures)}

    #change resolution to MxN with N=2xM 
    for pic in pictures:
        img = cv2.imread(pic,1)
        if img is None:
            desc['nframes'] = desc['nframes']-1
            continue
        img = cv2.resize(img,(M,N),interpolation=interp)
        grey = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
        flip = cv2.flip(grey,0)
        grey = np.concatenate((grey,flip),axis=1)
        ### 1. Fingerprint 
        th = thumbnail(grey)
        desc['thumb'].append(th)
        ### 2. Fingerprint
        cc = color_correlation(img)
        desc['cc'].append(cc)
        ### 3. Fingerprint (local)
        orb = orb_detection(grey,orb=orbfunc)
        desc['orb'].append(orb[1])        
    
    return desc

### 1. Fingerprint
def thumbnail(frame,interp=cv2.INTER_AREA):
    """
        create a thumbnail with 30x30 pixel
    """
    return cv2.resize(frame,(30,30),interpolation=interp)

### 2. Fingerprint 
def color_correlation(frame,b=8):
    """
        computes the color correlation according to Lei, Luo, Wang, and Huang (2012)
        input:
            frame = a keyframe (color is assumed to be in gbr, as given from ocv2)
        output:
            cc = color correlation histogram
        
        function:
            1. divide the frame into bxb blocks and separately add up the red, green, and blue color components within these blocks
            2. decide on one of the 6 possible cases
                1 r > g > b
                2 r > b > g
                3 g > r > b
                4 g > b > r
                5 b > r > g
                6 b > g > r
             and make a histogram over all the all the blocks and normalize it
            3. return normalized histogram of the cases
    """
    
    rblock = []
    bblock = []
    gblock = []
    #Step 1:
    gblocks = blockshaped(frame[:,:,0],b,b)
    bblocks = blockshaped(frame[:,:,1],b,b)
    rblocks = blockshaped(frame[:,:,2],b,b)
    
    gb = np.array([np.sum(gblocks[i,:,:]) for i in range(len(gblocks[:,0,0]))])
    bb = np.array([np.sum(bblocks[i,:,:]) for i in range(len(bblocks[:,0,0]))])
    rb = np.array([np.sum(rblocks[i,:,:]) for i in range(len(rblocks[:,0,0]))])
    
                  
    #Step 2:
    hist = np.zeros(6)              
    for i in range(len(gb)):
        if rb[i]>gb[i] and gb[i]>bb[i]:
            hist[0] = hist[0]+1
        elif rb[i]>bb[i] and bb[i]>gb[i]:
            hist[1] = hist[1]+1
        elif gb[i]>rb[i] and rb[i]>bb[i]:
            hist[2] = hist[2]+1 
        elif gb[i]>bb[i] and bb[i]>rb[i]:
            hist[3] = hist[3]+1
        elif bb[i]>rb[i] and rb[i]>gb[i]:
            hist[4] = hist[4]+1 
        elif bb[i]>gb[i] and gb[i]>rb[i]:
            hist[5] = hist[5]+1 
    
    #Step 3
    norm = np.sum(hist)
    if norm != 0:
        hist = hist/norm
    hist = hist * 100
    return hist[:5].astype('uint8')

# 3rd Fingerprint
def orb_detection(frame,orb=None):
    """
        detects keypoints of an image according to the ORB function
    """
    if orb == None:
        orb = cv2.ORB_create()

    # find the keypoints with ORB
    kp = orb.detect(frame,None)
    # compute the descriptors with ORB
    if len(kp)>0:
        kp, des = orb.compute(frame, kp)
        return kp,des
    else:
        return [],[]


def compare_frame(querry,source,wth=0.25,wcc=0.25,worb=0.5,qth=0.5,qcc=0.75,qorb=0.7,orb_matcher=None):
    """
        compare the fingerprints of two keyframes and return a probability score of how similar they are
    """
    cor = correlation(querry[0],source[0])
    if cor >= qth:
        dist_cc = 1-distance_precomp(querry[1],source[1])
        if dist_cc >= qcc: 
            if len(querry[2]) > 0 and len(source[2]) > 0:
                dist_orb = match_orb(querry[2],source[2],matcher=orb_matcher)
                if dist_orb >= qorb:
                    return wth * cor + wcc * dist_cc + worb *dist_orb
                else:
                    return wth * cor + wcc * dist_cc
            else:
                return wth * cor + wcc * dist_cc
        else:
            return wth * cor
    else:
        return 0.0


def compare_clips(querry,source,threshold=0.75,orb_matcher=None):
    """
        compare two clips based on their keyframes. 
        Returns the maximum probability score of all the keyframe pairs 
    """
    start_match_q = []
    end_match_q = []
    idf_q = []
    start_match_s = []
    end_match_s = []
    idf_s = []
    score = []
    
    for i in range(querry['nframes']):
        if len(idf_q)>0 and idf_q[-1] == i-1:
            offset = idf_s[-1]+1
        else:
            offset = 0
            
        for j in range(offset,source['nframes']):
            thq = querry['thumb'][i]
            ths = source['thumb'][j]
            ccq = querry['cc'][i]
            ccs = source['cc'][j]
            orbq = querry['orb'][i]
            orbs = source['orb'][j]
            sim = compare_frame([thq,ccq,orbq],[ths,ccs,orbs],orb_matcher=orb_matcher)
            if sim > threshold:
                if len(idf_q) > 0 and idf_q[-1] == i-1:
                    idf_q[-1] = i
                    end_match_q[-1] = querry['tend'][i]
                    idf_s[-1] = j
                    end_match_s[-1] = source['tend'][j]
                    score[-1] = max([score[-1],sim*100]) 
                else:
                    idf_q.append(i)
                    start_match_q.append(querry['tstart'][i])
                    end_match_q.append(querry['tend'][i])
                    idf_s.append(j)
                    start_match_s.append(source['tstart'][j])
                    end_match_s.append(source['tend'][j])
                    score.append(sim*100)
                break

    return np.array([idf_q, start_match_q,end_match_q ,idf_s, start_match_s,end_match_s,score],dtype = 'uint32')

    
def compare_pictures(querry,source,threshold=0.75,orb_matcher=None):
    """
        compare two picture sets. 
        Returns the maximum probability score of all the picture pairs 
    """
    idf_q_start = []
    idf_q_end = []
    idf_s_start = []
    idf_s_end = []
    score = []
    for i in range(querry['nframes']):
        if len(idf_q_start)>0 and idf_q_end[-1] == i-1:
            offset = idf_s_start[-1]+1
        else:
            offset = 0
            
        for j in range(offset,source['nframes']):
            thq = querry['thumb'][i]
            ths = source['thumb'][j]
            ccq = querry['cc'][i]
            ccs = source['cc'][j]
            orbq = querry['orb'][i]
            orbs = source['orb'][j]
            sim = compare_frame([thq,ccq,orbq],[ths,ccs,orbs],orb_matcher=orb_matcher)
            if sim > threshold:
                if len(idf_q_start) > 0 and idf_q_end[-1] == i-1:
                    idf_q_end[-1] = i
                    idf_s_end[-1] = j
                    score[-1] = max([score[-1],sim*100]) 
                else:
                    idf_q_start.append(i)
                    idf_q_end.append(i)
                    idf_s_start.append(j)
                    idf_s_end.append(j)
                    score.append(sim*100)
                break

    return np.array([idf_q_start, idf_q_end, idf_s_start, idf_s_end,score],dtype = 'uint32')

def distance(querry,source,length=7):
    """
        computes the hamming distance between the two vectors querry and source:
            (#of 1s in bitwise_xor(querry, source) )/ (# of total bits) 
            
        keyword length: specifies, how many bits of the vector entries should be used for the normalization
                        default: 7 (assuming input with dtype='uint8', where only 7 bits are used)
                        
    """
    xor = np.bitwise_xor(querry,source)
    x = np.array([bin(i).count("1") for i in xor])
    return 1.0*np.sum(x)/(length*len(querry))


_nbits = np.array(
      [0, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 3, 2, 3, 3, 4, 1, 2, 2, 3, 2, 3, 3,
       4, 2, 3, 3, 4, 3, 4, 4, 5, 1, 2, 2, 3, 2, 3, 3, 4, 2, 3, 3, 4, 3, 4,
       4, 5, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 1, 2, 2, 3, 2,
       3, 3, 4, 2, 3, 3, 4, 3, 4, 4, 5, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5,
       4, 5, 5, 6, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 3, 4, 4,
       5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7, 1, 2, 2, 3, 2, 3, 3, 4, 2, 3,
       3, 4, 3, 4, 4, 5, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 2,
       3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5, 6, 3, 4, 4, 5, 4, 5, 5, 6,
       4, 5, 5, 6, 5, 6, 6, 7, 2, 3, 3, 4, 3, 4, 4, 5, 3, 4, 4, 5, 4, 5, 5,
       6, 3, 4, 4, 5, 4, 5, 5, 6, 4, 5, 5, 6, 5, 6, 6, 7, 3, 4, 4, 5, 4, 5,
       5, 6, 4, 5, 5, 6, 5, 6, 6, 7, 4, 5, 5, 6, 5, 6, 6, 7, 5, 6, 6, 7, 6,
       7, 7, 8], dtype='uint8')

def distance_precomp(querry,source,length=7):
    """
        computes the hamming distance between the two vectors querry and source:
            (#of 1s in bitwise_xor(querry, source) )/ (# of total bits) 
    
        This version uses a precomputed table for the number of 1s in ints up to a bit length of 8. 
        
        keyword length: specifies, how many bits of the vector entries should be used for the normalization
                        default: 7 (assuming input with dtype='uint8', where only 7 bits are used)
                        
    """

    xor = np.bitwise_xor(querry,source)
    x = _nbits[xor].sum()
    return 1.0*np.sum(x)/(length*len(querry))


def match_orb(querry,source,thorb=40,matcher=None):
    """
        compare the keypoints given and return a matching score 
        depending on which fraction of keypoints could be matched
        \\TODO is there a better method to do this, in case of very few keypoints?
    """
    if matcher == None:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    else:
        bf = matcher
    matches = bf.match(querry,source)
    
    count = 0
    for i in matches:
        if i.distance < thorb:
            count = count +1
    r = 1.0*count/len(querry)
    
    if r >= 0.7:
        return 1.0
    elif r >= 0.4:
        return 0.9
    elif r >= 0.2:
        return 0.8
    elif r >= 0.1:
        return 0.7
    else:
        return 0.0
                

def correlation(querry,source):
    """
        returns the correlation distance of two arrays 
        this is used to compare the thumbnail fingerprints
    """
    q = querry.flatten()
    s = source.flatten()
    return -(scipy.spatial.distance.correlation(q,s)-1.0)


def blockshaped(arr, nrows, ncols):
    """
    Return an array of shape (n, nrows, ncols) where
    n * nrows * ncols = arr.size

    If arr is a 2D array, the returned array should look like n subblocks with
    each subblock preserving the "physical" layout of arr.
    """
    h, w = arr.shape
    return (arr.reshape(h//nrows, nrows, -1, ncols)
               .swapaxes(1,2)
               .reshape(-1, nrows, ncols))
               
def rreplace(s,old,new,number):
    """
        replace the first 'number' appearances (from the right) of string 'old' with 'new'
    """
    li = s.rsplit(old, number)
    return new.join(li)
