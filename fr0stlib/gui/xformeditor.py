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
import wx, os, sys, functools, itertools
from wx import gizmos
from collections import defaultdict
from functools import partial

from fr0stlib.decorators import Bind,BindEvents
from fr0stlib import polar, rect
from fr0stlib import pyflam3
from fr0stlib.gui.config import config
from fr0stlib.gui.utils import LoadIcon, MultiSliderMixin, NumberTextCtrl, \
     MakeTCs


class XformTabs(wx.Notebook):

    def __init__(self, parent):
        self.parent = parent
        wx.Notebook.__init__(self, parent, -1, size=(262,100), style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             # | wx.NB_MULTILINE
                             )

        self.Xform = XformPanel(self)
        self.AddPage(self.Xform, "Xform")

        self.Vars = VarPanel(self)
        self.AddPage(self.Vars, "Vars")

        self.Color = ColorPanel(self)
        self.AddPage(self.Color, "Color")

        self.Chaos = ChaosPanel(self)
        self.AddPage(self.Chaos, "Chaos")

        self.Selector = wx.Choice(self.parent, -1)
        self.Selector.Bind(wx.EVT_CHOICE, self.OnChoice)


    def UpdateView(self):
        choices = map(repr, self.parent.flame.iter_xforms())
        self.Selector.Items = choices
        xform = self.parent.ActiveXform
        isfinal = xform.isfinal()
        ispost = config['Edit-Post-Xform']
        self.Selector.Selection = len(choices)-1 if isfinal else xform.index

        # Update weight tc.
        if ispost or isfinal:
            self.Xform.weight.SetValue("--")
            self.Xform.weight.Disable()
            
        else:
            self.Xform.weight.SetFloat(xform.weight)
            if not self.parent.scriptrunning:
                self.Xform.weight.Enable()
            

        # Show the correct tabs depending on whether the xform is post or final
        current = self.GetPageCount()
        target = 1 if ispost else 3 if isfinal else 4
        if target <= self.Selection:
            self.Selection = target - 1
        for i in range(current - target):
            self.RemovePage(target)
        for i in ("Xform", "Vars", "Color", "Chaos")[current:target]:
            self.AddPage(getattr(self, i), i)
                
        for i in self.Xform, self.Vars, self.Color, self.Chaos:
            i.UpdateView()


    def OnChoice(self, e):
        index = e.GetInt()
        xforms = self.parent.flame.xform
        if index >= len(xforms):
            self.parent.ActiveXform = self.parent.flame.final
        else:
            self.parent.ActiveXform = xforms[index]

        self.parent.canvas.ShowFlame(rezoom=False)
        self.UpdateView()



