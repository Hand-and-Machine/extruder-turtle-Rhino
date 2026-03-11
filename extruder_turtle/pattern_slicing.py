import Rhino.Geometry as geom
import rhinoscriptsyntax as rs
import ExtruderTurtle as e
import operator as op
import math
import random
import extruder_turtle
import slicer_utilities as su
from extruder_turtle import *


def first_pattern_pixel(pattern_row):
	if (pattern_row is False):
		return -1

	first_pattern_pixel=False
	for i in range (0,len(pattern_row)):
		if (first_pattern_pixel==False and pattern_row[i]<.5):
			first_pattern_pixel=i
			break

	if (first_pattern_pixel is False):
		return -1
	
	# check to see if the pattern began before 0
	j=len(pattern_row)-1
	if (first_pattern_pixel==0):
		while (pattern_row[j]<=.5 and j>=0):
			first_pattern_pixel=j
			j-=1

	return first_pattern_pixel

def last_pattern_pixel(pattern_row):
	last_pattern_pixel=False

	for i in range (len(pattern_row)-1,0,-1):
		# print(i)
		if (last_pattern_pixel==False and pattern_row[i]<.5):
			last_pattern_pixel=i
			break

	if (last_pattern_pixel is False):
		return -1
	
	# check to see if the pattern ends after length of pattern row
	max=len(pattern_row)-1
	j=0
	if (last_pattern_pixel==max):
		while (pattern_row[j]<=.5 and j<=max):
			last_pattern_pixel=j
			j+=1

	return last_pattern_pixel

def clean_edge_rounded_beg (t2,t):
	t2.left(90)
	t2.forward(t.get_extrude_width()*1.5)
	t.set_position_point(t2.get_position())
	t2.back(t.get_extrude_width()*1.5)
	t2.right(90)


def clean_edge_rounded_end (t2,t):
	t2.left(90)
	t2.forward(t.get_extrude_width()*1.5)
	t.set_position_point(t2.get_position())
	t.penup()
	t2.lift(1)
	t2.forward(t.get_extrude_width()*2)
	t.set_position_point(t2.get_position())
	t2.back(t.get_extrude_width()*3.5)
	t.set_position_point(t2.get_position())
	t2.right(90)


def follow_points_clean_edges(t,points,follow_z=True,closed=False,pattern_row=False,pattern_mode=0):
	if (pattern_row!=False):
		if (len(points)!=len(pattern_row)):
			print("Number of points doesn't match pattern size")
			return

	t2=ExtruderTurtle()

	i=0
	speed=t.get_speed()
	for point in points:
		if (i==0):
			t.penup()
			if (follow_z):
				t.set_position(point.X,point.Y,point.Z)
				t2.set_position(point.X,point.Y,point.Z)
			else:
				t.set_position(point.X,point.Y)
				t2.set_position(point.X,point.Y)

		if (pattern_row==False or (pattern_row[i]<.5 and pattern_mode==1) or (pattern_row[i]>.5 and pattern_mode==0)):
			# if this is the first pixel in a pattern
			if (t.get_pen()==False):
				# check to make sure you're not just at the beginning of a row
				if (i>0 or (i==0 and pattern_row[len(pattern_row)-1]<.5 and pattern_mode==0)):
					t.set_speed(5000)
					t.extrude(3)
					t.set_speed(speed)
				else:
					t.set_position_point(points[len(pattern_row)-1])
					t.pendown()

			t.pendown()
			t.set_speed(speed)
			if (follow_z):
				t.set_position(point.X,point.Y,point.Z)
				t2.set_position(point.X,point.Y,point.Z)
			else:
				t.set_position(point.X,point.Y)
				t2.set_position(point.X,point.Y)

			# if this is the last pixel in a pattern
			if (pattern_row!=False and i<len(pattern_row)-1 and ((pattern_row[i+1]>.5 and pattern_mode==1) or (pattern_row[i+1]<.5 and pattern_mode==0))):
				t.set_speed(5000)
				t.extrude(2)
				t.extrude(-1)
				t.set_speed(speed)
			if (pattern_row!=False and i==len(pattern_row)-1 and ((pattern_row[0]>.5 and pattern_mode==1) or (pattern_row[0]<.5 and pattern_mode==0))):
				t.set_speed(5000)
				t.extrude(2)
				t.extrude(-1)
				t.set_speed(speed)
		else:
			t.penup()
			t.set_speed(speed*2)
			if (follow_z):
				t.set_position(point.X,point.Y,point.Z)
			else:
				t.set_position(point.X,point.Y,t.get_z())
		i+=1
	if (closed and pattern_row==False):
		t.set_position_point(points[0])
	t.set_speed(speed)


