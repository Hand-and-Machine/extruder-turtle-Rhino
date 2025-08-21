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


	shape_slices2=[]
	z = zlist[0]["z"]
	for i in range (len(shape_slices)):
		z = zlist[i]["z"]
		index = zlist[i]["index"]
		shape_slices2.append(shape_slices[index])
	return shape_slices_layer

def find_points_and_angles_angles(slice0, slice1, period):
	resolution = period/2.0
	flag = False
	points = rs.DivideCurveEquidistant(slice0, resolution) # create points resolution apart to find correct #
	point_number = len(points)
	if (point_number<10):
		# print("warning very small layer!")
		# print("number of points: " +str(point_number))
		if (point_number<6):
			print("skipping small layer")
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
		# print("layer swap")
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

def weave_points_and_angles(t,points,angles,wall_width=3.0,mode=1,offset=False):
	t2 = ExtruderTurtle()
	t2.set_position_point(points[len(points)-1])
	# for all points in the slice

	for j in range(0,len(points)):
		# it is possible, if you're using angles from the prior slice 
		# that you have more points than you have angles
		# if this is the case, don't update the angle variable
		if (j<len(angles)): 
			angle = angles[j]	
		amplitude = (wall_width/2.0)/math.cos(math.radians(angle))
		if (amplitude>wall_width*3):
			# amplitude is too large. Return fail code
			return -1
		t2.set_position_point(points[j])
		if (offset==True):
			o=j+1
		else:
			o=j
		if (o%2==0):
			if (mode==1): # zig zag on line
				t2.left(90)
				t2.forward(amplitude)
				t.set_position_point(t2.get_position())
				if (j==0):
					point0=t.get_position()
				t2.forward(-amplitude)
				t2.right(90)
			elif(mode==2): # zig zag set into shape
				t2.right(90)
				t2.forward(amplitude*2)
				t.set_position_point(t2.get_position())
				if (j==0):
					point0=t.get_position()
				t2.forward(-amplitude*2)
				t2.left(90)
			else:
				t2.left(90)
				t2.forward(amplitude*2)
				t.set_position_point(t2.get_position())
				if (j==0):
					point0=t.get_position()
				t2.forward(-amplitude*2)
				t2.right(90)
		else:
			if (mode==1):
				t2.right(90)
				t2.forward(amplitude)
				t.set_position_point(t2.get_position())
				t2.forward(-amplitude)
				t2.left(90)
			else:
				t.set_position_point(t2.get_position())
		if (j==0):
			t.pendown()

def find_closest_slice(slice0,next_slices):
	min_distance=10000
	index=-1
	points0 = rs.DivideCurveEquidistant(slice0, 10)
	for i in range (0,len(next_slices)):
		closest=rs.CurveClosestPoint(next_slices[i],points0[0])
		closest_point = rs.EvaluateCurve(next_slices[i], closest)
		distance = abs(rs.Distance(points0[0],closest_point))
		if (distance<min_distance):
			min_distance=distance
			index=i
	return index


def weave_slice_turtle (t,shape,wall_width=3.0,period=2.0, mode=1, top_layer=1):
	layer_height = t.get_layer_height()
	shape_slices = slice_shape(shape,layer_height=layer_height)
	# for all slices in shape
	offset=True 
	angles0=[]
	old_wall_width = wall_width
	for i in range (0,len(shape_slices)-1):
		branch=False
		slice0 = shape_slices[i][0] # current slice
		slice1 = shape_slices[i+1][0] # slice above

		if (i==0 and rs.IsCurveClosed(slice0)):
			print("could create a bottom")

		if (len(shape_slices[i])>1):
			branch=True
			t.penup()

		points0,points1,angles = find_points_and_angles_angles(slice0,slice1,period)

		if (angles and angles[0]>86 and angles[0]<92):
			# found an almost horizontal layer transition. Make sure it's valid
			index = find_closest_slice(slice0,shape_slices[i+1])
			slice1 = shape_slices[i+1][index] 
			points0,points1,angles = find_points_and_angles_angles(slice0,slice1,period)
			
		if (rs.CurveArea(slice0) and rs.CurveArea(slice0)[0]<math.pi*wall_width*wall_width*15):
			# if the curve area is small, increase the period and decrease amplitude to reduce over extrusion
			# note: the area calculation depends on the units of the Rhino file. Assumes mmprint("Warning: the WeaveSlicer library is doing operations that assume your Rhino environment is in millimeters. If you are getting strange results, set your Rhino units to millimeters.")
			# print("Warning: the WeaveSlicer library is doing operations that assume your Rhino environment is in millimeters. If you are getting strange results, set your Rhino units to millimeters.")
			new_wall_width=wall_width/1.5
			wall_width=new_wall_width
			points0,points1,angles = find_points_and_angles_angles(slice0,slice1,period*1.5)
		else:
			wall_width=old_wall_width

		if (points0 and points1 and angles):
			x = weave_points_and_angles(t,points0,angles,wall_width=wall_width,mode=mode,offset=offset)

		if (x==-1):
			# found an error. Try to find a better next slice
			index = find_closest_slice(slice0,shape_slices[i+1])
			slice1 = shape_slices[i+1][index] 
			points0,points1,angles = find_points_and_angles_angles(slice0,slice1,period)
			if (points0 and points1 and angles):
				x = weave_points_and_angles(t,points0,angles,wall_width=wall_width,mode=mode,offset=offset)

		if (branch):
			# if there is more than one slice on this layer
			# create the toolpath for the remaining slices
			k=1
			while (k<len(shape_slices[i])):
				t.penup()
				slice0 = shape_slices[i][k] # current slice
				index = find_closest_slice(slice0,shape_slices[i+1])
				slice1 = shape_slices[i+1][index] # slice above
				points0,points1,angles = find_points_and_angles_angles(slice0,slice1,period)
				if (points0 and points1 and angles):
					x=weave_points_and_angles(t,points0,angles,wall_width=wall_width,mode=mode,offset=offset)
				if (x==-1):
					print("error at index: " +str(i))
				t.pendown()
				k+=1
			
		offset=not(offset)

		if (rs.IsCurveClosed(slice1)==False or rs.IsCurveClosed(slice0)==False ): # if current or next curve is not closed, lift pen
			t.penup()

	# top slice
	if (top_layer):
		if (points0 and points1 and angles):
			weave_points_and_angles(t,points1,angles,wall_width=wall_width,mode=mode,offset=offset)

	return len(shape_slices)

def weave_slice (shape, file=False, layer_height=1.0, wall_width=3.0, period=3.0, mode=1, top_layer=1):
	t = ExtruderTurtle()
	if (file):
		t.setup(filename=file, printer = "eazao")
	else:
		t.setup(printer = "eazao")
	t.set_layer_height(layer_height)
	t.penup()
	weave_slice_turtle(t,shape,wall_width=wall_width,period=period, mode=mode, top_layer=top_layer)
	t.finish()
	return t.get_lines()

		

