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
import wx, copy

from fr0stlib.decorators import *
from fr0stlib.gui.config import config, update_dict
from fr0stlib.gui.utils import NumberTextCtrl, Box
from fr0stlib.pyflam3.cuda import is_cuda_capable


class ConfigDialog(wx.Dialog):

    @BindEvents
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title='Preferences')

        # Save a copy of config to work with. Allows us to implement cancel
        self.local_config = copy.deepcopy(config)

        notebook = wx.Notebook(self, style=wx.BK_DEFAULT)
        notebook.AddPage(PreviewPanel(notebook),'Preview Quality', select=True)
        notebook.AddPage(RenderPanel(notebook), 'Renderer')
        notebook.AddPage(MiscPanel(notebook), 'Misc')

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 0, wx.ALL, 5)

        btnsizer = self.CreateButtonSizer(wx.OK|wx.CANCEL)
        if btnsizer:
            sizer.Add(btnsizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

        self.SetSizerAndFit(sizer)
        

    @Bind(wx.EVT_BUTTON, id=wx.ID_OK)
    def OnOK(self, e):
        update_dict(config, self.local_config)
        e.Skip()
        
        # Immediately update GUI to see changes in quality, etc.
        self.Parent.canvas.ShowFlame(rezoom=False)
        self.Parent.image.RenderPreview()
        self.Parent.previewframe.cache.clear()
        self.Parent.previewframe.RenderPreview()



class RenderPanel(wx.Panel):
    @BindEvents
    def __init__(self, parent):
        self.parent = parent.Parent
        wx.Panel.__init__(self, parent, -1)

        choices = ["flam3", "flam4"]
        
        self.rb = wx.RadioBox(self, -1, label="Renderer", choices=choices,
                              style=wx.RA_VERTICAL)
        self.rb.SetStringSelection(self.parent.local_config["renderer"])

        if not is_cuda_capable():
            self.rb.EnableItem(1, False)

        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(self.rb)
        self.SetSizerAndFit(szr)
        

    @Bind(wx.EVT_RADIOBOX)
    def OnRadio(self, e):
        self.parent.local_config["renderer"] = self.rb.GetStringSelection()
        

class PreviewPanel(wx.Panel):

    def __init__(self, parent):
        self.parent = parent.Parent
        wx.Panel.__init__(self, parent, -1)
        gbs = wx.GridBagSizer(5, 5)
        gbs.Add(self.CreateSmallPreviewSettings(self.parent), (0, 0), flag=wx.EXPAND)
        gbs.Add(self.CreateLargePreviewSettings(self.parent), (1, 0))
        gbs.Add(self.CreateXformPreviewSettings(self.parent), (0, 1), flag=wx.EXPAND)
        self.SetSizerAndFit(gbs)

    def CreateXformPreviewSettings(self, parent):
        gbs = wx.GridBagSizer(5, 5)
        gbs.AddGrowableCol(0)

        number_text(self, parent, gbs, 0, 'Range', 
                'Xform-Preview-Settings', 'range', 1.0, 5.0, set_focus=True)
        
        number_text(self, parent, gbs, 1, 'Quality', 
                'Xform-Preview-Settings', 'numvals', 5, 50, is_int=True)

        number_text(self, parent, gbs, 2, 'Depth',
                'Xform-Preview-Settings', 'depth', 1, 10, is_int=True) 

        return Box(self, 'Xform Preview', (gbs, 0, wx.EXPAND))

    def CreateSmallPreviewSettings(self, parent):
        gbs = wx.GridBagSizer(5, 5)
        gbs.AddGrowableCol(0)

        number_text(self, parent, gbs, 0, 'Quality', 
                'Preview-Settings', 'quality', 1, 100, is_int=True)

        number_text(self, parent, gbs, 1, 'Density Estimator', 
                'Preview-Settings', 'estimator', 0, 10) 

        number_text(self, parent, gbs, 2, 'Filter Radius', 
                'Preview-Settings', 'filter_radius', 0.0, 2.0)

        number_text(self, parent, gbs, 3, 'Oversample', 
                'Preview-Settings', 'spatial_oversample', 1, 4, is_int=True)
        return Box(self, 'Preview', (gbs, 0, wx.EXPAND))

    def CreateLargePreviewSettings(self, parent):
        gbs = wx.GridBagSizer(5, 5)
        gbs.AddGrowableCol(0)

        number_text(self, parent, gbs, 0, 'Quality', 
                'Large-Preview-Settings', 'quality', 1, 1000, is_int=True)

        number_text(self, parent, gbs, 1, 'Density Estimator', 
                'Large-Preview-Settings', 'estimator', 0, 10)

        number_text(self, parent, gbs, 2, 'Filter Radius', 
                'Large-Preview-Settings', 'filter_radius', 0.0, 2.0)

        number_text(self, parent, gbs, 3, 'Oversample', 
                'Large-Preview-Settings', 'spatial_oversample', 1, 4, is_int=True)

        return Box(self, 'Large Preview', (gbs, 0, wx.EXPAND))


class MiscPanel(wx.Panel):
    def __init__(self, parent):
        self.parent = parent.Parent
        wx.Panel.__init__(self, parent, -1)

        gbs = wx.GridBagSizer(5, 5)
##        gbs.AddGrowableCol(0)
        
        number_text(self, self.parent, gbs, 0, 'jpg Quality',
                    '', 'jpg-quality', 1, 100, is_int=True)
        
        self.SetSizerAndFit(gbs)
    

def number_text(panel, parent, sizer, row, label, config_section, config_key,
                min, max, is_int=False, set_focus=False):
    if config_section:
        section = parent.local_config[config_section]
    else:
        section = parent.local_config

    def cb(tempsave=False):
        section[config_key] = ntc.GetFloat()    
    ntc = NumberTextCtrl(panel, section[config_key], min, max, callback=cb)
    if is_int:
        ntc.MakeIntOnly()
    if set_focus:
        ntc.SetFocus()

    sizer.Add(wx.StaticText(panel, label=label), (row, 0), flag=wx.ALIGN_CENTER_VERTICAL)
    sizer.Add(ntc, (row, 1))
