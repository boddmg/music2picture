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
import itertools, numpy as N, wx, sys, math
from functools import partial
from wx.lib.floatcanvas import FloatCanvas as FC
from wx.lib.floatcanvas.Utilities import BBox

from fr0stlib.decorators import Bind, BindEvents
from fr0stlib import polar, rect, Xform
from fr0stlib import pyflam3
from fr0stlib.pyflam3 import Genome, c_double, RandomContext, flam3_xform_preview
from fr0stlib.gui.config import config


def angle_helper(*points):
    """Given 3 vectors with the same origin, checks if the first falls
    between the other 2."""
    itr = (polar(i)[1] for i in points)
    vect = itr.next() # vector being checked
    low, high = sorted(itr) # the 2 triangle legs.
    if high - low > 180:
        low, high = high-360, low
    if vect > high:
        vect -= 360
    return high > vect > low


class VarPreview(object):
    def __init__(self, xform, Color):
        self.genome = Genome.from_string(xform._parent.to_string(True))[0][0]
        xform = xform._parent if xform.ispost() else xform
        self.index = xform.index
        if self.index is None:
            self.index = self.genome.final_xform_index

        kwds = config["Xform-Preview-Settings"].copy()
        depth = kwds.pop("depth")
        self.objects = [FC.PointSet(self.var_preview(depth=i + 1, **kwds), 
                                    Color=tuple(c/(depth - i) for c in Color))
                        for i in range(depth)]

    def var_preview(self, range, numvals, depth):
        numvals = int(numvals * range)
        result = (c_double * (2* (2*numvals+1)**2))()
        flam3_xform_preview(self.genome, self.index, range, numvals, depth,
                            result, RandomContext())
        return [(x,-y) for x,y in zip(*[iter(result)]*2)]



class AlphaPolygon(FC.Polygon):
    """Polygon that can draw with opacity.

    Similar to what's described here:
    http://trac.paulmcnett.com/floatcanvas/wiki/AlphaCircle."""
    def __init__(self, *a, **k):
        self.Opacity = k.pop('Opacity', 0)
        FC.Polygon.__init__(self, *a, **k)


    def SetBrush(self, FillColor, FillStyle):
        r,g,b = FillColor
        c = wx.Color(r,g,b, self.Opacity)
        self.Brush = wx.Brush(c)


    def _Draw(self, dc, WorldToPixel, ScaleWorldToPixel=None, HTdc=None): 
        Points = WorldToPixel(self.Points)

        # draw just the outline, using the dc so the lines are solid
        dc.SetPen(self.Pen)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawPolygon(Points)

        # fill in the triangle  with the gc
        if self.Opacity:
            gc = wx.GraphicsContext.Create(dc)
            gc.SetBrush(self.Brush)
            gc.DrawLines(Points)

        

class XFormTriangle(FC.Group):
    def __init__(self, parent, xform, color, isactive, isselected, style):
        self.xform = xform
        self.coefs = xform.coefs
        self.parent = parent
        points = xform.points

        self.triangle = AlphaPolygon(points, LineColor=color, FillColor=color,
                                     LineStyle=style,
                                     Opacity=isselected * 96 or isactive * 64)

        diameter = parent.circle_radius * 2
        circles = map(partial(FC.Circle, Diameter=diameter, LineColor=color),
                      points)
        text = map(partial(FC.Text, Size=10,Color=color), "XYO", points)
        self._circles = circles
        
        if isactive:
            parent._cornerpoints = self.GetCornerPoints()
            corners = [FC.Line(i, LineColor=color)
                       for i in parent._cornerpoints]
            text.extend(corners)

        FC.Group.__init__(self, [self.triangle] + circles + text)


    def GetCornerPoints(self):
        """Calculate the lines making up the corners of the triangle."""
        a,d,b,e,c,f = self.xform.coefs

        # Get the 4 corner points
        p1 = c + a + b, f + d + e
        p2 = c + a - b, f + d - e
        p3 = c - a + b, f - d + e
        p4 = c - a - b, f - d - e

        # define towards which other corners the corner lines will point.
        # (p1, p4) and (p2, p3) are opposing corners.
        combinations = ((p1,p2,p3),
                        (p2,p1,p4),
                        (p3,p1,p4),
                        (p4,p2,p3))

        # Make the length of the corner lines 1/10th of the distance to the
        # respective corner. The lists of points returned will be drawn as
        # multilines.
        return [((x1+(x2-x1)/10, y1+(y2-y1)/10),
                 (x1, y1),
                 (x1+(x3-x1)/10, y1+(y3-y1)/10))
                for (x1,y1),(x2,y2),(x3,y3) in combinations]            



