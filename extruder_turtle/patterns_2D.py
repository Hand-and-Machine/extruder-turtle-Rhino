import Rhino.Geometry as geom
import rhinoscriptsyntax as rs
import ExtruderTurtle as e
import operator as op
import math
import random
import extruder_turtle
from extruder_turtle import *

def line_drawing(t):
	t.penup()
	a0 = 6
	a=a0
	for y in range (0,30):
		t.penup()
		t.lift(3)
		t.set_speed(5000)
		for x in range (0,360):
			f = y*3+a+a*math.cos(math.radians(x*5)) + y*1+a+a*math.sin(math.radians(x*3))+ y*1+a+a*math.sin(math.radians(x*10)) + y*2+a+a*math.cos(math.radians(x*.5))
			if (x==1):
				t.pendown()
				t.lift(-3)
				t.set_speed(1000)
			t.set_position(x*2.5/3.6-120,f-70)
		if(a>=0):
			a = a-a0/30

