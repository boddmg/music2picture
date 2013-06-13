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
from wx.lib.mixins import treemixin

from fr0stlib import Flame, save_flames
from fr0stlib.decorators import *
from fr0stlib.gui.constants import ID
from fr0stlib.gui.itemdata import ItemData, ParentData
from fr0stlib.gui.utils import IsInvalidPath


class TreePanel(wx.Panel):

    @BindEvents
    def __init__(self, parent):
        # Use the WANTS_CHARS style so the panel doesn't eat the Return key.
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)
        self.parent = parent

        # Specify a size instead of using wx.DefaultSize
        self.tree = FlameTree(self, wx.NewId(), size=(180,520),
                               style=wx.TR_DEFAULT_STYLE
                                     #wx.TR_HAS_BUTTONS
                                     | wx.TR_EDIT_LABELS
                                     #| wx.TR_MULTIPLE
                                     | wx.TR_HIDE_ROOT)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        self.SetDoubleBuffered(True)


    @Bind(wx.EVT_TREE_SEL_CHANGED)
    def OnSelChanged(self, event):
        item = event.GetItem()
        event.Skip()

        if self.tree._dragging:
            # Don't reselect flames when a drop is happening.
            return

        if item and len(self.tree.GetIndexOfItem(item)) == 2:
            # Item is a flame
            self.tree.item = item
            self.tree.parentselected = False
            string = self.tree.GetFlameData(item)[-1]
            self.parent.SetFlame(Flame(string=string))
        else:
            # Item is a flamefile
            self.tree.parentselected = True
            self.parent.Enable(ID.UNDO, False)
            self.parent.Enable(ID.REDO, False)


    @Bind(wx.EVT_TREE_END_LABEL_EDIT)
    def OnEndEdit(self, e):
        e.Veto()
        newname = str(e.GetLabel())
        newname = newname[2:] if newname.startswith('* ') else newname
        
        if not newname:
            # Make sure edits don't change the name to an empty string
            return

        if len(self.tree.GetIndexOfItem(e.Item)) == 1:
            # Don't allow the name of the file to be changed
            return

        olditem = self.tree.item
        self.tree.SelectItem(e.Item)
        data = self.tree.GetFlameData(e.Item)
        self.parent.flame.name = data.name = newname
        self.parent.TempSave()
        self.tree.SelectItem(olditem)


    @Bind(wx.EVT_CONTEXT_MENU)
    def OnContext(self, e):
        menu = wx.Menu()
        menu.Append(ID.RENAME, "Rename")
        menu.Append(ID.DELETE, "Delete")
        self.PopupMenu(menu)
        menu.Destroy()


    @Bind(wx.EVT_MENU, id=ID.RENAME)
    def OnRename(self, e):
        self.tree.EditLabel(self.tree.item)


    @Bind(wx.EVT_MENU, id=ID.DELETE)
    def OnDelete(self, e):
        path = self.tree.GetFilePath()
        if IsInvalidPath(self, path):
            return
        index = self.tree.GetIndexOfItem(self.tree.item)[-1]
        children = self.tree.GetChildItems((0,))
        children.pop(index)
        if not children:
            # Make sure the flamefile is never empty.
            self.parent.OnFlameNew()
        self.tree.RefreshItems()
        
        index = min(index, len(children) - 1)
        # Select parent before selecting flame to ensure GUI is always updated.
        self.tree.SelectItem(self.tree.itemparent) 
        self.tree.SelectItem(self.tree.GetItemByIndex((0,index)))
        
        save_flames(path, *(i[0] for i in self.tree.GetDataGen()))
        self.parent.DumpChanges()


    @Bind(wx.EVT_TREE_ITEM_COLLAPSING)
    def OnTreeItemCollapsing(self, evt):
        item = evt.GetItem()
        parent = self.tree.GetItemParent(item)

        if parent == self.tree.root:
            evt.Veto()



