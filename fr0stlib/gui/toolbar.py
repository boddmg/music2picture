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
from fr0stlib.gui.constants import ID
from fr0stlib.gui.utils import LoadIcon

def GetBMP(name,client=wx.ART_TOOLBAR,size=(16,16)):
    return wx.ArtProvider.GetBitmap(name, client, size)


def CreateToolBar(parent):
    parent.tb = tb = parent.CreateToolBar(wx.TB_HORIZONTAL | wx.TB_FLAT)
    add = tb.AddSimpleTool
    
    add(ID.FNEW, GetBMP(wx.ART_NEW),
        "New", " New flame")
    add(ID.FOPEN, GetBMP(wx.ART_FILE_OPEN),
        "Open", " Open a flame file")
    add(ID.FSAVE, GetBMP(wx.ART_FLOPPY),
        "Save", " Save the current flame file.")    
    add(ID.FSAVEAS, GetBMP(wx.ART_FLOPPY),
        "Save as", " Save the current flame file to a different location.")
    tb.AddSeparator()
    add(ID.UNDO, GetBMP(wx.ART_UNDO),
        "Undo", " Undo the last change to the current flame.")    
    add(ID.REDO, GetBMP(wx.ART_REDO),
        "Redo", " Redo the last change to the current flame.")   
    tb.AddSeparator()   
    add(ID.SOPEN, GetBMP(wx.ART_FILE_OPEN),
        "Open Script", "")
    add(ID.RUN, LoadIcon('toolbar', 'Run'),
        "Run Script", " Run the currently loaded script file") 
    add(ID.STOP, LoadIcon('toolbar', 'Stop'),
        "Stop Script", " Stop script execution")
    add(ID.EDITOR, LoadIcon('toolbar', 'Script-Editor'),
        "Editor", " Open the script editor")
    tb.AddSeparator()
    add(ID.PREVIEW, LoadIcon('toolbar', 'Preview'),
        "Preview", " Open the preview frame")
    add(ID.RENDER, LoadIcon('toolbar', 'Render'),
        "Render", " Render flame to image file")
    
    tb.Realize()
    tb.toggle_run_stop = MakeToggleFunction(tb, ID.RUN, ID.STOP)


def CreateEditorToolBar(parent):
    parent.tb = tb = parent.CreateToolBar(wx.TB_HORIZONTAL | wx.TB_FLAT)
    add = tb.AddSimpleTool
 
    add(ID.SNEW, GetBMP(wx.ART_NEW),
        "New", " Long help for 'New'")
    add(ID.SOPEN, GetBMP(wx.ART_FILE_OPEN),
        "Open", " Long help for 'Open'")
    add(ID.SSAVE, GetBMP(wx.ART_FLOPPY),
        "Save", " Long help for 'Save'")
    add(ID.SSAVEAS, GetBMP(wx.ART_FLOPPY),
        "Save as", " Long help for 'Save as'")
    tb.AddSeparator()
    add(ID.RUN, LoadIcon('toolbar', 'Run'),
        "Run Script", " Run currently loaded script.")
    add(ID.STOP, LoadIcon('toolbar', 'Stop'),
        "Stop Script", " Stop script execution")

    tb.Realize()
    tb.toggle_run_stop = MakeToggleFunction(tb, ID.RUN, ID.STOP)


def MakeToggleFunction(tb, id1, id2):
    ids = id1, id2
    tools = map(tb.FindById, ids)
    pos = tb.GetToolPos(id1)
    tb.RemoveTool(id2)
    def toggle(flag):
        tb.RemoveTool(ids[not flag])
        tb.InsertToolItem(pos, tools[flag])
        tb.Realize()
    return toggle

