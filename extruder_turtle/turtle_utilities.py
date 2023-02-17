import copy
import Rhino.Geometry as geom
import rhinoscriptsyntax as rs
import ExtruderTurtle as e
import operator as op
import math
import random

def translate(g,x,y,z):
	translation = geom.Transform.Translation(x,y,z)
	g.Transform(translation)
	
def rotate(g,angle):
	rotation = geom.Transform.Rotation(math.radians(angle),rs.CreatePoint(0,0,0))
	g.Transform(rotation)
	
def scale(g,scale_factor):
	point = rs.CurveAreaCentroid(g)[0]
	scale= geom.Transform.Scale(point,scale_factor)
	g.Transform(scale)

# versions of transformations that do not alter input shape
def translate_copy(g,x,y,z):
	shape = copy.deepcopy(g)
	translation = geom.Transform.Translation(x,y,z)
	shape.Transform(translation)
	return shape
	
def rotate_copy(g,angle):
	shape = copy.deepcopy(g)
	rotation = geom.Transform.Rotation(math.radians(angle),rs.CreatePoint(0,0,0))
	shape.Transform(rotation)
	return shape
	
def scale_copy(g,scale_factor):
	shape = copy.deepcopy(g)
	scale= geom.Transform.Scale(rs.CreatePoint(0,0,0),scale_factor)
	shape.Transform(scale)
	return shape

# generates a surface of size*2 squared
# around the origin at height z
def surface_for_slice(z,size):
	points = []
	points.append(rs.CreatePoint(-size,-size,z))
	points.append(rs.CreatePoint(-size,size,z))
	points.append(rs.CreatePoint(size,size,z))
	points.append(rs.CreatePoint(size,-size,z))
	plane = rs.AddSrfPt(points)
	return plane

def convex_hull(points):
	start = a
	hull_points = []
	lines = []
	while a:
		o = a
		a = points[0]
		for b in points:
			if (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0]) < 0: a = b
		lines.append(rs.AddLine(o,a))
		hull_points.append(o)
		if (a == start): 
			break
	return lines, hull_points

def mix_factor_metal(t):
	t.do("M163 S0 P0.96; Set Mix Factor small auger extruder \nM163 S1 P0.04; Set Mix Factor large plunger extruder\nM164 S0 ; Finalize mix")
	

# slices a solid (shape)
def slice_solid (shape, layer_height):
	bb = rs.BoundingBox(shape)
	height = rs.Distance(bb[0], bb[4])
	layers = int(height/layer_height)
	size = rs.Distance(bb[0], bb[2])*2
	slices = []
	z = 0
	for i in range (0,layers):
		slice = one_slice(shape,z,size)
		if (slice):
			slices.append(slice)
		z = z+layer_height
	return slices

# creates one slice of a shape at height z
def one_slice(shape,z,size,plane = False):
	if (plane==False):
		plane = surface_for_slice(z,size)
	intersection = rs.BooleanIntersection(plane, shape, delete_input=False)
	if (intersection):
		surfaces = rs.ExplodePolysurfaces(intersection, delete_input=False)
	else:
		return
	if (len(surfaces)>1):
		curves = rs.DuplicateEdgeCurves(surfaces[2])
		if (len(curves)>1):
			curves = rs.JoinCurves(curves)
		return curves[0]

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
	follow_slice_curves_with_turtle(t,slices,walls=walls,spiral_up=spiral_up)

	return slices

# generates a turtle path and g-code that slices a solid (shape)
# optional number of walls, walls are offset into interior of shape
def slice_with_turtle_2 (t, shape, walls = 1, layer_height=False, spiral_up=False):
	if (layer_height==False or layer_height == 0):
		layer_height = t.get_layer_height()

	bb = rs.BoundingBox(shape)
	height = rs.Distance(bb[0], bb[4])
	layers = int(round(height/layer_height)) # number of slices
	size = rs.Distance(bb[0], bb[6])*2 # size of slicing plane
	slices = []
	z = bb[0].Z

	slice = one_slice(shape,z,size)
	if (slice==False):
		print("Slicing error. Move your shape closer to the origin for slicing.")
		return

	#generate slice curves
	for i in range (0,layers+1):
		slice = one_slice(shape,z,size)
		if (slice):
			slices.append(slice)
		z = z+layer_height

	#slice the top layer
	z = height
	slice = one_slice(shape,z,size)
	if (slice):
		slices.append(slice)

	if (bottom and len(slices)>0):
		spiral_bottom(t,slices[0])
		t.lift(layer_height)

	layers = len(slices)
	#follow slice curves with turtle
	follow_slice_curves_with_turtle(t,slices,walls=walls,spiral_up=spiral_up)

	print("number of slices of layer_height tall is: " +str(len(slices)))
	return slices

