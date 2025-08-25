import copy
import Rhino.Geometry as geom
import rhinoscriptsyntax as rs
import ExtruderTurtle as e
import operator as op
import math
import random
import extruder_turtle
from extruder_turtle import *

def slice_shape(shape, layer_height=1.0):
	bounding_box = rs.BoundingBox(shape)
	slice_vector=(bounding_box[0], bounding_box[4])
	shape_slices = rs.AddSrfContourCrvs(shape, slice_vector, interval=layer_height)

	# sort slices in x and then z
	# makes sure slices are correctly ordered
	zlist=[]
	for i in range (len(shape_slices)):
		points0 = rs.DivideCurve(shape_slices[i], 10)
		zlist.append({"z":round(points0[0].Z,3),"x": round(points0[0].X,3),"y": round(points0[0].Y,3), "index": i})
	zlist.sort(key=lambda item: item["y"])
	zlist.sort(key=lambda item: item["x"])
	zlist.sort(key=lambda item: item["z"]) 

	shape_slices_layer=[]
	i=0
	while (i<len(shape_slices)):
		layer=[]
		layer_sort=[]
		z0 = zlist[i]["z"]
		index0 = zlist[i]["index"]
		layer.append(shape_slices[index0])
		if (i<len(shape_slices)-1):
			z1 = zlist[i+1]["z"]
			j=i+1
			delta = abs(z1-z0)
		else:
			# add top slice and return
			shape_slices_layer.append(layer)
			break

		# check for multiple branches, multiple curves at same z
		while (j<len(shape_slices) and abs(z1-z0)<layer_height/50):
			# print("found multiple branches at: " +str(i))
			index1 = zlist[j]["index"]
			layer.append(shape_slices[index1])
			j+=1
			i+=1
			if (j<len(zlist)):
				z1 = zlist[j]["z"]
			else:
				break
		shape_slices_layer.append(layer)
		i+=1

	return shape_slices_layer

def find_points_and_angles_angles(slice0, slice1, period):
	resolution = period/2.0
	flag = False
	points = rs.DivideCurveEquidistant(slice0, resolution) # create points resolution apart to find correct #
	point_number = len(points)
	if (point_number<7):
		print("skipping very small layer")
		return False, False, False
	while (point_number%2!=0): #want even number of points to complete circle
		point_number+=1
	points0 = rs.DivideCurve(slice0, point_number)
	points1 = rs.DivideCurve(slice1, point_number) 

	# check for discontinuity between two curves
	slice0_closed = rs.IsCurveClosed(slice0)
	slice1_closed = rs.IsCurveClosed(slice1)
	length_difference = rs.CurveLength(slice1)-rs.CurveLength(slice0)
	if ((abs(length_difference)>.1 and length_difference<0) or (slice0_closed and not(slice1_closed))): 
		# if slice0 is closed and slice1 is open, slice1 is begining of hole and can't find all angles
		# if slice0 is significantly longer than slice1, also can't find all angles
		# in these cases, swap slice0 and slice1 to calculate angles
		slice_placeholder = slice0
		slice0 = slice1
		slice1 = slice_placeholder
		points0 = rs.DivideCurve(slice0, point_number)
		points1 = rs.DivideCurve(slice1, point_number) 
		flag = True
	
	angles=[]
	for j in range(0,len(points0)):
		# compare against closest point on next layer
		# assumption: this is the point directly above the current point
		closest=rs.CurveClosestPoint(slice1, points0[j])
		point1 = rs.EvaluateCurve(slice1, closest)
		vector = rs.VectorSubtract(point1,points0[j])
		if (flag):
			# calculating angles based on layer below
			angle = rs.VectorAngle([0,0,-1.0],vector)
		else:
			# calculating angles based on layer above
			angle = rs.VectorAngle([0,0,1.0],vector)
		angles.append(angle)
	if (flag): 
		# set points back to correct values for layer
		slice_placeholder = slice0
		slice0 = slice1
		slice1 = slice_placeholder
		points0 = rs.DivideCurve(slice0, point_number)
		points1 = rs.DivideCurve(slice1, point_number)

	return points0,points1,angles

