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
import collections, sys, numpy


class _property_array(numpy.ndarray):
    def __new__(cls, parent, instance, data):
        obj = numpy.asarray(data).view(cls)
        def callback():
            parent.fset(instance, obj)
        obj.callback = callback
        return obj


    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.callback = getattr(obj, "callback", None)


    def __setitem__(self, pos, val):
        numpy.ndarray.__setitem__(self, pos, val)
        self.callback()


    def __eq__(self, other):
        return all(numpy.equal(self, other))


    def __ne__(self, other):
        return not self == other
    


class property_array(property): 
    def __init__(self, fget, fset=None, fdel=None, fdoc=None):
        if fdel is not None or fdoc is not None:
            raise ValueError("fdel and fdoc are not supported")
        
        def _fget(instance):
            return _property_array(self, instance, fget(instance))
        
        property.__init__(self, _fget, fset)