def max_distance_between_slices(points0,points1):
	maxd = 0
	for i in range (0, len(points0)):
		distance = rs.Distance(points0[i],points1[i])
		if (distance > maxd):
			maxd = distance
	return maxd

# slices a shape with an equal distance between layers
# calculates distance based on maximum total distance 
# (vertical and horizontal) between layers
def slice_with_turtle_even_layers (t, shape, walls = 1, layer_height=False, bottom=False, spiral_up=False):
	if (layer_height==False or layer_height == 0):
		layer_height = t.get_layer_height()

	num_comparison_points = 2
	bb = rs.BoundingBox(shape)
	height = rs.Distance(bb[0], bb[4])
	bottom_z = bb[0].Z
	top_z = bb[4].Z
	size = rs.Distance(bb[0], bb[6])*2 # size of slicing plane = diagonal*2
	slices = []
	z = bottom_z
	print("z: " +str(z))
	p0 = bb[0]
	p1 = rs.CreatePoint(bb[0].X,bb[0].Y,z+.1)
	slice = rs.AddSrfContourCrvs(shape,(p0,p1),layer_height)

	#slice = one_slice(shape,z,size)
	if (slice):
		points = rs.DivideCurve (slice[len(slice)-1], num_comparison_points)
	else: 
		print("Slicing error. Move your shape closer to the origin for slicing.")
		return

	#generate slice curves
	count_main = 0
	while (z < top_z and count_main <100):
		print("z: " +str(z))
		# measure max distance between point this slice & previous slice
		# calculate z based on that distance
		new_layer_height = 0
		previous_points = copy.deepcopy(points)
		p0 = rs.CreatePoint(bb[0].X,bb[0].Y,z)
		p1 = rs.CreatePoint(bb[0].X,bb[0].Y,z+layer_height)
		slice = rs.AddSrfContourCrvs(shape,(p0,p1),layer_height)
		if (slice):
			points = rs.DivideCurve (slice[len(slice)-1], num_comparison_points)

		maxd = max_distance_between_slices(previous_points,points)
		desired_distance = layer_height*1.0
		print("maxd: " +str(maxd))
		if (maxd>desired_distance): # generate a new slice
			print("generating new slice at layer: " +str(count_main))
			theta = math.asin(layer_height/maxd)
			new_layer_height = math.sin(theta)*desired_distance
			print("new layer height: " +str(new_layer_height))
			p0 = rs.CreatePoint(bb[0].X,bb[0].Y,z)
			p1 = rs.CreatePoint(bb[0].X,bb[0].Y,z+new_layer_height)
			slice = rs.AddSrfContourCrvs(shape,(p0,p1),new_layer_height*2)
			points = rs.DivideCurve (slice[len(slice)-1], num_comparison_points)

		# if you're close to the top of the shape
		# make sure you account for thinner layers
		if (z+layer_height >= top_z-layer_height):
			print("top slice")
			if (new_layer_height):
				if (z+new_layer_height < top_z):
					z = z+new_layer_height
				else:
					print("very top")
					slices = slices + slice
					z0 = bb[4].Z -.05
					z = bb[4].Z+.05
					p0 = rs.CreatePoint(bb[0].X,bb[0].Y,z0)
					p1 = rs.CreatePoint(bb[0].X,bb[0].Y,z)
					slice = rs.AddSrfContourCrvs(shape,(p0,p1),new_layer_height)
					slices.append(slice[len(slice)-1])
					break
			else:
				z = z+layer_height/2

		else:
			if (new_layer_height>0):
				print("adding new layer height")
				z = z+new_layer_height
			else:
				print("adding normal layer height")
				z = z+layer_height

		#print("new distance: " +str(maxd))
		if (slice):
			print("number new slices: " + str(len(slice)))
			slices.append(slice[len(slice)-1])

		count_main = count_main + 1
	'''
	#slice the top layer
	z = bb[7].Z-.01
	p0 = rs.CreatePoint(bb[0].X,bb[0].Y,z)
	p1 = rs.CreatePoint(bb[0].X,bb[0].Y,z+layer_height)
	slice = rs.AddSrfContourCrvs(shape,(p0,p1),layer_height)
	#slice = one_slice(shape,z,size)
	if (slice):
		slices = slices + slice
	else:
		print("final slice failed")
	'''
	return slices

	follow_slice_curves_with_turtle(t,slices,walls=walls,spiral_up=spiral_up)

	print("number of equal distanced slices is: " +str(len(slices)))
	return slices