class XformCanvas(FC.FloatCanvas):
    colors = [( 255,   0,   0), # red
              ( 255, 255,   0), # yellow
              (   0, 255,   0), # green
              (   0, 255, 255), # light blue
              (   0,   0, 255), # dark blue
              ( 255,   0, 255), # purple
              ( 255, 127,   0), # orange
              ( 255,   0, 127)  # another purplish one
              ] # TODO: extend the color list.

    style = "ShortDash" if "linux" in sys.platform else "Dot"
    preview = [] 

    @BindEvents
    def __init__(self, parent):
        self.parent = parent.parent
        FC.FloatCanvas.__init__(self, parent,
                                size=(300,300), # HACK: This needs to be here.
                                BackgroundColor="BLACK")

        # Create the reference triangle
        points = ((0,0),(1,0),(0,1))
        self.AddPolygon(points,
                        LineColor="Grey",
                        LineStyle=self.style)
        map(lambda x,y,z: self.AddText(x,y,Position=z,Size=10,Color="Grey"),
            "OXY",points,("tr","tl","br"))


        # Lists that hold draw objects
        self.xform_groups = []
        self.objects = []
        self.shadow = []
        self.edit_post = False

        self.MakeGrid()

        # These are used in the OnIdle Method
        self._idle_right_drag = None
        self._idle_left_drag = None
        self._idle_resize = 1
        self._idle_refresh = False

        # These mark different states of the canvas
        self.parent.ActiveXform = None
        self.SelectedXform = None
        self.HasChanged = False
        self.StartMove = None
        self.callback = None
        self.last_mouse_pos = 0,0
        self._cornerpoints = ()


    def ShowFlame(self, flame=None, rezoom=True):
        flame = flame or self.parent.flame
        active = self.parent.ActiveXform
        
        self.RemoveObjects(self.preview)
        del self.preview[:]
        if config["Variation-Preview"]:
            self.preview[:] = VarPreview(active, Color=self.color_helper(active)).objects[:]
            self.AddObjects(self.preview)  

        self.RemoveObjects(self.xform_groups)
        if config['Edit-Post-Xform']:
            self.xform_groups = [self.AddXform(active, isactive=False),
                                 self.AddXform(active.post, isactive=True)]
        else:
            self.xform_groups = [self.AddXform(i, isactive=False)
                                 for i in flame.iter_xforms() if i != active]
            self.xform_groups.append(self.AddXform(active, isactive=True))

        if rezoom:
            self.ZoomToFit()
        else:
            # This is an else because ZoomToFit already forces a Draw.
            self.Draw()
        self._idle_refresh = False


    def AddXform(self, xform, isactive=False, isselected=None, style='Solid'):
        color = self.color_helper(xform)
        if isselected is None:
            isselected = xform is self.SelectedXform
           
        t = XFormTriangle(self, xform, color, isactive, isselected, style)       
        self.AddObject(t)
        return t


    def color_helper(self, xform):
        xform = xform._parent if xform.ispost() else xform
        if xform.isfinal():
            return (255, 255, 255)
        return self.colors[xform.index%len(self.colors)]


    def MakeGrid(self):
        self.GridUnder = FC.DotGrid(Spacing=(.1, .1),
                                    Size=150,
                                    Color=(100,100,100),
                                    Cross=True,
                                    CrossThickness=1)


    def AdjustZoom(self, factor, refresh=True):
        """Changes the scale, resets the grid and circle sizes and refreshes
        the canvas."""
        self.Scale *= factor
        self.SetToNewScale(DrawFlag=False)
        
        # Adjust Grid Spacing
        # k / scale means: 1 line each k pixels. This is truncated to the
        # closest power of 10.
        spacing = 10 ** round(math.log10(75 / self.Scale))
        self.GridUnder.Spacing = N.array((spacing,spacing))

        # Adjust the circles at the triangle edges
        diameter = self.circle_radius * 2
        map(lambda x: x.SetDiameter(diameter),
            itertools.chain(*(i._circles for i in self.xform_groups)))

        # Refresh canvas
        self._BackgroundDirty = True
        self.Draw()


    def IterXforms(self):
        active = self.parent.ActiveXform
        if config['Edit-Post-Xform']:
            return active.post, active
        # the iteration needs to be reversed here so that the ordering is
        # consistent with the display on canvas (last xform on top)
        lst = [i for i in reversed(list(self.parent.flame.iter_xforms()))
               if i != active]
        return [active] + lst


    def ActivateCallback(self,coords):
        if self.callback:
            self.callback(coords)
            self.HasChanged = True
            self.ShowFlame(rezoom=False)
            # Only update Xform, not all 4 tabs. makes updates somewhat faster.
            self.parent.XformTabs.Xform.UpdateView()
            self.parent.image.RenderPreview()


    def VertexHitTest(self,x,y):
        """Checks if the given point is on top of a vertex."""
        for xform in self.IterXforms():
            a,d,b,e,c,f = xform.coefs

            if polar((x - c, y - f))[0] < self.circle_radius:
                cb = (partial(setattr, xform, "pos") if config["Lock-Axes"] 
                      else partial(setattr, xform, "o"))
                return xform.o, xform, cb
            elif polar((x - a - c, y - d - f))[0] < self.circle_radius:
                return xform.x, xform, partial(setattr, xform, "x")
            elif polar((x - b - c, y - e - f))[0] < self.circle_radius:
                return xform.y, xform, partial(setattr, xform, "y")

        return None, None, None



    def CalcScale(self, points, h, v, hittest=False):
        """Returns the proportion by which the xform needs to be scaled to make
        the hypot pass through the point.
        If hittest is set to true, this func doubles as a hittest, and checks
        if the point is inside the line's hitbox."""

        xf = Xform(None, points=points)
        a,d,b,e,c,f = xf.coefs

        # Get angle of the hypothenuse
        angle = polar(((b-a), (e-d)))[1]

        # create a rotated triangle and (c,f)->(h,v) vector. This way, the
        # hypothenuse is guaranteed to be horizontal, which makes everything
        # easier.
        xf.rotate(-angle)
        l, theta = polar(((h-c), (v-f)))
        width,height = rect((l, theta - angle))

        # return the result.
        # Note that xf.d and xf.e are guaranteed to be equal.
        if hittest:
            return xf.a < width < xf.b and \
                   abs(height - xf.d) < self.circle_radius
        return height / xf.d


    def side_helper(self, xform, funcname, h, v):
        """Takes the result of SideHitTest and builds a proper callback."""
        if funcname == 'scale':
            def cb((h,v)):
                return xform.scale(self.CalcScale(xform.points, h, v))
            return cb

        if funcname == "rotate":
            pivot = xform.o
            func = partial(xform.rotate, pivot=pivot)
        elif config["Lock-Axes"]:
            pivot = (0,0) if config["World-Pivot"] else xform.o
            func = partial(xform.rotate, pivot=pivot)
        else:
            pivot = xform.o
            func = getattr(xform, funcname)

        def cb((h, v)):
            angle = polar((h - pivot[0], v - pivot[1]))[1]
            func(angle - cb.prev_angle)
            cb.prev_angle = angle
        cb.prev_angle = polar((h - pivot[0], v - pivot[1]))[1]
        return cb


    def SideHitTest(self, h, v):
        """Checks if the given point is near one of the triangle sides
        or corners."""
        for xform in self.IterXforms():
            xf = xform # TODO:refactor
            x,y,o = xf.points
            for points,func in (((x,y,o), 'scale'),
                                ((x,o,y), 'rotate_x'),
                                ((y,o,x), 'rotate_y')):
                if self.CalcScale(points, h, v, hittest=True):
                    return (points[:2], xform,
                            self.side_helper(xf, func, h,v))

        # TODO: detect the actual lines. Right now, it just checks a radius
        # from the middle point.
        radius = self.circle_radius * 3 # better too big than too small.
        for i,j,k in (self._cornerpoints):
            if polar((h - j[0], v - j[1]))[0] < radius:
                if config["Edit-Post-Xform"]:
                    xform = self.parent.ActiveXform.post
                else:
                    xform = self.parent.ActiveXform
                return ((i,j,k), xform, self.side_helper(xform, 'rotate', h,v))

        return None, None, None


    def XformHitTest(self,x,y):
        """Checks if the given point is inside the area of the xform.
        This is done by testing if it falls inside the angles projected from
        at least 2 of its vertices."""

        for xform in self.IterXforms():
            a,d,b,e,c,f = xform.coefs

            if angle_helper((x-c, y-f), (a, d), (b, e)) and \
               angle_helper((x-a-c, y-d-f), (-a, -d), (b-a, e-d)):
                diff = x - c, y - f
                return xform, lambda coord: setattr(xform, "pos", coord-diff)

        return None, None


    def ZoomToFit(self):
        # Calculate bounding box by hand, FC doesn't work right.
        points = list(itertools.chain(x.points for x in self.IterXforms()))
        self.ZoomToBB(NewBB=BBox.fromPoints(points), DrawFlag=False)
        
        # Factor of .8 is to leave some breathing room
        self.AdjustZoom(.8)


    @Bind(wx.EVT_ENTER_WINDOW)
    def OnEnter(self,e):
