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
import random
from collections import defaultdict
from functools import partial

from constants import flam3_nvariations


VAR_LINEAR = 0
VAR_SINUSOIDAL =   1
VAR_SPHERICAL = 2
VAR_SWIRL =3
VAR_HORSESHOE  =4
VAR_POLAR =5
VAR_HANDKERCHIEF =6
VAR_HEART = 7
VAR_DISC = 8
VAR_SPIRAL = 9
VAR_HYPERBOLIC = 10
VAR_DIAMOND = 11
VAR_EX = 12
VAR_JULIA = 13
VAR_BENT = 14
VAR_WAVES = 15
VAR_FISHEYE = 16
VAR_POPCORN = 17
VAR_EXPONENTIAL = 18
VAR_POWER = 19
VAR_COSINE = 20
VAR_RINGS = 21
VAR_FAN = 22
VAR_BLOB = 23
VAR_PDJ = 24
VAR_FAN2 = 25
VAR_RINGS2 = 26
VAR_EYEFISH = 27
VAR_BUBBLE = 28
VAR_CYLINDER = 29
VAR_PERSPECTIVE = 30
VAR_NOISE = 31
VAR_JULIAN = 32
VAR_JULIASCOPE = 33
VAR_BLUR = 34
VAR_GAUSSIAN_BLUR = 35
VAR_RADIAL_BLUR = 36
VAR_PIE = 37
VAR_NGON = 38
VAR_CURL = 39
VAR_RECTANGLES = 40
VAR_ARCH = 41
VAR_TANGENT = 42
VAR_SQUARE = 43
VAR_RAYS = 44
VAR_BLADE = 45
VAR_SECANT2 = 46
VAR_TWINTRIAN = 47
VAR_CROSS = 48
VAR_DISC2 = 49
VAR_SUPER_SHAPE = 50
VAR_FLOWER = 51
VAR_CONIC = 52
VAR_PARABOLA = 53
VAR_BENT2 = 54
VAR_BIPOLAR = 55
VAR_BOARDERS = 56
VAR_BUTTERFLY = 57
VAR_CELL = 58
VAR_CPOW = 59
VAR_CURVE = 60
VAR_EDISC = 61
VAR_ELLIPTIC = 62
VAR_ESCHER = 63
VAR_FOCI = 64
VAR_LAZYSUSAN = 65
VAR_LOONIE = 66
VAR_PRE_BLUR = 67
VAR_MODULUS = 68
VAR_OSCILLOSCOPE = 69
VAR_POLAR2 = 70
VAR_POPCORN2 = 71
VAR_SCRY = 72
VAR_SEPARATION = 73
VAR_SPLIT = 74
VAR_SPLITS = 75
VAR_STRIPES = 76
VAR_WEDGE = 77
VAR_WEDGE_JULIA = 78
VAR_WEDGE_SPH = 79
VAR_WHORL = 80
VAR_WAVES2 = 81
VAR_EXP = 82
VAR_LOG = 83
VAR_SIN = 84
VAR_COS = 85
VAR_TAN = 86
VAR_SEC = 87
VAR_CSC = 88
VAR_COT = 89
VAR_SINH = 90
VAR_COSH = 91
VAR_TANH = 92
VAR_SECH = 93
VAR_CSCH = 94
VAR_COTH = 95
VAR_AUGER = 96
VAR_FLUX = 97
VAR_MOBIUS = 98


variations = {}
variation_list = [None] * 99 #flam3_nvariations
for k,v in locals().items():
    if k.startswith("VAR_"):
        name = k[4:].lower()
        variations[name] = v
        variation_list[v] = name


