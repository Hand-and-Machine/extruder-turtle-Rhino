import copy
import Rhino.Geometry as geom
import rhinoscriptsyntax as rs
import ExtruderTurtle as e
import operator as op
import math
import random

# slices a shape using layer_height
def slice_with_turtle (t, shape, walls = 1, layer_height=False, spiral_up=False, bottom = False):
	if (layer_height==False or layer_height == 0):
		layer_height = t.get_layer_height()
	bb = rs.BoundingBox(shape)
	height = rs.Distance(bb[0], bb[4])
	print("height: " +str(height))
	layers = int(round(height/layer_height)) # number of slices
	print("layers: " +str(layers))
	size = rs.Distance(bb[0], bb[6])*2 # size of slicing plane
	point_bottom = (rs.CreatePoint(0,0,bb[0].Z))
	point_top = (rs.CreatePoint(0,0,bb[4].Z))

	slices = rs.AddSrfContourCrvs(shape,(point_bottom,point_top),layer_height)

	#follow slice curves with turtle
	follow_slice_curves_with_turtle(t,slices,walls=walls,spiral_up=spiral_up, bottom=bottom)

	return slices

# given a list of curves that slice a shape (slices)
# follow the curves with the turtle
def follow_slice_curves_with_turtle(t,slices,walls=1, bottom = False, spiral_up=False, matrix = False):
	resolution = t.get_resolution()

	if (bottom!=False):
		bottom_layers = bottom
	else:
		bottom_layers = 0

	#z0 = t.getZ()
	points = rs.DivideCurve (slices[0], 100)
	t.set_position(points[0].X, points[0].Y, points[0].Z)
	z0 = points[0].Z

	layers = len(slices)
	# generate paths for all layers
	for i in range (0,layers):
		if (matrix):
			num_points = len(matrix)
		else:
			points = rs.DivideCurve (slices[i], 100)
			ll = line_length(points)
			num_points = int(ll/resolution)
		points = rs.DivideCurve (slices[i], num_points)

		# account for current z position
		# move slices up if necessary
		if (z0 != 0):
			for j in range (num_points):
				points[j].Z = points[j].Z+z0
		
		# spiral up if possible and relevant
		# don't spiral up on the last layer
		# don't spiral up on the bottom layers
		if (walls == 1 and spiral_up and i<layers-1 and i>bottom_layers):
			points_next = rs.DivideCurve (slices[i+1], num_points)
			z_inc = (points_next[0].Z+z0-points[0].Z)/num_points
			follow_closed_line (t,points,z_inc=z_inc, matrix = matrix)
		else:
			follow_closed_line(t,points,walls=walls, matrix = matrix)

		if (i < bottom_layers):
			spiral_bottom(t,slices[i],walls)   

# given a list of curves that slice a shape (slices)
# follow the curves with the turtle
def follow_slice_curves_woven(t,slices, bottom = False, spiral_up=False, matrix = False, num_oscillations=False, amplitude = False):
	resolution = t.get_resolution()
	initial_n_points = 25
	if (num_oscillations==False):
		num_oscillations = 21
	if (amplitude==False):
		amplitude=1
	if (bottom!=False):
		bottom_layers = bottom
	else:
		bottom_layers = 0
	
	# find starting point
	points = rs.DivideCurve (slices[0], initial_n_points)
	t.penup()
	t.set_position(points[0].X, points[0].Y, points[0].Z)
	t.pendown()
	z0 = points[0].Z
	layers = len(slices)

	# create shape
	# generate paths for all layers
	volume = 0
	extruder_distance = 0
	mass = 0
	#t.set_tube_color(159, 102, 119)
	#t.set_tube_color(180, 43, 97)
	for i in range (0,layers):
		if (matrix):
			num_points = len(matrix)
		else:
			points = rs.DivideCurve (slices[i], initial_n_points)
			ll = line_length(points)
			num_points = int(ll/resolution)

		points = rs.DivideCurve (slices[i], num_points)

		# change number of oscillations to fit layer
		# comment out for constant number of oscillations
		#num_oscillations = len(points)/8
		if (num_oscillations%2==0):
			num_oscillations = num_oscillations+1

		#print("num_oscillations: " +str(num_oscillations))

		if (i%2==0):
			theta_offset = 0
		else:
			theta_offset = 180

		#main wall layers
		if (spiral_up and i<layers-1 and i>bottom_layers):
			points_next = rs.DivideCurve (slices[i+1], num_points)
			z_inc = (points_next[0].Z+z0-points[0].Z)/num_points
			follow_closed_line_weave(t,points=points, num_oscillations=num_oscillations, amplitude = amplitude, z_inc = z_inc, theta_offset=theta_offset)
		# bottom layers
		else:
			follow_closed_line_weave(t,points=points, num_oscillations=num_oscillations, amplitude = amplitude, theta_offset=theta_offset)

		if (i < bottom_layers):
			spiral_bottom(t,slices[i],walls=1) 
		if (spiral_up==False or i<bottom_layers):
			t.lift(t.get_layer_height())
		if (i==bottom_layers or i==layers-2):
			t.lift(t.get_layer_height()/2)


