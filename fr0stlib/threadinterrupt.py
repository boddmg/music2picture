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
import ctypes, inspect, threading, sys


class ThreadInterrupt(BaseException):
    pass


def interrupt(thread, exctype=ThreadInterrupt):
    """Raises an exception in a thread"""
    if not inspect.isclass(exctype):
        raise TypeError("Only types can be raised (not instances)")
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thread.ident),
                                                     ctypes.py_object(exctype))
    # res 0 means the thread doesn't exist (or has already finished)
    # res 1 is expected exit status.
    if res > 1:
        # if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def interruptall(name=None, exctype=ThreadInterrupt):
    """Interrupts all threads other than the caller which share the given name.
    If no name is given, all threads other than the caller are interrupted."""
    for thread in threading.enumerate():
        if name and thread.name != name:
            continue        
        if thread is threading.currentThread():
            continue
        interrupt(thread, exctype)
