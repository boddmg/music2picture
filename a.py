# -*- coding: cp936 -*-
import wx,pygame
def getMusicFilePath():
    dialog = wx.FileDialog(None, message="选择要转换的音乐", defaultDir="", 
        defaultFile="", wildcard="Music (*.wav;*.mp3)|*.wav;*.mp3|All files (*.*)|*.*", style=0, 
        pos=wx.DefaultPosition)
    if dialog.ShowModal() == wx.ID_OK:
        path=dialog.GetPath()
    else:
        path=False
    dialog.Destroy()
    return path
