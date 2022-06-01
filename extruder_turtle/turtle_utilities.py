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

def surfaceForSlice(z,size):
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
		if a == start: break
	return lines, hull_points
	
def slice_solid (shape, layer_height):
	bb = rs.BoundingBox(shape)
	height = rs.Distance(bb[0], bb[4])
	layers = int(height/layer_height)
	size = rs.Distance(bb[0], bb[2])
	planes = []
	slices = []
	z = 0
	for i in range (0,layers):
		plane = surfaceForSlice(z,size)
		planes.append(plane)
		intersection = rs.BooleanIntersection(plane, shape, delete_input=False)
		surfaces = rs.ExplodePolysurfaces(intersection, delete_input=False)
		curves = rs.DuplicateEdgeCurves(surfaces[2])
		slices.append(curves[0])
		z = z+layer_height
	return slices

def slice_with_turtle (t, shape, walls = 1):
	resolution = t.get_resolution()
	layer_height = t.get_layer_height()
	if (layer_height == 0):
		layer_height = 1
	bb = rs.BoundingBox(shape)
	height = rs.Distance(bb[0], bb[4])
	layers = int(round(height/layer_height))
	size = rs.Distance(bb[0], bb[2])
	planes = []
	slices = []
	z = 0
	#generate slice curves
	for i in range (0,layers):
		plane = surfaceForSlice(z,size)
		planes.append(plane)
		intersection = rs.BooleanIntersection(plane, shape, delete_input=False)
		surfaces = rs.ExplodePolysurfaces(intersection, delete_input=False)
		if (len(surfaces)>1)
			curves = rs.DuplicateEdgeCurves(surfaces[2])
		else:
			break
		slices.append(curves[0])
		z = z+layer_height

	layers = len(slices)
	#follow slice curves with turtle
	for i in range (0,layers):
		points = rs.DivideCurve (slices[i], 100)
		ll = line_length(points)
		num_points = int(ll/resolution)+1
		points = rs.DivideCurve (slices[i], num_points)
		follow_closed_line(t,points,walls=walls)
		t.penup()
		t.lift(layer_height)
		t.pendown()

#generates a turtle path from a list of rhinoscript points
def follow_closed_line(t,points,z_inc=0, walls = 1):
	t.penup()
	t.set_position(points[0].X,points[0].Y)
	t.pendown()

	t2 = e.ExtruderTurtle()
	if (walls>1):
		t2.set_position(points[0].X,points[0].Y)

	points2 = []
	for i in range (1, len(points)):
		t.set_position(points[i].X,points[i].Y)
		if (walls>1):
			t2.set_position(points[i].X,points[i].Y)
			t2.right(90)
			t2.forward(t.get_extrude_width())
			x1 = t2.getX()
			y1 = t2.getY()
			z1 = t2.getZ()
			t2.backward(t.get_extrude_width())
			t2.left(90)
			points2.append(rs.CreatePoint(x1,y1,z1))
	t.set_position(points[0].X,points[0].Y)

	while (walls>1):
		t.penup()
		t.set_position(points2[0].X,points2[0].Y)
		t.pendown()
		for i in range (1, len(points2)):
			t.set_position(points2[i].X,points2[i].Y)
		t.set_position(points2[0].X,points2[0].Y)
		walls = walls-1
		if (walls > 1):
			follow_closed_line(t, points2, walls = walls)

	t.lift(z_inc)

