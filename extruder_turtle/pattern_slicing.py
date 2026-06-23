import Rhino.Geometry as geom
import rhinoscriptsyntax as rs
import ExtruderTurtle as e
import operator as op
import math
import random
import extruder_turtle
import slicer_utilities as su
from extruder_turtle import *


def first_pattern_pixel(pattern_row,pattern_mode=0):
	if (pattern_row is False):
		return -1

	first_pattern_pixel=False
	for i in range (0,len(pattern_row)):
		if (first_pattern_pixel==False and print_pixel_at_index(pattern_row, i, pattern_mode=pattern_mode)):
			first_pattern_pixel=i
			break

	if (first_pattern_pixel is False):
		return -1
	
	# print("first pattern pixel before adjustment: " +str(first_pattern_pixel))
	# check to see if the pattern began before 0
	j=len(pattern_row)-1
	if (first_pattern_pixel==0):
		while (print_pixel_at_index(pattern_row, j, pattern_mode=pattern_mode) and j>=0):
			first_pattern_pixel=j
			j-=1

	# print("first pattern pixel after adjustment: " +str(first_pattern_pixel))

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

def is_pattern_empty(pattern_row,extruder=0):
	# 0 is pattern, 1 is nopattern
	# 0 is printed with extruder 0, 1 is printed with extruder 1 
	if (pattern_row==False):
		if (extruder==0):
			return False
		else:
			return True
			
	pattern_empty = True
	for i in range (len(pattern_row)):
		if (extruder==0 and pattern_row[i]>=.5):
			pattern_empty = False
			return pattern_empty
		if (extruder==1 and pattern_row[i]<.5):
			pattern_empty = False
			return pattern_empty
	return pattern_empty

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

def print_pixel_at_index(pattern_row, index, pattern_mode=0):
	if (index>len(pattern_row) or index<0):
		print("bad index to print pixel at index: " +str(index))
		return False
	if ((pattern_row[index]<.5 and pattern_mode==1) or (pattern_row[index]>=.5 and pattern_mode==0)):
		return True
	else:
		return False

def at_beginning_of_pattern(t,pattern_row, index, pattern_mode=0):
	if (index<0):
		new_index = len(pattern_row)-index
		index = new_index
	if (print_pixel_at_index(pattern_row,index,pattern_mode=pattern_mode)):
		if (t.get_pen() is False):
			return True 
		else:
			return False

def at_end_of_pattern(t,pattern_row, index, pattern_mode=0):
	if (index>len(pattern_row)):
		new_index = index
		index = new_index
	if (print_pixel_at_index(pattern_row,index,pattern_mode=pattern_mode) is False):
		if (t.get_pen() is True):
			return True 
		else:
			return False

def distance_per_pixel(points,pattern_row):
	return rs.Distance(points[0],points[1])

def distance_next_pattern(points,pattern_row,index,pattern_mode=0):
	# if pattern mode is 0, distance across next stretch of 1s
	# if pattern mode is 1, distance across next stretch of 0s
	distance=0
	if ((pattern_mode==0 and pattern_row[index]==0) or (pattern_mode==1 and pattern_row[index]==1)):
			return distance
	i=index
	count=0
	while(count<len(points)):
		current_point=points[i]
		if ((i+1)<len(points)-1):
			next_index=i+1
		else:
			next_index=0
		next_point=points[next_index]
		distance = distance + rs.Distance(current_point,next_point)
		try:
			if ((pattern_mode==0 and pattern_row[next_index]==0) or (pattern_mode==1 and pattern_row[next_index]==1)):
				return distance
		except Exception as e:
			print("exception in distance")
			print("index: " +str(i))
			print("next index: " +str(next_index))
			print("pattern length: " +str(len(pattern_row)))
			print("num points: " +str(len(points)))
		count+=1
		i+=1
		if (i>=len(points)):
			i=0
	return -1 

# determine if there are any long distances in the 
# pattern or should entire pattern be skipped
def check_small_pattern_distances(t, points, pattern_row, pattern_mode=0,d_threshold=5):

	for i in range (len(pattern_row)):
		if (at_beginning_of_pattern(t,pattern_row,i,pattern_mode=pattern_mode)):
			d = distance_next_pattern(points,pattern_row,index=i,pattern_mode=pattern_mode)
			if (d>d_threshold):
				return False

	return True


