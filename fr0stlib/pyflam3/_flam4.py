import sys
from ctypes import *
from fr0stlib.pyflam3.find_dll import find_dll


libflam4 = find_dll('Flam4CUDA_LIB', omit_lib_in_windows=True)
        

LastRenderSize = 0, 0
cudaRunning = False


class rgba(Structure):
    _fields_ = [  ('r', c_float)
                , ('g', c_float)
                , ('b', c_float)
                , ('a', c_float) ]

class xForm(Structure):
    _fields_ = [  ('a', c_float)
                , ('b', c_float)
                , ('c', c_float)
                , ('d', c_float)
                , ('e', c_float)
                , ('f', c_float)
                , ('linear', c_float)
                , ('sinusoidal', c_float)
                , ('spherical', c_float)
                , ('swirl', c_float)
                , ('horseshoe', c_float)
                , ('polar', c_float)
                , ('handkerchief', c_float)
                , ('heart', c_float)
                , ('disc', c_float)
                , ('spiral', c_float)
                , ('hyperbolic', c_float)
                , ('diamond', c_float)
                , ('ex', c_float)
                , ('julia', c_float)
                , ('bent', c_float)
                , ('waves', c_float)
                , ('fisheye', c_float)
                , ('popcorn', c_float)
                , ('exponential', c_float)
                , ('power', c_float)
                , ('cosine', c_float)
                , ('rings', c_float)
                , ('fan', c_float)
                , ('blob', c_float)
                , ('pdj', c_float)
                , ('fan2', c_float)
                , ('rings2', c_float)
                , ('eyefish', c_float)
                , ('bubble', c_float)
                , ('cylinder', c_float)
                , ('perspective', c_float)
                , ('noise', c_float)
                , ('julian', c_float)
                , ('juliascope', c_float)
                , ('blur', c_float)
                , ('gaussian_blur', c_float)
                , ('radial_blur', c_float)
                , ('pie', c_float)
                , ('ngon', c_float)
                , ('curl', c_float)
                , ('rectangles', c_float)
                , ('arch', c_float)
                , ('tangent', c_float)
                , ('square', c_float)
                , ('rays', c_float)
                , ('blade', c_float)
                , ('secant', c_float)
                , ('twintrian', c_float)
                , ('cross', c_float)
                , ('disc2', c_float)
                , ('supershape', c_float)
                , ('flower', c_float)
                , ('conic', c_float)
                , ('parabola', c_float)
                , ('pa', c_float)
                , ('pb', c_float)
                , ('pc', c_float)
                , ('pd', c_float)
                , ('pe', c_float)
                , ('pf', c_float)

                , ('blob_high', c_float)
                , ('blob_low', c_float)
                , ('blob_waves', c_float)
                , ('pdj_a', c_float)
                , ('pdj_b', c_float)
                , ('pdj_c', c_float)
                , ('pdj_d', c_float)
                , ('fan2_x', c_float)
                , ('fan2_y', c_float)
                , ('rings2_val', c_float)
                , ('perspective_angle', c_float)
                , ('perspective_dist', c_float)
                , ('julian_power', c_float)
                , ('julian_dist', c_float)
                , ('juliascope_power', c_float)
                , ('juliascope_dist', c_float)
                , ('radial_blur_angle', c_float)
                , ('pie_slices', c_float)
                , ('pie_rotation', c_float)
                , ('pie_thickness', c_float)
                , ('ngon_power', c_float)
                , ('ngon_sides', c_float)
                , ('ngon_corners', c_float)
                , ('ngon_circle', c_float)
                , ('curl_c1', c_float)
                , ('curl_c2', c_float)
                , ('rectangles_x', c_float)
                , ('rectangles_y', c_float)
                , ('disc2_rot', c_float)
                , ('disc2_twist', c_float)
                , ('supershape_m', c_float)
                , ('supershape_n1', c_float)
                , ('supershape_n2', c_float)
                , ('supershape_n3', c_float)
                , ('supershape_holes', c_float)
                , ('supershape_rnd', c_float)
                , ('flower_holes', c_float)
                , ('flower_petals', c_float)
                , ('conic_holes', c_float)
                , ('conic_eccen', c_float)
                , ('parabola_height', c_float)
                , ('parabola_width', c_float)
            
                , ('color', c_float)
                , ('symmetry', c_float)
                , ('weight', c_float)
                , ('opacity', c_float)]

######################################################
#Should be unused in fr0st - included for completeness
class unAnimatedxForm(Structure):
    _fields_ = [  ('a', c_float)
                , ('b', c_float)
                , ('d', c_float)
                , ('e', c_float) ]
######################################################

class Flame(Structure):
    _fields_ = [  ('center', c_float*2)
                , ('size', c_float*2)
                , ('hue', c_float)
                , ('quality', c_float)
                , ('rotation', c_float)
                , ('symmetryKind', c_float)
                , ('background', rgba)
                , ('brightness', c_float)
                , ('gamma', c_float)
                , ('vibrancy', c_float)
                , ('numTrans', c_int)
                , ('isFinalXform', c_int)
                , ('finalXform', xForm)
                
                ,('numColors', c_int)
                ,('trans', POINTER(xForm))
                ,('transAff', POINTER(unAnimatedxForm))
                ,('colorIndex', POINTER(rgba)) ]

