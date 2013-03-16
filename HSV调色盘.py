# -*- coding: cp936 -*-
import pygame
from pygame.locals import *
from sys import exit
import colorsys

pygame.init()
 
screen = pygame.display.set_mode((640, 480), 0, 32)
 
def create_scales(height,hue,saturation,value):
    #创建surface
    hue_scale_surface = pygame.surface.Surface((640, height))
    saturation_scale_surface = pygame.surface.Surface((640, height))
    value_scale_surface = pygame.surface.Surface((640, height))
    
    for x in range(640):
        _hue=[255*y for y in colorsys.hsv_to_rgb(x/640.,saturation,value)]
        _saturation =[255*y for y in colorsys.hsv_to_rgb(hue,x/640.,value)]
        _value =[255*y for y in colorsys.hsv_to_rgb(hue,saturation,x/640.)]

        line_rect = Rect(x, 0, 1, height)
        
        pygame.draw.rect(hue_scale_surface, _hue, line_rect)
        pygame.draw.rect(saturation_scale_surface, _saturation, line_rect)
        pygame.draw.rect(value_scale_surface, _value, line_rect)
        
    return hue_scale_surface, saturation_scale_surface, value_scale_surface
 
hue_scale, saturation_scale, value_scale = create_scales(80,0.5,0.5,0.5)
color_hsv=[0.1,0.7,0.7]
color_rgb=[0,0,0]
mainloop = True
while mainloop:
 
    hue_scale, saturation_scale, value_scale = create_scales(80,color_hsv[0],color_hsv[1],color_hsv[2])
    screen.fill((0, 0, 0))
 
    screen.blit(hue_scale, (0, 00))
    screen.blit(saturation_scale, (0, 80))
    screen.blit(value_scale, (0, 160))
 
    x, y = pygame.mouse.get_pos()
 
    if pygame.mouse.get_pressed()[0]:
        for component in range(3):
            if y > component*80 and y < (component+1)*80:
                color_hsv[component] = x/639.
        color_rgb=[255*x for x in colorsys.hsv_to_rgb(color_hsv[0],color_hsv[1],color_hsv[2])]
        pygame.display.set_caption("PyGame Color Test - "+str(tuple(color_hsv)))
 
    for component in range(3):
        pos = ( int((color_hsv[component])*639.), component*80+40 )
        pygame.draw.circle(screen, (255, 255, 255), pos, 20)
 
    pygame.draw.rect(screen, tuple(color_rgb), (0, 240, 640, 240))
 
    pygame.display.update()
    
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            mainloop = False
            pygame.display.quit()
            pygame.quit()
            break