class FlameTree(treemixin.DragAndDrop, treemixin.VirtualTree, wx.TreeCtrl):
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        super(FlameTree, self).__init__(parent, *args, **kwargs)

        # Change font size so it fits nicely with images
        font = self.GetFont()
        font.SetPointSize(9)
        self.SetFont(font)

        self.Indent = 8 # default is 15
        self.Spacing = 12 # default is 18

        self.isz = isz = (23,23)
        self.il = il = wx.ImageList(*self.isz)
        il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER,      wx.ART_OTHER, isz))
        il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, isz))
        il.Add(wx.ArtProvider_GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, isz))
        self.SetImageList(il)

        self.root = self.AddRoot("The Root Item")
        self.item = None
        self.flamefiles = []
        self._dragging = False
        self._render_thumbnails = True


    def SetFlames(self, path, *flamestrings):
        lst = [(ItemData(s), ()) for s in flamestrings]
        self.flamefiles = [(ParentData(path), lst),]

        self.RefreshItems()
        self.Expand(self.itemparent)

        # cancel all outstanding thumbnails.
        del self.parent.parent.renderer.thumbqueue[:]

        if len(flamestrings) > 1000:
            self._render_thumbnails = False
            self.parent.parent.SetStatusText("Thumbnail rendering disabled (too many flames)")
        else:
            self._render_thumbnails = True
            self.parent.parent.SetStatusText("")

        flag = self.flag = wx.NewId()
        for child, data in zip(self.GetItemChildren(), (i[0] for i in lst)):
            self.RenderThumbnail(child, data, flag)
            # Set item to default until thumbnail is ready.
            self.SetItemImage(child, 2)

        self.SelectItem(self.itemparent)
        self.SelectItem(self.GetItemByIndex((0,0)))
        self.parent.parent.DumpChanges()

        return self.itemparent


    def RenderThumbnail(self, child=None, data=None, flag=None):
        if not self._render_thumbnails:
            return
        if child is None:
            child = self.item
            data = self.GetFlameData(child)
        req = self.parent.parent.renderer.ThumbnailRequest
        req(partial(self.UpdateThumbnail, child=child, data=data, flag=flag),
            data[-1], self.isz, quality=10, estimator=1, filter_radius=0)


    def UpdateThumbnail(self, bmp, child, data, flag):
        """Callback function to process rendered thumbnails."""
        if flag and flag != self.flag:
            # This means the current thumbnail was for a file that is no longer
            # open. Trying to update with this itemid would cause a crash.
            return

        if data.imgindex == -1:
            data.imgindex = self.il.Add(bmp)
        else:
            self.il.Replace(data.imgindex, bmp)
        
        self.SetItemImage(child, data.imgindex)


    def CheckForChanges(self):
        datalist = list(self.GetDataGen())
        if any(i.HasChanged() for i in datalist):
            path = self.GetFilePath()
            dlg = wx.MessageDialog(self, 'Save changes to %s?' % path,
                                   'Fr0st',wx.YES_NO|wx.CANCEL)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                if IsInvalidPath(self, path):
                    return wx.ID_CANCEL
                save_flames(path, *(i[-1] for i in datalist))
            dlg.Destroy()
            return result
        

    def GetFlameData(self, item):
        """Gets the ItemData instance corresponding to item."""
        return self.GetItem(self.GetIndexOfItem(item))[0]


    def GetFilePath(self):
        return self.GetItem((0,))[0].path


    def OnDrop(self, *args):
        """This method is used by the DragAndDrop mixin."""
        self._dragging = False
        
        dropindex, dragindex = map(self.GetIndexOfItem, args)
        if not dropindex:
            return
        
        # HACK: Select dragitem here so the right item is selected during the
        # dialog if IsInvalidPath fails. The correct item is reselected later.
        self.SelectItem(args[1])
        path = self.GetFilePath()
        if IsInvalidPath(self, path):
            return

        lst = self.GetChildItems((0,))

        fromindex = dragindex[1] if len(dragindex) > 1 else 0
        toindex = dropindex[1] if len(dropindex) > 1 else -1
        toindex += fromindex > toindex

        lst.insert(toindex, lst.pop(fromindex))
        self.RefreshItems()

        self.item = self.GetItemByIndex((0, min(toindex, len(lst)-1)))
        self.SelectItem(self.item)
        
        save_flames(path, *(i[0] for i in self.GetDataGen()))
        self.parent.parent.DumpChanges()


    def GetItem(self, indices):
        data, children = " ", self.flamefiles
        for index in indices:
            data, children = children[index]
        return data, children


    def GetChildItems(self, indices):
        return self.GetItem(indices)[1]


    def GetItemChildren(self, item=None):
        if item is None:
            item = self.itemparent
        return treemixin.VirtualTree.GetItemChildren(self, item)


    @property
    def itemparent(self):
        return self.GetItemByIndex((-1,))


    @property
    def itemdata(self):
        if self.item:
            return self.GetFlameData(self.item)


    def GetDataGen(self):
        """Returns all itemdata instances as a generator."""
        return (i for i,_ in self.GetChildItems((0,)))


    def GetFlames(self, type=Flame):
        """Returns all flames in the currently selected file. Type can be Flame
        (default) or str. Meant to be called from a script."""
        return [type(i[-1]) for i in self.GetDataGen()]
            

    #-------------------------------------------------------------------------
    # These Methods are used by the VirtualTreeMixin.

    def OnGetItemText(self, indices):
        return self.GetItem(indices)[0].name

    def OnGetChildrenCount(self, indices):
        return len(self.GetChildItems(indices))

    def OnGetItemImage(self, indices, *args):
        return self.GetItem(indices)[0].imgindex


    #-------------------------------------------------------------------------
    # These Methods override the DragAndDropMixin to produce desired behaviour

    def StartDragging(self):
        """When you start to drag an item, the panel will scroll up until the
        parent is visible, making it impossible to drop on lower items.
        Therefore, we don't bind EVT_MOTION to avoid calling OnDragging.
        Also, self._dragging is set to let OnSelChanged know how to behave."""
        self.Bind(wx.EVT_TREE_END_DRAG, self.OnEndDrag)
        self.SetCursorToDragging()
        self._dragging = True


    def IsValidDragItem(self, dragItem):
        """Make sure only flames can be dragged."""
        return dragItem and dragItem != self.itemparent


    def IsValidDropTarget(self, dropTarget):
        """The original method vetoes the dragItem's parent, but we want to
        allow that. Also, there's no need to check for children because our
        tree is flat."""
        return True
