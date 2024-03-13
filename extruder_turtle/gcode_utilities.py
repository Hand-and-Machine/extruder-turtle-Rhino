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
                    # if you're starting from a travel move
                    # add the travel move to travel_lines
                    if (len(travel_points)>1):
                        #print("adding travel line")
                        line = rs.AddPolyline(travel_points)
                        travel_lines.append(line)
                        section_length = rs.CurveLength(line)
                        if (section_length>travel_length):
                            #print("length of travel at line " +str(i) +" is: " +str(rs.CurveLength(line)))
                            number_true_travels +=1
                            true_travel_lines.append(line)
                            true_travel_length = true_travel_length+section_length
                        else:
                            number_all_travels +=1
                        travel_points=[]
                    # get next point
                    point = get_point_from_gcode_line(r,relative_position,current_z)
                    if (point!=False):
                        if (relative_position):
                            point = point+previous_point
                            previous_point = point
                        else:
                            if (point.Z>0):
                                current_z =point.Z
                        # add point to list of print points
                        print_points.append(point)

                elif (r[0]=='G0'): # travel command
                    # if you're starting from a print movement
                    # add the print move to print_lines
                    if (len(print_points)>1):
                        #print("adding print line at row: " + str(i))
                        print_lines.append(rs.AddPolyline(print_points))
                        print_points = []
                    # get next point
                    point = get_point_from_gcode_line(r,relative_position,current_z)
                    if (point!=False):
                        if (relative_position):
                            point = point+previous_point
                            previous_point = point
                        else:
                            if (point.Z>0):
                                current_z =point.Z
                        travel_points.append(point)
                            

    if (len(print_points)>1):
        print_lines.append(rs.AddPolyline(print_points))
    file.close()
    print("The number of travels with a length of at least: " +str(travel_length) +" mm is: " +str(number_true_travels))
    print("The total length of these travels is: " +str(round(true_travel_length,0)))
    return print_lines, travel_lines, true_travel_lines, number_true_travels, true_travel_length

def data_parse(file, relative_position=True):
    exceptions = []
    data = []
    all_points = []
    extrusion = []
    travel_lines = []
    travel_points = []
    points = []
    all_points = []
    lines = []
    with open(file) as file:
        reader = csv.reader(file)
        i = 0
        previous_point = rs.CreatePoint(0,0,0)
        current_z = 0
        x = False
        y = False
        z = False
        for row in reader:
            i= i+1
            #try:
            if (len(row)>=1):
                r = row[0].split()
                if (r[0]=='G1' and len(r)>3): # format: G1 X Y 
                    travel_points = []
                    XX = r[1].split("X")
                    if (len(XX)>1):
                        x = float(XX[1])
                    YY = r[2].split("Y")
                    if (len(YY)>1):
                        y = float(YY[1])

                    if (len(r)>4): # format: G1 X Y Z
                        ZZ = r[3].split("Z")
                        #print("length of ZZ: " +str(len(ZZ)))
                        if (len(ZZ)>1):
                            z = float(ZZ[1])
                            #print("z: " +str(z))
                            current_z = z
                        EE = r[4].split("E")
                        #print("length of EE: " +str(len(EE)))
                        if (len(EE)>1):
                            e = float(EE[1])
                            extrusion.append(e)
                    else:
                        EE = r[3].split("E")
                        #print("length of EE: " +str(len(EE)))
                        if (len(EE)>1):
                            e = float(EE[1])
                            extrusion.append(e)
                    if (x!=False and y!=False):
                        if (relative_position):
                            if (z==False): z=0
                            current_point = rs.CreatePoint(x,y,z) + previous_point
                            previous_point = current_point
                        else:
                            if (z==False): z = current_z 
                            current_point = rs.CreatePoint(x,y,z)
                        points.append(current_point)
                        all_points.append(current_point)
                elif (r[0]=='G0'):
                    # G0 means travel move
                    # finish the non-traveling line
                    if (len(points)>1):
                        points.append(points[0])
                        lines.append(rs.AddPolyline(points))
                    # add travel line
                    try:
                        if (len(r)==3): # format: G0 X Y
                            XX = r[1].split("X")
                            x = float(XX[1])
                            YY = r[2].split("Y")
                            y = float(YY[1])
                            z = False
                        elif(len(r)>=4): 
                            if (relative_position): # format: G0 X Y Z (TRAvel slicer and turtle)
                                XX = r[1].split("X")
                                x = float(XX[1])
                                YY = r[2].split("Y")
                                y = float(YY[1])
                                ZZ = r[3].split("Z")
                                z = float(ZZ[1])
                                if (z<0):
                                    print("move z: " +str(z) + " to: " +str(current_point.Z+z) + " at line: " +str(i))
                            else: # format: G0 F X Y
                                f = r[1] #Cura specific, these lines include F command
                                XX = r[2].split("X")
                                x = float(XX[1])
                                YY = r[3].split("Y")
                                y = float(YY[1])
                                z = False
                                if (len(r) == 5): # format: G0 F X Y Z
                                    ZZ = r[4].split("Z")
                                    z = float(ZZ[1])
                                    current_z = z
                                    print("updated z")
                    except Exception as e:
                        print("problem in travel at row: "+str(i))
                        print(e)
                        print(r)
                    
                    if (relative_position):
                        if (z==False): z=0
                        current_point = rs.CreatePoint(x,y,z) + previous_point
                        if (z<0):
                            print("previous point: " +str(previous_point.Z))
                            print("current point: " +str(current_point.Z))
                        previous_point = current_point
                    else:
                        if (z==False): z = current_z 
                        current_point = rs.CreatePoint(x,y,z)
                        
                    if (len(points)>1):
                        travel_lines.append(rs.AddLine(points[len(points)-2], current_point))
                        travel_points.append(current_point)
                    else: 
                        #print("DEBUGGING*************************************")
                        #print("travel point: " + str(travel_points[len(travel_points)-1]))
                        #print("current point: " +str(current_point))
                        #print("previous point: " +str(previous_point))
                        #travel_lines.append(rs.AddLine(travel_points[len(travel_points)-1], current_point))
                        travel_points.append(current_point)
                    
                    #print("added travel line at: " +str(i))
                    points = []
            # except Exception as e:
            #     print("problem in file parsing at row: " +str(i))
            #     print(e)
            #     print(r)
            #     exceptions.append(e)
    file.close()
    return all_points, lines, travel_lines
