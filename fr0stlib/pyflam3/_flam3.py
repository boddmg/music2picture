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
import itertools, sys, os
from ctypes import *
from fr0stlib.pyflam3.constants import *
from fr0stlib.pyflam3.variations import *
from fr0stlib.pyflam3.find_dll import find_dll


libflam3 = find_dll('libflam3')


IteratorFunction = CFUNCTYPE(None, c_void_p, c_double)
SpatialFilterFunction = CFUNCTYPE(c_double, c_double)
ProgressFunction = CFUNCTYPE(c_int, POINTER(py_object), c_double, c_int, c_double)


def copy_to(src, dest):
    for (src_val, dest_val) in itertools.izip(src, dest):
        dest_val = src_val


class RandomContext(Structure):
    _fields_ = [ ('randcnt', c_ulong)
               , ('randrsl', c_ulong * flam3_RANDSIZ)
               , ('randmem', c_ulong * flam3_RANDSIZ)
               , ('randa', c_ulong)
               , ('randb', c_ulong)
               , ('randc', c_ulong)
               ]


class BaseImageComments(Structure): pass

class RenderStats(Structure):
    _fields_ = [ ('badvals', c_double)
               , ('num_iters', c_long)
               , ('render_seconds', c_int)]

class ImageStore(Structure): pass

class PaletteEntry(Structure):
    _fields_ = [('index', c_double),
                ('color', c_double * 4)]

class BasePalette(Structure):
    _fields_ = [('entries', PaletteEntry * 256)]

class BaseXForm(Structure): pass

class BaseGenome(Structure):
    _fields_ = [ ('name', c_char * (flam3_name_len + 1))
               , ('time', c_double)
               , ('interpolation', c_int)
               , ('interpolation_type', c_int)
               , ('palette_interpolation', c_int)
               , ('num_xforms', c_int)
               , ('final_xform_index', c_int)
               , ('final_xform_enable', c_int)
               , ('xform', POINTER(BaseXForm))
               , ('chaos', POINTER(c_double)) # what to do with this?
               , ('chaos_enable', c_int)
               , ('genome_index', c_int)
               , ('parent_fname', c_char * flam3_parent_fn_len)
               , ('symmetry', c_int)
               , ('palette', BasePalette)
               , ('input_image', c_char_p)
               , ('palette_index', c_int )      #TODO: Propertyize this(huh?)
               , ('brightness', c_double)
               , ('contrast', c_double)
               , ('gamma', c_double)
               , ('highlight_power', c_double)
               , ('width', c_int )                  # wrapped
               , ('height', c_int )                 # wrapped
               , ('spatial_oversample', c_int )
               , ('_center', c_double * 2)          # wrapped
               , ('rot_center', c_double * 2)       # wrapped
               , ('rotate', c_double)           #TODO: Propertyize this
                                                #TODO: Add a angle version of the property
               , ('vibrancy', c_double)
               , ('hue_rotation', c_double)
               , ('background', c_double * 3)   #TODO: Propertyize this
               , ('zoom', c_double)
               , ('pixels_per_unit', c_double)
               , ('spatial_filter_radius', c_double)
               , ('spatial_filter_select', c_int)
               , ('sample_density', c_double)
               , ('nbatches', c_int)
               , ('ntemporal_samples', c_int)
               , ('estimator', c_double)
               , ('estimator_curve', c_double)
               , ('estimator_minimum', c_double)
               , ('edits', py_object) # or c_void_p?
               , ('gam_lin_thresh', c_double)
               , ('palette_index0', c_int)
               , ('hue_rotation0', c_double)
               , ('palette_index1', c_int)
               , ('hue_rotation1', c_double)
               , ('palette_blend', c_double)
               , ('temporal_filter_type', c_int)
               , ('temporal_filter_width', c_double)
               , ('temporal_filter_exp', c_double)
               , ('palette_mode', c_int)
               ]


class BaseFrame(Structure):
    _fields_ = [ #('temporal_filter_radius', c_double)
                ('pixel_aspect_ratio', c_double)
               , ('genomes', POINTER(BaseGenome))
               , ('ngenomes', c_int)
               , ('verbose', c_int)
               , ('bits', c_int)
               , ('bytes_per_channel', c_int)
               , ('earlyclip', c_int)
               , ('time', c_double)
               , ('progress', ProgressFunction)
               , ('progress_parameter', py_object) # or c_void_p?
               , ('rc', RandomContext)
               , ('nthreads', c_int)
               , ('sub_batch_size', c_int)
               ]