variable_list = [('blob_low', 0.2, 0.7, float),  
                 ('blob_high', 0.8, 1.2, float),  
                 ('blob_waves', 2, 7, int),  
                 ('pdj_a', -3.0, 3.0, float),  
                 ('pdj_b', -3.0, 3.0, float),
                 ('pdj_c', -3.0, 3.0, float),
                 ('pdj_d', -3.0, 3.0, float),
                 ('fan2_x', 0.2, 0.8, float),  
                 ('fan2_y', 2, 6, int),  
                 ('rings2_val', 0.1, 2.0, float),  
                 ('perspective_angle', 0, 1, float),  
                 ('perspective_dist', 1, 3, float),  
                 ('julian_power', 4, 10, int),  
                 ('julian_dist', 0.5, 2.0, float),  
                 ('juliascope_power', 4, 10, int),  
                 ('juliascope_dist', 0.5, 2.0, float),  
                 ('radial_blur_angle', -1, 1, float),  
                 ('pie_slices', 3, 10, int),  
                 ('pie_rotation', 0.0, 0.0, float),  
                 ('pie_thickness', 0.2, 0.8, float),  
                 ('ngon_sides', 3, 9, int),
                 ('ngon_power', 1.0, 4.0, float),  
                 ('ngon_circle', 0.0, 3.0, float),  
                 ('ngon_corners', 0.0, 2.0, float),  
                 ('curl_c1', 0.1, 0.7, float),  
                 ('curl_c2', 0.1, 0.7, float),  
                 ('rectangles_x', 0, 1, float),  
                 ('rectangles_y', 0, 1, float),  
                 ('disc2_rot', 0, 0.5, float),  
                 ('disc2_twist', 0, 0.5, float),  
                 ('super_shape_rnd', 0, 1, float),  
                 ('super_shape_m', 1, 6, int),  
                 ('super_shape_n1', 0, 40, float),  
                 ('super_shape_n2', 0, 20, float),  
                 ('super_shape_n3', 0, 40, float),  
                 ('super_shape_holes', 0, 0, float),  
                 ('flower_petals', 3, 7, int),  
                 ('flower_holes', 0, 0.5, float),
                 ('conic_eccentricity', 0, 1, float),  
                 ('conic_holes', 0, 1, float),  
                 ('parabola_height',  .5, 1.5, float),  
                 ('parabola_width', .5, 1.5, float),  
                 ('bent2_x', -1.5, 1.5, float),  
                 ('bent2_y', -1.5, 1.5, float),  
                 ('bipolar_shift', -1, 1, float),  
                 ('cell_size', 0.5, 2.5, float),  
                 ('cpow_r', 0, 3, float),                   
                 ('cpow_i', -0.5, 0.5, float),  
                 ('cpow_power', 1, 5, int),                   
                 ('curve_xamp', -2.5, 2.5, float),                   
                 ('curve_yamp', -2, 2, float),                   
                 ('curve_xlength', 1, 3, float),                   
                 ('curve_ylength', 1, 3, float),                   
                 ('escher_beta', -3, 3, float),                   
                 ('lazysusan_spin', -3, 3, float),                   
                 ('lazysusan_space', -2, 2, float),                   
                 ('lazysusan_twist', -2, 2, float),                   
                 ('lazysusan_x', 0.0, 0.0, float),  
                 ('lazysusan_y', 0.0, 0.0, float),                   
                 ('modulus_x', -1.0, 1.0, float),                   
                 ('modulus_y', -1.0, 1.0, float),                   
                 ('oscilloscope_separation', 0, 2, float),                   
                 ('oscilloscope_frequency', -3, 3, float),                   
                 ('oscilloscope_amplitude', 1, 3, float),                   
                 ('oscilloscope_damping', 0, 1, float),                   
                 ('popcorn2_x', 0, 0.2, float),                   
                 ('popcorn2_y', 0, 0.2, float),                   
                 ('popcorn2_c', 0, 5, float),  
                 ('separation_x', 0, 2, float),                   
                 ('separation_xinside', -1, 1, float),                   
                 ('separation_y', 0, 2, float),                   
                 ('separation_yinside', -1, 1, float),                   
                 ('split_xsize', -1, 1, float),                   
                 ('split_ysize', -1, 1, float),                   
                 ('splits_x', -1, 1, float),                   
                 ('splits_y', -1, 1, float),                   
                 ('stripes_space',  0, 1, float),                   
                 ('stripes_warp',  0, 5, float),  
                 ('wedge_angle', 0, 3, float),                   
                 ('wedge_hole', -.5, .5, float),                   
                 ('wedge_count', 1, 6, int),                   
                 ('wedge_swirl', 0, 1, float),                   
                 ('wedge_julia_angle', 0, 3, float),                   
                 ('wedge_julia_count', 2, 7, int),                   
                 ('wedge_julia_power', 2, 7, int),                   
                 ('wedge_julia_dist', 1, 4, float),                   
                 ('wedge_sph_angle', 0, 3, float),                   
                 ('wedge_sph_count', 1, 5, int),  
                 ('wedge_sph_hole', -.5, .5, float),                   
                 ('wedge_sph_swirl', 0, 1, float),                   
                 ('whorl_inside', -.5, .5, float),                   
                 ('whorl_outside', -.5, .5, float),                   
                 ('waves2_freqx', 0, 4, float),                   
                 ('waves2_scalex', 0.5, 1.5, float),                   
                 ('waves2_freqy', 0, 4, float),                   
                 ('waves2_scaley', 0.5, 1.5, float),         
                 ('auger_freq', 3, 6, int),
                 ('auger_scale', .1, .8, float),
                 ('auger_sym', 0, 1, float),
                 ('auger_weight', 0, 1, float),
                 ('flux_spread', 0.5, 1, float),
                 ('mobius_re_a', -1, 1, float),
                 ('mobius_im_a', -1, 1, float),
                 ('mobius_re_b', -1, 1, float),
                 ('mobius_im_b', -1, 1, float),
                 ('mobius_re_c', -1, 1, float),
                 ('mobius_im_c', -1, 1, float),
                 ('mobius_re_d', -1, 1, float),
                 ('mobius_im_d', -1, 1, float)]


variables = defaultdict(list)
for k, lo, hi, ty in variable_list:
    variation, variable = k.rsplit("_", 1)
    randfunc = random.randint if ty is int else random.uniform
    variables[variation].append((variable, partial(randfunc, lo, hi)))

