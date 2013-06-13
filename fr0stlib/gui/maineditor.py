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
import wx, itertools, copy

from fr0stlib.decorators import *
from fr0stlib.gui.canvas import XformCanvas
from fr0stlib.gui.utils import LoadIcon, MultiSliderMixin, Box, NumberTextCtrl,\
                          SizePanel, MakeTCs, MakeChoices
from fr0stlib.gui.config import config
from fr0stlib.gui.gradientbrowser import GradientBrowser
from fr0stlib.gui.constants import ID
from fr0stlib.pyflam3 import flam3_colorhist, Genome, RandomContext
from ctypes import c_double

class MainNotebook(wx.Notebook):

    def __init__(self, parent):
        self.parent = parent
        wx.Notebook.__init__(self, parent, -1, style=wx.BK_DEFAULT)

        self.transform = TransformPanel(self)
        self.canvas = self.transform.canvas
        self.AddPage(self.transform, "Transform Editor")

        self.grad = GradientPanel(self)
        self.AddPage(self.grad, "Gradient Editor")

        self.adjust = AdjustPanel(self)
        self.AddPage(self.adjust, "Adjust")

        self.anim = AnimPanel(self)
        self.AddPage(self.anim, "Anim")


    def UpdateView(self, rezoom=False):
        for i in self.grad, self.adjust, self.anim:
            i.UpdateView()
        self.canvas.ClearSelectedXform()
        self.canvas.PerformHitTests()
        self.canvas.ShowFlame(rezoom=rezoom)
        self.transform.toolbar.ToggleTool(ID.EditPostXform,
                                          config['Edit-Post-Xform'])



class TransformPanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        self.parent = parent.parent
        wx.Panel.__init__(self,parent,-1)
        self.toolbar = self.AddToolbar()
        self.canvas = XformCanvas(self)

        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(self.toolbar, 0, wx.EXPAND)
        szr.Add(self.canvas, 1, wx.EXPAND)

        self.SetSizer(szr)
        self.Layout()


    def AddToolbar(self):
        self.tool_ids = {}

        self.toolbar = wx.ToolBar(self, -1, style=wx.TB_HORIZONTAL|wx.TB_FLAT)

        def add_tool(name, toggle=False):
            name_nodash = name.replace("-","")
            id = getattr(ID, name_nodash)
            self.tool_ids[id] = name_nodash
            
            self.toolbar.AddSimpleTool(id, LoadIcon('toolbar', name),
                                       name, isToggle=toggle)
            if toggle:
                self.toolbar.ToggleTool(id, config[name])
                self.MakeConfigFunc(name)

        add_tool('Clear-Flame')
        add_tool('Add-Xform')
        add_tool('Add-Final-Xform')
        add_tool('Duplicate-Xform')
        add_tool('Delete-Xform')
        add_tool('Zoom-In')
        add_tool('Zoom-Out')
        add_tool('Zoom-To-Fit')

        add_tool('World-Pivot', True)
        add_tool('Lock-Axes', True)
        add_tool('Variation-Preview', True)
        add_tool('Edit-Post-Xform', True)            

        self.toolbar.Realize()

        return self.toolbar


    def MakeConfigFunc(self, i):
        def onbtn():
            config[i] = not config[i]
            # HACK: This is a setflame so the post xform flag updates correctly
            self.parent.SetFlame(self.parent.flame, rezoom=False)
        setattr(self, i.replace("-",""), onbtn)


    @Bind(wx.EVT_TOOL)
    def OnButton(self, e):
        getattr(self, self.tool_ids[e.GetId()])()

    def modifyxform(f):
        """This decorator wraps away common code in the button functions."""
        def inner(self):
            # NOTE: passes in the xform, never the post xform.
            f(self, self.parent.ActiveXform)
            self.parent.TempSave()
        return inner

    @modifyxform
    def ClearFlame(self, xform):
        self.parent.flame.clear()
        self.parent.ActiveXform = self.parent.flame.add_xform()
        self.canvas.ZoomToFit()

    @modifyxform
    def AddXform(self, xform):
        self.parent.ActiveXform = self.parent.flame.add_xform()

    @modifyxform
    def AddFinalXform(self, xform):
        # add_final already checks if a final xform exists.
        self.parent.ActiveXform = self.parent.flame.add_final()

    @modifyxform
    def DuplicateXform(self, xform):
        self.parent.ActiveXform = xform.copy()

    @modifyxform
    def DeleteXform(self, xform):
        if config['Edit-Post-Xform']:
            xform.post.coefs = 1.0, 0.0, 0.0, 1.0, 0.0, 0.0
            config['Edit-Post-Xform'] = False
            return
        lst = xform._parent.xform
        if not xform.isfinal() and len(lst) == 1:
            return #  Can't delete last remaining xform.
        index = xform.index or 0 # None is turned to 0 
        xform.delete()
        self.parent.ActiveXform = lst[min(index, len(lst) - 1)]

    def ZoomIn(self):
        self.canvas.AdjustZoom(1.25)

    def ZoomOut(self):
        self.canvas.AdjustZoom(.8)

    def ZoomToFit(self):
        self.canvas.ZoomToFit()
        


