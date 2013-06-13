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

from fr0stlib.decorators import *


def ErrorMessage(self, msg):
    wx.MessageDialog(self, msg, 'Fr0st', wx.OK | wx.ICON_ERROR).ShowModal()

    
def validate_path(path):
    """Returns None if path is valid and user has write permission. Otherwise,
    return the generated exception."""
    exists = os.path.exists(path)
    dirname = os.path.dirname(path)
    try:
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        open(path, 'a').close()
        if not exists:
            os.remove(path)
    except Exception as e:
        return e


def IsInvalidPath(parent, path):
    e = validate_path(path)
    if e is None:
        return False
    ErrorMessage(parent, "Can't write to path:\n%s" %e)
    return True
        

def LoadIcon(*path):
    # Check for an icons dir in app base path first for development
    filename = os.path.join(wx.GetApp().AppBaseDir, 'icons', *path) + '.png'

    if not os.path.exists(filename):
        # Not there, check install path
        filename = os.path.join(wx.GetApp().IconsDir, *path) + '.png'

    img = wx.Image(filename, type=wx.BITMAP_TYPE_PNG)
    img.Rescale(16,16)
    return wx.BitmapFromImage(img)


def Box(self, name, *a, **k):
    box = wx.StaticBoxSizer(wx.StaticBox(self, -1, name),
                            k.get('orient', wx.VERTICAL))
    box.AddMany(a)
    return box


