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
import wx, sys, numpy as N, time
from functools import partial

from fr0stlib.decorators import *
from config import config
from _events import InMainFast


class ImageCache(object):
    def __init__(self, maxmb=50, penalty=0.5):
        # penalty is an arbitrary constant added to the weight of each image,
        # which affects small images more than larger ones. This ensures that
        # sorting speed won't be affected too much by many small images.
        self.maxbytes = maxmb * 1024**2
        self.penalty = penalty * 1024**2
        self.d = {}
        self.timedict = {}
        self.currentbytes = 0


    def clear(self):
        self.d.clear()
        self.currentbytes = 0
            

    def lighten(self):
        # Delete items from the cache until it's more than 50% empty
        for v,k in sorted((v,k) for (k,v) in self.timedict.items()):
            del self.d[k], self.timedict[k]
            w,h = k[1]
            self.currentbytes -= w * h * 3 + self.penalty
            if self.currentbytes < self.maxbytes / 2:
                break
            

    def get(self, parameter, size):
        k = parameter, size
        v = self.d.get(k)
        if v is not None:
            self.timedict[k] = time.time()
        return v


    def put(self, parameter, size, bmp):
        k = parameter, size
        self.d[k] = bmp
        self.timedict[k] = time.time()
        self.currentbytes += size[0] * size[1] * 3 + self.penalty
        if self.currentbytes > self.maxbytes:
            self.lighten()
        



class PreviewFrame(wx.Frame):
    @BindEvents    
    def __init__(self, parent):
        self.title = "Flame Preview"
        self.parent = parent
        wx.Frame.__init__(self,parent,wx.ID_ANY, self.title)

        wx.GetApp().LoadIconsInto(self)

        self.CreateStatusBar()
        self.cache = ImageCache()
        
        self.image = PreviewPanel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.image, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetDoubleBuffered(True)

        # This must be 0,0 so OnIdle doesn't render anything on startup.
        self._lastsize = 0,0

        self.rendering = False
        self.idlefunc = None
        
        self.SetSize((520,413))
        self.SetMinSize((128,119)) # This makes for a 120x90 bitmap


    def GetPanelSize(self):
        """This method corrects platform dependency issues."""
##        if "linux" in sys.platform:
##            return self.GetSize()
        return self.GetSizer().GetSize()


    @Bind(wx.EVT_CLOSE)
    def OnExit(self,e): 
        self.Show(False)
        self.Parent.Raise()


    @Bind(wx.EVT_SIZE)
    def OnResize(self, e):
        if not self.image.oldbmp:
            self.image.oldbmp = self.image.bmp
        image = wx.ImageFromBitmap(self.image.oldbmp)


        # TODO: This was here for windows. Need to find a clean way to make
        # resize work nice and consistent cross-platform.
##        if self._lastsize == (0,0):
##            return
        
        pw, ph = map(float, self.GetPanelSize())
        fw, fh = map(float, self.parent.flame.size)

        ratio = min(pw/fw, ph/fh)
        image.Rescale(int(fw * ratio), int(fh * ratio))
        self.image.bmp = wx.BitmapFromImage(image)

        self.Refresh()
        e.Skip()


    @Bind(wx.EVT_IDLE)
    def OnIdle(self, e):
        size = self.GetPanelSize()
        if size != self._lastsize:
            self._lastsize = size
            self.RenderPreview()

        if self.idlefunc and not self.rendering:
            self.idlefunc()
            self.idlefunc = None
        

    @InMainFast
    def RenderPreview(self, flame=None):
        if not self.IsShown():
            return
        flame = flame or self.parent.flame
        
        pw, ph = map(float, self.GetPanelSize())
        fw, fh = map(float, flame.size)
        ratio = min(pw/fw, ph/fh)
        size = int(fw * ratio), int(fh * ratio)

        # Remove name so that cache will hit if that's the only difference.
        oldname, flame.name = flame.name, ""
        flamestr = flame.to_string()
        flame.name = oldname

        bmp = self.cache.get(flamestr, size)
        if bmp is not None:
            self.idlefunc = partial(self.RenderCallback,
                                    flamestr, bmp, fromcache=True)
            return
        
        self.rendering = True
        req = self.parent.renderer.LargePreviewRequest
        req(partial(self.RenderCallback, flamestr), flame, size,
            progress_func=self.prog, cancel_func=self.CancelCallback,
            **config["Large-Preview-Settings"])
        self.SetTitle("Rendering - Flame Preview")


    def CancelCallback(self):
        self.rendering = False


    def RenderCallback(self, flamestr, bmp, fromcache=False):
        self.image.UpdateBitmap(bmp)
        self.SetTitle("%s - Flame Preview" % self.parent.flame.name)
        if fromcache:
            self.SetStatusText("rendering: retrieved from cache")
        else:
            self.rendering = False
            self.cache.put(flamestr, tuple(bmp.Size), bmp)
            self.SetStatusText("rendering: 100.00 %")


    def prog(self, *a):
        self._prog(*a)
        return int(not self.IsShown())
    

    @InMainFast
    @Catches(wx.PyDeadObjectError)
    def _prog(self, py_object, fraction, stage, eta):
        self.SetStatusText("rendering: %.2f %%" %fraction)


        