class XformPanel(wx.Panel):
    choices = {"rotate": map(str, (5, 15, 30, 45, 60, 90, 120, 180)),
               "translate": map(str,(1.0, 0.5, 0.25, 0.1, 0.05, 0.025, 0.01)),
               "scale": map(str, (1.1, 1.25, 1.5, 1.75, 2.0))}

    @BindEvents
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.config = config["Xform-Combo"]

        # The view tells us what attributes need to be displayed
        self.view = "triangle"
        self.parent = parent.parent

        def cb(tempsave=True):
            self.UpdateFlame(tempsave=tempsave)
            self.parent.image.RenderPreview()
            self.parent.canvas.ShowFlame(rezoom=False)
            
        # Add weight box. Note that parent of MakeTCs is parent, not self.
        # This will be added to the sizer of the XformTabs directly.
        self.weightszr, d = MakeTCs(self.parent, ('weight', 1),
                                    callback=cb, low=0)
        self.weight = d['weight']

        # Add the number fields
        for i in "adbecf":
            setattr(self, i, NumberTextCtrl(self, callback=cb))
        xyo_btn = [wx.Button(self,-1,i,name=i,style=wx.BU_EXACTFIT) for i in "xyo"]
        fgs = wx.FlexGridSizer(3,3,1,1)
        itr = (getattr(self, i) for i in "adbecf")
        fgs.AddMany(itertools.chain(*zip(xyo_btn, itr, itr)))

        # Add the view buttons
        r1 = wx.RadioButton(self, -1, "triangle", style = wx.RB_GROUP )
        r2 = wx.RadioButton(self, -1, "xform" )
        r3 = wx.RadioButton(self, -1, "polar" )
        self.postflag = wx.CheckBox(self,-1,"post  ")
        radiosizer = wx.BoxSizer(wx.VERTICAL)
        border = 3 * ('win' in sys.platform)
        radiosizer.AddMany(((r1, 0, wx.ALL, border),
                            (r2, 0, wx.ALL, border),
                            (r3, 0, wx.ALL, border),
                            (self.postflag, 0, wx.ALL, border)))

        # Put the view buttons to the right of the number fields
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.AddMany((fgs, (radiosizer, 0, wx.ALL, 1)))

        # Add other buttons
        reset = wx.Button(self, -1, "Reset xform", name="Reset",
                          style=wx.BU_EXACTFIT)
        solo = wx.Button(self, -1, "Make solo", name="Solo",
                         style=wx.BU_EXACTFIT)
        btnszr = wx.BoxSizer(wx.HORIZONTAL)
        btnszr.AddMany((reset, (10, 5), solo))

        # Add the Comboboxes and buttons
        map(self.MakeComboBox, *zip(*self.config.iteritems()))
        
        btn = [wx.BitmapButton(self, -1, LoadIcon('xformtab',i),
                               name=i.replace("-",""))
               for i in ('90-Left', 'Rotate-Left', 'Rotate-Right', '90-Right',
                         'Move-Up', 'Move-Down', 'Move-Left', 'Move-Right',
                         'Shrink', 'Grow')]
        
        btn.insert(2, self.rotate)
        btn.insert(7, self.translate)
        btn.insert(10, (0,0))
        btn.insert(12, self.scale)
        
        fgs2 = wx.FlexGridSizer(4, 5, 1, 1)
        fgs2.AddMany(btn)        
        
        # Finally, put everything together
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddMany((
                (5, 10),
                hsizer, 
                (5, 5),
                (btnszr, 0, wx.ALIGN_CENTER|wx.ALL, 5), 
                (5, 5),
                (fgs2, 0, wx.ALIGN_CENTER|wx.ALL, 5),
            ))
        self.SetSizer(sizer)
        self.Layout()

        # Setup tab order
        tab_order = iter([
                xyo_btn[0], self.a, self.d,
                xyo_btn[1], self.b, self.e,
                xyo_btn[2], self.c, self.f,
                r1, r2, r3, self.postflag,
                reset, solo,
                ]  + btn[:10] + btn[11:11+3])

        prev = tab_order.next()
        for x in tab_order:
            x.MoveAfterInTabOrder(prev)
            prev = x

    def MakeComboBox(self, name, default):
        cb = wx.ComboBox(self, -1, str(default), name=name, size=(80,28),
                         choices=self.choices[name])
        setattr(self, name, cb)
        f = functools.partial(self.OnCombo, cb, name)
        cb.Bind(wx.EVT_TEXT_ENTER, f)
        cb.Bind(wx.EVT_COMBOBOX, f)
        cb.Bind(wx.EVT_KILL_FOCUS, f)


    @Bind(wx.EVT_RADIOBUTTON)
    def OnRadioSelected(self,e):
        self.view = e.GetEventObject().GetLabel()
        self.UpdateView()


    @Bind(wx.EVT_CHECKBOX)
    def OnCheckbox(self,e):
        """Toggles post transform selection."""
        config['Edit-Post-Xform'] = e.IsChecked()
        # HACK: This is a setflame so the post xform button updates correctly
        self.parent.SetFlame(self.parent.flame, rezoom=False)


    def OnCombo(self, cb, name, e):
        try:
            self.config[name] = float(cb.GetValue())
        except ValueError:
            cb.SetValue(str(self.config[name]))
        

    @Bind(wx.EVT_BUTTON)
    def OnButton(self, e):    
        getattr(self, "Func%s" %e.EventObject.Name)(self.GetActive())
        self.parent.TempSave()


    def Funcx(self, xform):
        xform.a, xform.d = 1,0

    def Funcy(self, xform):
        xform.b, xform.e = 0,1

    def Funco(self, xform):
        xform.c, xform.f = 0,0

    def FuncReset(self, xform):
        xform.coefs = 1.0, 0.0, 0.0, 1.0, 0.0, 0.0

    def FuncSolo(self, xform):
        if xform.ispost():
            xform = xform._parent
        xform.opacity = 1
        for i in xform._parent.xform:
            if i == xform:
                continue
            i.opacity = 0

    def Func90Left(self, xform):
        xform.rotate(90, pivot=(0,0) if config["World-Pivot"] else None)

    def FuncRotateLeft(self, xform):
        xform.rotate(self.config["rotate"],
                     pivot=(0,0) if config["World-Pivot"] else None)

    def FuncRotateRight(self, xform):
        xform.rotate(-self.config["rotate"],
                     pivot=(0,0) if config["World-Pivot"] else None)

    def Func90Right(self, xform):
        xform.rotate(-90, pivot=(0,0) if config["World-Pivot"] else None)

    def FuncMoveUp(self, xform):
        xform.move_pos(0, self.config["translate"])

    def FuncMoveDown(self, xform):
        xform.move_pos(0, -self.config["translate"])

    def FuncMoveLeft(self, xform):
        xform.move_pos(-self.config["translate"], 0)

    def FuncMoveRight(self, xform):
        xform.move_pos(self.config["translate"], 0)

    def FuncShrink(self, xform):
        xform.scale(1.0/self.config["scale"])

    def FuncGrow(self, xform):
        xform.scale(self.config["scale"])


    def GetActive(self):
        xform = self.parent.ActiveXform
        if config['Edit-Post-Xform']:
            return xform.post
        return xform


    def UpdateView(self):
        xform, view = self.GetActive(), self.view
            
        if view == "triangle":
            self.coefs = itertools.chain(*xform.points)
        elif view == "xform":
            self.coefs = xform.coefs
        elif view == "polar":
            self.coefs = itertools.chain(*xform.polars)

        active = (xform if xform.ispost() else xform.post).isactive()
        font = self.postflag.GetFont()
        font.Weight = wx.FONTWEIGHT_BOLD if active else wx.FONTWEIGHT_NORMAL
        self.postflag.SetFont(font)
        self.postflag.SetValue(xform.ispost())


    def UpdateFlame(self,e=None, tempsave=True):
        xform, view = self.GetActive(), self.view

        # Update weight.
        if not (xform.ispost() or xform.isfinal()):
            xform.weight = self.weight.GetFloat()

        if view == "triangle":
            xform.points = zip(*[iter(self.coefs)]*2)
        elif view == "xform":
            xform.coefs = self.coefs
        elif view == "polar":
            xform.polars = zip(*[iter(self.coefs)]*2)

        if tempsave:
            self.parent.TempSave()

                             
    @property
    def coefs(self):
        return (getattr(self,i).GetFloat() for i in "adbecf")
    @coefs.setter
    def coefs(self,v):
        map(lambda x,y: getattr(self,x).SetFloat(y), "adbecf", v)



class VarPanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent.parent

        self.tree = gizmos.TreeListCtrl(self, -1, style =
                                          wx.TR_DEFAULT_STYLE
                                        | wx.TR_ROW_LINES
                                        | wx.TR_COLUMN_LINES
                                        | wx.TR_NO_LINES
                                        | wx.TR_HIDE_ROOT
                                        | wx.TR_FULL_ROW_HIGHLIGHT
                                   )

        self.tree.AddColumn("Var")
        self.tree.AddColumn("Value")

##        self.tree.SetMainColumn(0)
        self.tree.SetColumnWidth(0, 160)
        self.tree.SetColumnWidth(1, 60)
        self.tree.SetColumnEditable(1,True)

        self.root = self.tree.AddRoot("The Root Item")
        self.item = self.root

        for i in pyflam3.variation_list:
            child = self.tree.AppendItem(self.root, i)

            for k,v in pyflam3.variables[i]:
                item = self.tree.AppendItem(child,  k)
                self.SetItemText(item, str(float(v())), 1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree,1,wx.EXPAND)
        self.SetSizer(sizer)

        window = self.tree.GetMainWindow()
        window.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        window.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        window.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        window.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.HasChanged = False


    def itervars(self, item=None):
        if not item:
            item = self.root
        child,cookie = self.tree.GetFirstChild(item)  
        while child.IsOk():
            name = self.tree.GetItemText(child)
            yield (child, name)
            child,cookie = self.tree.GetNextChild(item,cookie)


    def UpdateView(self):
        xform = self.parent.ActiveXform
        for i, name in self.itervars():
            # Looping through variations
            attr = str(getattr(xform, name))
            if self.tree.GetItemText(i, 1) != attr:
                self.SetItemText(i, attr, 1)
            if attr == '0.0':
                continue
            for j, name2 in self.itervars(i):
                # Looping through variables
                variable = "%s_%s" %(name, name2)
                if variable not in xform.__dict__:
                    # Avoid overwriting variables set in GUI with value of 0
                    continue
                attr = str(getattr(xform, variable))
                if self.tree.GetItemText(j, 1) != attr:
                    self.SetItemText(j, attr, 1)              


    def SetItemText(self, i, s, col):
        """A wrapper for tree.SetItemText, which also sets color according to
        value."""
        self.tree.SetItemText(i, s, col)

        if self.tree.GetItemParent(i) == self.root:
            color = "BLACK" if s != '0.0' else (128, 128, 128)
            self.tree.SetItemTextColour(i, color)

            child, cookie = self.tree.GetFirstChild(i)
            while child.IsOk():
                self.tree.SetItemTextColour(child, color)
                child, cookie = self.tree.GetNextChild(i, cookie)
            

    def SetFlameAttribute(self, item, value):
        xform = self.parent.ActiveXform
        parent = self.tree.GetItemParent(item)
        if parent == self.root:
            # it's a variation
            name = self.tree.GetItemText(item, 0)
            if value:
                # populate xform with values from tree.
                for j, name2 in self.itervars(item):
                    value2 = float(self.tree.GetItemText(j, 1))
                    setattr(xform, "%s_%s" %(name, name2), value2)
            else:
                # Remove all variables from file.
                for j, name2 in self.itervars(item):
                    variable = "%s_%s" %(name, name2)
                    if hasattr(xform ,variable):
                        delattr(xform, variable) 
        else:
            # it's a variable
            variation = self.tree.GetItemText(parent, 0)
            if not getattr(xform, variation):
                return
            name = "%s_%s" %(variation, self.tree.GetItemText(item, 0))
        setattr(xform, name, value)
        # TODO: This could be optimized to just redraw the var preview.
        self.parent.canvas.ShowFlame(rezoom=False)
        

    @Bind(wx.EVT_TREE_END_LABEL_EDIT)
    def OnEndEdit(self, e):
        e.Veto()
        item = e.GetItem()
        oldvalue = self.tree.GetItemText(item, 1)
        try:
            value = float(e.GetLabel() or "0.0")
            self.SetItemText(item,str(value),1)
        except ValueError:
            return
        if value:
            self.tree.Expand(item)
        if value != oldvalue:
            self.SetFlameAttribute(item, value)
            self.parent.TempSave()