class GradientPanel(wx.Panel):
    _new = None
    _changed = False
    _startval = None
    _flame = None # Only used to check identity

    @BindEvents
    def __init__(self,parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent.parent

        # Double buffering is needed to prevent flickering.
        self.SetDoubleBuffered(True)

        self.config = config["Gradient-Settings"]
        self.dict = {}

        choicelist = (('rotate', (-128, 128)),
                      ('hue',(-180, 180)),
                      ('saturation', (-100, 100)),
                      ('brightness', (-100, 100)))
        self.choices = dict(choicelist)
        self.choice = 'rotate'

        #Gradient image
        self.image = Gradient(self)
        #Controls - choice for method and slider
        self.Selector = wx.Choice(self, -1, choices=[i[0] for i in choicelist])
        self.Selector.SetSelection(0)
        self.Selector.Bind(wx.EVT_CHOICE, self.OnChoice)

        self.slider = wx.Slider(self, -1, 0, -180, 180,
                                style=wx.SL_HORIZONTAL |wx.SL_LABELS)
        self.slider.Bind(wx.EVT_SLIDER, self.OnSlider)
        self.slider.Bind(wx.EVT_LEFT_DOWN, self.OnSliderDown)
        self.slider.Bind(wx.EVT_LEFT_UP, self.OnSliderUp)

        opts = self.MakeTCs("hue", "saturation", "value", "nodes",
                            low=0, high=1, callback=self.OptCallback)
        for i in self.dict["nodes"]:
            i.MakeIntOnly()
            i.SetAllowedRange(1, 256)
        # Set Defaults for tcs.
        for k, tcs in self.dict.iteritems():
            [tc.SetFloat(i) for tc,i in zip(tcs, self.config[k])]

        btnszr = wx.BoxSizer(wx.VERTICAL)
        rdm = wx.Button(self, -1, "Randomize")
        rdm.Bind(wx.EVT_BUTTON, self.OnRandomize)
        btnszr.Add(rdm, 0, wx.LEFT | wx.TOP, 5)
        
        inv = wx.Button(self, -1, "Invert")
        inv.Bind(wx.EVT_BUTTON, self.OnInvert)
        btnszr.Add(inv, 0, wx.LEFT, 5)
        
        rev = wx.Button(self, -1, "Reverse")
        rev.Bind(wx.EVT_BUTTON, self.OnReverse)
        btnszr.Add(rev, 0, wx.LEFT, 5)

        bx = Box(self, "Gradient Generation", opts, btnszr,
                 orient=wx.HORIZONTAL)

        gb = GradientBrowser(self)

        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.image, 0, wx.EXPAND)
        sizer1.Add(self.Selector,0)
        sizer1.Add(self.slider,0,wx.EXPAND)
        sizer1.Add(bx, 0, wx.EXPAND)
        sizer1.Add(gb, 0, wx.EXPAND)

        self.SetSizer(sizer1)


    def MakeTCs(self, *a, **k):
        fgs = wx.FlexGridSizer(99, 3, 1, 1)
        fgs.Add((0,0))
        fgs.AddMany((wx.StaticText(self, -1, i), 0, wx.ALIGN_CENTER)
                    for i in ("Min", "Max"))
        for i in a:
            tcs = tuple(NumberTextCtrl(self, **k) for i in range(2))
            self.dict[i] = tcs
            fgs.Add(wx.StaticText(self, -1, i.replace("_", " ").title()),
                    0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
            fgs.AddMany((tc, 0, wx.ALIGN_LEFT, 5) for tc in tcs)
        return fgs


    def UpdateView(self):
        self.image.Update()
        if self.parent.flame != self._flame:
            # Hack: only change the slider when the flame object id changes.
            self.ResetSlider()
            self._flame = self.parent.flame


    def OptCallback(self, tempsave=None):
        for k,v in self.dict.iteritems():
            self.config[k] = tuple(i.GetFloat() for i in v)


    def OnRandomize(self, e):
        self.parent.flame.gradient.random(**self.config)
        self.parent.TempSave()


    def OnInvert(self, e):
        self.parent.flame.gradient.invert()
        self.parent.TempSave()


    def OnReverse(self, e):
        self.parent.flame.gradient.reverse()
        self.parent.TempSave()


    @Bind(wx.EVT_IDLE)
    def OnIdle(self, e):
        if self._new is not None:
            self.parent.flame.gradient = copy.deepcopy(self._grad_copy)
            getattr(self.parent.flame.gradient, self.choice)(self._new)
            self._new = None
            self._changed = True

            self.image.Update()
            self.parent.image.RenderPreview()
            # HACK: Updating the color tab without calling SetFlame.
            self.parent.XformTabs.Color.UpdateView()


    def OnChoice(self, e):
        self.choice = e.GetString()
        self.ResetSlider()


    def ResetSlider(self):
        self.slider.SetValue(0)
        self.slider.SetRange(*self.choices[self.choice])


    def OnSliderDown(self, e):
        self._grad_copy = copy.deepcopy(self.parent.flame.gradient)
        self._startval = self.slider.GetValue()
        e.Skip()


    def OnSliderUp(self, e):
        if self._changed:
            self.parent.TempSave()
            self._changed = False
            self._new = None
        self._startval = None
        e.Skip()


    def OnSlider(self, e):
        if self._startval is not None:
            self._new = e.GetInt() - self._startval



class Gradient(wx.Panel):
    @BindEvents
    def __init__(self,parent):
        self.parent = parent.parent
        wx.Panel.__init__(self, parent, -1, size=(390, 95))
        self.bmp = wx.EmptyBitmap(1,1,32)
        self.colorhist_array = (c_double *256)()
        self._startpos = None


    def Update(self, flame=None):
        flame = flame or self.parent.flame

        # Make the gradient image
        img = wx.ImageFromBuffer(256, 1, flame.gradient.to_buffer())
        img.Rescale(384, 50)
        self.bmp = wx.BitmapFromImage(img)

        # Calculate the color histogram
        genome = Genome.from_string(flame.to_string(omit_details=True))[0]
        flam3_colorhist(genome, 3, RandomContext(), self.colorhist_array)

        self.Refresh()


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 2, 37, True)
        dc.DrawLines([(i*1.5, 30-j*500)
                      for i,j in enumerate(self.colorhist_array)], 2, 2)


    @Bind(wx.EVT_MOUSE_CAPTURE_LOST)
    def OnLostMouseCapture(self, e):
        self._startpos = None


    @Bind(wx.EVT_LEFT_DOWN)
    def OnLeftDown(self, e):
        self.CaptureMouse()
        self._startpos = e.Position[0]
        parent = self.Parent
        self._oldchoice = parent.choice
        parent.choice = 'rotate'
        parent.OnSliderDown(e)


    @Bind(wx.EVT_LEFT_UP)
    def OnLeftUp(self, e):
        if self._startpos is None:
            return
        self.ReleaseMouse()
        self._startpos = None
        parent = self.Parent
        parent.choice = self._oldchoice
        parent.OnSliderUp(e)


    @Bind(wx.EVT_MOTION)
    def OnMove(self, e):
        if self._startpos is not None:
            self.Parent._new = int((e.Position[0] - self._startpos)/1.5)


    @Bind(wx.EVT_LEFT_DCLICK)
    def OnDoubleClick(self, e):
        self.Parent.OnRandomize(None)



