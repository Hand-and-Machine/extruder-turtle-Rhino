import copy
import Rhino.Geometry as geom
import rhinoscriptsyntax as rs
import ExtruderTurtle as e
import operator as op
import math

def translate(g,x,y,z):
	translation = geom.Transform.Translation(x,y,z)
	g.Transform(translation)
	
def rotate(g,angle):
	rotation = geom.Transform.Rotation(math.radians(angle),rs.CreatePoint(0,0,0))
	g.Transform(rotation)
	
def scale(g,scale_factor):
	scale= geom.Transform.Scale(rs.CreatePoint(0,0,0),scale_factor)
	g.Transform(scale)

# versions of transformations that do not alter input shape
def translate_copy(g,x,y,z):
	shape = copy.deepcopy(g)
	translation = geom.Transform.Translation(x,y,z)
	return shape.Transform(translation)
	
def rotate_copy(g,angle):
	shape = copy.deepcopy(g)
	rotation = geom.Transform.Rotation(math.radians(angle),rs.CreatePoint(0,0,0))
	return shape.Transform(rotation)
	
def scale_copy(g,scale_factor):
	shape = copy.deepcopy(g)
	scale= geom.Transform.Scale(rs.CreatePoint(0,0,0),scale_factor)
	return shape.Transform(scale)

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

# generates a turtle path and g-code that slices a solid (shape)
# optional number of walls, walls are offset into interior of shape
def slice_with_turtle (t, shape, walls = 1, layer_height=False, spiral_up=False):
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
		spiral_bottom_convex_shape(t,slices[0])
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

	bb = rs.BoundingBox(shape)
	height = rs.Distance(bb[0], bb[4])
	size = rs.Distance(bb[0], bb[6])*2 # size of slicing plane
	slices = []
	z = bb[0].Z

	slice = one_slice(shape,z,size)
	if (slice):
		points = rs.DivideCurve (slice, 20)
	else: 
		print("Slicing error. Move your shape closer to the origin for slicing.")
		return

	#generate slice curves
	count_main = 0
	new_layer_height = layer_height
	while (z < height-bb[0].Z and count_main <100):
		count_main = count_main + 1
		# measure max distance between point this slice & previous slice
		# calculate z based on that distance
		previous_points = copy.deepcopy(points)
		slice = one_slice(shape,z,size)
		if (slice):
			points = rs.DivideCurve (slice, 20)
		maxd = max_distance_between_slices(previous_points,points)
		count = 0
		desired_distance = layer_height*1.25
		if (maxd>desired_distance): # generate a new slice
			theta = math.asin(layer_height/maxd)
			new_layer_height = math.sin(theta)*desired_distance
			#print(new_layer_height)
			z = z-layer_height+new_layer_height
			slice = one_slice(shape,z,size)
			points = rs.DivideCurve (slice, 20)

		# if you're close to the top of the shape
		# make sure you account for thinner layers
		if (z+layer_height >= height):
			if (new_layer_height):
				z = z+new_layer_height
			else:
				z = z+layer_height/2
		else:
			z = z+layer_height

		#print("new distance: " +str(maxd))
		if (slice and maxd>0):
			#print("added slice")
			slices.append(slice)

	#slice the top layer
	z = bb[7].Z-.01
	slice = one_slice(shape,z,size)
	if (slice):
		slices.append(slice)
	else:
		print("final slice failed")

	follow_slice_curves_with_turtle(t,slices,walls=walls,spiral_up=spiral_up)

	print("number of equal distanced slices is: " +str(len(slices)))
	return slices

# given a list of curves that slice a shape (slices)
# follow the curves with the turtle
def follow_slice_curves_with_turtle(t,slices,walls=1,spiral_up=False):
	resolution = t.get_resolution()

	z0 = t.getZ()
	layers = len(slices)
	for i in range (0,layers):
		points = rs.DivideCurve (slices[i], 100)
		ll = line_length(points)
		num_points = int(ll/resolution)+1
		points = rs.DivideCurve (slices[i], num_points)
		if (z0 != 0):
			for i in range (num_points):
				points[i].Z = points[i].Z+z0
		
		# spiral up if possible and relevant
		if (walls == 1 and spiral_up):
			if (i < layers-1):
				points_next = rs.DivideCurve (slices[i+1], num_points)
				z_inc = (points_next[0].Z-points[0].Z)/num_points
				follow_closed_line (t,points,z_inc=z_inc)
		else:
			follow_closed_line(t,points,walls=walls)