# given a list of curves that slice a shape (slices)
# follow the curves with the turtle
def follow_slice_curves_with_turtle(t,slices,walls=1, bottom = False, spiral_up=False, matrix = False):
	resolution = t.get_resolution()

	if (bottom!=False):
		bottom_layers = bottom
	else:
		bottom_layers = 3

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

# given a list of curves that slice a shape (slices)
# follow the curves with the turtle
def follow_slice_curves_woven_data(t,slices, bottom = False, spiral_up=False, matrix = False, num_oscillations=False, amplitude = False):
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


	# color variables
	layers_per_week = len(slices)/50.0
	print("layers per week: " +str(layers_per_week))

	months = ['october', 'september','august','july','june','may','april','march','february','january','december','november' ]
	weeks_per_month = [31/7.0, 30/7.0, 31/7.0, 31/7.0, 30/7.0, 31/7.0, 30/7.0, 31/7.0, 28/7.0, 31/7.0, 31/7.0, 30/7.0]

	december = 0
	for i in range(0,10):
		december = december+weeks_per_month[i]*layers_per_week
	december = int(december)
	
	january = 0
	for i in range(0,9):
		january = january+weeks_per_month[i]*layers_per_week
	january = int(january)

	february = 0
	for i in range(0,8):
		february = february+weeks_per_month[i]*layers_per_week
	february = int(february)

	june = 0
	for i in range(0,4):
		june = june+weeks_per_month[i]*layers_per_week
	june = int(june)
	
	july = 0
	for i in range(0,3):
		july = july+weeks_per_month[i]*layers_per_week
	july = int(july)
	
	august = 0
	for i in range(0,2):
		august = august+weeks_per_month[i]*layers_per_week
	august = int(august)
	
	# find starting point
	points = rs.DivideCurve (slices[0], initial_n_points)
	t.penup()
	t.set_position(points[0].X, points[0].Y, points[0].Z)
	t.pendown()
	z0 = points[0].Z
	layers = len(slices)

	# create shape
	# generate paths for all layers
	# white color
	r0 = 247
	g0 = 239
	b0 = 215
	blue = 60,170,210
	orange = 255,150,57
	purple = 70,60,210
	red = 240,130,120
	volume = 0
	extruder_distance = 0
	mass = 0
	t.set_tube_color(r0,g0,b0)
	for i in range (0,layers):
		if (i>=august and i<=june): 
			r = 255
			g = 150
			b = 57
			if (i==august):
				t.set_tube_color(red[0],red[1], red[2])
			if (i==int(june)):
				t.set_tube_color(r0,g0,b0)
		if (i>=february and i<=december):   

			r = 60
			g = 170
			b = 210
			if (i==february):
				t.set_tube_color(purple[0],purple[1], purple[2])
			if (i==december):
				print(i)
				t.set_tube_color(r0,g0,b0)

		if (matrix):
			num_points = len(matrix)
		else:
			points = rs.DivideCurve (slices[i], initial_n_points)
			ll = line_length(points)
			num_points = int(ll/resolution)

		points = rs.DivideCurve (slices[i], num_points)
		#print("number_points: " +str(len(points)))

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
			print("Challenging bottom 3. Exiting.")
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


