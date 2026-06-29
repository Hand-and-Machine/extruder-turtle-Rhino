import Rhino.Geometry as geom
import rhinoscriptsyntax as rs
import scriptcontext as sc
import ExtruderTurtle as e
import operator as op
import math
import random
import extruder_turtle
import pattern_slicing as ps
from extruder_turtle import *


def first_point_on_curve(curve):
    points = rs.DivideCurve(curve,100)
    return points[0]

def slice_at_z (shape, z):
    bounding_box = rs.BoundingBox(shape)
    plane = rs.WorldXYPlane()
    # moved_plane = rs.MovePlane(plane, bounding_box[0])
    moved_plane = rs.MovePlane(plane, [bounding_box[0].X, bounding_box[0].Y, z])
    # success, curves, points = geom.Intersect.Intersection.BrepPlane(shape, moved_plane, 0.1)
    surface = rs.AddPlaneSurface(moved_plane, 1000.0, 1000.0)
    curves = rs.IntersectBreps(surface,shape)
    rs.DeleteObject(surface)
    return curves

def non_planar_points_along_shape (t,shape,n=5,az=1,double_wall=False,function="sine",slope=0,begin=0,steps=100):
    theta_inc = 360.0/steps
    zs = []
    slices = []
    xy_points = []
    non_planar_points = []
    t.penup()
    if (function=="sine"):
        begin=0
    for i in range (0+begin,steps+begin):
        if (function=="sine"):
            z = t.getZ() + az*math.sin(n*math.radians(i*theta_inc))
        elif(function=="tilt"):
            if (i<(begin+steps/2)):
                z = t.getZ() + slope
            else:
                z = t.getZ() - slope
        else:
            print("no function!")
        slice = slice_at_z(shape,z)
        slices.append(slice)
        if (slice is not None):
            points = rs.DivideCurve(slice,steps)
            point_ref=rs.CurveClosestPoint(slice, points[i%steps])
            point = rs.EvaluateCurve(slice, point_ref)
            non_planar_points.append(rs.AddPoint(point.X,point.Y,z))
        else:
            print("no slice!")
            return non_planar_points
    return non_planar_points

def slice_shape(shape, layer_height=1.0, debug=False):
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

    if (debug is True):
        print("layers: " +str(len(shape_slices_layer)))
    return shape_slices_layer

def get_offset_curve (curve, distance):
    if (rs.IsCurveClosable(curve)):
        point = rs.CurveAreaCentroid(curve)[0]
    else:
        # create a new closed curve and find the center of that
        points = rs.DivideCurve(curve,20)
        points.append(points[0]) 
        closed_curve = rs.AddCurve(points)
        point = rs.CurveAreaCentroid(closed_curve)[0]

    offset_curve = rs.OffsetCurve(curve, point, distance)
    return offset_curve

def get_offset_curves (curve, distance):
    if (rs.IsCurveClosable(curve)==False):
        print("Can't get offsets for an open form.")
        return

    point = rs.CurveAreaCentroid(curve)[0]
    next_curve=True
    count=0

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
    if (distance>math.sqrt(a/5)):
        # print("offset end condition curve area")
        return []

    next_curve_list=rs.OffsetCurve(curve, point, distance=distance,style=3)
    if (not(next_curve_list)):
        # print("couldn't find any more offsets")
        return []
    try:
        for i in range (0,len(next_curve_list)):
            # add current offset curve to list:
            # find new offsets for current offset:
            curve_list = curve_list + [next_curve_list[i]]+recursive_offset(next_curve_list[i],curve_list,distance)
    except Exception as e:
        print("exception in recursive offset")
        print(e)
        print(len(next_curve_list))

    return curve_list


