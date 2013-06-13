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
import os, sys, shutil, random, itertools, ctypes, collections, re, numpy, \
       colorsys
import xml.etree.cElementTree as etree
from math import *
from functools import partial

from fr0stlib.pyflam3 import Genome, RandomContext, flam3_nvariations, \
  variable_list, variation_list, variations, variables, flam3_estimate_bounding_box
from fr0stlib.compatibility import compatibilize
from fr0stlib.property_array import property_array


VERSION = "Fr0st 1.4"
GUI = False


class ParsingError(Exception):
    pass


class Flame(object):
    _never_write = set(("final", "gradient", "xform", "name", "scale",
                        "width", "height", "x_offset", "y_offset"))
    
    def __init__(self, string=""):
        # Set minimum required attributes.
        self.name = "Untitled"
        self.xform = []
        self.final = None
        self.gradient = Palette()
        self.size = 640, 480 # property
        self.center = 0.0, 0.0 # property
        self.scale = 25.
        self.rotate = 0.0
        self.background = (0.0, 0.0, 0.0)
        self.brightness = 4
        self.gamma = 4
        self.gamma_threshold = 0.04
        self.vibrancy = 1
        self.highlight_power = -1
        self.time = 0
        self.interpolation_type = "log"
        self.interpolation = "linear"
        self.palette_mode = "linear"