def weave_points_and_angles(t,points,points1,angles,slice0,slice1,wall_width=3.0,mode=1,offset=False,top=False):

	if (not(points) or not(points1) or not(angles)):
		return -1

	if (top):
		slice0=slice1
		points=points1

	t2 = ExtruderTurtle()
	t2.set_position_point(points[0])
	t2.set_position_point(points[1])
	t2.left(90)
	t2.forward(1)
	point = t2.get_position()

	slice0_closed = rs.IsCurveClosed(slice0)

	if (slice0_closed):
		test = rs.PointInPlanarClosedCurve(point, slice0)
		if (test==False):
			# point is outside
			# should be inside, swap modes
			if (mode==3):
				mode=2
			elif (mode==2):
				mode=3

	t2.set_position_point(points[len(points)-1])

	# t3 will create the slice for this layer and return it as a path
	t3 = ExtruderTurtle()
	t3.penup()
	t3.set_position_point(points[len(points)-1])
	# for all points in the slice

	if (not(slice0_closed)):
		# open curve
		t.penup()
		t.set_position_point(points[0])
		t3.penup()
		t3.set_position_point(points[0])
	else:
		# closed curve
		t.penup()
		t.set_position_point(points[0])
		t.pendown()

	for j in range(0,len(points)):
		# it is possible, if you're using angles from the prior slice 
		# that you have more points than you have angles
		# if this is the case, don't update the angle variable
		if (j<len(angles)): 
			angle = angles[j]	

		amplitude = (wall_width/2.0)/math.cos(math.radians(angle))
		amplitude = small_curve_check(slice0,amplitude,mode)

		t2.set_position_point(points[j])
		if (offset==True):
			o=j+1
		else:
			o=j
		if (o%2==0):
			if (mode==1): #path should be on curve
				t2.left(90)
				t2.forward(amplitude)
				t.set_position_point(t2.get_position())
				t3.set_position_point(t2.get_position())
				if (j==0):
					point0=t.get_position()
				t2.forward(-amplitude)
				t2.right(90)
			elif(mode==2): #path should be outside curve
				t2.right(90)
				t2.forward(amplitude*2)
				t.set_position_point(t2.get_position())
				if (j==0):
					point0=t.get_position()
				t2.forward(-amplitude*2)
				t2.left(90)
			elif(mode==3): #path should be inside curve
				t2.left(90)
				t2.forward(amplitude*2)
				t.set_position_point(t2.get_position())
				t3.set_position_point(t2.get_position())
				if (j==0):
					point0=t.get_position()
				t2.forward(-amplitude*2)
				t2.right(90)
			else:
				print("MODE ERROR")
				return
		else:
			if (mode==1):
				t2.right(90)
				t2.forward(amplitude)
				t.set_position_point(t2.get_position())
				t3.set_position_point(t2.get_position())
				t2.forward(-amplitude)
				t2.left(90)
			else:
				t.set_position_point(t2.get_position())
				t3.set_position_point(t2.get_position())
		if (j<1 and rs.IsCurveClosed(slice0)==False):
			t.penup()
			t3.penup()
		else:
			t.pendown()
			t3.pendown()

	# if the curve is closed, close the curve
	if (slice0_closed==True):
		t.set_position_point(points[0])
		t3.set_position_point(points[0])
	return t3.get_lines()