#assumes curve is flat, doesn't work for non-planar curves
def zig_zag_bottom(t,curve):
	resolution = t.get_resolution()
	points = curve_to_points(curve,resolution)
	#find bounding box points, will define slicing line boundaries
	minPx = min(points, key=op.itemgetter(0))
	maxPx = max(points, key=op.itemgetter(0))
	minPy = min(points, key=op.itemgetter(1))
	maxPy = max(points, key=op.itemgetter(1))
	index = go_to_point_on_curve(t,curve,minPx)
	# print("index: " +str(index))
	x = minPx.X
	z = minPx.Z
	x = x + t.get_extrude_width()
	intersections_list = []
	while (x < maxPx.X):
		index = go_to_point_on_curve(t,curve,t.get_position())
		# generate slicing line
		# slice in x
		# x increment = one spacing width
		# line = current x from miny to maxy
		line = rs.AddLine(rs.CreatePoint(x,minPy.Y,z),rs.CreatePoint(x,maxPy.Y,z))
		# check for intersections between line and curve
		intersections = rs.CurveCurveIntersection(curve,line)
		intersections_list.append(intersections)
		# find intersection at curve turtle is on
		# travel along curve to the intersection
		# jump to intersection across curve, stay inside shape
		for i in range (len(intersections)):
			d = distance_on_curve(t,curve,intersections[i][1],index)
			if (d < t.get_extrude_width()*2):
				# print("found the point at intersections: " +str(i))
				# print("distance is: " +str(d))
				t.set_position_point(intersections[i][1])
				break

		x = x + t.get_extrude_width()
		# print("x slice: " +str(x))
	return intersections_list

# generates points from a curve
# number of points determined by resolution
def curve_to_points(curve,resolution):
	points = rs.DivideCurve (curve, 100)
	ll = line_length(points)
	num_points = int(ll/resolution)
	points = rs.DivideCurve (curve, num_points)
	return points

# go to point on curve, start at beginning of curve
def go_to_point_on_curve(t,curve,point):
	resolution = t.get_resolution()
	t.penup()
	points = curve_to_points(curve,resolution)
	for i in range (len(points)):
		d = rs.Distance(points[i],point)
		t.set_position_point(points[i])
		if (d <resolution*2):
			t.pendown()
			return i
	print("Point was not on curve. At end of curve.")
	return 0

# distance between t and point on curve
# index is index of t's position on curve/points array
# assumes t is on the curve
def distance_on_curve(t,curve,point,index):
	resolution = t.get_resolution()
	points = curve_to_points(curve,resolution)
	
	distance = 0
	# goes forward along curve
	for i in range (index,len(points)-1):
		d = rs.Distance(points[i],point)
		distance = distance + abs(rs.Distance(points[i],points[i+1]))
		if (abs(d) <= resolution):
			#print("Found the point on curve in distance function at:")
			#print(distance)
			return distance

	distance = 0
	# goes backward along curve
	i = index
	while (i>0):
		d=rs.Distance(points[i],point)
		distance = distance + abs(rs.Distance(points[i],points[i+1]))
		if (abs(d) <= resolution):
			# print("Found the point on curve in distance function at:")
			# print(distance)
			return distance
		i = i-1

	print("Point was not on curve. At end of curve.")
	return resolution*1000

def line_length(points):
	length = 0
	for i in range (1, len(points)):
		length = length + rs.Distance(points[i-1],points[i])
	length = length + rs.Distance(points[len(points)-1],points[0])
	return length


#bump_width in number of steps NOT mm
def bump_square(t,bump_length,c_bump,dtheta,z_inc=0,bump_width=0):
	t.left(90)
	t.forward(bump_length)
	t.right(90)
	if (bump_width!=0):
		for j in range(int(bump_width)):
			t.forward_lift(c_bump,z_inc)
			t.right(dtheta)
	t.right(90)
	t.forward(bump_length)
	t.left(90)

def bump_triangle(t,bump_length, bump_width, c_inc, d_theta,z_inc=0):
	# convert width into steps
	number_steps = int(bump_width/c_inc)
	
	x0 = t.getX()
	y0 = t.getY()
	z0 = t.getZ()
	yaw0 = t.get_yaw()
	t2 = e.ExtruderTurtle()
	t2.set_position(x0,y0,z0)
	t2.set_heading(yaw0)
	if (bump_width==0):
		bump_square(t,bump_length,0,d_theta)
		return

	for i in range (0,number_steps/2):
		t2.forward_lift(c_inc,z_inc)
		t2.right(d_theta)
	t2.left(90)
	t2.forward(bump_length)
	x1 = t2.getX()
	y1 = t2.getY()
	z1 = t2.getZ()
	t2.backward(bump_length)
	t2.right(90)
	for i in range (0,number_steps/2):
		t2.forward_lift(c_inc,z_inc)
		t2.right(d_theta)

	# NOTE should do for all angles, right now yaw only
	yaw = t2.get_yaw()

	x2 = t2.getX()
	y2 = t2.getY()
	z2 = t2.getZ()

	t.set_position(x1,y1,z1)
	t.set_position(x2,y2,z2)
	# NOTE should do for all angles, right now yaw only
	t.set_heading(yaw)