#generates a turtle path from a list of rhinoscript points
def follow_closed_line(t,points,z_inc=0,walls = 1):
	smooth_seam = 3 # on multi-walled prints, stop extruding near the seam to avoid a bump
	t.penup()
	t2 = e.ExtruderTurtle()
	if (z_inc==0 or walls > 1):
		t2.set_position(points[0].X,points[0].Y,points[0].Z)

	points2 = []
	for i in range (0, len(points)):
		if (z_inc==0 or walls > 1):
			t.set_position(points[i].X,points[i].Y,points[i].Z)
		else:
			t.set_position(points[i].X,points[i].Y)
			t.lift(z_inc)
		if (i>=smooth_seam):
			t.pendown()
		if ((i>=len(points)-smooth_seam) and walls>1):
			t.penup()

		if (walls>1):
			t2.set_position(points[i].X,points[i].Y,points[i].Z)
			t2.penup()
			t2.right(90)
			t2.forward(t.get_extrude_width())
			t2.pendown()
			x1 = t2.getX()
			y1 = t2.getY()
			z1 = t2.getZ()
			t2.backward(t.get_extrude_width())
			t2.left(90)
			points2.append(rs.CreatePoint(x1,y1,z1))

	#close the layer curve
	if (z_inc==0 or walls > 1):
		t.set_position(points[0].X,points[0].Y,points[0].Z)
	else:
		t.set_position(points[0].X,points[0].Y)

	while (walls>1):
		t.penup()
		t.set_position(points2[0].X,points2[0].Y,points[0].Z)
		for i in range (1, len(points2)):
			t.set_position(points2[i].X,points2[i].Y,points[i].Z)
			if (i>=smooth_seam):
				t.pendown()
			if (i>=len(points2)-smooth_seam):
				t.penup()
		
		t.pendown()
		walls = walls-1
		if (walls > 1):
			follow_closed_line(t, points2, walls = walls)


# generates a bottom for convex shapes
# does not work for concave shapes
def spiral_bottom_convex_shape(t,curve):
	resolution = t.get_resolution()
	points = curve_to_points(curve,resolution)
	t2 = e.ExtruderTurtle()
	t2.penup()
	ll = line_length(points)
	num_points = int(ll/t.get_extrude_width())
	previous_num_points = num_points
	follow_closed_line(t,points)

	count = 0
	while (num_points > t.get_extrude_width()*6 and count < 50):
		#print(num_points)
		points2 = []
		t2.set_position(points[0].X,points[0].Y)
		for i in range (1, len(points)):
			t2.set_position(points[i].X,points[i].Y)
			t2.right(90)
			t2.forward(t.get_extrude_width())
			x1 = t2.getX()
			y1 = t2.getY()
			z1 = t2.getZ()
			t2.backward(t.get_extrude_width())
			t2.left(90)
			new_point = rs.CreatePoint(x1,y1,z1)
			t.set_position(new_point.X,new_point.Y)
			points2.append(new_point)

		curve = rs.AddCurve(points2,2)
		points = rs.DivideCurve (curve, 100)
		ll = line_length(points)
		previous_num_points = num_points
		num_points = int(ll/t.get_extrude_width())
		if (num_points>previous_num_points):
			return
		points = rs.DivideCurve (curve, num_points)
		count = count+1

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


def follow_closed_line_simple_bumps(t,points,num_bumps=0,bump_length=0, bump_start = 0, z_inc=0):
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