def find_curve_rotation(outer_curve, inner_curve):
	outer_points = rs.DivideCurve(outer_curve, 20)
	inner_points = rs.DivideCurve(inner_curve, 20)
	closest=rs.CurveClosestPoint(inner_curve,outer_points[9])
	closest_point = rs.EvaluateCurve(inner_curve, closest)
	vector0 = rs.AddPoint(closest_point.X, closest_point.Y,0)
	vector1 = rs.AddPoint(inner_points[9].X, inner_points[9].Y,0)
	angle=rs.VectorAngle(vector0,vector1)
	return angle

def rotate_pattern(pattern_row,angle,step_shift=False):
	if (pattern_row is False):
		return False
	steps = len(pattern_row)
	steps_per_angle = steps/360.0
	if (step_shift is False):
		step_shift = int(steps_per_angle*angle)
	rotated_pattern_row = []
	index = 0
	for i in range (step_shift,len(pattern_row)+step_shift):
		ii = i%len(pattern_row)
		rotated_pattern_row.append(pattern_row[ii])
	return rotated_pattern_row


def pixel_size(curve,pattern_row):
	length = rs.CurveLength(curve)
	n_pixels = len(pattern_row)
	p_size = length/n_pixels
	# print("pixel size: " +str(p_size))
	return p_size

def pad_pattern(pattern_row, pad_beginning=4, pad_end=2, reverse=False):
	# pad pattern
	new_pattern_row=[]
	old_pattern_row=[]
	for i in range (0,len(pattern_row)):
		new_pattern_row.append(pattern_row[i])
		old_pattern_row.append(pattern_row[i])

	if (reverse):
		new_pattern_row.reverse()
		new_pattern_row = rotate_pattern(new_pattern_row,angle=0,step_shift=-1)
		old_pattern_row.reverse()
		old_pattern_row = rotate_pattern(old_pattern_row,angle=0,step_shift=-1)

	for i in range (pad_end,len(new_pattern_row)-pad_beginning-1):
		for j in range (-pad_end,pad_beginning+1):
			if (old_pattern_row[i+j]<=.5):
				new_pattern_row[i]=0

	if (new_pattern_row[0]<= .5):
		for j in range (len(new_pattern_row)-pad_end,len(new_pattern_row)):
			new_pattern_row[j]=0

	if (new_pattern_row[len(new_pattern_row)-1]<=.5):
		for j in range (0,pad_beginning):
			new_pattern_row[j]=0

	return new_pattern_row

def follow_curve_pattern_only(t, curve=False, points=False, steps=100, number_walls=1, pattern_row=False, reverse=False):

	if (curve is False and points is False):
		print("Fail. Need to supply a curve or a list of points")
		return

	new_pattern_row = pad_pattern(pattern_row, pad_beginning=3, pad_end=2,reverse=reverse)	

	# find the first pattern pixel
	first_pixel = first_pattern_pixel(new_pattern_row)

	# if there's no pattern (even if there is a pattern_row), return
	if (first_pixel==-1):
		return

	# actually print the pattern
	t.lift(3)
	t.penup()
	t.set_extruder(1)

	if (points is False):
		curve = get_offset_curve(curve,t.get_extrude_width()*number_walls*.3)
		points = rs.DivideCurve (curve, steps=steps)

	if (reverse):
		points.reverse()

	# extrude some at first pattern pixel to get ready
	speed = t.get_speed()
	t.penup()
	t.set_position_point(points[first_pixel])
	t.set_speed(3000)
	t.extrude(15)
	t.set_speed(speed)

	follow_points (t,points,closed=True,pattern_row=new_pattern_row,pattern_mode=1)
	
	t.penup() # don't extrude between walls
	t.set_extruder(0)
	t.lift(3)


