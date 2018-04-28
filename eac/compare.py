
# coding: utf-8

# In[1]:


import cv2
import subprocess
import tempfile
import numpy as np
import scipy.spatial
import os




#input file
inp = 'SampleVideo_1280x720_1mb.mp4'


# ## Video transformation

# In[3]:

def get_video_descriptor(video,nfps=10,M=640,N=320,nkey=100):
    import encode
    # using ffmpeg and storing the file in a temp folder 
    # use the (modified) code from the Desktop pc with video conversion!
    #tempdir = tempfile.mkdtemp()
    #test the performance with QCIF (= 72×144) and 320x640
    
    #change fps to nfps (ffmpeg option is -r nfps)
    
    
    #change resolution to MxN with N=2xM (ffmpeg option is -s 2*NxN) 
    outpath = tempfile.mkdtemp()
    output = outpath + "\\" + os.path.split(video)[-1]
    encode.encode(video,outpath,inpath_is_file=True,quality='320x640',processes=1,options=['-r', nfps])
    
    fr,gfr,ts,te = get_keyframes(output,nkey,M=M,N=N,nfps=nfps)
    os.remove(outpath)
    return get_fingerprints(fr,gfr,ts,te)
    

def get_keyframes(video,nkey,N=320,M=640,nfps=10):
    #keyframes are averaged frames over a specific length 
    #we also need keyframes in grey color
    v = cv2.VideoCapture(video)
    
    keyframes = []
    graykeyframes = []
    nframes = 1
    key = np.zeros([M,N,3],dtype='float16')
    gray = np.zeros([M,N],dtype='float16')
    
    while(v.isOpened()):
        ret, frame = v.read()
        if frame is None:
            keyframes.append(key.astype('uint8'))
            graykeyframes.append(gray.astype('uint8'))
            break
        else:
            key = key + frame/(nkey)
            gray = gray + cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)/(nkey)
        if nframes == nkey:
            keyframes.append(key.astype('uint8'))
            graykeyframes.append(gray.astype('uint8'))
            nframes = 1
            key = np.zeros([M,N,3],dtype='float16')
            gray = np.zeros([M,N],dtype='float16')
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
# ## Create fingerprints

# In[75]:

def get_fingerprints(kframes,gkframes,tstart,tend):
    fprin = {'thumb': [],'cc': [],'orb': [],'tstart': [],'tend': []}
    orbfunc = cv2.ORB_create()
    thrs = 0.5
    
    for i,f in enumerate(kframes):
        ### 1. Fingerprint 
        th = thumbnail(gkframes[i])
        ### 2. Fingerprint
        cc = color_correlation(f)
        ### 3. Fingerprint (local)
        orb = orb_detection(f,orb=orbfunc)
        ### compare fingerprints to the previous fingerprint and discard too similar ones
        if i > 0:
            sim = compare_frame([th,cc,orb],[prev_th,prev_cc,prev_orb])
            if sim <= thrs:
                fprin['thumb'].append(th)
                fprin['cc'].append(cc)
                fprin['orb'].append(orb)
                fprin['tstart'].append(tstart[i])
                fprin['tend'].append(tend[i])
                prev_th = th
                prev_cc = cc
                prev_orb = orb
                norb = len(orb[0])
            else:
                #discard the keyframe with less orb points. Update the timestamps accordingly
                if len(orb[0]) > norb:
                    fprin['thumb'][-1] = th
                    fprin['cc'][-1] = cc
                    fprin['orb'][-1] = orb
                    fprin['tend'][-1] = tend[i]
                    prev_th = th
                    prev_cc = cc
                    prev_orb = orb
                    norb = len(orb[0])
                else:
                    fprin['tend'][-1] = tend[i]
        else:
            fprin['thumb'].append(th)
            fprin['cc'].append(cc)
            fprin['orb'].append(orb)
            fprin['tstart'].append(tstart[i])
            fprin['tend'].append(tend[i])
            prev_th = th
            prev_cc = cc
            prev_orb = orb
            norb = len(orb[0])        
            
    fprin['nframes'] = len(fprin['th'])      
    return fprin

# In[12]:


### 1. Fingerprint
def thumbnail(frame,interp=cv2.INTER_AREA):
    return cv2.resize(frame,(30,30),interpolation=interp)


# In[13]:


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


# In[15]:


# 3rd Fingerprint

def orb_detection(frame,orb=None):
    if orb == None:
        orb = cv2.ORB_create()

    # find the keypoints with ORB
    kp = orb.detect(frame,None)
    # compute the descriptors with ORB
    if len(kp)>0:
        kp, des = orb.compute(frame, kb)
        return des
    else:
        return []


# In[159]:


wth  = 0.25
wcc  = 0.25
worb = 0.50
qth  = 0.50
qcc  = 0.75
qorb = 0.70
def compare_frame(querry,source):
    cor = correlation(querry[0],source[0])
    if cor >= qth:
        dist_cc = distance(querry[1],source[1])
        if dist_cc >= qcc: 
            if len(querry[2]) > 0 and len(source[2]) > 0:
                dist_orb = match_orb(querry[2],source[2])
                if dist_orb >= qorb:
                    return wth * cor + wcc * dist_cc + worb *dist_orb
            else:
                return wth * cor + wcc * dist_cc
        else:
            return wth * cor
    else:
        return 0.0


# In[157]:


threshold = 0.5
def compare_clips(querry,source):
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
            sim = compare_frame([thq,ccq,orbq],[ths,ccs,orbs])
            
            if sim > threshold:
                if len(idf_q) > 0 and idf_q[-1] == i-1:
                    idf_q[-1] = i
                    end_match_q[-1] = querry['tend'][i]
                    idf_s[-1] = j
                    end_match_s[-1] = source['tend'][j]
                    score[-1] = max([score[-1],sim]) 
                else:
                    idf_q.append(i)
                    start_match_q.append(querry['tstart'][i])
                    end_match_q.append(querry['tend'][i])
                    idf_s.append(j)
                    start_match_s.append(source['tstart'][i])
                    end_match_s.append(source['tend'][j])
                    score.append(sim)
                    
    return {'idq': idf_q, 'tsq': start_match_q,'teq': end_match_q ,'ids': idf_s, 'tss': start_match_s,'tes': end_match_s, 'score': score }


# In[108]:


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


# In[107]:


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


# In[138]:


thorb = 0.7

def match_orb(querry,source):
    count = 0
    for q in querry:
        for s in source:
            if 1.0-distance_precomp(q,s,length=8) > thorb:
                count = count + 1
                break
                
    r = 1.0*count/len(querry)
    print(count,r)
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
                


# In[63]:


def correlation(querry,source):
    q = querry.flatten()
    s = source.flatten()
    return -(scipy.spatial.distance.correlation(q,s)-1.0)


# In[20]:


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

