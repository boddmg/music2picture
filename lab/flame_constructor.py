# -*- coding: cp936 -*-
from xml.dom import minidom
import flame_render
flame=minidom.parseString(file("template/template1.flame").read())
a=flame.getElementsByTagName('flame')
a=a[0]
node1=a.attributes.getNamedItem('gamma')
node1.value='3'
a.attributes.setNamedItem(node1)
flame.replaceChild(a,a)
xml=flame.toxml()[22:]
file("samples.flame",'w').write(xml)
flam_render.render()