def bottom_layer (t, bottom_curve,offset_first_curve=False,stop_radius=False):
    bottom_layer=[]
    if (rs.IsCurveClosed(bottom_curve)==False):
        print("Can't create bottom for an open form.")
        return

    point = rs.CurveAreaCentroid(bottom_curve)[0]

    if (offset_first_curve is True):
        bottom_curve_new = get_offset_curve(bottom_curve,t.get_extrude_width())
        bottom_curve = bottom_curve_new
    
    point = first_point_on_curve(bottom_curve)
    t.set_position_point(point)
    t.extrude(5)

    bottom_curves=get_offset_curves(bottom_curve,t.get_extrude_width())
    bottom_layer = bottom_layer + [follow_curve(t,bottom_curve)]
    for c in range (0,len(bottom_curves)):
        bottom_layer = bottom_layer + [follow_curve(t,bottom_curves[c])]
        if (stop_radius is not False):
            point0 = first_point_on_curve(bottom_curves[c])
            point1 = rs.CurveAreaCentroid(bottom_curves[c])[0]
            d = rs.Distance(point1,point0)
            if(d is not None and d<=(stop_radius+t.get_extrude_width())):
                return bottom_layer
        t.penup()

    # t.lift(5)
    return bottom_layer


def slice_turtle (t,shape, number_walls=1, bottom_layers=0, pattern=False):
    t.write_gcode_comment("**************************************************")
    t.write_gcode_comment("******* file generated by Extruder Turtle ********")
    t.write_gcode_comment("****** python implementation: Leah Buechley ******")
    t.write_gcode_comment("************** 2023 - present ********************")
    t.write_gcode_comment("**************************************************")
    layer_height = t.get_layer_height()
    shape_slices = slice_shape(shape,layer_height=layer_height)
    # for all slices in shape

    for i in range (0,len(shape_slices)):
        k=0
        reverse=False
        if (pattern is not False and i>bottom_layers):
            # find correct vertical index into pattern
            ratio = len(pattern)/len(shape_slices)
            pattern_index = int(round(i*ratio,0))
            pattern_row = pattern[pattern_index]
            if (i%2==0):
                reverse=True
        else:
            pattern_row=False

        while (k<len(shape_slices[i])):
        # for all branches in current slice
            slice0 = shape_slices[i][k] # current slice

            if (i<bottom_layers and rs.IsCurveClosed(slice0)):
                bottom_layer(t,slice0)
            else:
                print("layer: " + str(i))
                follow_curve(t,slice0,number_walls=number_walls,pattern_row=pattern_row,reverse=reverse)
            k+=1
def randomize_points(points):
    new_points = []
    num = len(points)
    r = random.randint(0,len(points))
    while(r%4!=0):
        r-=1
    for i in range (r,len(points)+r):
        index = i%len(points)
        new_points.append(points[index])
    return new_points, r