class PreviewBase(wx.Panel):
    HasChanged = False
    StartMove = None
    EndMove = None
    _move = None
    _zoom = 1


    @BindEvents
    def __init__(self, parent):
        self.bmp = wx.EmptyBitmap(400,300, 32)
        wx.Panel.__init__(self, parent, -1)
        

    @Bind(wx.EVT_IDLE)
    def OnIdle(self, e):
        if self._move is not None:
            diff = self._move
            self._move = None
            self.StartMove = self.EndMove
            self.Move(diff)
        elif self._zoom != 1:
            diff = self._zoom
            self._zoom = 1
            self.Zoom(diff)
            

    def Move(self, diff):
        flame = self.parent.flame
        fw,fh = self.bmp.GetSize()
        pixel_per_unit = fw * flame.scale / 100.
        flame.move_center([i / pixel_per_unit for i in diff])
        self.parent.image.RenderPreview()
        self.parent.adjust.UpdateView()


    def Zoom(self, diff):
        self.parent.flame.scale *= diff
        self.parent.image.RenderPreview()
        self.parent.adjust.UpdateView()
        self.HasChanged = True       


    @Bind(wx.EVT_LEFT_DOWN)
    def OnLeftDown(self, e):
        self.SetFocus()
        self.StartMove = N.array(e.GetPosition())


    @Bind(wx.EVT_LEFT_UP)
    def OnLeftUp(self, e):
        self.StartMove = None
        if self.EndMove is not None:
            self.EndMove = None
            self.parent.TempSave()


    @Bind(wx.EVT_MOUSE_EVENTS)
    def OnMove(self, e):
        if self.StartMove is not None:
            self.EndMove = N.array(e.GetPosition())
            self._move = self.StartMove - self.EndMove

        
    @Bind(wx.EVT_MOUSEWHEEL)
    def OnWheel(self, e):
        if e.ControlDown():
            if e.AltDown():
                diff = 1.01
            else:
                diff = 1.1
        elif e.AltDown():
            diff = 1.001
        else:
            return

        self._zoom *= diff**((e.GetWheelRotation() > 0)*2 -1)

        self.SetFocus() # Makes sure OnKeyUp gets called.
         

    @Bind(wx.EVT_KEY_UP)
    def OnKeyUp(self, e):
        key = e.GetKeyCode()
        if (key == wx.WXK_CONTROL and not e.AltDown()) or (
            key == wx.WXK_ALT and not e.ControlDown()):
            if self.HasChanged:
                self.parent.TempSave()
                self.HasChanged = False



class PreviewPanel(PreviewBase):
    _offset = N.array([0,0])
    _zoomfactor = 1.0
    oldbmp = None

    @BindEvents
    def __init__(self, parent):
        self.__class__ = PreviewBase
        PreviewBase.__init__(self, parent)
        self.__class__ = PreviewPanel
        self.parent = parent.parent
        self.GetPanelSize = parent.GetPanelSize       


    def UpdateBitmap(self, bmp):
        self.bmp = bmp
        self.oldbmp = bmp
        self._offset = N.array([0,0])
        self._zoomfactor = 1.0
        self.Refresh()


    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):       
        fw,fh = self.bmp.GetSize()
        pw,ph = self.GetPanelSize()
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, (pw-fw)/2, (ph-fh)/2, True)


    def NewEmptyImage(self, w, h):
        newimg = wx.EmptyImage(w, h, 32)
        # TODO: not sure if this is efficient for filling an image with a
        # given color. wx.Image has no other API to do this, however.
        bgcolor = (min(255, c*256) for c in self.parent.flame.background)
        newimg.SetRGBRect((0 ,0, w, h), *bgcolor)
        return newimg
    

    def Move(self, diff):
        PreviewBase.Move(self, diff)
        self._offset += diff
        self.MoveAndZoom()
        

    def Zoom(self, val):
        PreviewBase.Zoom(self, val)
        self._zoomfactor *= val        
        self._offset *= val
        self.MoveAndZoom()
        

    def MoveAndZoom(self):
        fw,fh = self.bmp.GetSize()
        ow, oh = self._offset
        image = wx.ImageFromBitmap(self.oldbmp)

        # Use fastest order of operations in each case (i.e. the order that
        # avoids huge images that will just be shrinked or cropped).
        # Both paths yield equivalent results.
        zoom = self._zoomfactor
        if zoom > 1:
            iw, ih = int(fw/zoom), int(fh/zoom)
            newimg = self.NewEmptyImage(iw, ih)
            newimg.Paste(image, (iw-fw)/2 - ow/zoom,
                                (ih-fh)/2 - oh/zoom)
            newimg.Rescale(fw,fh)
        else:
            iw, ih = int(fw*zoom), int(fh*zoom)
            image.Rescale(iw, ih)
            newimg = self.NewEmptyImage(fw, fh)
            newimg.Paste(image, (fw-iw)/2 - ow,
                                (fh-ih)/2 - oh)
        self.bmp = wx.BitmapFromImage(newimg)
        self.Refresh()        