libflam4.cuStartCuda.argtypes = [c_uint, c_int, c_int]
libflam4.cuStopCuda.argtypes = []
libflam4.cuRunFuse.argtypes = [POINTER(Flame)]
libflam4.cuStartFrame.argtypes = [POINTER(Flame)]
libflam4.cuRenderBatch.argtypes = [POINTER(Flame)]
libflam4.cuFinishFrame.argtypes = [POINTER(Flame), POINTER(c_ubyte), c_uint]
libflam4.cuEzRenderFrame.argtypes= [POINTER(Flame), POINTER(c_ubyte), c_uint, c_int]
libflam4.cuCalcNumBatches.argtypes= [c_int, c_int, c_int]

def loadFlam4(flame):
    flam4Flame = Flame()
    flam4Flame.center[0] = flame.center[0]
    flam4Flame.center[1] = flame.center[1]
    flam4Flame.size[0] = 100./flame.scale
    flam4Flame.size[1] = -100.*(flame.height/float(flame.width))/flame.scale        # flip the image right side up!
    flam4Flame.hue = 0                              #LINKME
    flam4Flame.rotation = flame.angle # flam4 uses radians for rotate!
    flam4Flame.symmetry = 0                         #LINKME
    flam4Flame.background = rgba(flame.background[0]/255.,flame.background[1]/255.,flame.background[2]/255.,0)
    flam4Flame.brightness = flame.brightness
    flam4Flame.gamma = flame.gamma
    flam4Flame.vibrancy = 1                         #LINKME
    flam4Flame.numTrans = len(flame.xform)
    flam4Flame.isFinalXform = bool(flame.final)
    flam4Flame.numColors = len(flame.gradient)
    flam4Flame.colorIndex = (rgba*flam4Flame.numColors)()

    for ci, color in zip(flam4Flame.colorIndex, flame.gradient):
        ci.r, ci.g, ci.b = (i/255. for i in color)
        ci.a = 1
                
    flam4Flame.trans = (xForm*flam4Flame.numTrans)()
    uxf = (unAnimatedxForm*flam4Flame.numTrans)()
    flam4Flame.transAff = uxf
    for x in range(len(flame.xform)):
        loadXform(flame.xform[x],flam4Flame.trans[x])
        setTransAff(flam4Flame.transAff[x],flam4Flame.trans[x])
    sum = 0
    for n in range(flam4Flame.numTrans):
        sum = sum+flam4Flame.trans[n].weight
    sum2 = 0
    for n in range(flam4Flame.numTrans):
        sum2 = sum2+flam4Flame.trans[n].weight/sum
        flam4Flame.trans[n].weight = sum2
    if flam4Flame.isFinalXform:
        loadXform(flame.final, flam4Flame.finalXform)
    return flam4Flame
    
def loadXform(inxform, xform):
    for x in xform._fields_:
        try:
            object.__setattr__(xform, x[0],inxform.__getattribute__(x[0]))
        except AttributeError:
            object.__setattr__(xform, x[0],0)
    post = inxform.post
    xform.b = -xform.b
    xform.d = -xform.d
    xform.f = -xform.f
    xform.pa = post.a
    xform.pb = -post.b
    xform.pc = post.c
    xform.pd = -post.d
    xform.pe = post.e
    xform.pf = -post.f
    # Convert from flam3 color_speed back to symmetry, so flam4 will interpret
    # the color correctly.
    xform.symmetry = 1. - inxform.color_speed * 2
    return xform
    
def setTransAff(transAff, xform):
    transAff.a = xform.a
    transAff.b = xform.b
    transAff.d = xform.d
    transAff.e = xform.e
    
def renderFlam4(flame, size, quality, progress_func, transparent=False,
                **kwds):
    global LastRenderSize, cudaRunning
    w,h = size
    outputBuffer = (c_ubyte*(w*h*4))()
    if LastRenderSize != size:
        if cudaRunning:
            libflam4.cuStopCuda()
        cudaRunning = True
        libflam4.cuStartCuda(c_uint(0),c_int(w),c_int(h))
        LastRenderSize = size

    numBatches = max(3, libflam4.cuCalcNumBatches(w, h, quality))
    flame.quality = numBatches
    libflam4.cuStartFrame(pointer(flame))
    # HACK: if we're only doing 3 batches, assume preview and don't run fuse
    if flame.quality > 3:
        libflam4.cuRunFuse(pointer(flame))
    for x in range(numBatches):
        libflam4.cuRenderBatch(pointer(flame))
        flag = progress_func(None, float(x+1)*100/flame.quality, 0, 0)
        # HACK: the print forces a refresh. Without it, the prog func will
        # never have time to run.
        sys.stdout.write("")
        if flag:
            return outputBuffer
    libflam4.cuFinishFrame(pointer(flame), outputBuffer, transparent)
    return outputBuffer