##    # TODO: is it preferrable to have:
##    #   -ITEM_ACTIVATED: ability to search with letters.
##    #   -SEL_CHANGED:    immediate edit of values
##    # TODO: Need to test this under win!
####    @Bind(wx.EVT_TREE_ITEM_ACTIVATED)
    @Bind(wx.EVT_TREE_SEL_CHANGED)
    def OnSelChanged(self,e):
        """Makes sure the tree always knows what item is selected."""
        self.item = e.GetItem()
        

    def OnKeyDown(self ,e):
        key = e.GetKeyCode()
        if key in (wx.WXK_NUMPAD_ENTER, wx.WXK_RETURN):
            self.tree.EditLabel(self.item, 1)

            #HACK: See http://trac.wxwidgets.org/ticket/11418
            # Find the edit TextCtrl so we can modify it
            child_texts = filter(lambda x: x.GetClassName() == 'wxTextCtrl',
                    self.tree.GetMainWindow().GetChildren())

            if len(child_texts) == 1:
                # If we find more than one TextCtrl, something is wrong.
                # Silenty ignore that.  Worst that happens is the old behavior
                # of the control having to lose focus to end editing
                child_texts[0].SetWindowStyle(
                        child_texts[0].GetWindowStyle()|wx.TE_PROCESS_ENTER)

            self._editing = True
        else:
            e.Skip()
            

    def OnLeftDClick(self, e):
        # HACK: col is either -1 or 1. I don't know what the 2 param is.
        item, _, col =  self.tree.HitTest(e.Position)
        if not item.IsOk():
            return
        
        if col == 1:
            self.tree.EditLabel(item, 1)

            #HACK: See http://trac.wxwidgets.org/ticket/11418
            # Find the edit TextCtrl so we can modify it
            child_texts = filter(lambda x: x.GetClassName() == 'wxTextCtrl',
                    self.tree.GetMainWindow().GetChildren())

            if len(child_texts) == 1:
                # If we find more than one TextCtrl, something is wrong.
                # Silenty ignore that.  Worst that happens is the old behavior
                # of the control having to lose focus to end editing
                child_texts[0].SetWindowStyle(
                        child_texts[0].GetWindowStyle()|wx.TE_PROCESS_ENTER)

        elif col == -1:
            text = self.tree.GetItemText(item, 1)
            if text == '0.0':
                new = 1.0
                self.tree.Expand(item)
            else:
                new = 0.0
            self.SetFlameAttribute(item, new)
            self.SetItemText(item, str(new), 1)
            self.parent.TempSave()
        

    def OnWheel(self,e):
        if e.ControlDown():
            if e.AltDown():
                diff = 0.01
            else:
                diff = 0.1
        elif e.AltDown():
            diff = 0.001
        else:
            e.Skip()
            return

        self.SetFocus() # Makes sure OnKeyUp gets called.
        
        item = self.tree.HitTest(e.GetPosition())[0]
        if not item.IsOk():
            return
        
        try:
            name = self.tree.GetItemText(item)
        except wx.PyAssertionError:
            # Widget may have focus when mouse is elsewhere.
            return
        val = self.tree.GetItemText(item, 1) or "0.0"
        
        val = float(val) + (diff if e.GetWheelRotation() > 0 else -diff)
        self.SetFlameAttribute(item, val)
        self.SetItemText(item, str(val), 1)
        self.parent.image.RenderPreview()
        self.HasChanged = True
        

    def OnKeyUp(self, e):
        key = e.GetKeyCode()
        if (key == wx.WXK_CONTROL and not e.AltDown()) or (
            key == wx.WXK_ALT and not e.ControlDown()):
            if self.HasChanged:
                self.parent.TempSave()
                self.HasChanged = False