def follow_closed_line_simple_bumps(t,points,curve=False, num_bumps=0,bump_length=0, bump_start = 0, z_inc=0):
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

	l = len(points)
	if (num_bumps !=0):
		bump_distance = int(l/num_bumps)
	else:
		bump_distance = 0

	for i in range (len(points)):
		t.set_position(points[i].X,points[i].Y)
		t.lift(z_inc)
		if (num_bumps!=0 and (i+bump_start)%bump_distance==0 and i>0):
			t.right(90)
			t.forward(bump_length)
			t.backward(bump_length)
			t.left(90)

	t.set_position(points[0].X,points[0].Y)
	t.lift(z_inc)

def distance_squaredXY (p0, p1):
	ds = (p1.X-p0.X)*(p1.X-p0.X)+(p1.Y-p0.Y)*(p1.Y-p0.Y)
	return ds

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

	#print("number of points in slice: " +str(num_points))

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

def pattern_cylinder_1D (t,diameter, height, array1D=False, walls= 1, offset = 0):
	layers = int(height/t.get_layer_height())
	circumference = diameter*math.pi
	steps = 360
	c_inc = circumference/steps
	dtheta = steps/360

	if (array1D):
		steps_per_array_entry = steps/len(array1D)
	else:
		steps_per_array_entry = circumference/3
	if (steps_per_array_entry==0):
		steps_per_array_entry = 1

	if (offset>0):
		offset_steps = int(offset/c_inc)
		t.penup()
		for o in range (0,offset_steps):
			t.forward(c_inc)
			t.right(dtheta)
		t.pendown()

	for l in range (layers):
		ai = 0
		for i in range (steps):
			if (i%steps_per_array_entry==0):
				if (array1D and array1D[ai] == 1):
					t.penup()
				else:
					t.pendown()
				ai = ai+1
			t.forward(c_inc)
			t.right(dtheta)
		# use recursion to generate another wall inside this one
		if (walls>1):
			t.penup()
			t.right(90)
			t.forward(t.get_extrude_width())
			t.left(90)
			t.pendown()
			wall_height = t.get_layer_height()
			pattern_cylinder_1D(t,diameter-t.get_extrude_width()*2,wall_height,array1D,walls-1)
			t.penup()
			t.left(90)
			t.forward(t.get_extrude_width())
			t.right(90)
			t.pendown()
		
		# lift only once per layer
		# not for every wall in layer!
		if (walls ==1):
			t.penup()
			t.lift(t.get_layer_height())
			t.pendown()


