import copy
import Rhino.Geometry as geom
import rhinoscriptsyntax as rs
import ExtruderTurtle as e
import operator as op
import math
import random
import extruder_turtle
from extruder_turtle import *

def slice_shape(t, shape, layer_height=False):
	if (layer_height==False):
		layer_height = t.get_layer_height()
	bounding_box = rs.BoundingBox(shape)
	slice_vector=(bounding_box[0], bounding_box[4])
	shape_slices = rs.AddSrfContourCrvs(shape, slice_vector, interval=layer_height)
	
	# sort slices in z
	zlist=[]
	for i in range (len(shape_slices)):
		points0 = rs.DivideCurve(shape_slices[i], 10)
		zlist.append({"z":points0[0].Z,"index": i})
	zlist.sort(key=lambda item: item["z"])
	shape_slices2=[]
	z = zlist[0]["z"]
	for i in range (len(shape_slices)):
		z = zlist[i]["z"]
		index = zlist[i]["index"]
		shape_slices2.append(shape_slices[index])
	return shape_slices2

def find_points_and_angles_angles(slice0,slice1,period):
	resolution = period/2.0
	flag = False
	points = rs.DivideCurveEquidistant(slice0, resolution) # create points resolution apart to find correct #
	point_number = len(points)
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

def weave_points_and_angles(t,points,angles,wall_width=3.0,period=2.0, on=1.0):

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
			print("Error. Too thick! Amplitude: " +str(amplitude))
			print("Angle: " +str(angle))
			return
		t2.set_position_point(points[j])
		if (j%2==0):
			if (on==1): # zig zag on line
				t2.left(90)
				t2.forward(amplitude)
				t.set_position_point(t2.get_position())
				if (j==0):
					point0=t.get_position()
				t2.forward(-amplitude)
				t2.right(90)
			elif(on==2): # zig zag set into shape
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
			if (on==1):
				t2.right(90)
				t2.forward(amplitude)
				t.set_position_point(t2.get_position())
				t2.forward(-amplitude)
				t2.left(90)
			else:
				t.set_position_point(t2.get_position())
		if (j==0):
			t.pendown()
	
def weave_slice(t,shape,wall_width=3.0,period=2.0, on=1, top=1):
	layer_height = t.get_layer_height()
	shape_slices = slice_shape(t,shape,layer_height=layer_height)
	# for all slices in shape
	for i in range (0,len(shape_slices)-1):
		slice0 = shape_slices[i] # current slice
		slice1 = shape_slices[i+1] # slice above
		points0,points1,angles = find_points_and_angles_angles(slice0,slice1,period)
		if (angles[0]>86 and angles[0]<92):
			print("Found a branch. Can't slice a model with branches!")
			return
		
		weave_points_and_angles(t,points0,angles,wall_width=wall_width,period=period, on=on)

		if (rs.IsCurveClosed(slice1)==False or rs.IsCurveClosed(slice0)==False ): # if current or next curve is not closed, lift pen
			t.penup()

	# top slice
	if (top):
		weave_points_and_angles(t,points1,angles,wall_width=wall_width,period=period, on=on)

	return len(shape_slices)

def weave_single_slice(t,shape,slice=0, wall_width=3.0,period=2.0, on=1):
	layer_height = t.get_layer_height()
	shape_slices = slice_shape(t,shape,layer_height=layer_height)
	angles0=False
	# for all slices in shape
	for i in range (slice,slice+1):
		slice0 = shape_slices[i] # current slice
		slice1 = shape_slices[i+1] # slice above
		points0,points1,angles = find_points_and_angles_angles(slice0,slice1,angles0,period)
		if (angles==False):
			print("Error! Found layer discontinuity on first 2 layers. Can't slice.")
			print("Error at index i: " +str(i))
			return()
		
		weave_points_and_angles(t,points0,angles,wall_width=wall_width,period=period, on=on)

		if (rs.IsCurveClosed(slice1)==False or rs.IsCurveClosed(slice0)==False ): # if current or next curve is not closed, lift pen
			t.penup()
		angles0=angles

	return points0

		