class ColorPanel(MultiSliderMixin, wx.Panel):

    @BindEvents
    def __init__(self, parent):
        self.parent = parent.parent
        super(ColorPanel, self).__init__(parent, -1)

        self.bmp = self.bmp2 = self.bmp3 = wx.EmptyBitmap(1, 32)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((198,50))
        sizer.AddMany((self.MakeSlider(*i), 0, wx.EXPAND) for i in
                      (("color", 0, 0, 1),
                       ("color_speed", 0.5, 0, 1),
                       ("opacity", 1, 0, 1)))

        self.animflag = wx.CheckBox(self,-1,"animate")
        
        sizer.Add(self.animflag, 0, wx.ALL, 5)
        self.SetSizer(sizer)
        self.SetDoubleBuffered(True)


    def UpdateView(self):
        xform = self.parent.ActiveXform
        for name in self.sliders:
            self.UpdateSlider(name, getattr(xform, name))
        self.animflag.SetValue(xform.animate)

        buff = self.parent.flame.gradient.to_buffer()
        color = min(max(int(xform.color * 256), 1), 255)
        
        img = wx.ImageFromBuffer(color, 1, buff[:color*3])
        img.Rescale(96, 28)
        self.bmp = wx.BitmapFromImage(img)

        img = wx.ImageFromBuffer(1, 1, buff[color*3:color*3+3])
        img.Rescale(12, 32)
        self.bmp2 = wx.BitmapFromImage(img)

        img = wx.ImageFromBuffer(256-color, 1, buff[color*3:])
        img.Rescale(96, 28)
        self.bmp3 = wx.BitmapFromImage(img)
        
        self.Refresh()


    def UpdateFlame(self, tempsave=False):
        # Note: This method is also called by OnIdle.
        for name, val in self.IterSliders():
            setattr(self.parent.ActiveXform, name, val)
        self.parent.ActiveXform.animate = float(self.animflag.IsChecked())
        self.UpdateView()
        self.parent.image.RenderPreview() 
        self.parent.grad.image.Update()
        if tempsave:
            self.parent.TempSave()
        

    @Bind(wx.EVT_PAINT)
    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        w = self.bmp.Width
        dc.DrawBitmap(self.bmp, 6, 8, True)
        dc.DrawBitmap(self.bmp2, w + 8, 6, True)
        dc.DrawBitmap(self.bmp3, w + 22, 8, True)   


    @Bind(wx.EVT_CHECKBOX)
    def OnCheckbox(self,evt):
        self.UpdateFlame()
        self.parent.TempSave()


class ChaosPanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent.parent

        self.tree1 = self.init_tree("To")
        self.tree2 = self.init_tree("From")

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.tree1, 1, wx.EXPAND)
        sizer.Add(self.tree2, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.HasChanged = False


    def init_tree(self, label):

        tree = gizmos.TreeListCtrl(self, -1, style =
                                          wx.TR_DEFAULT_STYLE
                                        | wx.TR_ROW_LINES
                                        | wx.TR_COLUMN_LINES
                                        | wx.TR_NO_LINES
                                        | wx.TR_HIDE_ROOT
                                        | wx.TR_FULL_ROW_HIGHLIGHT
                                        | wx.NO_BORDER
                                   )
        
        tree.AddColumn(label)
        tree.AddColumn("Value")
        tree.SetColumnWidth(0, 50)
        tree.SetColumnWidth(1, 60)
        tree.SetColumnEditable(1,True)
        tree.AddRoot("The Root Item")

        window = tree.GetMainWindow()
        window.Bind(wx.EVT_MOUSEWHEEL, partial(self.OnWheel, tree))
        window.Bind(wx.EVT_KEY_UP, partial(self.OnKeyUp, tree))
        window.Bind(wx.EVT_LEFT_DCLICK, partial(self.OnLeftDClick, tree))
        window.Bind(wx.EVT_KEY_DOWN, partial(self.OnKeyDown, tree))
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, partial(self.OnEndEdit, tree),
                  tree)
        
        return tree
    
        
    def IterTree(self, tree):
        root = tree.GetRootItem()
        child, cookie = tree.GetFirstChild(root)
        while child.IsOk():
            yield child
            child, cookie = tree.GetNextChild(root, cookie)        


    def BuildTrees(self, count):
        for tree in (self.tree1, self.tree2):
            lst = list(self.IterTree(tree))
            for child in lst[count:]:
                tree.Delete(child)
            root = tree.GetRootItem()
            for i in range(len(lst), count):
                tree.AppendItem(root, str(i+1))


    def UpdateView(self):
        tree1, tree2 = self.tree1, self.tree2
        xform = self.parent.ActiveXform
        if xform.isfinal():
            return
        self.BuildTrees(len(self.parent.flame.xform))
 
        for i, val in zip(self.IterTree(tree1), xform.chaos):
            new = str(val)
            if tree1.GetItemText(i,1) != new:
                tree1.SetItemText(i, new, 1)

        index = xform.index       
        for i, xf in zip(self.IterTree(tree2), self.parent.flame.xform):
            new = str(xf.chaos[index])
            if tree2.GetItemText(i,1) != new:
                tree2.SetItemText(i, new, 1)            


    def SetFlameAttribute(self, tree, item, value):
        if value < 0:
            value = 0
            tree.SetItemText(item, "0.0", 1)
        active = self.parent.ActiveXform
        index = int(tree.GetItemText(item, 0)) -1
        if tree == self.tree2:
            self.parent.flame.xform[index].chaos[active.index] = value
        else:
            active.chaos[index] = value


    def OnEndEdit(self, tree, e):
        item = e.GetItem()
        oldvalue = tree.GetItemText(item, 1)
        try:
            value = float(e.GetLabel() or "0.0")
            tree.SetItemText(item, str(value), 1)
        except ValueError:
            e.Veto()
            return

        if value != oldvalue:
            self.SetFlameAttribute(tree, item, value)
            self.parent.TempSave()

        e.Veto()


    @Bind(wx.EVT_TREE_SEL_CHANGED)
    def OnSelChanged(self,e):
        """Makes sure the tree always knows what item is selected."""
        self.item = e.GetItem()
        

    def OnKeyDown(self, tree, e):
        key = e.GetKeyCode()
        if key in (wx.WXK_NUMPAD_ENTER, wx.WXK_RETURN):
            tree.EditLabel(self.item, 1)

            #HACK: See http://trac.wxwidgets.org/ticket/11418
            # Find the edit TextCtrl so we can modify it
            child_texts = filter(lambda x: x.GetClassName() == 'wxTextCtrl',
                    tree.GetMainWindow().GetChildren())

            if len(child_texts) == 1:
                # If we find more than one TextCtrl, something is wrong.
                # Silenty ignore that.  Worst that happens is the old behavior
                # of the control having to lose focus to end editing
                child_texts[0].SetWindowStyle(
                        child_texts[0].GetWindowStyle()|wx.TE_PROCESS_ENTER)

        else:
            e.Skip()
            

    def OnLeftDClick(self, tree, e):
        item, _, col =  tree.HitTest(e.Position)
        if not item.IsOk():
            return
        
        if col == 1:
            tree.EditLabel(item, 1)

            #HACK: See http://trac.wxwidgets.org/ticket/11418
            # Find the edit TextCtrl so we can modify it
            child_texts = filter(lambda x: x.GetClassName() == 'wxTextCtrl',
                    tree.GetMainWindow().GetChildren())

            if len(child_texts) == 1:
                # If we find more than one TextCtrl, something is wrong.
                # Silenty ignore that.  Worst that happens is the old behavior
                # of the control having to lose focus to end editing
                child_texts[0].SetWindowStyle(
                        child_texts[0].GetWindowStyle()|wx.TE_PROCESS_ENTER)
        else:
            text = tree.GetItemText(item, 1)
            new = 0.0 if text == '1.0' else 1.0
            tree.SetItemText(item, str(new), 1)
            self.SetFlameAttribute(tree, item, new)
            self.parent.TempSave()
        e.Skip()
        

    def OnWheel(self, tree, e):
        if e.ControlDown():
            if e.AltDown():
                diff = 0.01
            else:
                diff = 0.1
        elif e.AltDown():
            diff = 0.001
        else:
            e.Skip()
            return

        self.SetFocus() # Makes sure OnKeyUp gets called.
        
        item = tree.HitTest(e.GetPosition())[0]
        if not item.IsOk():
            return

        name = tree.GetItemText(item)
        val = tree.GetItemText(item, 1) or "0.0"
        
        val = float(val) + (diff if e.GetWheelRotation() > 0 else -diff)
        tree.SetItemText(item, str(val), 1)
        self.SetFlameAttribute(tree, item, val)
        self.parent.image.RenderPreview()
        self.HasChanged = True
        

    def OnKeyUp(self, tree, e):
        key = e.GetKeyCode()
        if (key == wx.WXK_CONTROL and not e.AltDown()) or (
            key == wx.WXK_ALT and not e.ControlDown()):
            if self.HasChanged:
                self.parent.TempSave()
                self.HasChanged = False
    