def pattern_cylinder(t, b_diameter, height, t_diameter=False, array=False, pattern_amplitude = False, pattern_spacing = 0, bottom_layers=3, oscillations = False, spiral_up = True):
	base_amplitude = 1.25
	if (pattern_amplitude == False):
		pattern_amplitude = base_amplitude-1.4
	if (t_diameter == False):
		t_diameter = b_diameter
	layers = int(height/t.get_layer_height())
	diameter = b_diameter
	diameter_inc = float(t_diameter - b_diameter)/layers

	circumference = diameter*math.pi
	if (array):
		pattern_width = len(array)
		pattern_height = len(array[0])
	else:
		if (oscillations):
			pattern_width = oscillations+1
		else:
			pattern_width = circumference/4
	pattern_steps = pattern_width
	if (oscillations):
		nOscillations = int(pattern_steps)-1
		distance_per_oscillation = circumference/nOscillations
		steps_per_oscillation = 2
		c_inc = distance_per_oscillation/steps_per_oscillation
		print("distance_per_oscillation: " +str(distance_per_oscillation))
	# else:
	#   nOscillations = 0
	#   c_inc = circumference/100
	#   steps_per_oscillation = 1

	print("number of oscillations: " +str(nOscillations))

	 
	steps = int(circumference/c_inc)

	if (spiral_up): 
		z_inc = t.get_layer_height()/steps
	else:
		z_inc = 0

	dtheta = 360.0/steps
	# to get 180 degrees out of phase add: theta_one_oscillation/2
	b = diameter/2
	x0 = t.getX()
	y0 = t.getY()
	z0 = t.getZ()
	z = z0

	theta_offset = 0
	axy = base_amplitude
	theta0 = 0

	#pattern access variables
	xp = 0
	yp = 0

	for l in range (layers):
		extrude_rate = t.get_extrude_rate()
		# create bottom layers if relevant
		if (l < bottom_layers):
			t.set_position(0,0)
			if (nOscillations>0):
				k = int(diameter/t.get_extrude_width()-2) # number of circles in diameter
			else:
				k = int(diameter/t.get_extrude_width()-1) # number of circles in diameter
			t.set_position(0,0,z)
			t.pendown() 
			polygon_layer(t,k*t.get_extrude_width(),return_to_center=False,offset=(l%2))
		# if (l== bottom_layers):
		#   print("BOTTOM PRINT INFO")
		#   t.volume_of_path()

		# reset x pattern variable for each layer
		xp = 0
		# generate theta offset for weaving oscillations
		# every other layer is offset
		if (l%2==0):
			theta_offset = 180
			x0 = t.getX()
			# this is a problematic if statement. Will cause problems later!
			if (x0==0):
				theta0 = 0
				# could also be theta0 = 90 or theta0 = 270
			elif (x0 < 0):
				theta0 = math.degrees(math.atan(y0/x0))+180
			else:
				theta0 = math.degrees(math.atan(y0/x0))
			steps_offset = 1
		else:
			theta_offset = 0
			theta0 = 0
			steps_offset = 2

		# generate steps around circumference
		for s in range(1,steps+steps_offset):
			# put the pen down at the second step of each layer
			# to allow for penup transitions for bottom layers
			if (s>=2):
				t.pendown()
			# generate pattern for every other layer
			# top 4 layers have no pattern
			# bottom layers have no pattern
			if (l<layers-4 and l>=bottom_layers and l%2==0):
				if (s%steps_per_oscillation==0):
					if (array and xp<len(array) and array[xp][yp]==1):
						axy = pattern_amplitude
						if (pattern_amplitude==-1):
							t.penup()
						elif(s>1):
							t.pendown()
					else:
						if (s>1):
							t.pendown()
						axy = base_amplitude
					xp = xp+1
			else:
				axy = base_amplitude

			# comment out else statement to skip alternate layers
			# keep else statement in to show pattern on all layers
			'''
			else:
				if (s%steps_per_oscillation==0):
					if (array and xp<len(array) and array[xp][yp]==1):
						axy = pattern_amplitude
					else:
						axy = base_amplitude
					xp = xp+1
			'''

			# calculate and move to next position
			theta = theta0+dtheta*s
			if (theta_offset==0):
				r= b+axy*math.cos(nOscillations*math.radians(theta))
			else:
				r= b+axy*math.cos(nOscillations*math.radians(theta+theta_offset))
			x = r*math.cos(math.radians(theta))
			y = r*math.sin(math.radians(theta))
			# bottom layers and last layer are flat, no spiraling up in z
			if (z_inc != 0 and l < layers-1 and l>bottom_layers):
				z = z + z_inc
			if (z_inc != 0 and l >= layers-1):
				z = z + z_inc/3

			t.set_position(x,y,z)

		# increment diameter if relevant
		diameter = diameter+diameter_inc
		b = diameter/2

		# update pattern yp (vertical) variable
		if (l%2==0 and l<layers-4 and l>bottom_layers):
			yp = yp+1

		# if you are not spiraling up, step up to the next layer
		if (z_inc == 0 or l < bottom_layers):
			#print("printing bottom layer z up")
			t.penup()
			z = z + t.get_layer_height()
			if (l < bottom_layers-1):   #add a little extra height for all but last of bottom layers
				z = z + t.get_layer_height()/4
			if (l >= layers-1): #subtract a little height for top layer
				z = z - t.get_layer_height()/4
			t.write_gcode_comment("z up for bottom and non spiraling walls")
			t.set_position(z=z)
			t.pendown()

		# penup and lift to transition to next layer
		if (l<bottom_layers):
			t.penup()
			t.lift(5)
	

# adjust the number of steps in a circle 
# to avoid generating too many points for small shapes
# minimum step size = resolution
def adjust_circle_steps(diameter, steps, resolution, layer_height):
	#resolution = resolution # use smaller resolution here
	circumference = diameter * math.pi
	c_inc = circumference/steps
	if (c_inc < resolution):
		c_inc = resolution
		steps = int(circumference/c_inc)

	return steps

