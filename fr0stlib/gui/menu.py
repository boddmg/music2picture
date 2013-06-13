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
import wx
from functools import partial

from fr0stlib.gui.constants import ID


class Filemenu(wx.Menu):
    name = "&File"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.FNEW, "&New Flame\tCtrl-N"," Create a new flame")        
        self.Append(ID.FOPEN, "&Open...\tCtrl-O"," Open a flame file")
        self.AppendSeparator()
        self.Append(ID.FSAVE, "&Save\tCtrl-S"," Save a flame to a file")
        self.Append(ID.FSAVEAS, "Save &As...\tCtrl-Shift-S"," Save a flame to a file")
        self.AppendSeparator()
        self.Append(ID.RENDER, "&Render...\tCtrl-R"," Render a flame to an image")
        self.AppendSeparator()
        self.Append(ID.ABOUT, "A&bout"," Information about this program")
        self.AppendSeparator()
        self.Append(ID.EXIT,"E&xit\tCtrl-Q"," Terminate the program")


class Editmenu(wx.Menu):
    name = "&Edit"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.UNDO, "&Undo\tCtrl-Z", " Undo last change to the current flame.")
        self.Append(ID.UNDOALL, "U&ndo All\tCtrl-Shift-Z", " Undo all changes to the current flame.")
        self.Append(ID.REDO, "&Redo\tCtrl-Y", " Redo last change to the current flame.")
        self.Append(ID.REDOALL, "R&edo All\tCtrl-Shift-Y", "Redo all changes to the current flame.")
        self.AppendSeparator()
        self.Append(wx.ID_COPY, "&Copy\tCtrl-C", "Copy a flame to the clipboard.")
        self.Append(wx.ID_PASTE, "&Paste\tCtrl-V", "Open a flame from the clipboard.")
        self.AppendSeparator()
        self.Append(wx.ID_PREFERENCES, "Pre&ferences", "Edit preferences")
        
        
class Viewmenu(wx.Menu):
    name = "&View"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.PREVIEW, "&Preview\tCtrl-P", " Open the preview window.")


class Scriptmenu(wx.Menu):
    name = "&Script"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.RUN, "&Run\tF8"," Run currently open script")
        self.Append(ID.STOP, "&Stop\tF9"," Stop script execution")
        self.AppendSeparator()
        self.Append(ID.SOPEN, "&Open...\tCtrl-Shift-O"," Open a script file")
        self.AppendSeparator()
        self.Append(ID.EDITOR, "&Editor\tCtrl-E"," Open the script editor")


class EditorFilemenu(wx.Menu):
    name = "&File"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.SNEW, "&New Script\tCtrl-N"," Create a new script")
        self.Append(ID.SOPEN, "&Open...\tCtrl-O"," Open a script file")
        self.AppendSeparator()
        self.Append(ID.SSAVE, "&Save\tCtrl-S"," Save the current script")
        self.Append(ID.SSAVEAS, "Save &As...\tCtrl-Shift-S"," Save the current script to a new file")
        self.AppendSeparator()
        self.Append(ID.RUN, "&Run\tF8"," Run currently open script")
        self.Append(ID.STOP, "&Stop\tF9"," Stop script execution")
        self.AppendSeparator()
        self.Append(ID.EXIT,"E&xit\tCtrl-Q"," Close the editor")        


class EditorEditmenu(wx.Menu):
    name = "&Edit"
    def __init__(self):
        wx.Menu.__init__(self)
        self.Append(ID.UNDO, "&Undo\tCtrl-Z", "")
        self.Append(ID.REDO, "&Redo\tCtrl-Shift-Z", "")
        

def Create(lst, parent):
    menu = wx.MenuBar()
    map(menu.Append,*zip(*((menu(), menu.name) for menu in lst)))
    parent.SetMenuBar(menu)
    parent.menu = menu


CreateMenu = partial(Create, (Filemenu, Editmenu, Viewmenu, Scriptmenu))
CreateEditorMenu = partial(Create, (EditorFilemenu, EditorEditmenu))