#generates a turtle path from a curve or a list of rhinoscript points
def follow_closed_line(t,points=False,curve=False,z_inc=0,walls = 1,matrix=False):
	if (not(curve) and not(points)):
		print("You need to provide this function with either a curve or a list of points")
		return
	if (curve):
		#print("got a curve")
		resolution = t.get_resolution()
		points = rs.DivideCurve (curve, 100)
		ll = line_length(points)
		num_points = int(ll/resolution)+1
		points = rs.DivideCurve (curve, num_points)

	# on multi-walled prints
	# stop extruding near the seam to avoid a bump
	smooth_seam = 0 
	#start with pen up
	t.penup()

	# t2 keeps track of points for next wall
	t2 = e.ExtruderTurtle()
	t2.penup()

	# follow the curve
	# generate points for next wall if applicable (poinst2)
	points2 = []
	for i in range (0, len(points)):
		# matrix marks pen up spots in path
		if (matrix and matrix[i]==1):
			t.penup()
		else:
			t.pendown()

		# move to next point
		if (z_inc==0 or walls > 1):
			t.set_position(points[i].X,points[i].Y,points[i].Z)
		else:
			t.set_position(points[i].X,points[i].Y)
			t.lift(z_inc)

		# pen up between walls
		if (i>=smooth_seam):
			t.pendown()
		if ((i>=len(points)-smooth_seam) and walls>1):
			t.penup()

		# get points for next wall
		if (walls>1):
			t2.set_position(points[i].X,points[i].Y,points[i].Z)
			t2.left(90)
			t2.forward(t.get_extrude_width()*.75)
			x1 = t2.getX()
			y1 = t2.getY()
			z1 = t2.getZ()
			t2.backward(t.get_extrude_width()*.75)
			t2.right(90)
			points2.append(rs.CreatePoint(x1,y1,z1))

	#close the layer curve
	if (z_inc==0 or walls > 1):
		t.set_position(points[0].X,points[0].Y,points[0].Z)
	else:
		t.set_position(points[0].X,points[0].Y)

	# draw second wall
	while (walls>1):
		t.penup()
		for i in range (1, len(points2)):
			if (matrix and matrix[i]==1):
				t.penup()
			else:
				t.pendown()
			t.set_position(points2[i].X,points2[i].Y,points[i].Z)
			if (i>=smooth_seam):
				t.pendown()
			if (i>=len(points2)-smooth_seam):
				t.penup()
		walls = walls-1
		# you've drawn 2 walls, subtract these and draw the next wall
		'''
		walls = walls-2
		if (walls > 1):
			follow_closed_line(t, points2, walls = walls)
		'''

def spiral_bottom(t,curve,walls=1):
	extrude_rate = t.get_extrude_rate()\
	area = 0
	previous_area = 10
	i = 0
	count = 100
	previous_area = rs.CurveArea(curve)
	area = previous_area
	curve_center_previous =0

	while (area <=previous_area and i<count):
		curve_center = rs.CurveAreaCentroid(curve)
		if (curve_center):
			curve_center = curve_center[0]
			curve_center_previous = curve_center
		else:
			print("Couldn't get a center point, using previous.")
			curve_center = curve_center_previous

		o = rs.OffsetCurve(curve,curve_center,t.get_extrude_width())
		if (area):	
			previous_area = area
		else:
			print("Couldn't get an area, using previous.")
		
		# if there is a viable offset curve, compute the new area
		# otherwise, get out ot the loop
		if (o):
			try:
				area = rs.CurveArea(o)
			except:
				print("Challenging bottom 1. Re-computing.")
				try:
					o = rs.OffsetCurve(curve,curve_center,t.get_extrude_width()-.5)
				except:
					print("Challenging bottom 2. Re-computing.")
					o = rs.OffsetCurve(curve,curve_center,t.get_extrude_width()+.5)
				try:
					area = rs.CurveArea(o)
				except:
					print("Couldn't get an area.")
					break
		else:
			#print("Challenging bottom 3. Exiting.")
			break

		# if you have reached the inner-most ring of bottom, get out of loop
		if (area>previous_area):
			print("Next area larger. ")
			print("previous_area = " +str(previous_area) + ", area: " +str(area))
			#follow_closed_line(t,curve=o)
			print(i)
			break
		else:
			follow_closed_line(t,curve=o)
			curve = o
		i = i+1

	if (curve_center):
		return curve_center
	else:
		return curve_center_previous