def secondWallAddPointXYR(t,t2,points):
	t2.penup()
	t2.set_position_point(t.get_position())
	t2.right(90)
	t2.forward(t.get_extrude_width()*.75)
	x1 = t2.getX()
	y1 = t2.getY()
	z1 = t2.getZ()
	t2.backward(t.get_extrude_width()*.75)
	t2.left(90)
	return rs.CreatePoint(x1,y1,z1)

#creates a circle or polygon with the edge begining at the turtle's location
def non_centered_poly(t, diameter, steps=360, walls = 1):
	position = t.get_position()
	initial_angle = t.get_yaw()
	steps = adjust_circle_steps(diameter, steps,t.get_resolution(),t.get_layer_height())
	if (t.write_gcode):
		t.write_gcode_comment("starting polygon")
	circumference = diameter * math.pi
	c_inc = circumference/steps
	dtheta = 360.0/steps

	if (walls>1):
		t2 = e.ExtruderTurtle()
		points = []

	t.right(dtheta/2)
	for i in range (steps):
		t.forward(c_inc)
		t.right(dtheta)
		if (walls>1):
			points.append(secondWallAddPointXYR(t,t2,points))

	t.left(dtheta/2)

	if (walls>1):
		t.penup()
		for i in range (0,len(points)):
			if (i>2):
				t.pendown()
			t.set_position(points[i].X,points[i].Y,points[i].Z)
	t.set_position_point(position)
	t.set_heading(initial_angle)

def circular_bottom(t,diameter,layers):
	t.extrude(t.get_nozzle_size()*3)
	extrude_rate = t.get_extrude_rate()
	#t.set_extrude_rate(extrude_rate/2)
	for i in range (layers-1):
		t.right(360/layers)
		polygon_layer(t,diameter,return_to_center=True,offset=(i%2))
		t.lift(t.get_layer_height()*1.25)

	t.right(360/layers)
	polygon_layer(t,diameter,return_to_center=False)    
	t.set_extrude_rate(extrude_rate)

def circular_layer(t,diameter,spiral_up = True):
	t.write_gcode_comment("starting circular layer")
	# avoid generating too many points for small shapes
	steps = adjust_circle_steps(diameter,360,t.get_resolution(),t.get_layer_height())
	circumference = diameter * math.pi
	c_inc = circumference/steps

	if (spiral_up): 
		z_inc = t.get_layer_height()/steps
	else:
		z_inc = 0
	
	dtheta = 360.0/steps
	
	for s in range(0,steps):
		if (spiral_up):
			t.forward_lift(c_inc,z_inc)
		else:
			t.forward(c_inc)
		t.left(dtheta)


# creates a solid flat layer of polygons that spiral out from a center point
def polygon_layer (t, diameter, steps=360, return_to_center = False, offset=0.0):
	t.set_heading(yaw=0)
	initial_position = t.get_position()
	initial_angle = t.get_yaw()
	if (t.write_gcode):
		t.write_gcode_comment("starting solid layer")
	#set initial diameter d
	if (offset>0):
		d = t.get_extrude_width()*1
	else:
		d = t.get_extrude_width()*2

	t.extrude(2)
	t.forward(d/2)
	t.right(90)
	while (d < diameter-t.get_extrude_width()*2):
		non_centered_poly(t,d)
		t.left(90)
		t.forward(t.get_extrude_width())
		t.right(90)
		d = d+t.get_extrude_width()*2

	non_centered_poly(t,d)
	t.left(90)
	t.forward((diameter-d)/2)
	t.right(90)

	if (d<diameter-t.get_extrude_width()/2):
		non_centered_poly(t,diameter)

	if (return_to_center):
		t.penup()
		t.lift(t.get_layer_height()*2)
		t.set_position_point(initial_position)
		t.set_heading(yaw=initial_angle)
		t.pendown()


#creates a polygon centered around the turtle's current location
def centered_poly(t,diameter, steps=360):
	# avoid generating too many points for small shapes
	#steps = adjust_circle_steps(diameter, steps,t.get_resolution(),t.get_layer_height())
	r = diameter/2
	circumference = diameter * math.pi
	c_inc = circumference/steps

	outer_angle = 360/steps
	inner_angle = 180-360/steps

	t.penup()
	t.forward(r)
	t.left(outer_angle + inner_angle/2)
	t.pendown()

	for i in range (steps):
		t.forward(c_inc)
		t.left(outer_angle)

	t.penup()
	t.left(outer_angle + inner_angle/2)
	t.forward(r)
	t.pendown()