def follow_pattern_curve_clean_edges(t,curve,pattern_row=False,pattern_mode=0,number_walls=1,reverse=False):
	# if there is no pattern, just follow the curve and return
	if (pattern_row==False or is_pattern_empty(pattern_row,extruder=1-pattern_mode)):
		su.follow_curve(t,curve,number_walls=number_walls,pattern_row=False)
		return

	speed=t.get_speed()
	fast_speed = t.get_speed()*1.5
	extrude_rate=t.get_extrude_rate()
	if (rs.IsPolyline(curve)):
		points = rs.PolylineVertices(curve)
		if (len(points)!=len(pattern_row)):
			print("got polyline but points don't match")
			print("polyline points: " +str(len(points)))
			print("pattern length: " +str(len(pattern_row)))
			points = rs.DivideCurve(curve,len(pattern_row))
	else:
		points = rs.DivideCurve(curve,len(pattern_row))
	if (number_walls==1):
		offset = t.get_extrude_width()/2
	else:
		offset = t.get_extrude_width()
	inner_curve = su.get_offset_curve(curve,offset)
	inner_points = rs.DivideCurve(inner_curve,len(pattern_row))
	travel_curve = su.get_offset_curve(inner_curve,offset*1.5)
	if (pattern_mode==1):
		travel_points = rs.DivideCurve(travel_curve,len(pattern_row))
	else:
		# travel points are not shifted in for clay
		# don't pull clay out of position with travel
		travel_points = rs.DivideCurve(inner_curve,len(pattern_row))

	if (reverse):
		points.reverse()
		inner_points.reverse()
		pattern_row.reverse()

	# check to see how far you have to move and lift up if necessary to avoid scraping
	# check distance in XY only
	first_pixel = first_pattern_pixel(pattern_row,pattern_mode=pattern_mode)
	first_point = points[first_pixel]
	current_position = t.get_position()
	current_point = rs.CreatePoint(current_position.X,current_position.Y,first_point.Z)
	# distance = rs.Distance(current_point,first_point)
	# if (distance>t.get_extrude_width()*2):
	# 	# print("lifting up before printing to travel: " +str(distance))
	# 	t.penup()
	# 	t.forward_lift(3,3)
	# 	t.set_position(travel_points[first_pixel].X,travel_points[first_pixel].Y)


	# pad pattern 
	# for clay only
	# to address under extrusion on inner walls & overlap on outer walls
	if (pattern_mode==0 and distance_per_pixel(points,pattern_row)<t.get_extrude_width()):
		pattern_row = pad_pattern(pattern_row,pad_beginning=1,pad_end=1)
		# need to refind first pixel
		first_pixel = first_pattern_pixel(pattern_row,pattern_mode=pattern_mode)

	# inner wall
	t.penup()
	d_threshold=t.get_extrude_width()*2.25
	print_pattern_block = True
	flag = False
	if (number_walls>1 and check_small_pattern_distances(t,inner_points,pattern_row,pattern_mode=pattern_mode,d_threshold=d_threshold)==False):
		for p in range (first_pixel, len(points)+first_pixel):
			i = p%len(points)
			if (pattern_mode==1 and p<.25*len(points)):
				t.set_extrude_rate(extrude_rate*1.5)
			elif(pattern_mode==1 and p<.8*len(points)):
				t.set_extrude_rate(extrude_rate*1.25)
			else:
				t.set_extrude_rate(extrude_rate)
			# first pixel is garunteed to be a print pixel
			if (p==first_pixel):
				d = distance_next_pattern(inner_points,pattern_row,index=i,pattern_mode=pattern_mode)
				if (d>d_threshold):
					if (i+1<len(inner_points)):
						t.set_position_point(inner_points[i+1])
					else:
						t.set_position_point(inner_points[i])
					t.pendown()
					t.extrude(6)
			if (print_pixel_at_index(pattern_row,i,pattern_mode=pattern_mode)):
				if (at_beginning_of_pattern(t,pattern_row,i,pattern_mode=pattern_mode)):
					# first, check to see if the pattern block is large enough to print
					d = distance_next_pattern(inner_points,pattern_row,index=i,pattern_mode=pattern_mode)
					if (d>d_threshold):
						print_pattern_block = True
					else:
						# print("should be skipping this inner block")
						print_pattern_block = False
						t.penup()
						t.set_position_point(inner_points[i])
						t.set_speed(fast_speed)
					# if the pattern block is large enough to print
					# move to the first pixel of the pattern
					if (print_pattern_block):
						t.penup()
						t.set_position_point(inner_points[i])
						t.set_speed(speed)
						t.set_position_point(inner_points[i])
						if (i+1<len(inner_points)):
							t.set_position_point(inner_points[i+1]) # set penup position to next point
						else:
							print(i+1,len(inner_points))
						# extrude a little at the beginning of a pattern block
						t.extrude(3) 
						if (pattern_mode==1): # extrude more for glass
							t.extrude(2)
					flag=False # set to false at beginning o pattern block

				if (flag):
					try:
						if (i+1<len(pattern_row) and at_end_of_pattern(t,pattern_row,i+1,pattern_mode=pattern_mode)):
							t.set_position_point(inner_points[i])
							t.penup()
							t.set_position_point(inner_points[i])
						elif (i+1>=len(pattern_row) and at_end_of_pattern(t,pattern_row,0,pattern_mode=pattern_mode)):
							t.set_position_point(inner_points[i])
							t.penup()
							t.set_position_point(inner_points[i])
						elif (print_pattern_block):
							t.set_position_point(inner_points[i])
					except Exception as e:
						print(e)
						print("failed end of pattern. i+1: " +str(i+1))
						print("length of array: " +str(len(pattern_row)))
				else:
					flag=True # set to true after skipping the first pixel of a pattern block
					if (print_pattern_block):
						t.pendown()
			else:
				t.penup()
				t.set_speed(fast_speed)
	
	t.penup()

	# check to see how far you have to move and lift up if necessary
	first_point = points[first_pixel]
	current_position = t.get_position()
	current_point = rs.CreatePoint(current_position.X,current_position.Y,first_point.Z)
	# distance = rs.Distance(current_point,first_point)
	# if (distance>t.get_extrude_width()*2):
	# 	# print("lifting up before printing to travel to outer: " +str(distance))
	# 	t.penup()
	# 	t.forward_lift(3,3)
	# 	t.set_position(travel_points[first_pixel].X,travel_points[first_pixel].Y)

	# outer wall
	# your first position is an edge and will be printed
	# move to edge position and put pen down
	# t.set_position_point(inner_points[first_pixel])
	# t.pendown()
	for p in range (first_pixel, len(points)+first_pixel):
		i = p%len(points)
		# if (p==first_pixel):
		# 	t.set_position_point(travel_points[i])
		# 	t.set_position_point(inner_points[i])
		# 	t.extrude(5)
		if (print_pixel_at_index(pattern_row,i,pattern_mode=pattern_mode)):
			if (at_beginning_of_pattern(t,pattern_row,i,pattern_mode=pattern_mode)):
				t.penup()
				t.set_position_point(travel_points[i])
				t.set_speed(speed)
				t.set_position_point(inner_points[i])
				t.extrude(3) # extrude a little at the beginning of a pattern block
				if (pattern_mode==1):
					t.extrude(3)
			t.pendown()
			t.set_position_point(points[i])
		else:
			if (at_end_of_pattern(t,pattern_row,i,pattern_mode=pattern_mode)):
				t.set_position_point(points[i])
				t.set_position_point(inner_points[i])
				t.extrude(1) # extrude a little at the end of a pattern block
				t.penup()
				t.set_position_point(travel_points[i])
				t.set_speed(fast_speed)
			t.penup()
		if (i==first_pixel):
			point0 = t.get_position()
	
	# print("print pixel e1: " +print_pixel_at_index(pattern_row,first_pixel,pattern_mode=pattern_mode))	
	# if (rs.IsCurveClosed(curve) and print_pixel_at_index(pattern_row,first_pixel,pattern_mode=pattern_mode)):
	# 	# print("ending form with pen: " +str(t.get_pen()))
	# 	# print("print pixel: " +str(print_pixel_at_index(pattern_row,first_pixel,pattern_mode=pattern_mode)))
	# 	# t.pendown()
	# 	t.set_position_point(points[first_pixel])
	
	t.penup()




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