##        self.CaptureMouse()
        pass

    @Bind(wx.EVT_LEAVE_WINDOW)
    def OnLeave(self,e):
##        self.ReleaseMouse()
        pass


    @Bind(wx.EVT_IDLE)
    def OnIdle(self,e):
        if self._idle_left_drag is not None:
            coords = self._idle_left_drag
            self._idle_left_drag = None
            self.ActivateCallback(coords)

        if self._idle_right_drag is not None:
            move = self._idle_right_drag
            self._idle_right_drag = None
            self.StartMove = self.EndMove
            self.MoveImage(move, 'Pixel')

        if self._idle_resize != 1:
            self.AdjustZoom(self._idle_resize, refresh=False)
            self.PerformHitTests()
            self._idle_resize = 1

        if self._idle_refresh and not self.parent.scriptrunning:
            self.ShowFlame(rezoom=False)


    @Bind(FC.EVT_MOUSEWHEEL)
    def OnWheel(self,e):
        self._idle_resize *= 1.25 if e.GetWheelRotation()>0 else 0.8


    @Bind(FC.EVT_LEFT_DOWN)
    def OnLeftDown(self,e):
        self.CaptureMouse()
        if self.SelectedXform:
            if config['Edit-Post-Xform']:
                if self.SelectedXform.ispost():
                    self.parent.ActiveXform = self.SelectedXform._parent
                else:
                    # If the parent is selected, we move back into normal
                    # editing mode. UpdateView is required to refresh toggle
                    # in toolbar.
                    self.parent.ActiveXform = self.SelectedXform
                    config['Edit-Post-Xform'] = False
                    self.parent.notebook.UpdateView()
            else:
                self.parent.ActiveXform = self.SelectedXform
            self.ShowFlame(rezoom=False)
            self.parent.XformTabs.UpdateView()

            # EXPERIMENT!
            t = self.AddXform(self.SelectedXform, isselected=False,
                              style=self.style)
            self.shadow.append(t)


    @Bind(FC.EVT_LEFT_UP)
    def OnLeftUp(self,e):
        # This release mouse causes a bug under windows.