def follow_curve(t, curve, number_walls=1, pattern_row=False, reverse=False, randomize=False, overlap=0):
    speed=t.get_speed()
    if (pattern_row is not False):
        steps = len(pattern_row)
        points = rs.DivideCurveEquidistant(curve, steps)
    else:
        resolution = 1.0 # use a resolution of 1 point per mm
        points = rs.DivideCurveEquidistant(curve, resolution) # create points resolution apart to find correct #
        steps = len(points)
    closed = rs.IsCurveClosed(curve)
    wall = 0
    curve0=curve
    walls = find_walls(t,curve,number_walls)
    walls.reverse() # inner walls first, outer walls last

    if (reverse and number_walls==1):
        rs.ReverseCurve(curve)

    # check to see if the inner walls are significantly rotated
    # if they are, rotate the pattern to align with the wall rotation
    rotated_pattern_row = pattern_row   
    if (len(walls)>1):
        angle = ps.find_curve_rotation(walls[len(walls)-1],walls[len(walls)-2])
        if (angle>1):
            # print("rotating pattern")
            rotated_pattern_row = ps.rotate_pattern(pattern_row,angle)

    # rs.RotateObject(inner_curve,[0,0,t.getZ()],-angle)


    for i in range (0,len(walls)):
        # print("\t wall: " +str(i))
        curve = walls[i]
        if (curve):
            if (pattern_row is not False):
                steps = len(pattern_row)
            else:
                points = rs.DivideCurveEquidistant(curve, resolution) # create points resolution apart to find correct #
                steps = len(points)
            points = rs.DivideCurve (curve, steps)
        else:
            #if offset fails, just return
            print("Couldn't create an offset curve to follow at wall: " +str(wall+1))
            return()
        if (i==len(walls)-1 and pattern_row is not False): # outer wall with pattern
            # print("\t outer wall with pattern")
            follow_points(t,points,closed=closed,pattern_row=rotated_pattern_row)
            # ps.follow_pattern_curve_clean_edges(t,curve,pattern_row=pattern_row)
        else: 
            if (pattern_row is not False): # inner wall with pattern, use adjusted pattern row
                # pattern_row_inner = pad_pattern(pattern_row,pad_beginning=1,pad_end=1)
                follow_points(t,points,closed=closed,pattern_row=rotated_pattern_row)
            else: # inner or outer wall without pattern
                if (randomize):
                    original_points = points
                    new_points,r = randomize_points(points)
                    t.penup()
                    t.lift(t.get_layer_height())
                    t.set_speed(3*speed)
                    t.set_position(original_points[r-1].X, original_points[r-1].Y)
                    t.extrude(1)
                    t.set_speed(speed)
                    points = new_points
                t.set_speed(3*speed)
                t.set_position_point(points[0])
                t.set_speed(speed)
                follow_points(t,points,closed=closed,pattern_row=False)
                

        if (closed==False): # if curve is not closed, lift pen
            t.penup()
        else: # close curve
            t.set_position_point(points[0])
            if (overlap!=0):
                t.set_position_point(points[overlap])
            # t.set_position_point(points[3])
            # if (pattern_row==False):
            #   t.set_position(points[0].X,points[0].Y,points[0].Z) # close curve
        t.penup() # don't extrude between walls

    # if there's no pattern, return
    if (pattern_row==False):
        return

    # ***************************************************
    # ********************* PATTERN *********************
    # ***************************************************

    # ps.follow_curve_pattern_only(t, curve, number_walls=1, pattern_row=rotated_pattern_row, reverse=reverse)

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


def follow_points(t,points,follow_z=True,closed=False,pattern_row=False,pattern_mode=0):
    # pattern mode 0 = structure (clay)
    # pattern mode 1`= decoration (glass)
    speed = t.get_speed()
    if (pattern_row is not False):
        if (len(points)!=len(pattern_row)):
            print("Number of points " +str (len(points)) + " doesn't match pattern size " +str(len(pattern_row)))
            return

    first_pixel = ps.first_pattern_pixel(pattern_row)
    # if (first_pixel==6):
    #   print("trying to fix bug")
    #   first_pixel=0
    #   t.set_position_point(points[len(points)-1])
    #   t.pendown()
    # print("first pixel: " +str(first_pixel))
    if (first_pixel==-1):
            pattern_row=False # there is no pattern, even if you have an array
            first_pixel=0

    for i in range (first_pixel,len(points)+first_pixel):
        index = i%len(points)
        point = points[index]
        # if (index==first_pixel):
        #   t.penup()
        #   t.set_position_point(points[index])
        if (pattern_row==False or (pattern_row[index]<=.5 and pattern_mode==1) or (pattern_row[index]>=.5 and pattern_mode==0)):
            # change to pattern speed
            if (t.get_speed()>speed):
                t.set_speed(speed)
            # if pen is currently up, it means this is the first pixel
            if (t.get_pen()==False):
                # set your position and extrude a bit
                if (index>0):
                    t.set_position_point(points[index-1])
                else:
                    t.set_position_point(points[index])
                if (pattern_row!=False):
                    t.extrude(4)        
            # put pen down for pattern  
            t.pendown()
            t.set_position_point(points[index])
        else:
            t.penup()
            if(i!=first_pixel):
                if (t.get_speed()==speed):
                    t.set_speed(2*speed)
            t.set_position_point(points[index])
        i+=1

    if (closed and pattern_row==False):
        t.set_position_point(points[0])
    t.set_speed(speed)


def find_walls(t,curve,number_walls):
    walls = []
    walls.append(curve)
    wall_number=1
    while (wall_number<number_walls):
        inner_curve = get_offset_curve(curve,t.get_extrude_width())
        walls.append(inner_curve)
        curve = inner_curve
        wall_number+=1
    return walls