def weave_slice_turtle (t,shape,wall_width=3.0,period=3.0, mode=1, bottom_layers=0, glass_clay=False):
	t.write_gcode_comment("**************************************************")
	t.write_gcode_comment("******* file generated by WeaveSlicer ************")
	t.write_gcode_comment("******* conception: Camila Friedman-Gerlicz ******")
	t.write_gcode_comment("****** python implementation: Leah Buechley ******")
	t.write_gcode_comment("************** 2023 - present ********************")
	t.write_gcode_comment("**************************************************")
	layer_height = t.get_layer_height()
	shape_slices = slice_shape(shape,layer_height=layer_height)
	# for all slices in shape
	offset=True 
	layers = []
	points=False
	x=-1
	for i in range (0,len(shape_slices)-1):
		k=0
		while (k<len(shape_slices[i])):
		# for all branches in current slice
			slice0 = shape_slices[i][k] # current slice

			if (i<bottom_layers and rs.IsCurveClosed(slice0)):
				point = rs.CurveAreaCentroid(slice0)[0]
				bottom_curve = slice0
				if (mode==1):
					bottom_curve = rs.OffsetCurve(slice0,point,wall_width)[0]
				elif(mode==3):
					bottom_curve = rs.OffsetCurve(slice0,point,wall_width*1.5)[0]
				else:
					bottom_curve = slice0
				bottom_curves=get_bottom_offset_curves(bottom_curve,t.get_extrude_width())
				follow_curve(t,bottom_curve)
				for c in range (0,len(bottom_curves)):
					follow_curve(t,bottom_curves[c])
					t.penup()

			if (len(shape_slices[i])==1):
				# if there is just one branch, use slice above to compute angles
				slice1 = shape_slices[i+1][k] # slice above
			else:
				# if there is more than one branch, lift pen and find the slice above
				t.penup()
				# if a branch is closing there may not be a matching branch above
				if (len(shape_slices[i+1])>k):
				# if there is a matching branch above:
					# try easy guess first
					slice1 = shape_slices[i+1][k] # slice above
				else:
				# if there is no matching branch above
					# find closest slice because you have to
					index = find_closest_slice(slice0,shape_slices[i+1]) 
					slice1 = shape_slices[i+1][index] # next slice
			
			points,points1,angles = find_points_and_angles_angles(slice0,slice1,period)
			count=0
			while (angles[0]>85 and angles[0]<95 and count<5):
				# if the angle is close to 90
				# a co-planar slice was found
				# this is probably the wrong one, try to find a better one
				index = find_closest_slice(slice0,shape_slices[i+1]) 
				slice1 = shape_slices[i+1][index] # next slice
				points,points1,angles = find_points_and_angles_angles(slice0,slice1,period)
				count+=1

			x=weave_points_and_angles(t,points,points1,angles,slice0,slice1,wall_width=wall_width,mode=mode,offset=offset)
			if (x==-1):
				print("error at index: " +str(i))
			else:
				layers.append(x)
			t.pendown()
			k+=1
			
		offset=not(offset)

		if (rs.IsCurveClosed(slice1)==False or rs.IsCurveClosed(slice0)==False ): # if current or next curve is not closed, lift pen
			t.penup()

	# top slice
	if (points and points1 and angles):
		x=weave_points_and_angles(t,points,points1,angles,slice0,slice1,wall_width=wall_width,mode=mode,offset=offset, top=True)
	if (x!=-1):
		layers.append(x)

	return layers

def weave_slice (shape, file=False, layer_height=1.0, wall_width=3.0, period=3.0, mode=1, bottom_layers=0):
	t = ExtruderTurtle()
	if (file):
		t.setup(filename=file, printer = "micro")
	else:
		t.setup(printer = "micro")
	t.write_gcode_comment("You can replace everything above this line with the correct header for your 3D printer.")
	t.set_layer_height(layer_height)
	t.penup()
	weave_slice_turtle(t,shape,wall_width=wall_width,period=period, mode=mode, bottom_layers=bottom_layers)
	t.finish()
	return t.get_lines()


		





def follow_curve(t, curve, double_wall = False, inner_wall=False, steps=100):
	points = rs.DivideCurve (curve, steps)
	dtheta = 360.0/steps

	i=0
	if (inner_wall==False):
		for point in points:
			if (i==0):
				t.set_position(point.X,point.Y,point.Z)
				t.pendown()
			else:
				t.pendown()
			t.set_position(point.X,point.Y,point.Z)
			i+=1

	if (rs.IsCurveClosed(curve)==False): # if curve is not closed, lift pen
			t.penup()

	t.set_position(points[0].X,points[0].Y,point.Z) # close curve
	t.set_position(points[1].X,points[1].Y,point.Z) # close curve

	if (double_wall or inner_wall):
		inner_curve = rs.OffsetCurve(curve, [0,0,0], t.get_extrude_width())
		print(inner_curve)
		if (inner_curve):
			inner_points = rs.DivideCurve (inner_curve, steps)
		else:
			#if offset fails, just return
			print("Couldn't create an offset curve to follow.")
			return()
		i=0
		for point in inner_points:
			if (i==0):	
				t.set_position(point.X,point.Y,point.Z)
				t.pendown()
			t.set_position(point.X,point.Y,point.Z)
			i+=1

		if (rs.IsCurveClosed(curve)==False): # if curve is not closed, lift pen
			t.penup()

		t.set_position(inner_points[0].X,inner_points[0].Y,inner_points[0].Z) # close curve
		t.set_position(inner_points[1].X,inner_points[1].Y,inner_points[0].Z) # close curve