##        self.ReleaseMouse()

        # EXPERIMENT!
        self.RemoveObjects(self.shadow)
        self.shadow = []

        if self.HasChanged:
            # Heisenbug, thou art no more! Since TempSave triggers a redraw,
            # It was possible that an idle event was still pending afterwards,
            # which could cause a different xform to change its position in
            # a bizarre way. Calling OnIdle fixes this.
            self.OnIdle(None)
            self.HasChanged = False
            self.parent.TempSave()


    @Bind(FC.EVT_RIGHT_DOWN)
    def OnRightDown(self,e):
        self.CaptureMouse()
        self.StartMove = N.array(e.GetPosition())
        self.PrevMoveXY = (0,0)


    @Bind(FC.EVT_RIGHT_UP)
    def OnRightUp(self,e):
        if self.HasCapture():
            self.ReleaseMouse()

        self.StartMove = None
        self.PerformHitTests()


    @Bind(wx.EVT_MOUSE_CAPTURE_LOST)
    def OnLostMouseCapture(self, e):
        self.StartMove = None


    @Bind(FC.EVT_MOTION)
    def OnMove(self,e):
        self.ClearSelectedXform()
        # NOTE: OnMove is called when scrolling, but the event itself doesn't
        # indicate that it was caused by scrolling.
        # Use e.Position (mouse pixels) i.o. e.Coords (world coordinates),
        # because ints can be compared and the Position remains invariant
        # even after AdjustZoom is called. See OnIdle for reference.
        self.last_mouse_pos = tuple(e.Position)

        if e.RightIsDown() and e.Dragging() and self.StartMove is not None:
            self.EndMove = N.array(e.GetPosition())
            self._idle_right_drag = self.StartMove - self.EndMove
        elif self.parent.scriptrunning:
            # Disable everything except canvas dragging.
            pass
        elif e.LeftIsDown() and e.Dragging():
            self._idle_left_drag = e.Coords
        else:
            self.PerformHitTests()


    def PerformHitTests(self):
        if self.parent.scriptrunning:
            return
        
        self.ClearSelectedXform()
        coords = self.PixelToWorld(self.last_mouse_pos)

        # First, test for vertices
        point, xform, cb = self.VertexHitTest(*coords)
        if cb:
            self.SelectXform(xform, highlight_point=point)
            self.callback = cb
            return

        # Then, test for sides
        line, xform, cb = self.SideHitTest(*coords)
        if cb:
            self.SelectXform(xform, highlight_line=line)
            self.callback = cb
            return 

        # Finally, test for area
        xform, cb = self.XformHitTest(*coords)
        if cb:
            self.SelectXform(xform)
            self.callback = cb
            return 
        

    def SelectXform(self, xform, highlight_line=None, highlight_point=None):
        self.SelectedXform = xform
        color = self.color_helper(xform)

        if not xform.ispost():
            varlist = [i for i in pyflam3.variation_list if getattr(xform,i)]
            hor, ver = self.GetSize()
            hor -= 5
            ver -= 5
            for i in reversed(varlist):
                ver -= 12
                self.objects.append(self.AddText(i, self.PixelToWorld((hor,ver)),
                                    Size = 8, Position = "tr", Color=color))

        if highlight_line is not None:
            self.objects.append(self.AddLine(highlight_line, LineColor=color,
                                             LineWidth=2))
        if highlight_point is not None:
            self.objects.append(self.AddCircle(highlight_point, Diameter=self.circle_radius * 1.7,
                                              FillColor=color))

        self._idle_refresh = True


    def ClearSelectedXform(self):
        self.SelectedXform = None
        self.RemoveObjects(self.objects)
        del self.objects[:]
        self._idle_refresh = True


    def BlockCanvas(self, flag):
        if not flag:
            self.PerformHitTests()
            return
        self.OnLeftUp(None)
        self.ClearSelectedXform()


    # Win uses MidMove, while Linux uses StartMove (WHY?). This makes the code
    # Compatible between both.
    @property
    def MidMove(self):
        return self.StartMove
    @MidMove.setter
    def MidMove(self,v):
        self.StartMove = v


    @property
    def circle_radius(self):
        return 5 / self.Scale

