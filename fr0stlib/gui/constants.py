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
from collections import defaultdict


class ConstantFactory():
    def __init__(self,default):
        self.__dict__["d"] = defaultdict(default)
        
    def __getattr__(self,name):
        return self.d[name]

    def __setattr__(self,name,v):
        raise AttributeError("IDs are read-only")

    def __delattr__(self,name):
        raise AttributeError("IDs are read-only")

ID = ConstantFactory(wx.NewId)


def NewIdRange(n):
    return [wx.NewId() for i in range(n)][0]

