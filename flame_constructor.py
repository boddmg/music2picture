# -*- coding: cp936 -*-
import fr0stlib
import xml.etree.cElementTree as etree
from fr0stlib.render import *
from xml.dom import minidom
import pygame
import numpy as np
import hashlib
from random import *
import colorsys

xform_const1=[['opacity','1.0'],
             ['weight','0.33333'],
             ['color','0.446'],
             ['color_speed',"0.5"],
             ['gaussian_blur',"0.7"],
             ['spiral',"0.549182653893"],
             ['animate',"1.0" ]]

xform_const2=[['opacity','1.0'],
             ['weight','0.33333'],
             ['color','1'],
             ['color_speed',"0.5"],
             ['swirl',"0.5"],
             ['horseshoe',"0.549182653893"],
             ['animate',"1.0" ]]

def getHash(data):
    return int(hashlib.new("md5", str(data)).hexdigest(),16)

def getAudio(path):
    pygame.mixer.init(44100,8,1,4096)
    audioData=pygame.sndarray.array(pygame.mixer.Sound(path))
    pygame.mixer.quit()
    return audioData

def findkey(subarray):
    
    nSampleNum = 44100.
    ncount = subsoundArray.size
    df = nSampleNum / ncount
    sampleTime = ncount / nSampleNum
    maxfreq=20000
    freqLine = maxfreq/df

    x = np.linspace(0,sampleTime,ncount)#时域波形x轴坐标

    fft = np.fft.fft(subsoundArray)[20/df:freqLine]  #调用fft变换算法计算频域波形
    fftx = np.linspace(20,df*freqLine,(maxfreq-20)/df)  #频域波形x轴坐标311)
    fftls=list(abs(fft))
    maxffts=max(fftls)
    maxfttsFrequency=fftx[fftls.index(maxffts)]
    return maxfttsFrequency/20000.0

def render(flame_string,level):
    c=wx.App()
    
    tree = etree.fromstring(flame_string)
    flame=[fr0stlib.Flame().from_element(e) for e in tree.findall('flame')][0]

    a=flam3_render(flame,[640,480],level)
    b=wx.BitmapFromBuffer(640,480,a)
    save_image("a.jpg",b)
    
def addXfromElement(flame,fromconst):
    xform=minidom.getDOMImplementation().createDocument(None, 'catalog', None).createElement('xform')
    for i in fromconst:
        xform.setAttribute(i[0],i[1])
    coefs=""
    for i in range(6):
        coefs+=str(random()*2-1)+' '
    coefs=coefs[:-1]
    xform.setAttribute('coefs',coefs)
    flame.appendChild(xform)
    return flame

def addColorElement(flame,index,hue):
    color=minidom.getDOMImplementation().createDocument(None, 'catalog', None).createElement('color')
    rgb=""
    for i in colorsys.hsv_to_rgb(hue,0.7,0.9):
        rgb+=str(int(i*255))+' '
    rgb=rgb[:-1]
    color.setAttribute('rgb',rgb)
    color.setAttribute('index',str(index))
    flame.appendChild(color)
    return flame

if __name__ == '__main__':
    flameDom=minidom.parseString(file("template/template2.flame").read())
    flame=flameDom.getElementsByTagName('flame')[0]

    flame=addXfromElement(flame,xform_const1)
    flame=addXfromElement(flame,xform_const2)
    flame=addXfromElement(flame,xform_const2)

    for i in range(256):
        flame=addColorElement(flame,i,i/255.0)
    
    flameDom.replaceChild(flame,flame)
    xml=flameDom.toprettyxml()[22:]
    file("a.flame",'w').write(xml)
    render(xml,100)
    '''
    musicInfo=[]
    soundArray=getAudio("升key.wav")
    for time in range(0,soundArray.size/255*255,soundArray.size/255):
        subsoundArray=soundArray[time:time+soundArray.size/255]
        musicInfo.append(findkey(subsoundArray))
    seed(getHash(musicInfo))
    print random()
    '''