#generates a turtle path from a curve or a list of rhinoscript points
def follow_closed_line_chase (t,points=False,curve=False,z_inc=0,angle=50,movement=1):
	if (not(curve) and not(points)):
		print("You need to provide this function with either a curve or a list of points")
		return
	if (curve):
		#print("got a curve")
		resolution = t.get_resolution()*4.5
		points = rs.DivideCurve (curve, 100)
		ll = line_length(points)
		num_points = int(ll/resolution)
		points = rs.DivideCurve (curve, num_points)

	if (points):
		num_points = len(points)
		t_extra_steps = 10

	if (num_points<15):
		movment = movement/3.5
		t_extra_steps = 12

	# t2 follows the basic curve, t will chase t2
	t2 = e.ExtruderTurtle()
	
	if (z_inc==0 or walls > 1):
		t2.set_position(points[0].X,points[0].Y,points[0].Z)
	else:
		t2.set_position(points[0].X,points[0].Y)

	previous_distance_sq = 10000000

	for i in range (0, len(points)):
		# move to next point
		if (z_inc==0 or walls > 1):
			t2.set_position(points[i].X,points[i].Y,points[i].Z)
			#t.set_position(z=points[i].Z)
		else:
			t2.set_position(points[i].X,points[i].Y)
			t2.lift(z_inc)

		for s in range (0,t_extra_steps):
			distance_sq = distance_squaredXY(t2.get_position(), t.get_position())
			if (distance_sq > previous_distance_sq):
				t.right(angle)
				t.forward (movement)
			else:
				t.right(random.randint(-(angle-15),angle-15))
				t.forward(movement)
			if (z_inc>0):
				t.lift(z_inc)
			previous_distance_sq = distance_sq


def follow_closed_line_weave(t,points=False, curve=False, num_oscillations=25.0, amplitude = 2, theta_offset=0, z_inc=0, extra_support=False):
	if (not(curve) and not(points)):
		print("You need to provide this function with either a curve or a list of points")
		return
	if (curve):
		resolution = t.get_resolution()/2
		points = rs.DivideCurve (curve, 100)
		ll = line_length(points)
		num_points = int(ll/resolution)+1
		points = rs.DivideCurve (curve, num_points)

	num_points = len(points)
	t2 = e.ExtruderTurtle()
	if (z_inc==0):
		t2.set_position(points[0].X,points[0].Y,points[0].Z)
	else:
		t2.set_position(points[0].X,points[0].Y)

	dtheta = 360.0/num_points
	theta = 0.0
	x0 = 0.0
	y0 = 0.0

	if (theta_offset):
		theta0 = 180
	else:
		theta_offset = 0
		theta0 = 0

	if (extra_support):
		#non-oscillating line for support
		delta = t.get_extrude_width()*1.25
		for i in range (0, num_points):
			if (z_inc==0):
				t2.set_position(points[i].X,points[i].Y,points[i].Z)
			else:
				t2.set_position(points[i].X,points[i].Y)
			#get the new point with spare turtle
			t2.right(90)
			t2.forward(-delta)
			x = t2.getX()
			y = t2.getY()
			if (i==0):
				x0 = x
				y0 = y
			t2.forward(delta)
			t2.left(90)
			#set main turtle's position
			if (i!=0):
				t.set_position(x,y)
			if (z_inc!=0):
				t.lift(z_inc)
			theta = theta + dtheta

	#weave
	for i in range (0, num_points):
		if (z_inc==0):
			t2.set_position(points[i].X,points[i].Y,points[i].Z)
		else:
			t2.set_position(points[i].X,points[i].Y)
		delta = amplitude*math.cos(num_oscillations*math.radians(theta+theta0))
		#get the oscillating point with spare turtle
		t2.right(90)
		t2.forward(delta)
		x = t2.getX()
		y = t2.getY()
		if (i==0):
			x0 = x
			y0 = y
		t2.backward(delta)
		t2.left(90)
		#set main turtle's position
		if (i!=0):
			t.set_position(x,y)
			if (t.get_pen()==False):
				t.pen_down()
		if (z_inc!=0):
			t.lift(z_inc)
		theta = theta + dtheta

	return t2

def distance_squaredXY (p0, p1):
	ds = (p1.X-p0.X)*(p1.X-p0.X)+(p1.Y-p0.Y)*(p1.Y-p0.Y)
	return ds