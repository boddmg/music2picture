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
import sys, wx, time, threading

myEVT_THREAD_MESSAGE = wx.NewEventType()
EVT_THREAD_MESSAGE = wx.PyEventBinder(myEVT_THREAD_MESSAGE, 1)
class ThreadMessageEvent(wx.PyCommandEvent):
    """Used to send information to a callback function in the main thread.

    Should have an id if the receiving widget has more than 1 handler. Can
    carry arbitrary information accessible through e.Args."""
    def __init__(self, id=wx.ID_ANY, *args):
        wx.PyCommandEvent.__init__(self, myEVT_THREAD_MESSAGE, id)
        self.Args = args



__ID = wx.NewId()
__ID_fast = wx.NewId()


def InMain(f):
    """Decorator that forces functions to be executed in the main thread.

    The thread in which the function is called waits on the result, so the code
    can be reasoned about as if it was single-threaded. Exceptions are also
    raised in the original thread."""
    def inner(*a, **k):
        if threading.currentThread().name == 'MainThread':
            return f(*a, **k)
        res = []
        wx.PostEvent(wx.GetApp(), ThreadMessageEvent(__ID, res, f, a, k))
        while not res:
            time.sleep(.0001)
        if len(res) == 3:
            raise res[0], res[1], res[2]
        return res[0]
    return inner


def InMainFast(f):
    """Faster version of InMain, which doesn't wait for the function to run.

    There are no guarantees when and in which thread the function runs, only
    that it eventually does. The return value may be ignored."""
    if 'win' in sys.platform:
        # wx is threadsafe on windows. This shortcut is not in InMain, because
        # said function gives stronger guarantees about its exact behaviour.
        return f
    def inner(*a, **k):
        wx.PostEvent(wx.GetApp(), ThreadMessageEvent(__ID_fast, f, a, k))
    return inner


def __callback(e):
    res, f, a, k = e.Args
    try:
        res.append(f(*a, **k))
    except Exception as e:
        res.extend(sys.exc_info())


def __callback_fast(e):
    apply(*e.Args)


def InMainSetup(__init__):
    def inner(self, *a, **k):
        __init__(self, *a, **k)
        self.Bind(EVT_THREAD_MESSAGE, __callback, id=__ID)
        self.Bind(EVT_THREAD_MESSAGE, __callback_fast, id=__ID_fast)
    return inner