#incomplete
def spiral_bottom(t,curve):
	resolution = t.get_resolution()
	points = curve_to_points(curve,resolution)
	t2 = e.ExtruderTurtle()
	#follow_closed_line(t,points)

	# number of spirals
	for j in range(0,4):
		points2 = []
		for i in range (0, len(points)):
			t2.penup()
			t2.set_position(points[i].X,points[i].Y)
			t2.right(90)
			t2.forward(t.get_extrude_width()*.75)
			x1 = t2.getX()
			y1 = t2.getY()
			z1 = t2.getZ()
			t2.backward(t.get_extrude_width()*.75)
			t2.left(90)
			new_point = rs.CreatePoint(x1,y1,z1)
			if (j==3):
				t.set_position(new_point.X,new_point.Y)
			points2.append(new_point)
		curve = rs.AddCurve(points2,2)
		intersections = rs.CurveCurveIntersection(curve)
		if (intersections!=None):
			# print("number of intersections " +str(len(intersections)))
			# print("first intersection: " +str(intersections[0][1]))
			#print(intersections)
			return intersections
		points = rs.DivideCurve (curve, 100)
		ll = line_length(points)
		num_points = int(ll/resolution)+1
		points = rs.DivideCurve (curve, num_points)

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
def bump_square(t,bump_length,c_bump,dtheta,z_inc,bump_width=0):
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

#bump_width in number of steps NOT mm
def bump_triangle(t,bump_length, bump_width, c_inc, d_theta,z_inc=0):
	x0 = t.getX()
	y0 = t.getY()
	z0 = t.getZ()
	yaw0 = t.get_yaw()
	t2 = e.ExtruderTurtle()
	t2.set_position(x0,y0,z0)
	t2.set_heading(yaw0)
	if (bump_width==0):
		bump(t,bump_length, bump_width, c_inc, d_theta,z_inc=0)
		return

	for i in range (0,bump_width/2):
		t2.forward_lift(c_inc,z_inc)
		t2.right(d_theta)
	t2.left(90)
	t2.forward(bump_length)
	x1 = t2.getX()
	y1 = t2.getY()
	z1 = t2.getZ()
	t2.backward(bump_length)
	t2.right(90)
	for i in range (0,bump_width/2):
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
	resolution = resolution/5 # use smaller resolution here
	circumference = diameter * math.pi
	c_inc = circumference/steps
	if (c_inc < resolution):
		c_inc = resolution
		steps = int(circumference/c_inc)
	return steps

#creates a polygon with the edge begining at the turtle's location
def non_centered_poly(diameter, steps, t):
	steps = adjust_circle_steps(diameter, steps,t.get_resolution())
	if (t.write_gcode):
		t.write_gcode_comment("starting polygon")
	circumference = diameter * math.pi
	c_inc = circumference/steps
	dtheta = 360.0/steps
	
	for i in range (steps):
		t.forward(c_inc)
		t.right(dtheta)

def circular_bottom(t,diameter,layers):
	for i in range (layers-1):
		polygon_layer(diameter,360,t,return_to_center=True)
		t.lift(t.get_layer_height()*1.25)
		t.right(360/layers)
	polygon_layer(diameter,360,t,return_to_center=False)		

def circular_layer(t,diameter,spiral_up = True):
	oscillating_circle(t,diameter, 0, 0, spiral_up = spiral_up)


# creates a solid flat layer of polygons that spiral out from a center point
def polygon_layer (diameter, steps, t, return_to_center = False):
	steps = adjust_circle_steps(diameter, steps, t.get_resolution())
	if (t.write_gcode):
		t.write_gcode_comment("starting solid layer")
	d = t.get_extrude_width()*2
	t.left(90)
	t.forward(t.get_extrude_width())
	t.right(90)

	t.extrude(10)
	non_centered_poly(d,steps,t)
	while (d < (diameter-t.get_extrude_width()*2)):
		t.left(90)
		t.forward(t.get_extrude_width())
		t.right(90)
		d = d+t.get_extrude_width()*2 
		non_centered_poly(d,steps,t)

	t.left(90)
	t.forward((diameter-d)/2)
	t.right(90)
	non_centered_poly(diameter,steps,t)

	if (return_to_center):
		t.penup()
		t.left(90)
		t.lift(1)
		t.backward(diameter/2)
		t.right(90)
		t.lift(-1)
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

def oscillating_circle(t, diameter, nOscillationsxy, axy, nOscillationsz=0, az=0, spiral_out=0, theta_offset=0, spiral_up = True):
	# avoid generating too many points for small shapes
	steps = adjust_circle_steps(diameter, 360,t.get_resolution())
	circumference = diameter * math.pi
	c_inc = circumference/steps
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
