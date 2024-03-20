import rhinoscriptsyntax as rs
import math
import csv

def get_point_from_gcode_line(r, relative_position=True, current_z=0.0):
    #rs.CurrentView('Top')
    x=False
    y=False
    if (relative_position): z=0.0
    else: z=current_z

    for j in range (0,len(r)):
        if ('X' in r[j]):
            XX = r[j].split("X")
            x = float(XX[1])
        if ('Y' in r[j]):
            YY = r[j].split("Y")
            y = float(YY[1])
        if ('Z' in r[j]):
            ZZ = r[j].split("Z")
            z = float(ZZ[1])
        if ('E' in r[j]):
            EE = r[j].split("E")
            e = float(EE[1])
        if (';' in r[j]):
            break #stop searching if you hit a comment
    
    if (x is not False and y is not False):
        return rs.CreatePoint(x,y,z)
    else:
        return False

def parse_gcode(file, relative_position=True, travel_length=15):
    print_points = []
    print_lines = []
    travel_points = []
    travel_lines = []
    true_travel_lines = []
    number_true_travels = 0
    true_travel_length = 0.0
    number_all_travels = 0
    relative_position_flag = relative_position

    with open(file) as file:
        reader = csv.reader(file)
        i = 0
        previous_point = rs.CreatePoint(0.0,0.0,0.0)
        print_points.append(previous_point)
        current_z = 0
        for row in reader:
            i= i+1
            if (len(row)>=1): 
                r = row[0].split()
                # if you are parsing a relative position gcode file,
                # wait for relative position command before parsing
                if (relative_position and relative_position_flag):
                    print("relative position")
                    if (r[0]=='G91'):
                        relative_position_flag=False 
                elif (r[0]=='G1'): # normal printing command
                    point = get_point_from_gcode_line(r,relative_position,current_z)
                    if (point!=False):
                        if (relative_position):
                            point = point+previous_point
                        else:
                            if (point.Z>0):
                                current_z =point.Z
                        try:
                            current_line = rs.AddPolyline([previous_point,point])
                        except:
                            print ("error adding line at row: " +str(i))
                        print_lines.append(current_line)
                        previous_point = point

                elif (r[0]=='G0'): # travel command
                    point = get_point_from_gcode_line(r,relative_position,current_z)
                    if (point!=False):
                        if (relative_position):
                            point = point+previous_point
                        else:
                            if (point.Z>0):
                                current_z =point.Z
                        try:
                            current_line = rs.AddPolyline([previous_point, point])
                        except:
                            print ("error adding line at row: " +str(i))
                        section_length = rs.CurveLength(current_line)
                        if (section_length>travel_length):
                            number_true_travels +=1
                            true_travel_lines.append(current_line)
                            true_travel_length = true_travel_length+section_length
                        else:
                            number_all_travels +=1
                        travel_lines.append(current_line)
                        previous_point = point

    file.close()
    print("The number of travels with a length of at least: " +str(travel_length) +" mm is: " +str(number_true_travels))
    print("The total length of these travels is: " +str(round(true_travel_length,0)))
    return print_lines, travel_lines, true_travel_lines, number_true_travels, true_travel_length

