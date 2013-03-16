# -*- coding: cp936 -*-
from pylab import *
import pygame
import numpy as np

pygame.mixer.init(44100,8,1,4096)
soundArray=pygame.sndarray.array(pygame.mixer.Sound("升key.wav"))
pygame.mixer.quit()

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
    return maxfttsFrequency,maxffts

def create_scales(musicFreAmpData):
    height=320
    #创建surface
    musicPictureSurface = pygame.surface.Surface((640, height))
    
    for x in range(640):
        _hue=[255*y for y in colorsys.hsv_to_rgb(x/640.,saturation,value)]
        _saturation =[255*y for y in colorsys.hsv_to_rgb(hue,x/640.,value)]
        _value =[255*y for y in colorsys.hsv_to_rgb(hue,saturation,x/640.)]

        line_rect = Rect(x, 0, 1, height)
        
        pygame.draw.rect(hue_scale_surface, _hue, line_rect)
        pygame.draw.rect(saturation_scale_surface, _saturation, line_rect)
        pygame.draw.rect(value_scale_surface, _value, line_rect)
        
    return hue_scale_surface, saturation_scale_surface, value_scale_surface

musicInfo=[]
for time in range(0,soundArray.size/44100*44100,4410):
    subsoundArray=soundArray[time:time+4410]
    musicInfo.append(findkey(subsoundArray))
print len(musicInfo)
