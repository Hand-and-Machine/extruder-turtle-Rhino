import copy
import Rhino.Geometry as geom
import rhinoscriptsyntax as rs
import ExtruderTurtle as e
import operator as op
import math
import random
import extruder_turtle
from extruder_turtle import *

def circle(t, diameter, steps=100, start=0, overlap=1):
	r = diameter/2.0
	circumference = math.pi*diameter
	dcirc = circumference/steps
	if (dcirc<1.0):
		steps = int(circumference) # sets step size to 1mm
	dtheta = 360.0/steps
	for i in range (start, steps+start+2+overlap):
		x = r*math.cos(math.radians(i*dtheta))
		y = r*math.sin(math.radians(i*dtheta))
		if (i==start):	
			t.penup()
			t.set_position(x,y)
			t.pendown()
			# print("in circle x: " +str(x))
			# print("in circle y: " +str(y))
		t.set_position(x,y)


def circular_surface_in_out (t,diameter):
	w = t.get_extrude_width()
	number_circles = int(diameter/(w*2.0))
	delta_d = diameter/number_circles
	d = w*2.0
	while (d<diameter):
		circle(t,d)
		d = d+delta_d
	if (d<=diameter):
		circle(t,diameter)

def circular_surface_out_in(t,diameter):
	w = t.get_extrude_width()
	d = diameter
	while (d>=w):
		circle(t,d)
		d = d-w*2.0

def circular_surface_in_out_dual(t,diameter):
	w = t.get_extrude_width()
	number_circles = int(diameter/(w*2.0))
	delta_d = diameter/number_circles
	d = w*2.0
	while (d<diameter):
		circle(t,d)
		d = d+delta_d
	if (d<=diameter):
		circle(t,diameter)

	# glass
	d = diameter-w
	i=0
	t.swap_extruder()
	t.extrude(2)
	while (d>=w):
		d = d-w*2.0
		if (i%1==0 and d>w):
			circle(t,d, overlap=3)
			t.extrude(2)
			d = d-w*2.0
		i+=1
	t.swap_extruder()

def circular_surface_out_in_dual(t,diameter):
	w = t.get_extrude_width()
	d = diameter
	# primary materail
	while (d>=w):
		circle(t,d)
		d = d-w*2.0

	t.lift(t.get_layer_height()/2.0)

	# secondary material
	d = diameter-w
	i=0
	t.swap_extruder()
	t.extrude(2)
	while (d>=w):
		d = d-w*2.0
		if (i%1==0 and d>w):
			circle(t,d, overlap=3)
			t.extrude(2)
			d = d-w*2.0
		i+=1
	t.swap_extruder()

def zig_zag_circle(t,diameter,amplitude,period,offset=0):
	r = diameter/2.0
	steps = int(360.0/(2*period))
	dtheta = 360.0/steps
	if (offset>0):
		amplitude*=-1
	for i in range (0,steps+1):
		if (i%2==0):
			x = (r+amplitude)*math.cos(math.radians(i*dtheta))
			y = (r+amplitude)*math.sin(math.radians(i*dtheta))

		else:
			x = (r-amplitude)*math.cos(math.radians(i*dtheta))
			y = (r-amplitude)*math.sin(math.radians(i*dtheta))
		if (i==0):	
			t.penup()
			t.set_position(x,y)
			t.pendown()
		t.set_position(x,y)

def pattern_cylinder(t, b_diameter, height, t_diameter=False, array=False, pattern_amplitude = False, bottom_layers=3, top_layers=3):
	base_amplitude = 0.0
	t.set_extrude_rate(2.5)
	base_extrude = t.get_extrude_rate()
	
	if (pattern_amplitude == False):
		pattern_amplitude = base_amplitude+4.0
	if (t_diameter == False):
		t_diameter = b_diameter
	layers = int(height/t.get_layer_height())
	diameter_inc = float(t_diameter - b_diameter)/layers
	extra_bottom_layers = 0 #number of extra layers at the bottom with no pattern
	diameter = b_diameter
	diameter_inc = float(t_diameter - b_diameter)/layers
	circumference = diameter*math.pi

	if (array):
		pattern_width = len(array)-1
		pattern_height = len(array[0])
		steps = pattern_width
		nOscillations = pattern_width
		distance_per_oscillation = circumference/nOscillations

	else:
	  print("ERROR: you need to give this function an array")
	  return;

	steps = pattern_width
	dtheta = 360.0/steps

	#pattern access variables
	xp = 0
	yp = 0

	################################################
	# LAYER LOOP
	################################################
	for l in range (layers):
		r = diameter/2.0

		# create bottom layers if relevant
		if (l < bottom_layers):
			if (l%2==0):
				circular_surface_in_out(t,diameter)
			else:
				circular_surface_out_in(t,diameter)
			t.set_extrude_rate(base_extrude)

		# reset x pattern variable for each layer
		xp = 0
		if (l%2==0):
			base_amplitude*=-1

		################################################
		# MAIN LOOP: STRUCTURE
		# change to nozzle 0 and build structure
		################################################
		if (l>=bottom_layers):
			circle(t,diameter)
			# circle(t,diameter-2*t.get_extrude_width())
		t.lift(t.get_layer_height())

		# ###############################################
		# MAIN LOOP: PATTERN
		# change to nozzle 1 and apply pattern
		# ###############################################
		r_pattern = r-1.0
		if (l>bottom_layers and l%2==0 and l<= layers-top_layers): # only do the pattern for pattern rows
			t.set_extruder(1)
			t.set_extrude_rate(1.5)
			first_flag = True
			for s in range(0,steps+1):
				if (array[s][yp]==1):
					#inner radius: move nozzle to correct inner position
					x = r_pattern*math.cos(math.radians(s*dtheta))
					y = r_pattern*math.sin(math.radians(s*dtheta))
					t.set_position(x,y)
					if (first_flag):
						t.extrude(20)
						first_flag = False
					#pattern radius: bump out
					x = (r+pattern_amplitude)*math.cos(math.radians(s*dtheta))
					y = (r+pattern_amplitude)*math.sin(math.radians(s*dtheta))
					t.set_position(x,y)
					#inner radius: move nozzle back to inner position
					x = r_pattern*math.cos(math.radians(s*dtheta))
					y = r_pattern*math.sin(math.radians(s*dtheta))
					t.set_position(x,y)
				else:
					# don't extrude material where there is no pattern
					t.penup()
					x = r_pattern*math.cos(math.radians(s*dtheta))
					y = r_pattern*math.sin(math.radians(s*dtheta))
					t.set_position(x,y)
					t.pendown()
			t.lift(t.get_layer_height()/10.0) # lift up a little to accommodate dense pattern
		if (l%2==0 and l>=bottom_layers):
			yp+=1

		t.set_extruder(0)
		t.set_extrude_rate(base_extrude)
		diameter = diameter + diameter_inc