def MakeTCs(parent, *a, **k):
    fgs = wx.FlexGridSizer(99, 2, 1, 1)
    tcs = {}
    for i, default in a:
        tc = NumberTextCtrl(parent, default, **k)
        tcs[i] = tc
        fgs.Add(wx.StaticText(parent, -1, i.replace("_", " ").title()),
                0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        fgs.Add(tc, 0, wx.ALIGN_RIGHT, 5)
    return fgs, tcs


def MakeChoices(parent, *a, **k):
    fgs = k.pop("fgs", None) or wx.FlexGridSizer(99, 2, 1, 1)
    d = {}
    for i, choices, default in a:
        widg = MyChoice(parent, i, choices, default, **k)
        d[i] = widg
        fgs.Add(wx.StaticText(parent, -1, i.replace("_", " ").title()),
                0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        fgs.Add(widg, 0, wx.ALIGN_RIGHT, 5)
    return fgs, d



class MyChoice(wx.Choice):
    @BindEvents
    def __init__(self, parent, name, d, initial=None, callback=None):
        choices = sorted(d.iteritems())
        self.str_val_dict = d
        self.val_pos_dict = dict((v, i) for (i,(k,v)) in enumerate(choices))
        
        wx.Choice.__init__(self, parent, -1, choices=[k for k,_ in choices])
        if initial is not None:
            self.Set(initial)
        self.callback = callback or (lambda: None)
        

    def Get(self):
        return self.str_val_dict[self.GetStringSelection()]

    def Set(self, v):
        self.SetSelection(self.val_pos_dict[v])


    @Bind(wx.EVT_CHOICE)
    def OnSelection(self, e):
        self.callback()



class SizePanel(wx.Panel):
    def __init__(self, parent, callback=lambda: None):
        self.parent = parent
        self.keepratio = True
        self.callback = callback
        wx.Panel.__init__(self, parent, -1)

        fgs, tcs = MakeTCs(self, ("width", 512.), ("height", 384.), low=0,
                           callback=self.SizeCallback)
        self.__dict__.update(tcs)
        for i in (self.width, self.height):
            i.MakeIntOnly()
            i.low = 1

        ratio = wx.CheckBox(self, -1, "Keep Ratio")
        ratio.SetValue(True)
        ratio.Bind(wx.EVT_CHECKBOX, self.OnRatio)

        box = Box(self, "Size", fgs, ratio)
        self.SetSizer(box)
        box.Fit(self)
    

    @property
    def Size(self):
        return [tc.GetFloat() for tc in (self.width, self.height)]
    @Size.setter
    def Size(self, size):
        width, height = size
        self.width.SetFloat(width)
        self.height.SetFloat(height)
        self._oldsize = size


    def OnRatio(self, e):
        self.keepratio = e.GetInt()


    def SizeCallback(self, tempsave=True):
        if self.keepratio:
            w, h = self.Size
            oldw, oldh = self._oldsize
            newsize = (int(w * h / float(oldh)), int(h * w / float(oldw)))
            self.Size = newsize
        else:
            self._oldsize = self.Size
        self.callback(tempsave)



class NumberTextCtrl(wx.TextCtrl):
    @BindEvents
    def __init__(self, parent, val=0.0, low=None, high=None, callback=None,
                 int_only=False):
        self.parent = parent
        # Size is set to ubuntu default (75,27), maybe make it 75x21 in win
        wx.TextCtrl.__init__(self,parent,-1, size=(75,27))
        
        self.SetAllowedRange(low, high)
        self.callback = callback or (lambda tempsave=None: None)
        self.int_only = int_only
        self.SetFloat(val)
        self.has_changed = False

        

    def GetFloat(self):
        if self.int_only:
            return self.GetInt()
        try:
            return float(self.GetValue() or "0")
        except ValueError:
            self.SetFloat(self._old_val)
            return self._old_val

    def SetFloat(self, v):
        if self.int_only:
            return self.SetInt(v)
        v = self.ClipToRange(float(v))
        self._old_val = v
        string = ("%.6f" %v).rstrip("0")
        if string.endswith("."):
            string += "0" # Avoid values like '0.' or '1.'
        self.SetValue(string)


    def GetInt(self):
        try:
            return int(float(self.GetValue() or "0"))
        except ValueError:
            self.SetInt(self._old_val)
            return self._old_val

    def SetInt(self, v):
        v = self.ClipToRange(int(v))
        self._old_val = v
        self.SetValue(str(v))


    # Aliases for compatibility with other widgets (e.g. MyChoice)
    Get = GetFloat
    Set = SetFloat


    def MakeIntOnly(self):
        #HACK: this method is left here for the sake of existing code only
        self.SetInt(self.GetFloat())
        self.int_only = True
        

    def SetAllowedRange(self, low=None, high=None):
        self.low = low
        self.high = high


    def ClipToRange(self, v):
        if self.low is not None and v < self.low:
            return self.low
        elif self.high is not None and v > self.high:
            return self.high
        return v


    @Bind(wx.EVT_MOUSEWHEEL)
    def OnMouseWheel(self, evt):
        if evt.CmdDown():
            if evt.AltDown():
                delta = 0.01
            else:
                delta = 0.1
        elif evt.AltDown():
            delta = 0.001
        else:
            evt.Skip()
            return

        if self.int_only:
            delta *= 1000 # change intervals to 1, 10 and 100

        self.SetFocus() # Makes sure OnKeyUp gets called.

        v = self.GetFloat() + delta * ((evt.GetWheelRotation() > 0) * 2 - 1)
        self.SetFloat(v)
        self.callback(tempsave=False)
        self.has_changed = True

        
    @Bind(wx.EVT_KEY_UP)
    def OnKeyUp(self, e):
        # TODO: This code is duplicated with the one found in xformeditor.
        key = e.GetKeyCode()
        if (key == wx.WXK_CONTROL and not e.AltDown()) or (
            key == wx.WXK_ALT and not e.ControlDown()):
            if self.has_changed:
                self.callback(tempsave=True)
                self.has_changed = False


    @Bind(wx.EVT_CHAR)
    def OnChar(self, e):
        key = e.GetKeyCode()
        if key in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            self.OnKillFocus()
        elif key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255 or key == wx.WXK_TAB:
            e.Skip()
        elif chr(key) in "0123456789.-":
            e.Skip()  
        else:
            # not calling Skip() eats the event
            pass #wx.Bell()


    @Bind(wx.EVT_KILL_FOCUS)
    def OnKillFocus(self, e=None):
        # cmp done with strings because equal floats can compare differently.
        if "%.6f" %self._old_val != "%.6f" %self.GetFloat():
            # Calling GetFloat here purges badly formed input.
            self._old_val = self.GetFloat()
            self.callback(tempsave=True)
        


class MultiSliderMixin(object):
    """Class to dynamically create and control sliders."""
    _new = False
    _changed = False

    def __init__(self, *a, **k):
        super(MultiSliderMixin, self).__init__(*a, **k)
        self.sliders = {}
        self.Bind(wx.EVT_IDLE, self.OnIdle)


    def MakeSlider(self, name, init, low, high, strictrange=True):
        """Programatically builds stuff."""
        tc = NumberTextCtrl(self, callback=self.UpdateFlame)
        if strictrange:
            tc.SetAllowedRange(low, high)

        slider = wx.Slider(self, -1, init*100, low*100, high*100,
                           style=wx.SL_HORIZONTAL
                           | wx.SL_SELRANGE
                           )
        self.sliders[name] = slider, tc

        slider.Bind(wx.EVT_SLIDER, partial(self.OnSlider, tc=tc))
##        slider.Bind(wx.EVT_LEFT_DOWN, self.OnSliderDown)
        slider.Bind(wx.EVT_LEFT_UP, self.OnSliderUp)

        name = name.replace("_", " ").title()
        return Box(self, name, tc, (slider, wx.EXPAND), orient=wx.HORIZONTAL)


    def UpdateSlider(self, name, val):
        slider, tc = self.sliders[name]
        slider.SetValue(int(val*100))
        tc.SetFloat(val)         


    def IterSliders(self):
        for name, (_, tc) in self.sliders.iteritems():
            yield name, tc.GetFloat()

    
    def OnSlider(self, e, tc):
        self._new = True
        tc.SetFloat(e.GetInt()/100.)
        e.Skip()

     
##    def OnSliderDown(self, e):
##        e.Skip()


    def OnSliderUp(self, e):
        if self._changed:
            self.UpdateFlame(tempsave=True)
            self._changed = False
        e.Skip()


    def OnIdle(self, e):
        if self._new:
            self.UpdateFlame(tempsave=False)
            self._new = False
            self._changed = True


    def UpdateFlame(self, tempsave):
        Abstract


    def UpdateView(self):
        Abstract
