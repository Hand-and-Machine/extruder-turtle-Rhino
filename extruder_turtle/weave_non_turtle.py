import Rhino.Geometry as geom
import rhinoscriptsyntax as rs
import ExtruderTurtle as e
import operator as op
import math
import random
import extruder_turtle
import slicer_utilities as su
import pattern_slicing as ps
import weave_slicer as ws
from extruder_turtle import *

def curve_normal(curve,point):
	parameter = rs.CurveClosestPoint(curve, point)
	plane = rs.CurveFrame(curve,parameter)
	normal = plane[2]
	normal2 = plane[2]+point
	return normal,normal2

# number of calculations based on wavelength
# calculate the angles between curve0 and curve1
# find list of amplitudes based on angles and wall width
# break curve up into points
# move points in or out based on amplitude along normal vectors
def weave_points(slice0,slice1,wavelength=3.0,wall_width=4.0,mode=3):
	points,points1,angles=ws.find_points_and_angles(slice0,slice1,wavelength,wall_width=wall_width,mode=3)
	point_number = len(points)
	amplitudes = []
	
	for i in range (0,len(angles)):
		angle=angles[i]
		amplitude = ((wall_width)/math.cos(math.radians(angle)))
		amplitudes.append(amplitude)

	inner_points=[]
	outer_points=[]
	mid_points=[]
	weave_points=[]
	point_types=[]
	for i in range (0,len(points)):
		normal = curve_normal(slice0,points[i])[0]

		#interior point
		if (i%4==0):
			# move in by 1/2 amplitude
			if (mode==1):
				new_point = points[i]+normal*amplitudes[i]*.5
			# move in by amplitude
			elif(mode==3):
				new_point = points[i]+normal*amplitudes[i]
			inner_points.append(new_point)
			point_types.append('i')
			weave_points.append(new_point)

		# middle point
		# not appended to weave points or point type lists
		elif(i%4==1 or i%4==3):
			# do nothing
			if (mode==1):
				new_point = points[i]
			# move in by 1/2 amplitude
			elif(mode==3):
				new_point = points[i]+normal*amplitudes[i]*.5
			mid_points.append(new_point)

		# outer point
		elif(i%4==2):
			# move out by 1/2 
			if (mode==1):
				new_point = points[i]-normal*amplitudes[i]*.5
			# do nothing
			elif(mode==3):
				new_point = points[i]
			outer_points.append(new_point)
			point_types.append('o')
			weave_points.append(new_point)

	# close the curve if the curve is closed
	if (rs.IsCurveClosed(slice0)):
		weave_points.append(weave_points[0])
		point_types.append(point_types[0])
		if (point_types[0]=='o'):
			outer_points.append(weave_points[0])
		elif (point_types[0]=='i'):
			inner_points.append(weave_points[0])
		else:
			print("point type error")

	return weave_points,point_types,inner_points,outer_points,mid_points

def follow_weave_points_turtle(t,weave_points,point_types,inner_points,outer_points,pattern_row=False):
	extruder=t.get_extruder()

	for i in range(len(weave_points)):
		if (pattern_row is not False):
			ratio = len(pattern_row)/len(weave_points)
			pattern_index = int(round(i*ratio,1))
			if ((pattern_row[pattern_index]>.5 and extruder==0) or (pattern_row[pattern_index]<=.5 and extruder==1)):
				# if current point is outer, moving from inner to outer 
				# transitions insured to happen on inner points
				if (point_types[i]=='o'): 
					t.pendown()
			else:
				# if current point is outer, moving from inner to outer 
				# transitions insured to happen on inner points
				if (point_types[i]=='o'): 
					t.penup()	
		else:
			# if there is no pattern, pen is always down
			t.pendown()
		t.set_position_point(weave_points[i])

	# if you are ending a pattern block on the outside, move to inside
	if (pattern_row is not False and point_types[len(point_types)-1]=='o'):
		if ((pattern_row[pattern_index]>.5 and extruder==0) or (pattern_row[pattern_index]<=.5 and extruder==1)):
			t.set_position_point(inner_points[0])








