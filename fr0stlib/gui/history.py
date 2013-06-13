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
import wx, os
from functools import partial

from fr0stlib.gui.config import config
from fr0stlib.gui.utils import ErrorMessage
from fr0stlib.gui.constants import NewIdRange


class MyFileHistory(wx.FileHistory):
    def __init__(self, parent, configname, callback, n=4):
        self.configname = configname
        self.callback = callback
        self.n = n

        self.id = NewIdRange(n)
        
        wx.FileHistory.__init__(self, n, idBase=self.id)
        map(self.AddFileToHistory, reversed(config[configname]))
        self.BindMenu(parent)


    def BindMenu(self, parent, menuindex=0, pos=2):
        menu = parent.menu.GetMenu(menuindex)

        recent = wx.Menu()
        menu.InsertMenu(pos, -1, "Recent &Files", recent)
        self.UseMenu(recent)
        self.AddFilesToThisMenu(recent)
        parent.Bind(wx.EVT_MENU_RANGE, partial(self.OnHistory, parent),
                    id=self.id, id2=self.id + self.n)
        

    def SaveToConfig(self):
        config[self.configname] = tuple(self.GetHistoryFile(i)
                                        for i in range(self.GetCount()))


    def OnHistory(self, parent, e):
        index = e.GetId() - self.id
        if not index:
            return
        path = self.GetHistoryFile(index)
        if not os.path.exists(path):
            ErrorMessage(parent, "Could not find %s." % path)
            self.RemoveFileFromHistory(index)
            return
        self.callback(path)