def small_curve_check(slice, amplitude, mode):

	area = rs.CurveArea(slice)

	if (not(area)):
		#if curve is open
		return amplitude

	if(mode==3):
		multiplier=.5
	else:
		multiplier=.9

	area = area[0]
	threshold_amp = math.sqrt(area/math.pi)*multiplier

	if (amplitude>threshold_amp):
		new_amplitude = threshold_amp
		return new_amplitude
	else:
		return amplitude

def find_closest_slice(slice,next_slices):
	min_distance=10000
	index=-1
	# slice curve and pick an index for comparison point
	points0 = rs.DivideCurve(slice, 20)
	j = random.randint(4,16) #randomize the point that is chosen for comparison, avoiding the ends

	for i in range (0,len(next_slices)):
		# use a point along curve as a comparison to avoid branch comparison problems
		closest=rs.CurveClosestPoint(next_slices[i],points0[j])
		closest_point = rs.EvaluateCurve(next_slices[i], closest)
		distance = abs(rs.Distance(points0[j],closest_point))
		if (distance<min_distance):
			min_distance=distance
			index=i
	return index

def check_and_follow_curves(t,curve_list,last_curve):
	curve=last_curve
	for i in range(0,len(curve_list)):
		next_curve = curve_list[i]
		if (next_curve):
			try:
				area=rs.CurveArea(curve)[0]
				next_area=rs.CurveArea(next_curve)[0]
				if (len(curve_list)==1 and area-next_area<t.get_extrude_width()):
					#redundant curve, return and don't follow
					return
				else:
					follow_curve(t, next_curve)
					if(len(curve_list)>1):
						t.penup()
						t.lift(5)
			except Exception as e:
				print(e)
				print("Bottom layer may be problematic")
				# return
		else:
			break
		curve=next_curve

	return curve


def get_bottom_offset_curves (curve,distance):

	if (rs.IsCurveClosable(curve)==False):
		print("Can't make a bottom for an open form.")
		return

	point = rs.CurveAreaCentroid(curve)[0]
	next_curve=True
	count=0

	# while (next_curve and count<100):
	# 	if(curve):
	# 		next_curve_list=rs.OffsetCurve(curve, point, distance=distance,style=3)
	# 		if (not(next_curve_list)):
	# 			return
	# 		curve = check_and_follow_curves(t,next_curve_list,curve)

	# 	count+=1

	curve_list=[]
	curve_list=recursive_offset(curve,curve_list,distance)

	new_curve_list=[]

	#get rid of duplicate curves in list
	for i in range(0,len(curve_list)):
		flag=False
		curve=curve_list[i]
		start0 = rs.CurveStartPoint(curve)
		for j in range(i+1,len(curve_list)):
			start1 = rs.CurveStartPoint(curve_list[j])
			if(rs.Distance(start0,start1)<distance/2.0):
				flag=True
				break

		if (flag==False):
			compare_point=[-1000,0,0]
			closest=rs.CurveClosestPoint(curve_list[i], compare_point)
			sort_point = rs.EvaluateCurve(curve_list[i], closest)
			new_curve_list.append({"curve": curve_list[i], "x": sort_point.X})

	new_curve_list.sort(key=lambda item: item["x"])

	curves=[]
	for i in range(len(new_curve_list)):
		curves.append(new_curve_list[i]["curve"])

	return curves

def recursive_offset (curve,curve_list,distance):

	if (rs.IsCurveClosable(curve)==False):
		print("Can't make a bottom for an open form.")
		return []

	c=rs.CurveLength(curve)
	point = rs.CurveAreaCentroid(curve)[0]

	if (distance>c/10):
		# print("offset end condition curve length")
		return []

	a = rs.CurveArea(curve)[0]
	if (distance>math.sqrt(a/10)):
		# print("offset end condition curve area")
		return []

	next_curve_list=rs.OffsetCurve(curve, point, distance=distance,style=3)
	if (not(next_curve_list)):
		# print("couldn't find any more offsets")
		return []

	for i in range (0,len(next_curve_list)):
		# add current offset curve to list:
		# find new offsets for current offset:
		curve_list = curve_list + [next_curve_list[i]]+recursive_offset(next_curve_list[i],curve_list,distance)

	return curve_list