def follow_closed_line_weave(t,points,num_oscillations=50.0, amplitude = 5, z_inc=0):
	num_points = len(points)
	t2 = e.ExtruderTurtle()
	dtheta = 360.0/num_points
	theta = 0
	x0 = 0
	y0 = 0
	for i in range (0, num_points):
		t2.set_position(points[i].X,points[i].Y)
		delta = amplitude*math.cos(num_oscillations*math.radians(theta))
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
		t.lift(z_inc)
		theta = theta + dtheta
	return t2

# adjust the number of steps in a circle 
# to avoid generating too many points for small shapes
# minimum step size = resolution
def adjust_circle_steps(diameter, steps, resolution):
	#resolution = resolution # use smaller resolution here
	circumference = diameter * math.pi
	c_inc = circumference/steps
	if (c_inc < resolution):
		c_inc = resolution
		steps = int(circumference/c_inc)
	return steps

#creates a circle or polygon with the edge begining at the turtle's location
def non_centered_poly(t, diameter, steps=360):
	steps = adjust_circle_steps(diameter, steps,t.get_resolution())
	if (t.write_gcode):
		t.write_gcode_comment("starting polygon")
	circumference = diameter * math.pi
	c_inc = circumference/steps
	dtheta = 360.0/steps
	t.right(dtheta/2)
	
	for i in range (steps):
		t.forward(c_inc)
		t.right(dtheta)

	t.left(dtheta/2)

def circular_bottom(t,diameter,layers):
	for i in range (layers-1):
		t.right(360/layers)
		polygon_layer(t,diameter,return_to_center=True,offset=(i%2))
		t.lift(t.get_layer_height()*1.15)

	t.right(360/layers)
	polygon_layer(t,diameter,return_to_center=False)	

def circular_layer(t,diameter,spiral_up = True):
	oscillating_circle(t,diameter, 0, 0, spiral_up = spiral_up)


# creates a solid flat layer of polygons that spiral out from a center point
def polygon_layer (t, diameter, steps=360, return_to_center = False, offset=0.0):
	initial_position = t.get_position()
	initial_angle = t.get_yaw()
	if (t.write_gcode):
		t.write_gcode_comment("starting solid layer")
	if (offset>0):
		d = t.get_extrude_width()*3
	else:
		d = t.get_extrude_width()*2

	t.extrude(10)
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
def centered_poly(diameter, steps, t):
	# avoid generating too many points for small shapes
	steps = adjust_circle_steps(diameter, steps,t.get_resolution())
	r = diameter/2
	circumference = diameter * math.pi
	c_inc = circumference/steps
	outer_angle = 360/steps
	inner_angle = 180-360/steps
	t.lift(t.get_layer_height()*5)
	t.penup()
	t.forward(r)
	t.left(outer_angle + inner_angle/2)
	t.lift(-t.get_layer_height()*5)
	t.pendown()
	for i in range (steps):
		t.forward(c_inc)
		t.left(outer_angle)
	t.penup()
	t.lift(t.get_layer_height()*5)
	t.right(outer_angle + inner_angle/2)
	t.backward(r)
	t.lift(-t.get_layer_height()*5)
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
	steps = adjust_circle_steps(diameter, steps,t.get_resolution())
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
	steps = adjust_circle_steps(diameter,360,t.get_resolution())
	circumference = diameter * math.pi
	c_inc = circumference/steps
	if (spiral_up and z_inc==0):
		z_inc = t.get_layer_height()/steps
	elif (spiral_up):
		z_inc = (t.get_layer_height()+z_inc)/steps

	dtheta = 360.0/steps
	# to get 180 degrees out of phase add: theta_one_oscillation/2
	b = diameter/2
	x0 = t.getX()
	y0 = t.getY()
	z0 = t.getZ()
	z = z0
	#z_inc = t.get_layer_height()/steps
	# this is a problematic if statement. Will cause problems later!
	if (x0==0):
		theta0 = 0
		# could also be theta0 = 90 or theta0 = 270
	elif (x0 < 0):
		theta0 = math.degrees(math.atan(y0/x0))+180
	else:
		theta0 = math.degrees(math.atan(y0/x0))

	for s in range(1,steps+1):
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
	steps = adjust_circle_steps(diameter,360,t.get_resolution())
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
