##############################################################################
#  Fractal Fr0st - fr0st
#  https://launchpad.net/fr0st
#
#  Copyright (C) 2009 by Vitor Bosshard <algorias@gmail.com>
#
#  Fractal Fr0st is free software; you can redistribute
#  it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Library General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this library; see the file COPYING.LIB.  If not, write to
#  the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#  Boston, MA 02111-1307, USA.
##############################################################################
import os, wx, sys
from  wx.lib.filebrowsebutton import FileBrowseButton

class SaveDialog(wx.Dialog):
    def __init__(self, parent, path, name):
        wx.Dialog.__init__(self, parent, -1, "Save a copy of flame",
                           size=(400,120))

        path = os.path.abspath(path)
        self.fbb = FileBrowseButton(self, -1, fileMask=parent.wildcard,
                                    labelText='File:  ', initialValue=path,
                                    fileMode=wx.SAVE)
        self.nametc = wx.TextCtrl(self, -1)
        self.nametc.SetValue(name)
        self.nametc.SetMinSize((200,27))

        ok = wx.Button(self, wx.ID_OK)
        cancel = wx.Button(self, wx.ID_CANCEL)
        ok.SetDefault()
        btnsizer = wx.StdDialogButtonSizer()
        btnsizer.AddButton(ok)
        btnsizer.AddButton(cancel)
        btnsizer.Realize()
        
        szr0 = wx.BoxSizer(wx.HORIZONTAL)
        szr0.Add(wx.StaticText(self, -1, "Name:"))
        szr0.Add(self.nametc)
                     
        szr = wx.BoxSizer(wx.VERTICAL)
        szr.AddMany(((self.fbb, 0, wx.EXPAND | wx.ALL, 2),
                     (szr0, 0, wx.EXPAND | wx.ALL, 2),
                     (btnsizer, 0, wx.ALL, 2)))
        
        self.SetSizerAndFit(szr)
        self.SetSize((400,self.Size[1]))


    def GetPath(self):
        return self.fbb.GetValue()


    def GetName(self):
        return self.nametc.GetValue()   
