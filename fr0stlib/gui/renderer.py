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
import time, sys, traceback, wx

from fr0stlib.decorators import Catches, Threaded
from fr0stlib.render import render_funcs
from fr0stlib.gui.config import config
from fr0stlib.gui._events import InMainFast


class Renderer():
    def __init__(self, parent):
        self.parent = parent
        self.thumbqueue = []
        self.previewqueue = []
        self.largepreviewqueue = []
        self.bgqueue = []
        self.exitflag = 0
        self.previewflag = 0
        self.bgflag = 0
        self.RenderLoop()
        self.bgRenderLoop()


    def ThumbnailRequest(self, callback, *args, **kwds):
        """Schedules a thumbnail to be rendered."""
        # These settings are hardcoded on purpose, they can't be overridden
        # by the calling code.
        kwds["nthreads"] = 1
        kwds["fixed_seed"] = True
        kwds["renderer"] = "flam3"
        
        self.thumbqueue.append((callback,args,kwds))


    def PreviewRequest(self, callback, *args, **kwds):
        """Schedules a render immediately after the current render is done.
        Cancels previous requests (assuming they are obsolete)."""
        kwds["nthreads"] = -1
        kwds["fixed_seed"] = True
        kwds["renderer"] = "flam3"
        self.previewflag = 1
        
        self.previewqueue = [(callback,args,kwds)]

        
    def LargePreviewRequest(self, callback, *args, **kwds):
        """Makes a preview request with a progress function."""
        prog_func = kwds["progress_func"]
        kwds["progress_func"] = self.prog_wrapper(prog_func, "previewflag")
        kwds["renderer"] = kwds.get("renderer", config["renderer"])
        self.previewflag = 1

        self.largepreviewqueue = [(callback,args,kwds)]


    def RenderRequest(self, callback, *args, **kwds):
        """Makes a render request run in a different thread than previews,
        so it can be paused."""
        prog_func = kwds["progress_func"]
        kwds["progress_func"] = self.prog_wrapper(prog_func, "bgflag")
        kwds["renderer"] = kwds.get("renderer", config["renderer"])

        self.bgqueue.append((callback,args,kwds))
        

    @Threaded
    def RenderLoop(self):
        while not self.exitflag:
            queue = (self.previewqueue or self.thumbqueue 
                     or self.largepreviewqueue)
            if queue:
                self.bgflag = 2 # Pauses the other thread
                self.previewflag = 0
                self.process(*queue.pop(0))
                self.bgflag = 0
            else:
                time.sleep(.01)  # Ideal interval needs to be tested


    @Threaded
    def bgRenderLoop(self):
        while not self.exitflag:
            queue = self.bgqueue
            if queue:
                self.process(*queue.pop(0))
            else:
                time.sleep(.01)


    @Catches(wx.PyDeadObjectError)
    def process(self, callback, args, kwds):
        cancel_func = kwds.pop("cancel_func", None)
        renderer = kwds.pop("renderer")
        try:
            render = render_funcs[renderer]
        except KeyError as e:
            raise ValueError("Invalid renderer: %s" %e.args)
        try:
            output_buffer = render(*args,**kwds)
        except Exception:
            # Make sure render thread never crashes due to malformed flames.
            traceback.print_exc()
            return

        # HACK: If by the time the render finishes it has been obsoleted,
        # don't return the buffer in case of a large preview.
        if cancel_func is not None and self.previewflag:
            cancel_func()
            return

        if renderer == 'flam4':
            channels = 4
        else:
            channels = kwds.get('transparent', False) + 3
        # args[1] is always size...
        self.OnImageReady(callback, args[1], output_buffer, channels)
        

    def prog_wrapper(self, f, flag):
        @Catches(TypeError)
        def prog_func(*args):
            return self.exitflag or f(*args) or getattr(self, flag)
        return prog_func


    @InMainFast
    def OnImageReady(self, callback, (w,h), output_buffer, channels):
        if channels == 3:
            fun = wx.BitmapFromBuffer
        elif channels == 4:
            fun = wx.BitmapFromBufferRGBA
        else:
            raise ValueError("need 3 or 4 channels, not %s" % channels)
        callback(fun(w, h, output_buffer))
