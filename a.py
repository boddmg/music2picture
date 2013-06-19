# -*- coding: cp936 -*-
import pymedia,os,wx

def getMusicFilePath():
    dialog = wx.FileDialog(None, message="选择要转换的音乐", defaultDir="", 
        defaultFile="", wildcard="Music (*.wav;*.wma;*.mp2;*.mp3;*.ac3;*.aac;*.flac;*.ogg)|*.wav;*.wma;*.mp2;*.mp3;*.ac3;*.aac;*.flac;*.ogg", style=0, 
        pos=wx.DefaultPosition)
    if dialog.ShowModal() == wx.ID_OK:
        path=dialog.GetPath()
    else:
        path=False
    dialog.Destroy()
    return path

wxapp=wx.App()
path=getMusicFilePath()
fileType=os.path.splitext(path)[1][1:]
musicData=open(path,'rb').read()