##        self.oversample = 1
##        self.filter = 0.2
##        self.quality = 100        
          
        if string:
            self.from_element(etree.fromstring(string))
    

    def from_element(self, element):
        self.gradient.from_flame_element(element)

        xml_xforms = element.findall('xform')
        self.xform = [Xform(self) for i in xml_xforms]

        for xform, xform_element in zip(self.xform, xml_xforms):
            xform.from_element(xform_element)

        for final in element.findall('finalxform'):
            if self.final is not None:
                raise ParsingError("More than one final xform found")
            self.final = Xform(self)
            self.final.from_element(final)
            self.final.animate = 0

        # Record the header data.
        for name, val in element.items():
            try:
                if " " in val:
                    setattr(self, name, map(float, val.split()))
                else:
                    setattr(self, name, float(val))
            except ValueError:
                setattr(self, name, val)

        self.name = str(self.name)

        # Scale needs to be converted. This is reversed in _iter_attributes.
        self.scale = self.scale * 100 / self.size[0]
            
        sym = element.find('symmetry')
        if sym is not None:
            self.add_symmetry(int(sym.get('kind')))

        compatibilize(self, VERSION)

        return self


    def to_string(self, omit_details=False):
        """Extracts parameters from a Flame object and converts them into
        string format."""

        # Make the flame header
        lst =  ['<flame ']
        if omit_details:
            lst.append('name="fr0st" >\n')
        else:
            for name,val in self._iter_attributes():
                if isinstance(val, basestring):
                    pass
                elif hasattr(val, "__iter__"):
                    # Remember to convert round numbers to integer.
                    val = " ".join(str(i if i%1 else int(i)) for i in val)
                else:
                    # Assume number: int, float, some numpy type...
                    val = val if val%1 else int(val)
                lst.append('%s="%s" ' %(name, val))
            lst.append('>\n')

        # Make each xform
        lst.extend(xform.to_string() for xform in self.iter_xforms())
        
        # Make the gradient
        if not omit_details:
            lst.append(self.gradient.to_string())

        lst.append('</flame>')

        return "".join(lst)


    def __repr__(self):
        return '<flame "%s">' % self.name
    

    def add_final(self, **kwds):
        if self.final:
            return self.final
        defaults = dict(coefs=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
                        linear=1, color=0, color_speed=0, animate=0)
        defaults.update(kwds)
        self.final = Xform(self, **defaults)
        return self.final


    def add_xform(self, **kwds):
        defaults = dict(coefs=(1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
                        linear=1, color=0, weight=1)
        defaults.update(kwds)
        self.xform.append(Xform(self, **defaults))
        return self.xform[-1]


    def clear(self):
        self.xform = []
        self.final = None
        
    def copy(self):
        return Flame(string=self.to_string())


    def iter_xforms(self):
        for i in self.xform:
            yield i
        if self.final:
            yield self.final

    def iter_posts(self):
        for i in self.iter_xforms():
            if i.post.isactive():
                yield i.post


    @property
    def angle(self):
        return radians(self.rotate)
    @angle.setter
    def angle(self,v):
        self.rotate = degrees(v)

    def reframe(self):
        TwoDoubles = ctypes.c_double * 2

        b_min = TwoDoubles()
        b_max = TwoDoubles()
        b_eps = 0.1
        nsamples = 10000
        genome = Genome.from_string(self.to_string(False))[0]
        flam3_estimate_bounding_box(genome, b_eps, nsamples, b_min, b_max, RandomContext())
        bxoff = (b_min[0]+b_max[0])/2
        if abs(bxoff)<5:
            self.x_offset = bxoff

        byoff = (b_min[1]+b_max[1])/2
        if abs(byoff)<5:
            self.y_offset = byoff
            
        denom = min(b_max[1]-b_min[1],b_max[0]-b_min[0])

        if denom==0:
            tmpscale = 0.0
        else:
            tmpscale = 0.4 * 100.0/min(b_max[1]-b_min[1],b_max[0]-b_min[0])
        
        if tmpscale<10:
            self.scale = 10
        elif tmpscale>100:
            self.scale = 100
        else:
            self.scale = tmpscale
            
    def add_symmetry(self,sym):
        """Adds xforms as per symmetry tag - sym=0 chooses random symmetry"""
        if sym==0:
            sym_distrib = (-4, -3, -2, -2, -2, -1, -1, -1, 2, 2, 2, 3, 3, 4, 4)
            sym = random.choice(sym_distrib)
            
        if sym==0 or sym==1:
            return
            
        if sym<0:
            x = self.add_xform()
            x.weight = 1.0
            x.color_speed = 0.0
            x.animate = 0.0
            x.color = 1.0
            x.a = -1.0
            sym = -sym
        
        srot = 360.0 / float(sym)
        
        for k in range(1,sym):
            x = self.add_xform()
            x.weight = 1.0
            x.color_speed = 0.0
            x.animate = 0.0
            if (sym<3):
                x.color = 0.0
            else:
                x.color = (k-1.0)/(sym-2.0)
            
            x.rotate(k*srot)

    def move_center(self, diff):
        """Moves center point, adjusting for any flame rotation."""
        r, phi = polar(diff)
        phi -= self.rotate
        w, h = rect((r, phi))
        self.x_offset += w
        self.y_offset += h        


    def _iter_attributes(self):
        return itertools.chain((("name", self.name),
                                ("size", self.size),
                                ("center", self.center),
                                ("scale", self.scale * self.width / 100.)),
                               ((k,v) for (k,v) in self.__dict__.iteritems()
                                if k not in self._never_write))

    
    @property_array
    def size(self):
        return self.width, self.height
    @size.setter
    def size(self, v):
        self.width, self.height = v


    @property_array
    def center(self):
        return self.x_offset, self.y_offset
    @center.setter
    def center(self, v):
        self.x_offset, self.y_offset = v


class Palette(object):
    _template = "%c%c%c" * 256
    
    def __init__(self, element=None):
        self.data = numpy.zeros((256, 3), dtype=numpy.uint8)
        if element is not None:
            self.from_flame_element(element)

    def __len__(self):
        return 256

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __iter__(self):
        return iter(self.data)


    def to_string(self):
        return ''.join(['   <color index="%s" rgb="%s %s %s"/>\n' %
                        (idx,
                         int(self.data[idx, 0]),
                         int(self.data[idx, 1]),
                         int(self.data[idx, 2])) for idx in xrange(256)])


    def to_buffer(self):
        return self._template % tuple(int(i) for i in itertools.chain(*self))


    def from_flame_element(self, flame):
        palette_element = flame.find('palette')

        if palette_element is not None:
            # Parse Apo-style palette (block of hex values)
            if int(palette_element.get('count')) != 256:
                raise ParsingError('Palette must contain 256 entries')

            if palette_element.get('format').strip().lower() != 'rgb':
                raise ParsingError('Only rgb palettes are currently supported')

            lst = re.findall('[a-f0-9]{2}', palette_element.text, re.I)
            data = zip(*[(int(i, 16) for i in lst)]*3)            
        else:
            # parse flam3-style palette (list of <color> elements)
            data = [map(float, color.get('rgb').split())
                    for color in flame.findall('color')]
            
        if len(data) != 256:
            raise ParsingError('Wrong number of palette entries specified: '
                               '%s != %s' % (256, len(lst)))
        self.data[:] = data


    def reverse(self):
        self.data = numpy.array(self.data[::-1], dtype=numpy.uint8)


    def rotate(self, index):
        self.data = numpy.array(list(self.data[-index:]) +
                                list(self.data[:-index]), dtype=numpy.uint8)


    def hue(self, value):
        value = value/360.0
        for i in xrange(256):
            h,l,s = rgb2hls(self.data[i])
            h = (h + value) % 1
            rgb = hls2rgb((h,l,s))
            self.data[i] = hls2rgb((h,l,s))

            
    def saturation(self, value):
        value = value/100.0
        for i in xrange(256):
            h,l,s = rgb2hls(self.data[i])
            s = max(0, min(1, s + value))
            self.data[i] = hls2rgb((h,l,s))

            
    def brightness(self, value):
        value = value/100.0
        for i in xrange(256):
            h,l,s = rgb2hls(self.data[i])
            l = max(0, min(1, l + value))
            self.data[i] = hls2rgb((h,l,s))

            
    def invert(self):
        self.data = 255 - self.data


    def from_seeds(self, seeds, curve='cos'):
        ns = len(seeds)
        d = 256/ns
        r = 256%ns
        gen = []
        for i in xrange(ns):
            ds = d + (i < r)
            start, end = seeds[i-1], seeds[i]
            for j in xrange(ds):
                hsv = pblend_color(start, end, j/float(ds), curve)
                gen.append(hsv2rgb(hsv))
        self.data = numpy.array(gen, dtype=numpy.uint8)


    def random(self, hue=(0,1), saturation=(0,1), value=(0,1),  nodes=(5,5),
               curve='cos'):
        h1, h2 = hue
        if h1 > h2:
            hue = h1, h2 + 1
        dims = hue, saturation, value
        seeds = [tuple(random.uniform(*i) for i in dims)
                 for j in range(int(random.uniform(*nodes)))]
        self.from_seeds(seeds, curve)


class Xform(object):
    """Container for transform parameters."""

    # Control behavoir of certain attributes:
    # _always_write: is written to disk even if set at 0
    # _never write: is never written to disk directly.
    # _default: an attribute access returns 0.0 if the attr is not found.
    _always_write = set(("opacity", "color", "color_speed", "animate",
                         "symmetry", "weight")
                        ).union(i[0] for i in variable_list)
    _never_write = set(("_parent", "a", "b" ,"c", "d", "e", "f",
                        "chaos", "post"))
    _default = set(("weight", "a", "b" ,"c", "d", "e", "f",)
                   ).union(variation_list)

    def __init__(self, parent, chaos=(), post=(1.,0.,0.,1.,0.,0.), **kwds):
        self._parent = parent
           
        if not isinstance(self, PostXform):
            self.opacity = 1.0
            self.color = 0.0
            self.color_speed = 0.5
            self.animate = 1.0
            self.chaos = Chaos(self, chaos)
            self.post = PostXform(self, screen_coefs=post)
            
        if kwds:
            map(self.__setattr__, *zip(*kwds.iteritems()))


    @classmethod
    def random(cls, parent, xv=range(flam3_nvariations), n=1, xw=0, fx=False, col=0, ident=0, **kwds):

        # If there are strings in the xv that is passed in, convert them to numbers
        xv = [ variations.get(i,i) for i in xv ]

        badnames = [i for i in xv if type(i).__name__ == 'str']
        if badnames:
            raise AttributeError("Variation specification error: not found (%s)" % badnames[0])

        if fx:
            if parent.final:
                parent.final = None    
            x = parent.add_final()
        else:
            x = parent.add_xform()

        # Clear out the linearness
        x.linear=0
        
        # Randomize the coefficients
        if not ident:
            x.coefs = (random.uniform(-1,1) for i in range(6))
        
            if random.uniform(0,1)>0.7:
                x.c = 0.0
                x.f = 0.0
        
        if not x.isfinal():
            if xw>0: # If weight is > 0, set the weight directly
                x.weight = xw
            elif xw<0: # Weight < 0 means randomize from 0 to -xw
                x.weight = random.uniform(0,-xw)
            else: # Random from 0 to 1
                x.weight = random.uniform(0.1,1)
        
        # Select the variations to use
        use_vars = random.sample(xv,n)
        for uv in use_vars:
            if not ident:
                setattr(x,variation_list[uv],random.uniform(-1,1))
            else:
                setattr(x,variation_list[uv],1.0)
                
            for p,v in variables[variation_list[uv]]:
                setattr(x, "%s_%s" % (variation_list[uv],p), v())
            
        x.color = col
        
        if fx==0:
            x.animate=1
            
        return x


    def from_element(self, element):
        for name, val in element.items():
            if name in ('chaos', 'post'):
                continue
            try:
                if " " in val: 
                    setattr(self, name, map(float, val.split()))
                else:          
                    setattr(self, name, float(val))
            except ValueError:
                setattr(self, name, val)

        if not isinstance(self, PostXform):
            # Chaos and post were already set unconditionally at xform init
            # so they're set here only if they're not None.
            chaos = element.get('chaos', None)
            if chaos is not None:
                self.chaos = Chaos(self, map(float, chaos.split()))
                
            post = element.get('post', None)
            if post is not None:
                self.post = PostXform(self,
                                      screen_coefs=map(float, post.split()))

        # Convert from screen to complex plane orientation
        self.coefs = self.screen_coefs


    def to_string(self):
        lst = ['   <%sxform '%("final" if self.isfinal() else "")]
        lst.extend('%s="%s" ' %i for i in self._iter_attributes())
        lst.append('coefs="%s %s %s %s %s %s" ' % tuple(self.screen_coefs))
        lst.append(self.post.to_string())
        lst.append(self.chaos.to_string())
        lst.append('/>\n')
        
        return "".join(lst)
    
            
    def __repr__(self):
        try:
            index = self.index
        except ValueError:
            # For some reason, the xform is not found inside the parent
            return "<xform>"
        return "<finalxform>" if index is None else "<xform %d>" %(index + 1)

      
    def __getattr__(self,v):
        """Returns a default value for non-existing attributes"""
        # __getattribute__ is the real lookup special method,  __getattr__ is
        # only called when it fails.
        if v in self._default:
            return 0.0
        raise AttributeError(v)


    @property
    def index(self):
        if self.isfinal():
            return None
        try:
            return self._parent.xform.index(self)
        except (AttributeError, ValueError):
            return None

        
    @property_array
    def coefs(self):
        return self.a,self.d,self.b,self.e,self.c,self.f
    @coefs.setter
    def coefs(self,v):
        self.a,self.d,self.b,self.e,self.c,self.f = v

       
    @property_array
    def screen_coefs(self):
        return self.a,-self.d,-self.b,self.e,self.c,-self.f
    @screen_coefs.setter
    def screen_coefs(self, v):
        self.coefs = v
        self.d = -self.d
        self.b = -self.b
        self.f = -self.f


    def list_variations(self):
        return [i for i in variation_list if i in self.__dict__]


    def _iter_attributes(self):
        return ((k,v) for (k,v) in self.__dict__.iteritems()
                if k not in self._never_write and v or k in self._always_write)

#----------------------------------------------------------------------

    @property_array
    def pos(self):
        return self.c, self.f
    @pos.setter
    def pos(self, v1, v2=None):
        if v2 is None: v1, v2 = v1
        self.c = v1
        self.f = v2

    def move_pos(self,v1,v2=None):
        if v2 is None: v1, v2 = v1       
        self.c += v1
        self.f += v2

#----------------------------------------------------------------------
       
    @property_array
    def x(self):
        return self.a + self.c, self.d + self.f
    @x.setter
    def x(self,v1,v2=None):
        if v2 is None: v1, v2 = v1
        self.a  = v1 - self.c
        self.d  = v2 - self.f

    def move_x(self,v1,v2=None):     
        if v2 is None: v1, v2 = v1  
        self.a += v1
        self.d += v2

       
    @property_array
    def y(self):
        return self.b + self.c, self.e + self.f
    @y.setter
    def y(self, v1, v2=None):
        if v2 is None: v1, v2 = v1
        self.b  = v1 - self.c
        self.e  = v2 - self.f

    def move_y(self, v1, v2=None):     
        if v2 is None: v1, v2 = v1 
        self.b += v1
        self.e += v2

       
    @property_array
    def o(self):
        return self.c, self.f
    @o.setter
    def o(self, v1, v2=None):
        if v2 is None: v1, v2 = v1
        self.a += self.c - v1
        self.d += self.f - v2
        self.b += self.c - v1
        self.e += self.f - v2
        self.c  = v1
        self.f  = v2


    def move_o(self,v1,v2=None):
        if v2 is None: v1, v2 = v1
        self.a -= v1
        self.d -= v2
        self.b -= v1
        self.e -= v2
        self.c += v1
        self.f += v2

    @property_array
    def points(self):
        return self.x,self.y,self.o
    @points.setter
    def points(self, v):
        self.x,self.y,self.o = v

#----------------------------------------------------------------------
       
    @property_array
    def xp(self):
        return polar((self.a, self.d))
    @xp.setter
    def xp(self, coord):
        self.a, self.d = rect(coord)

       
    @property_array
    def yp(self):
        return polar((self.b, self.e))
    @yp.setter
    def yp(self, coord):
        self.b, self.e = rect(coord)

       
    @property_array
    def op(self):
        return polar((self.c, self.f))
    @op.setter
    def op(self, coord):
        self.c, self.f = rect(coord)

       
    @property_array
    def polars(self):
        return self.xp, self.yp, self.op
    @polars.setter
    def polars(self, coord):
        self.xp, self.yp, self.op = coord

#----------------------------------------------------------------------

    def scale_x(self, v):
        self.a *= v
        self.d *= v

    def scale_y(self, v):
        self.b *= v
        self.e *= v
        
    def scale(self,v):
        self.a *= v
        self.d *= v
        self.b *= v
        self.e *= v

        
    def rotate_x(self, deg):
        self.xp += (0, deg)
        
    def rotate_y(self, deg):
        self.yp += (0, deg)

    def rotate(self, deg, pivot=None):
        self.rotate_x(deg)
        self.rotate_y(deg)
        if pivot is not None:
            self.orbit(deg, pivot)
            
        
    # TODO: this function looks useless and unused
    def move(self, v):
        self.op = (self.op[0] + v, self.op[1])
        #self.op += (v, 0)


    def orbit(self, deg, pivot=(0, 0)):
        """Orbits the transform around a fixed point without rotating it."""
        if pivot == (0, 0):
            self.op += (0, deg)
        else:
            self.pos -= pivot
            self.op += (0, deg)
            self.pos += pivot

#----------------------------------------------------------------------

    def ispost(self):
        return type(self._parent) == Xform


    def isfinal(self):
        return self is self._parent.final


    def copy(self):
        if self.isfinal():
            return self
        xf = self._parent.add_xform(linear=0)
        xf.from_element(etree.fromstring(self.to_string()))
        return xf


    def delete(self):
        if self.isfinal():
            self._parent.final = None            
        else:
            self._parent.xform.remove(self)



class PostXform(Xform):
    _allowed = set(('coefs', 'points', 'polars', 'screen_coefs', '_parent',
                'a','b','c','d','e','f',
                'x','y','o','pos',
                'xp','yp','op'))
    index = None
    animate = 0

    def __repr__(self):
        return "<post-%s" % repr(self._parent)[1:]

    def __setattr__(self,name,v):
        if name not in self._allowed:
            raise AttributeError, 'Can\'t assign "%s" to %s' %(name,self)
        object.__setattr__(self,name,v)

    def copy(self):
        raise TypeError, "Can't copy a post transform"

    def delete(self):
        raise TypeError, "Can't delete a post transform"

    def isactive(self):
        return self.coefs != (1,0,0,1,0,0)

    def isfinal(self):
        return False

    def to_string(self):
        if self.isactive():
            return 'post="%s %s %s %s %s %s" ' % tuple(self.screen_coefs)
        return ""



class Chaos(object):
    """Handles the chaos values between xforms (as a directed graph).

    The order of xforms could be changed (deletions, insertions, reordering)
    and we need to keep the graph aligned, so the implementation is based on
    identity checks of xform objects. This implies that this class can't be
    instantiated until the flame object has populated its xform list."""
    def __repr__(self):
        return "Chaos(%s)" % list(self)
    
    def __init__(self, parent, lst=()):
        self._parent = parent
        self._dict = collections.defaultdict(partial(float, 1.0))
        if lst:
            xform = parent._parent.xform
            if len(xform) < len(lst):
                raise ValueError("Number of chaos values exceed xforms.")
            self._dict.update(zip(xform, lst))

    def __len__(self):
        if self._parent.isfinal():
            return 0
        return len(self._parent._parent.xform)

    def __iter__(self):
        return (self._dict[i] for i in self._parent._parent.xform)

    def __getitem__(self, pos):
        if isinstance(pos, slice):
            xform = self._parent._parent.xform
            return [self._dict[xform[i]] for i in range(len(self))[pos]]
        if isinstance(pos, Xform):
            return self._dict[pos]
        return self._dict[self._parent._parent.xform[pos]]

    def __setitem__(self, pos, val):
        if isinstance(pos, slice):
            indices = range(len(self))[pos]
            if len(indices) != len(val):
                raise IndexError("Assigned values don't match length of slice")
            map(self.__setitem__, indices, val)
            return
        if val < 0:
            raise ValueError(val)
        if isinstance(pos, Xform):
            self._dict[pos] = val
            return
        self._dict[self._parent._parent.xform[pos]] = val

    def to_string(self):
        lst = list(self)
        for i in reversed(lst):
            if i != 1:
                break
            lst.pop()
        return 'chaos="%s " ' % " ".join(str(i) for i in lst) if lst else ""



def save_flames(path, *flames):
    lst = [f.to_string() if isinstance(f, Flame) else f for f in flames]
    head, ext = os.path.splitext(path)
    if os.path.exists(path) and ext == ".flame":
        shutil.copy(path, head + ".bak")
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(path, "w") as f:
        f.write("""<flames version="%s">\n""" %VERSION)
        f.write("\n".join(lst))
        f.write("""</flames>""")


def split_flamestrings(string):
    return re.findall(r'<flame .*?</flame>', string, re.DOTALL)


def load_flamestrings(filename):
    """Reads a flame file and returns a list of flame strings."""
    return split_flamestrings(open(filename).read())


def load_flames(filename):
    """Reads a flame file and returns a list of flame objects."""
    tree = etree.parse(open(filename))
    return [Flame().from_element(e) for e in tree.findall('flame')]


def show_status(s):
    sys.stdout.write("\r" + " " *80)
    sys.stdout.write("\r%s" %s)
    sys.stdout.flush()


_re_version = re.compile('fr0st ([\d\.]*)', re.I).match
def compare_version(v1, v2=VERSION):
    return cmp(*(float(_re_version(v).group(1)) for v in (v1, v2)))


#Converters

def polar(coord):
    l = sqrt(coord[0]**2 + coord[1]**2)
    theta = atan2(coord[1], coord[0]) * (180.0/pi)
    return l, theta   


def rect(coord):
    real = coord[0] * cos(coord[1]*pi/180.0)
    imag = coord[0] * sin(coord[1]*pi/180.0)
    return real, imag


def rgb2hls(color):
    """Takes an rgb tuple (0-255) and returns hls tuple (hls is scalar)"""
    return colorsys.rgb_to_hls(*(x/255. for x in color))


def hls2rgb((h, l, s)):
    """Takes hls tuple and returns rgb tuple (rgb is int)"""
    return tuple(int(x*255) for x in colorsys.hls_to_rgb(h,l,s))


def rgb2hsv(color):
    return colorsys.rgb_to_hsv(*(x/255. for x in color))


def hsv2rgb((h, s, v)):
    return tuple(int(x*255) for x in colorsys.hsv_to_rgb(h,s,v))


def pblend(s, e, i, curve='linear'):
    """
    s = starting value
    e = ending value
    i = which value to grab (normalized between 0-1)
    """
    if i == 0:
        return s
    if i == 1:
        return e
    if s == e:
        return s

    if curve == 'linear':
        return s + ((e-s) * i)
    elif curve == 'cos':
        return s + ((e-s) * 0.5 * (cos((i+1)*pi)+1))
    elif curve == 'cubic':
        return s + ((e-s) * (3*i*i - 2*i*i*i))
    else:
        raise ValueError('invalid curve')


def pblend_vector(start, end, i, curve='linear'):
    if i == 0:
        return start
    if i == 1:
        return end
    if start == end:
        return start

    if curve == 'linear':
        t = i
    elif curve == 'cos':
        t = 0.5 * (cos((i+1)*pi)+1)
    elif curve == 'cubic':
        t = 3*i*i - 2*i*i*i
    else:
        raise ValueError('invalid curve')
    
    return [s + ((e-s) * t) for s, e in zip(start, end)]


def pblend_color((h1, s1, v1), (h2, s2, v2), n, curve='linear'):
    """Blend a color is hsv space, wrapping hue around 1.0 if necessary."""
    if h1 < h2 - .5:
        h1 += 1
    elif h2 < h1 - .5:
        h2 += 1
    return pblend_vector((h1, s1, v1), (h2, s2, v2), n, curve)