def allocate_output_buffer(size, channels):
    return (c_ubyte * (size[0] * size[1] * channels))()

#-----------------------------------------------------------------------------

#int flam3_colorhist(flam3_genome *cp, int num_batches, randctx *rc, double *hist)
libflam3.flam3_colorhist.argtypes = [POINTER(BaseGenome), c_int, POINTER(RandomContext), POINTER(c_double)]
flam3_colorhist = libflam3.flam3_colorhist

#void flam3_xform_preview(flam3_genome *cp, int xi, double range, int numvals, int depth, double *result, randctx *rc)
libflam3.flam3_xform_preview.argtypes = [POINTER(BaseGenome), c_int, c_double, c_int, c_int, POINTER(c_double), POINTER(RandomContext)]
flam3_xform_preview = libflam3.flam3_xform_preview

#-----------------------------------------------------------------------------

# char *flam3_version();
libflam3.flam3_version.restype = c_char_p
flam3_version = libflam3.flam3_version

# void flam3_create_xform_distrib(flam3_genome *cp, unsigned short *xform_distrib);
libflam3.flam3_create_xform_distrib.argtypes = [POINTER(BaseGenome), POINTER(c_ushort)]
flam3_create_xform_distrib = libflam3.flam3_create_xform_distrib

# void flam3_random(flam3_genome *g, int *ivars, int ivars_n, int sym, int spec_xforms);
libflam3.flam3_random.argtypes = [POINTER(BaseGenome), POINTER(c_int), c_int, c_int, c_int]
flam3_random = libflam3.flam3_random

# flam3_genome *flam3_parse_xml2(char *s, char *fn, int default_flag, int *ncps);
libflam3.flam3_parse_xml2.argtypes = [c_char_p, c_char_p, c_int, POINTER(c_int)]
libflam3.flam3_parse_xml2.restype = POINTER(BaseGenome)
flam3_parse_xml2 = libflam3.flam3_parse_xml2

# char *flam3_print_to_string(flam3_genome *cp) 
libflam3.flam3_print_to_string.argtypes = [POINTER(BaseGenome)]
libflam3.flam3_print_to_string.restype = c_char_p
flam3_print_to_string = libflam3.flam3_print_to_string

# int flam3_count_nthreads(void);
libflam3.flam3_count_nthreads.restype = c_int
flam3_count_nthreads = libflam3.flam3_count_nthreads

# void flam3_render(flam3_frame *f, unsigned char *out, int field, int nchan, int transp, stat_struct *stats);
# void flam3_render(flam3_frame *f, void *out         , int field, int nchan, int transp, stat_struct *stats)
libflam3.flam3_render.argtypes = [POINTER(BaseFrame), POINTER(c_ubyte), c_int, c_int, c_int, POINTER(RenderStats)]
flam3_render = libflam3.flam3_render

# void flam3_interpolate(flam3_genome *genomes, int ngenomes, double time, double stagger, flam3_genome *result);
libflam3.flam3_interpolate.argtypes = [POINTER(BaseGenome), c_int, c_double, c_double, POINTER(BaseGenome)]
flam3_interpolate = libflam3.flam3_interpolate

# double flam3_render_memory_required(flam3_frame *f);
libflam3.flam3_render_memory_required.argtypes = [POINTER(BaseFrame)]
libflam3.flam3_render_memory_required.restype = c_double
flam3_render_memory_required = libflam3.flam3_render_memory_required

# void flam3_init_frame(flam3_frame *f);
libflam3.flam3_init_frame.argtypes = [POINTER(BaseFrame)]
flam3_init_frame = libflam3.flam3_init_frame


flam3_malloc = libflam3.flam3_malloc
flam3_malloc.argtypes = [c_int]
flam3_malloc.restype = c_void_p

flam3_free = libflam3.flam3_free
flam3_free.argtypes = [c_void_p]

#int flam3_estimate_bounding_box(flam3_genome *cp, double eps, int nsamples,
#             double *bmin, double *bmax, randctx *rc)
libflam3.flam3_estimate_bounding_box.argtypes = [POINTER(BaseGenome), c_double, c_int, POINTER(c_double), POINTER(c_double), POINTER(RandomContext)]
flam3_estimate_bounding_box = libflam3.flam3_estimate_bounding_box


