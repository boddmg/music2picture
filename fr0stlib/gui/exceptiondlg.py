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
import sys
import wx
import traceback
import pprint
from wx.lib.scrolledpanel import ScrolledPanel
from threading import current_thread


from fr0stlib.gui.config import config
from fr0stlib.decorators import *


def unhandled_exception_handler(exc_type, exc_value, exc_traceback):
    if current_thread().name != 'MainThread':
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    exception_info = {}

    frame = wx.GetApp().GetTopWindow()

    #exception_info['version'] = wx.GetApp.Version

    exception_info['traceback'] = ''.join(traceback.format_exception(
            exc_type, exc_value, exc_traceback))

    exception_info['config'] = pprint.pformat(config)
    exception_info['flamepath'] = pprint.pformat(
            getattr(frame, 'flamepath', '<not set>'))

    exception_info['platform'] = sys.platform

    exception_info['UserParametersDir'] = wx.GetApp().UserParametersDir
    exception_info['RendersDir'] = wx.GetApp().RendersDir
    exception_info['UserScriptsDir'] = wx.GetApp().UserScriptsDir
    exception_info['ConfigDir'] = wx.GetApp().ConfigDir
    exception_info['Frozen'] = wx.GetApp().Frozen
    exception_info['AppBaseDir'] = wx.GetApp().AppBaseDir
    exception_info['IconsDir'] = wx.GetApp().IconsDir

    msg = """Error:
%(traceback)s

Platform: %(platform)s


Config: 
%(config)s

Flame Path:
%(flamepath)s

UserParametersDir: %(UserParametersDir)s
RendersDir: %(RendersDir)s
UserScriptsDir: %(UserScriptsDir)s
ConfigDir: %(ConfigDir)s
Frozen: %(Frozen)s
AppBaseDir: %(AppBaseDir)s
IconsDir: %(IconsDir)s
""" % exception_info

    print msg

    dlg = ExceptionDialog(frame, exc_type, exc_value, exception_info, msg)
    rv = dlg.ShowModal()
    dlg.Destroy()

    # Pass it on to python to crash or not
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

    if rv == wx.ID_EXIT:
        sys.exit(1)



class ExceptionDialog(wx.Dialog):
    @BindEvents
    def __init__(self, parent, exc_type, exc_value, exc_info, exc_msg):
        wx.Dialog.__init__(self, parent, 
                title="fr0st has encountered an error")

        self.exc_msg = exc_msg

        self.show_label = "Show Error Report >>"
        self.hide_label = "Hide Error Report <<"

        self.collapsible = wx.CollapsiblePane(self, label=self.show_label)

        pane = self.collapsible.GetPane()
        scrolled = ScrolledPanel(pane, size=(500, 250),
                style = wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)

        text = wx.StaticText(scrolled, label=exc_msg)
        copy_clipboard = wx.Button(pane, label='Copy to clipboard')
        self.Bind(wx.EVT_BUTTON, self.OnCopyClipboard, copy_clipboard)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(text, 1, wx.EXPAND)
        scrolled.SetSizer(sizer)

        scrolled.SetAutoLayout(True)
        scrolled.SetupScrolling()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(copy_clipboard, 0, wx.ALIGN_RIGHT|wx.RIGHT, 15)
        sizer.Add(scrolled, 1, wx.EXPAND|wx.ALL, 15)
        pane.SetSizer(sizer)

        sizer = wx.BoxSizer(wx.VERTICAL)

        static = wx.StaticText(self, 
                label="fr0st has encountered an error and must exit.")
        static.Wrap(500)
        sizer.Add(static, 0, wx.EXPAND|wx.ALL, 5)

        static = wx.StaticText(self, label="%s: %s" % (
                    exc_type.__name__, str(exc_value)), style=wx.BORDER_SUNKEN)

        static.Wrap(500)
        sizer.Add(static, 0, wx.EXPAND|wx.ALL, 5)
        static = wx.StaticText(self, 
                label="If this problem persists, please consider posting "
                      "the error report to the mailing list.")
        static.Wrap(500)
        sizer.Add(static, 0, wx.EXPAND|wx.ALL, 5)

        sizer.Add(self.collapsible, 0, wx.EXPAND|wx.ALL, 5)

        quit_button = wx.Button(self, label='Exit fr0st', id=wx.ID_EXIT)
        self.Bind(wx.EVT_BUTTON, self.OnExitFr0st, quit_button)

        ok_button = wx.Button(self, label='OK', id=wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnOK, ok_button)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(quit_button, 0, wx.ALL, 5)

        #buttons = self.CreateButtonSizer(wx.OK)
        #buttons = self.CreateSeparatedButtonSizer(wx.OK)
        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT)

        self.SetSizerAndFit(sizer)

    def OnOK(self, evt):
        self.EndModal(evt.GetId())

    def OnExitFr0st(self, evt):
        self.EndModal(evt.GetId())

    def OnCopyClipboard(self, evt):
        data = wx.TextDataObject()
        
        if 'win32' in sys.platform:
            data.SetText(self.exc_msg.replace('\n', '\r\n'))
        else:
            data.SetText(self.exc_msg)

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()

    @Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED)
    def OnPanelCollapseChanged(self, evt):
        self.Layout()
        self.Fit()

        if evt.GetCollapsed():
            self.collapsible.SetLabel(self.show_label)
        else:
            self.collapsible.SetLabel(self.hide_label)
                








