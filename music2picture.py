# -*- coding: cp936 -*-
import fr0stlib
import xml.etree.ElementTree
import xml.etree.cElementTree as etree
from fr0stlib.render import *
from xml.dom import minidom
import pygame,hashlib,colorsys,sys,os
import numpy as np
from random import *
import wave

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
    audioData=wave.open(path)
    audioData=audioData.readframes(audioData.getnframes())
    audioData=np.fromstring(audioData, dtype=np.short)
    audioData.shape = -1, 2
    audioData = audioData.T
    audioData=audioData[0][0:-1:10]
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
    return maxfttsFrequency

def render(flame_string,level,path):
  
    tree = etree.fromstring(flame_string)
    flame=[fr0stlib.Flame().from_element(e) for e in tree.findall('flame')][0]

    a=flam3_render(flame,[640,480],level)
    b=wx.BitmapFromBuffer(640,480,a)
    save_image(path,b)
    
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

def getMusicFilePath():
    dialog = wx.FileDialog(None, message="选择要转换的音乐", defaultDir="", 
        defaultFile="", wildcard="Music (*.wav)|*.wav|All files (*.*)|*.*", style=0, 
        pos=wx.DefaultPosition)
    if dialog.ShowModal() == wx.ID_OK:
        path=dialog.GetPath()
    else:
        path=False
    dialog.Destroy()
    return path

def getImageFilePath():
    dialog = wx.FileDialog(None, message="选择转换图像保存的路径", defaultDir="", 
        defaultFile="", wildcard="Image (*.jpg)|*.jpg", style=wx.SAVE, 
        pos=wx.DefaultPosition)
    if dialog.ShowModal() == wx.ID_OK:
        path=dialog.GetPath()
        if path[-4] !=".":
            path=path+".jpg"
    else:
        path=False
    dialog.Destroy()
    return path

if __name__ == '__main__':    
    wxapp=wx.App()
    parentPath=os.path.split(sys.argv[0])[0]
    musicPath=getMusicFilePath()
    imagePath=getImageFilePath()
    #判断路径是否正常
    if musicPath and imagePath:
        print "开始分析音乐特征....."
        musicInfo=[]
        soundArray=getAudio(musicPath)[44100:-44100]
        musicSliceNum=256
        musicSliceSize=soundArray.size/musicSliceNum
        for time in range(musicSliceNum):
            subsoundArray=soundArray[time*musicSliceSize:musicSliceSize+time*musicSliceSize]
            musicInfo.append(findkey(subsoundArray))
        musicInfo=[e/2000 for e in musicInfo]
        seed(getHash(musicInfo))        #设置利用音乐特征设置随机种子
        print "分析音乐特征完成！"

        
        print "开始渲染图像....."

        flameDom=minidom.parseString(file(parentPath+"\\template\\template2.flame").read())
        flame=flameDom.getElementsByTagName('flame')[0]

        flame=addXfromElement(flame,xform_const1)
        flame=addXfromElement(flame,xform_const2)
        flame=addXfromElement(flame,xform_const2)

        for i in range(256):
            flame=addColorElement(flame,i,musicInfo[i])
        
        flameDom.replaceChild(flame,flame)
        xml=flameDom.toprettyxml()[22:]
        render(xml,500,imagePath)
        print "渲染图像完成！"