def follow_curve(t, curve, double_wall = False, inner_wall=False, steps=100):
	points = rs.DivideCurve (curve, steps)
	dtheta = 360.0/steps


	################################################
	# MAIN LOOP: STRUCTURE
	# change to nozzle 0 and build structure
	################################################
	i=0
	if (inner_wall==False):
		for point in points:
			if (i==0):
				t.set_position(point.X,point.Y)
				t.pendown()
			else:
				t.pendown()
			t.set_position(point.X,point.Y)
			i+=1

	t.set_position(points[0].X,points[0].Y) # close curve
	t.set_position(points[1].X,points[1].Y) # close curve

	if (double_wall or inner_wall):
		inner_curve = rs.OffsetCurve(curve, [0,0,0], t.get_extrude_width())
		inner_points = rs.DivideCurve (inner_curve, steps)
		i=0
		for point in inner_points:
			if (i==0):	
				t.set_position(point.X,point.Y)
				t.pendown()
			t.set_position(point.X,point.Y)
			i+=1

		t.set_position(inner_points[0].X,inner_points[0].Y) # close curve
		t.set_position(inner_points[1].X,inner_points[1].Y) # close curve



def pattern_along_curve(t, curve, array=False, pattern_amplitude = False, pattern_layer=True, windows=False, support=False):
	base_amplitude = 0.0
	t.set_extrude_rate(2.5)
	base_extrude = t.get_extrude_rate()
	steps=100 # gets reset later
	
	if (pattern_amplitude == False):
		pattern_amplitude = base_amplitude+6.0

	if (array):
		pattern_width = len(array)
		steps = pattern_width
		nOscillations = pattern_width
	else:
	  print("ERROR: you need to give this function an array")
	  return;

	if (not(curve)):
		print("ERROR: You need to provide this function a curve")
		return
	else:
		points = rs.DivideCurve (curve, steps)

	dtheta = 360.0/steps

	#pattern access variables
	xp = 0


	################################################
	# MAIN LOOP: STRUCTURE
	# change to nozzle 0 and build structure
	################################################
	i=0
	for point in points:
		if (i==0):
			t.penup()	
			t.set_position(point.X,point.Y)
		if (array[i]==1 and windows==True and support==False):
			t.penup()
		else:
			t.pendown()
		t.set_position(point.X,point.Y)
		i+=1

	t.set_position(points[0].X,points[0].Y) # close curve

	inner_curve = rs.OffsetCurve(curve, [0,0,0], t.get_extrude_width())
	inner_points = rs.DivideCurve (inner_curve, steps)
	i=0
	for point in inner_points:
		if (array[i]==1 and windows==True and support==False):
			t.penup()
		else:
			t.pendown()
		t.set_position(point.X,point.Y)
		i+=1

	t.set_position(inner_points[0].X,inner_points[0].Y) # close curve

	# ###############################################
	# MAIN LOOP: PATTERN
	# change to nozzle 1 and apply pattern
	# ###############################################
	t.lift(t.get_layer_height()/2)
	t.penup()
	if (pattern_layer):
		t.set_extruder(1)
		t.set_extrude_rate(1.5)
		first_flag = True
		i=0
		for point in inner_points:
			if (array[i]==1 or (i<len(inner_points)-1 and array[i+1]==1) or (i>0 and array[i-1]==1)):
				t.set_position(point.X,point.Y)
				t.pendown()
				if (first_flag):
					t.extrude(15)
					first_flag=False
				t.left(90)
				t.forward(pattern_amplitude)
				t.back(pattern_amplitude)
				t.right(90)
			else:
				# don't extrude material where there is no pattern
				t.penup()
				# t.set_position(point.X,point.Y)
			i+=1
	t.penup()
	t.lift(t.get_layer_height()/2)

	t.set_extruder(0)
	t.set_extrude_rate(base_extrude)

