# -*- coding: cp936 -*-
import fr0stlib
from fr0stlib.render import *
c=wx.App()
flame=fr0stlib.load_flames("samples.flame")[0]
a=flam3_render(flame,[640,480],100)
b=wx.BitmapFromBuffer(640,480,a)
save_image("a.jpg",b)
