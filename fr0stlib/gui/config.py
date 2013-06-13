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
import os, atexit, wx, pprint, functools

from fr0stlib.pyflam3.cuda import is_cuda_capable


def load_config(path):
    configstr = open(path).read()
    if configstr.startswith("{"):
        return eval(configstr)
    # This code is here for backwards compatibility.
    return eval("{%s}" % ",".join(i for i in configstr.splitlines()))


def dump_config(path):
    with open(path, 'w') as f:
        f.write(pprint.pformat(config))


def update_dict(old, new):
    for k,v in new.iteritems():
        if k not in old:
            continue
        if type(v) == dict:
            update_dict(old[k], v)
        else:
            old[k] = v

config = {}
original_config = {}

def init_config(path):
    config.update(
         {"flamepath" : os.path.join(wx.GetApp().UserParametersDir,
                                     "samples.flame"),
          "Lock-Axes" : True,
          "World-Pivot": False,
          "Variation-Preview": True,
          "Edit-Post-Xform": False,
          "Xform-Preview-Settings": {"range": 2,
                                     "numvals": 10,
                                     "depth": 3},
          "Preview-Settings": {"quality": 5,
                               "estimator": 0,
                               "filter_radius": 0,
                               "spatial_oversample": 1},
          "Large-Preview-Settings": {"quality": 25,
                                     "estimator": 0,
                                     "filter_radius": 0.25,
                                     "spatial_oversample": 2},
          "Render-Settings": {"quality": 500,
                              "filter_radius": 0.5,
                              "spatial_oversample": 2,
                              "estimator": 9,
                              "estimator_curve": 0.4,
                              "estimator_minimum": 0,
                              "nthreads": 0,
                              "buffer_depth": 64,
                              "earlyclip": True,
                              "transparent": False,
                              "filter_kernel": 0},
          "Gradient-Settings": {"hue": (0, 1),
                                "saturation": (0, 1),
                                "value": (.25, 1),
                                "nodes": (4, 6)},
          "Img-Dir": wx.GetApp().RendersDir,
          "Img-Type": ".png",
          "jpg-quality": 95,
          "Bits": 0,
          "renderer": "flam3",
          "Rect-Main": None,
          "Rect-Editor": None,
          "Rect-Preview": None,
          "Recent-Flames": (),
          "Recent-Scripts": (),
          "Favorite-Scripts": [os.path.join(wx.GetApp().UserScriptsDir, i)
                               for i in ('reframe.py',
                                         'calculate_colors.py',
                                         'bilateral_symmetry.py',
                                         'xform_heat_map.py')
                               ] + ['None' for i in range(8)],
          "Xform-Combo": {"rotate": 15.0,
                          "scale": 1.25,
                          "translate": 0.1},
          "version": "Fr0st 0.0",
          })

    # Make a copy of default values, so they can be restored later.
    original_config.update(config)
    
    if os.path.exists(path):
        update_dict(config, load_config(path))

    # We always want to open an existing flame file. This also takes care of
    # older (1.0beta) config files, where a plain 'samples.flame' was included.
    if not os.path.exists(config["flamepath"]):
        config["flamepath"] = original_config["flamepath"]

    # HACK: Edit-Post-Xform doesn't really belong in the config dict, and we
    # don't want to keep its value between sessions.
    config['Edit-Post-Xform'] = False

    # Make sure no illegal renderer is selected.
    if config['renderer'] == 'flam4' and not is_cuda_capable():
        config['renderer'] = 'flam3'

    atexit.register(functools.partial(dump_config, path=path))