class AdjustPanel(MultiSliderMixin, wx.Panel):

    @BindEvents
    def __init__(self, parent):
        self.parent = parent.parent
        super(AdjustPanel, self).__init__(parent, -1)

        self.bgcolor_panel = wx.Panel(self, size=(64,10),
                                      style=wx.BORDER_SUNKEN)
        self.bgcolor_panel.SetBackgroundColour((0,0,0))
        self.bgcolor_change = wx.Button(self, label='Change...')
        bgcolor_box = Box(self, 'Background Color', 
                (self.bgcolor_panel, 0, wx.EXPAND|wx.ALL, 5),
                (self.bgcolor_change, 0, wx.ALL, 5),
                orient=wx.HORIZONTAL
                )
        self.Bind(wx.EVT_BUTTON, self.OnChangeBGColor, self.bgcolor_change)

        self.sizepanel = SizePanel(self, self.UpdateFlame)

        topsizer = wx.GridBagSizer(5, 5)
        topsizer.Add(self.sizepanel, (0, 0), (1, 1), wx.ALIGN_CENTER)
        topsizer.Add(bgcolor_box, (0, 1), (1, 1), wx.ALIGN_CENTER)
        topsizer.AddGrowableCol(0)
        topsizer.AddGrowableCol(1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(topsizer, 0, wx.EXPAND)
        sizer.AddMany(((self.MakeSlider(*i), 0, wx.EXPAND) for i in
                      (("scale", 25, 1, 100, False),
                       ("x_offset", 0, -5, 5, False),
                       ("y_offset", 0, -5, 5, False),
                       ("rotate", 0, -360, 360, True),
                       ("brightness", 4, 0, 100, False),
                       ("gamma", 4, 1, 10, False),
                       ("gamma_threshold", 0.01, 0, 1, False),
                       ("vibrancy", 1, 0, 1, True),
                       ("highlight_power", -1, -1, 5, False))))
        self.sliders["gamma_threshold"][1].SetAllowedRange(0, None)
        self.SetSizer(sizer)


    def OnChangeBGColor(self, e):
        color_data = wx.ColourData()
        color_data.SetChooseFull(True)
        color_data.SetColour(self.bgcolor_panel.GetBackgroundColour())

        dlg = wx.ColourDialog(self, color_data)

        if dlg.ShowModal() == wx.ID_OK:
            self.bgcolor_panel.SetBackgroundColour(dlg.GetColourData().GetColour())
            self.bgcolor_panel.Refresh()
            self.UpdateFlame(tempsave=True)

        dlg.Destroy()


    def UpdateView(self):
        flame = self.parent.flame
        for name in self.sliders:
            self.UpdateSlider(name, getattr(flame, name))
        self.sizepanel.Size = flame.size
        self.bgcolor_panel.SetBackgroundColour(
                tuple(c*255.0 for c in flame.background))
        self.bgcolor_panel.Refresh()


    def UpdateFlame(self, tempsave=False):
        flame = self.parent.flame
        for name, val in self.IterSliders():
            setattr(flame, name, val)
        flame.size = self.sizepanel.Size
        flame.background = tuple(c/255.0
                        for c in self.bgcolor_panel.GetBackgroundColour())
        self.UpdateView()
        self.parent.image.RenderPreview()

        if tempsave:
            self.parent.TempSave()



class AnimPanel(wx.Panel):
    # HACK: making this a dict for compat with MyChoice.
    interpolation_type_dict = dict((i,i) for i in ("linear", "log"))
    interpolation_dict = dict((i,i) for i in ("linear", "smooth"))
    palette_mode_dict = dict((i,i) for i in ("step", "linear"))

    @BindEvents
    def __init__(self, parent):
        self.parent = parent.parent
        wx.Panel.__init__(self, parent, -1)

        fgs, d = MakeTCs(self, ("time", 0), low=0, int_only=True,
                         callback=self.UpdateFlame)
        self.dict = d

        fgs2, d = MakeChoices(self, *((i, getattr(self, i+"_dict"), None)
                                      for i in ("interpolation_type",
                                                "interpolation",
                                                "palette_mode")),
                              callback=self.UpdateFlame)
        # TODO: second dict somehow needs to be updated separately.
        self.dict.update(d)

        szr = wx.BoxSizer(wx.VERTICAL)
        szr.Add(fgs)
        szr.Add(fgs2)
        self.SetSizerAndFit(szr)
        self.Show(True)
        
        
    def UpdateView(self):
        flame = self.parent.flame
        for k,v in self.dict.iteritems():
            v.Set(getattr(flame, k))


    def UpdateFlame(self, tempsave=True):
        flame = self.parent.flame
        for k,v in self.dict.iteritems():
            setattr(flame, k, v.Get())

        self.UpdateView()
        self.parent.image.RenderPreview()
        
        if tempsave:
            self.parent.TempSave()