def pad_pattern(pattern_row, pad_beginning=0, pad_end=0, reverse=False):
	# pad pattern
	new_pattern_row=[]
	old_pattern_row=[]
	for i in range (0,len(pattern_row)):
		new_pattern_row.append(pattern_row[i])
		old_pattern_row.append(pattern_row[i])

	if (reverse):
		new_pattern_row.reverse()
		# new_pattern_row = rotate_pattern(new_pattern_row,angle=0,step_shift=-1)
		old_pattern_row.reverse()
		# old_pattern_row = rotate_pattern(old_pattern_row,angle=0,step_shift=-1)

	# pad at beginning
	for i in range (0,len(pattern_row)):
		if (old_pattern_row[i]<=.5):
			for j in range(-pad_beginning,0):
				if (j+i>=0):
					new_pattern_row[i+j]=0
				else:
					new_pattern_row[len(pattern_row)+(i+j)]=0

	# pad at end
	for i in range (0,len(pattern_row)):
		if (old_pattern_row[i]<=.5):
			for j in range(0,pad_end+1):
				if (j+i<len(pattern_row)):
					new_pattern_row[i+j]=0
				else:
					new_pattern_row[j-(len(pattern_row)-i)]=0

	return new_pattern_row

def follow_curve_pattern_only(t, curve=False, points=False, steps=100, number_walls=1, pattern_row=False, reverse=False):

	if (curve is False and points is False):
		print("Fail. Need to supply a curve or a list of points")
		return

	new_pattern_row = pad_pattern(pattern_row, pad_beginning=0, pad_end=0,reverse=reverse)	

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
		curve = su.get_offset_curve(curve,t.get_extrude_width()*number_walls*.3)
		if (pattern_row is not False):
			steps = len(pattern_row)
		points = rs.DivideCurve (curve, steps)

	if (reverse):
		points.reverse()

	# # extrude some at first pattern pixel to get ready
	# speed = t.get_speed()
	# t.penup()
	# t.set_position_point(points[first_pixel])
	# t.set_speed(3000)
	# t.extrude(15)
	# t.set_speed(speed)

	su.follow_points (t,points,closed=True,pattern_row=new_pattern_row,pattern_mode=1)
	
	t.penup() # don't extrude between walls
	# t.set_extruder(0)
	# t.lift(3)


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