# generates a polygon with edges that are side_length long
def polygon(side_length, steps, t):
	r = side_length/(2*math.sin(math.radians(180/steps)))
	outer_angle = 360/steps
	inner_angle = 180-360/steps
	t.penup()
	t.forward(r)
	t.left(outer_angle + inner_angle/2)
	t.pendown()
	for j in range(steps):
		t.forward(side_length)
		t.left(outer_angle)
	t.penup()
	t.right(outer_angle + inner_angle/2)
	t.backward(r)
	t.pendown()

def filled_oscillating_circle_xy(diameter, a, nOscillations, t, steps=360):
	steps = adjust_circle_steps(diameter, steps,t.get_resolution(),t.get_layer_height())
	d = t.get_extrude_width()*2
	number_cycles = diameter/(t.get_extrude_width()*2)
	da = float(a)/number_cycles
	a2=da
	while(d<diameter):
		oscillating_circle_xy(d, a2, nOscillations, t, steps)
		t.left(90)
		t.forward(t.get_extrude_width())
		t.right(90)
		d = d+t.get_extrude_width()*2 
		a2 = a2+da
	oscillating_circle_xy(diameter, a2, nOscillations, t, steps)

def oscillating_circle(t, diameter, nOscillationsxy, axy, nOscillationsz=0, az=0, spiral_out=0, theta_offset=0, spiral_up = True, z_inc=0):
	# avoid generating too many points for small shapes
	steps = adjust_circle_steps(diameter,360,t.get_resolution(),t.get_layer_height())
	circumference = diameter * math.pi
	c_inc = circumference/steps
	if (spiral_up): 
		z_inc = t.get_layer_height()/steps
	else:
		z_inc = 0
	#print("z_inc x steps: " +str(round(z_inc,5)*steps))

	dtheta = 360.0/steps
	# to get 180 degrees out of phase add: theta_one_oscillation/2
	b = diameter/2
	x0 = t.getX()
	y0 = t.getY()
	z0 = t.getZ()
	z = z0
	# this is a problematic if statement. Will cause problems later!
	if (x0==0):
		theta0 = 0
		# could also be theta0 = 90 or theta0 = 270
	elif (x0 < 0):
		theta0 = math.degrees(math.atan(y0/x0))+180
	else:
		theta0 = math.degrees(math.atan(y0/x0))

	for s in range(0,steps+1):
		theta = theta0+dtheta*s
		if (theta_offset==0):
			r= b+axy*math.cos(nOscillationsxy*math.radians(theta))
		else:
			r= b+axy*math.cos(nOscillationsxy*math.radians(theta+theta_offset))
		x = r*math.cos(math.radians(theta))
		y = r*math.sin(math.radians(theta))
		z = z + az*math.sin(math.radians(nOscillationsz*theta))
		if (z_inc != 0):
			z = z + z_inc
		t.set_position(x,y,z)

def square_oscillating_circle(t,inner_diameter, outer_diameter, nOscillations):
	# avoid generating too many points for small shapes
	steps = adjust_circle_steps(diameter,360,t.get_resolution(),t.get_layer_height())
	inner_radius = inner_diameter/2
	outer_radius = outer_diameter/2
	r_dif = outer_radius-inner_radius
	inner_circumference = math.pi*inner_diameter
	outer_circumference = math.pi*outer_diameter
	inner_c_step = inner_circumference/steps
	outer_c_step = outer_circumference/steps
	theta_step = 360.0/steps
	for i in range(0,nOscillations):
		for j in range (0,int(steps/(nOscillations*2))):
			t.forward(inner_c_step)
			t.left(theta_step)
		t.right(90)
		t.forward(r_dif)
		t.left(90)
		for j in range (0,int(steps/(nOscillations*2))):
			t.forward(outer_c_step)
			t.left(theta_step)
		t.left(90)
		t.forward(r_dif)
		t.right(90)

def polar_rose(t, a, n, x0=False, y0=False):
	if (x0==False):
		x0 = t.getX()
		print("no x0")
	if (y0==False):
		y0 = t.getY()
	steps = 50

	dtheta = 360.0/steps
	total_steps = int(steps*1.5/(n)+1)

	for s in range(0,total_steps):
		if (s==1):
			t.pendown()
		theta = dtheta*s
		r= a*math.cos(n*math.radians(theta))
		x = r*math.cos(math.radians(theta))
		y = r*math.sin(math.radians(theta))

		t.set_position(x0+x,y0+y)

