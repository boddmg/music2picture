##############################################################################
#  The Combustion Flame Engine - pyflam3
#  http://combustion.sourceforge.net
#
#  Copyright (C) 2007 by Bobby R. Ward <bobbyrward@gmail.com>
#
#  The Combustion Flame Engine is free software; you can redistribute
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
import sys, os, marshal

from _flam3 import *

filter_kernel_dict = {"gaussian": 0,
                      "hermite": 1,
                      "box": 2,
                      "triangle": 3,
                      "bell": 4,
                      "b_spline": 5,
                      "lanczos3": 6,
                      "lanczos2": 7,
                      "mitchell": 8,
                      "blackman": 9,
                      "catrom": 10,
                      "hamming": 11,
                      "hanning": 12,
                      "quadratic": 13}



class Genome(BaseGenome):
    @classmethod
    def load(cls, flamestring, ntemporal_samples=1, temporal_filter=1.0,
             estimator=9, estimator_curve=.4, estimator_minimum=0,
             spatial_oversample=1, filter_radius=1, filter_kernel=0,
             interpolation=0, interpolation_type=1, **kwargs):
        if isinstance(filter_kernel, basestring):
            # if an invalid string is passed, let the KeyError propagate.
            filter_kernel = filter_kernel_dict[filter_kernel.lower()]

        if filter_kernel in (6,7):
            # HACK: force earlyclip for lanczos filters, which don't work
            # properly without it, generating lots of noise.
            kwargs["earlyclip"] = True
        
        frame = Frame(**kwargs)
        frame.genomes, frame.ngenomes = cls.from_string(flamestring)
        
        for i, genome in enumerate(frame.iter_genomes()):
            genome.interpolation = interpolation
            genome.interpolation_type = interpolation_type
            genome.ntemporal_samples = ntemporal_samples
            genome.temporal_filter_width = temporal_filter
            genome.estimator = estimator
            genome.estimator_curve = estimator_curve
            genome.estimator_minimum = estimator_minimum
            genome.spatial_oversample = spatial_oversample
            genome.spatial_filter_radius = filter_radius
            genome.spatial_filter_select = filter_kernel
            genome.time = i

        return frame


    @classmethod
    def from_string(cls, input_buffer, filename='<unknown>', defaults=True):
        # so, flam3_parse_xml2 actually free's the buffer passed in...
        # this hackery sucks but...meh
        string_len = len(input_buffer)
        ptr = flam3_malloc(string_len + 1)
        if not ptr:
            raise MemoryError()
        memset(ptr, 0, string_len+1)
        memmove(ptr, input_buffer, string_len)
        c_buffer = cast(ptr, c_char_p)

        ncps = c_int()

        result = flam3_parse_xml2(c_buffer, filename,
                defaults and flam3_defaults_on or flam3_defaults_off, byref(ncps))

        return result, ncps.value


    @classmethod
    def from_file(cls, filename=None, handle=None, **kwds):
        if not handle and filename:
            s = open(filename).read()
        elif handle:
            s = handle.read()
        else:
            raise IOError()
        return cls.from_string(s, filename=filename, **kwds)


    def to_string(self):
        return flam3_print_to_string(self)



class Frame(BaseFrame):
    def __del__(self):
        # TODO: what if self.genomes is not set?
        flam3_free(self.genomes)
    
    def __init__(self, fixed_seed=False, aspect=1.0, buffer_depth=64,
                 bytes_per_channel=1, progress_func=None, nthreads=0,
                 earlyclip=False, sub_batch_size=100000):
        if not fixed_seed:
            # Initializes the random seed based on system time.
            # A fixed seed is used for preview renders with high noise levels.
            flam3_init_frame(byref(self))

        self.pixel_aspect_ratio = aspect
        self.bits = buffer_depth
        self.bytes_per_channel = bytes_per_channel
        self.earlyclip = earlyclip
        self.sub_batch_size = sub_batch_size

        if callable(progress_func):
            self.progress = ProgressFunction(progress_func)

        if nthreads > 0:
            self.nthreads = nthreads
        else:
            # 0: all cores, -1: all cores except 1, etc...
            self.nthreads = max(1, flam3_count_nthreads() + nthreads)


    def iter_genomes(self):
        for i in xrange(self.ngenomes):
            yield self.genomes[i]
            

    def render(self, size, quality, transparent=0, time=0):
        if not all(size):
            raise ZeroDivisionError("Size passed to render function is 0.")

        self.time = time

        genome = self.genomes[time]
        width, height = size
        genome.pixels_per_unit /= genome.width/float(width) # adjusts scale
        genome.width = width
        genome.height = height
        genome.sample_density = quality

        output_buffer = allocate_output_buffer(size, transparent+3)
        stats = RenderStats()
        flam3_render(byref(self), output_buffer, flam3_field_both,
                     transparent+3, transparent, byref(stats))

        return output_buffer, stats