def follow_curve_loops(t,curve,num_loops,loop_width=.5, loop_length=4, offset=0, steps=200):
	# will make evenly spaced loops around curve
	
	steps_per = int(steps/(num_loops))
	steps = steps_per*num_loops

	#loop width is given as percentage of loop
	loop_steps = int(loop_width*steps_per)
	space_steps = steps_per-loop_steps

	#offset is given as percentage of loop
	if (offset>0):
		offset=int(steps_per*offset)

	offset=offset%steps_per

	print("number of loops: " +str(num_loops))
	print("offset: " +str(offset))
	print("steps around: " +str(steps))
	print("steps per loop and space: " +str(steps_per))
	print("steps per loop: " +str(loop_steps))
	print("steps per space: " +str(space_steps))
	print("")

	points = rs.DivideCurve (curve, steps)
	dtheta = 360.0/steps

	t2=ExtruderTurtle()
	t2.penup()
	t.penup()

	t2.set_position(points[len(points)-1].X,points[len(points)-1].Y,points[len(points)-1].Z)

	flag=False
	loop_count=0

	speed = t.get_speed()
	# t.set_speed(800)

	for i in range(offset,len(points)+offset+1):
		index = i%len(points)
		t2.set_position(points[index].X,points[index].Y,points[index].Z)

		#middle of loop
		if (i%steps_per==(loop_steps/2+offset) and flag==True):
			t2.right(90)
			t2.forward(loop_length)
			t.set_position_point(t2.get_position())
			t2.back(loop_length)
			t2.left(90)

		#end of loop with no space
		if (i%steps_per==offset and flag==True):
			# print("ending a no space loop")
			t2.right(90)
			t2.forward(loop_length)
			t.set_position_point(t2.get_position())
			t.set_position(points[index].X,points[index].Y,points[index].Z)
			t2.back(loop_length)
			t2.left(90)
			# move in a bit to make sure you catch the wall
			t2.left(90)
			t2.forward(t.get_extrude_width())
			t.set_position_point(t2.get_position())
			t2.back(t.get_extrude_width())
			t2.right(90)
			flag=False
			# print("end loop " +str(loop_count) +" at: " +str(i))
			loop_count+=1

		#end of normal loop
		if ((i%steps_per==loop_steps+offset or i%steps_per==(loop_steps+offset)%steps_per) and flag==True):
			t2.right(90)
			t2.forward(loop_length)
			t.set_position_point(t2.get_position())
			t.set_position(points[index].X,points[index].Y,points[index].Z)
			t2.back(loop_length)
			t2.left(90)
			# move in a bit to make sure you catch the wall
			t2.left(90)
			t2.forward(t.get_extrude_width())
			t.set_position_point(t2.get_position())
			t2.back(t.get_extrude_width())
			t2.right(90)
			flag=False
			# print("end loop " +str(loop_count) +" at: " +str(i))
			# print("loop_width + offset " +str(loop_width+offset))
			# print("i mod steps_per " +str(i%steps_per))
			loop_count+=1

		#beginning of loop
		if (i%steps_per==offset and flag==False and loop_count<num_loops):
			# move in a bit to make sure you catch the wall
			t2.left(90)
			t2.forward(t.get_extrude_width())
			t.set_position_point(t2.get_position())
			t.pendown()
			if (loop_count==0):
				t2.forward(1)
				t.set_position_point(t2.get_position())
				t.extrude(30)
				t2.back(1)
			t2.back(t.get_extrude_width())
			t2.right(90)
			# position on wall
			t.set_position(points[index].X,points[index].Y,points[index].Z)
			# begin loop
			t2.right(90)
			t2.forward(loop_length)
			t.set_position_point(t2.get_position())
			flag=True
			# print("begin loop " +str(loop_count) +" at: " +str(i))

	t2.set_position(points[index].X,points[index].Y,points[index].Z)
	t.set_position_point(t2.get_position())


	# t.set_speed(speed)
	return t2.get_lines() 
