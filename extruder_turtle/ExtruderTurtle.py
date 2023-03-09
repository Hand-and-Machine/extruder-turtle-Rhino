import os
import math
import rhinoscriptsyntax as rs
__location__ = os.path.dirname(__file__)


class ExtruderTurtle:

    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.forward_vec = [1, 0, 0]
        self.left_vec = [0, 1, 0]
        self.up_vec = [0, 0, 1]
        self.use_degrees = True
        self.pen = True

        # GCODE writing and history tracking
        self.write_gcode = False
        self.track_history = True
        self.prev_points = [(self.x,self.y,self.z)]
        self.line_segs = []
        self.extrusion_history = []
        self.current_color = 0, 0, 0
        self.color_history = []
        self.tube_color = 0, 0, 0, 0, 0, 0 # r,g,b,tube_dist,volume,mass
        self.tube_color_history = [] 

        # file settings
        self.out_filename = False
        self.initseq_filename = False
        self.finalseq_filename = False
        self.printer = False
        self.out_file = False;
        self.initseq_file = False;
        self.finalseq_file = False;

        # printer and material settings
        self.nozzle_size = 0;
        self.extrude_width = 0;
        self.layer_height = 0;
        self.extrude_rate = 0;
        self.speed = 0;
        self.density = 0.0;
        self.resolution = False;

        # GCODE text formats
        self.G1xyze = "G1 X{x} Y{y} Z{z} E{e}"
        self.G1xyz = "G1 X{x} Y{y} Z{z}"
        self.G1xye = "G1 X{x} Y{y} E{e}"
        self.G1xy = "G1 X{x} Y{y}"
        self.G1e = "G1 E{e}"
        self.G1f = "G1 F{f}"
        self.G1z = "G1 Z{z}"
        self.G4p = "G4 P{p}"
        self.M0 = "M0"
        self.M104s = "M104 S{s}\nM109 S{s}"
        self.M140s = "M140 S{s}\nM190 S{s}"


    # set up Turtle and GCODE file
    def setup(self, x=0,
                    y=0,
                    z=0,
                    filename=False,
                    printer=False
                    ):
        
        if (filename):
            self.out_filename = filename
            self.write_gcode = True
            self.out_file = True;
            self.initseq_file = True;
            self.finalseq_file = True;
            self.finalseq_filename = os.path.join(__location__, "data/finalseq.gcode")
        if (printer):
            self.set_printer(printer)
        if (filename and printer):
            self.write_header_comments()
        #else:
            #print("Warning can't write file. No printer selected or filename given.")
            
        if self.track_history: self.prev_points = [(x,y,z)]

    # set printer parameters
    def set_printer(self,printer):
        if (printer=="Ender" or printer=="ender" or printer=="creatlity" ):
            if(self.out_file):
                self.initseq_filename = os.path.join(__location__, "data/initseqEnder.gcode") 
            self.nozzle = 0.2
            self.extrude_width = 0.4 
            self.layer_height = .2
            self.extrude_rate = 0.05 #mm extruded/mm
            self.speed = 1000 #mm/minute
            self.printer = "ender"
            self.resolution = .05
            self.x_size = 220
            self.y_size = 220
            gcode_decimal_places = 7
        elif (printer=="super" or printer=="3Dpotter" or printer=="3D Potter"  or printer=="3d potter"  or printer=="Super"):
            if(self.out_file):
                self.initseq_filename = os.path.join(__location__, "data/initseq3DPotter.gcode")
            self.nozzle = 3.0
            self.extrude_width = 3.4 #mostly for solid bottoms
            self.layer_height = 2.2
            self.extrude_rate = 3.0 #mm extruded/mm
            self.speed = 1000 #mm/minute = 16.6 mm/second
            self.printer = "3D Potter Super"
            self.resolution = 1.0
            self.x_size = 400
            self.y_size = 400
            self.print_head_size = 102 # 3 inches
        elif (printer=="micro" or printer=="3DpotterMicro" or printer=="3D Potter Micro"  or printer=="Micro"):
            if(self.out_file):
                self.initseq_filename = os.path.join(__location__, "data/initseq3DPotterMicro.gcode")
            self.nozzle = 3.0
            self.extrude_width = 3.4 #mostly for solid bottoms
            self.layer_height = 2.2
            self.extrude_rate = 3.0 #mm extruded/mm
            self.speed = 1000 #mm/minute = 16.6 mm/second
            self.printer = "3D Potter Micro"
            self.resolution = 1.0
            self.x_size = 280
            self.y_size = 265
            self.print_head_size = 77 # 3 inches
        elif (printer=="Eazao" or printer=="eazao"):
            if(self.out_file):
                self.initseq_filename = os.path.join(__location__, "data/initseqEazao.gcode")
            self.nozzle = 1.5
            self.extrude_width = 2.1
            self.layer_height = 1.0
            self.extrude_rate = 1.25 #mm extruded/mm
            self.speed = 1000 #mm/minute
            self.printer = "eazao"
            self.resolution = 1.0
            self.x_size = 150
            self.y_size = 150
            self.print_head_size = 64 # 2.5 inches
        else:
            print ("No printer set!! \nCheck the name of your printer and try again. \nWe support: super, micro, eazao, and ender")

        if(self.out_file):
            self.finalseq_filename = os.path.join(__location__, "data/finalseq.gcode")

    ###################################################################
    # GCODE and printer functions
    ###################################################################

    def print_parameters(self):
        print("printer: " +str(self.printer))
        print("nozzle size: " +str(self.nozzle))
        print("speed: " +str(self.speed))
        print("layer height: " +str(self.layer_height))
        print("extrude rate: " +str(self.extrude_rate))
        print("extrude width: " +str(self.extrude_width))

    def print_printer_information(self):
        print("printer: " +str(self.printer))
        print("nozzle size: " +str(self.nozzle))
        print("speed: " +str(self.speed))
        print("layer height: " +str(self.layer_height))
        print("extrude rate: " +str(self.extrude_rate))
        print("extrude width: " +str(self.extrude_width))

    def write_header_comments(self):
        if self.write_gcode:
            self.out_file = open(self.out_filename, 'w+')

            # write printer information to top of file
            self.out_file.write("; *************************************************\n")
            self.out_file.write("; *************************************************\n")
            self.out_file.write("; ******* File generated by Extruder Turtle *******\n")
            self.out_file.write("; ******* written by Leah Buechley and  ***********\n")
            self.out_file.write("; ******* and Franklin Pezutti-Dyer ***************\n")
            self.out_file.write("; ******* Hand and Machine Lab, UNM, 2022 *********\n")
            self.out_file.write("; *************************************************\n")
            self.out_file.write("; *************************************************\n")
            self.out_file.write("; *************** Printer parameters **************\n")
            self.out_file.write("; Printer: " + self.printer + "\n")
            self.out_file.write("; Nozzle size: " + str(self.nozzle) + "\n")
            self.out_file.write("; Extrude width: " + str(self.extrude_width) + "\n")
            self.out_file.write("; Layer height: " + str(self.layer_height) + "\n")
            self.out_file.write("; Extrude rate: " + str(self.extrude_rate) + "\n")
            self.out_file.write("; Speed: " + str(self.speed) + "\n")

            # write printer initialization sequence 
            self.initseq_file = open(self.initseq_filename, 'r')
            self.do(self.initseq_file.read().format(**locals()))
            self.initseq_file.close()
            self.set_speed(self.speed);
            self.out_file.write("; *************** End printer initialization **************\n")

    def name(self, filename):
        self.out_filename = filename

    def write_gcode_comment(self, comment):
        if (self.out_file):
            self.out_file.write("; " + comment + "\n")

    def finish(self):
        if self.write_gcode:
            self.finalseq_file = open(self.finalseq_filename, 'r')
            self.do(self.finalseq_file.read())
            self.finalseq_file.close()
            self.out_file.close()

    def do(self, cmd):
        if self.write_gcode:
            self.out_file.write(cmd + "\n")

    def set_extrude_rate(self, extrude_rate):
        self.write_gcode_comment("Changed extrude rate to: " +str(extrude_rate))
        self.write_gcode_comment("*************************************************************")
        self.extrude_rate = extrude_rate

    def get_extrude_rate(self):
        return self.extrude_rate

    def set_extrude_width(self, extrude_width):
        self.extrude_width = extrude_width

    def get_extrude_width(self):
        return self.extrude_width

    def set_resolution(self, resolution):
        self.resolution = resolution

    def get_resolution(self):
        return self.resolution

    # density must be in g/ml
    def set_density(self, density):
        self.density = density

    def get_density(self):
        return self.density

    def set_nozzle_size(self, nozzle_size):
        self.nozzle = nozzle_size
        self.extrude_width = nozzle_size*1.15
        self.layer_height = nozzle_size*.8
        self.extrude_rate = nozzle_size
        print("nozzle size set to: " +str(nozzle_size))
        print("extrude width set to: " +str(self.extrude_width))
        print("extrude rate set to: " +str(self.extrude_rate))
        print("layer height set to: " +str(self.layer_height))

    def set_nozzle(self, nozzle_size):
        self.set_nozzle_size(nozzle_size)

    def get_nozzle_size(self):
        return self.nozzle

    def set_mix_factor(self, mix_factor):
        self.set_nozzle_size(nozzle_size)

    def get_mix_factor(self):
        return self.nozzle

    def get_nozzle(self):
        return self.nozzle

    def set_layer_height(self, layer_height):
        self.layer_height = layer_height
        print("new layer height set: " +str(round(layer_height,3)))

    def get_layer_height(self):
        return self.layer_height

    def rate(self, feedrate):
        self.do(self.G1f.format(f=feedrate))

    def set_feedrate(self, feedrate):
        self.do(self.G1f.format(f=feedrate))

    def set_speed(self, feedrate):
        self.do(self.G1f.format(f=feedrate))
        self.speed = feedrate

    def get_speed(self):
        return self.speed

    def dwell(self, ms):
        self.do(self.G4p.format(p=ms))

    def pause(self, ms):
        if (self.printer=="ender"):
            self.do(self.G4p.format(p=ms))
        else:
            self.write_gcode_comment("hack pause")
            self.set_speed(60) # mm/minute
            self.lift(-ms/1000)
            self.set_speed(self.speed)

    def pause_seconds(self, s):
        ms = s*1000
        if (self.printer=="ender"):
            self.do(self.G4p.format(p=ms))
        else:
            self.write_gcode_comment("hack pause")
            self.set_speed(60) # mm/minute
            self.lift(-s/1000) 
            self.set_speed(self.speed)

    def pause_and_wait(self):
        self.do(self.M0)

    def extrude(self, quantity):
        self.do(self.G1e.format(e=quantity))

    def set_bed_temp(self, temp):
        self.do(self.M140s.format(s=temp))

    def set_extruder_temp(self, temp):
        self.do(self.M104s.format(s=temp))

    def draw_print_bed(self):
        point1 = rs.AddPoint(-self.x_size/2, -self.y_size/2,0)
        point2 = rs.AddPoint(-self.x_size/2, self.y_size/2,0)
        point3 = rs.AddPoint(self.x_size/2, self.y_size/2,0)
        point4 = rs.AddPoint(self.x_size/2, -self.y_size/2,0)
        points = (point1, point2, point3, point4)
        return rs.AddSrfPt(points)

    def get_print_bed_size(self):
        return self.x_size, self.y_size

    def get_print_head_size(self):
        return self.print_head_size

    def get_printer(self):
        return self.printer

    ###################################################################
    # Turtle functions
    ###################################################################

    def penup(self):
        self.pen = False
        #self.do(self.G1e.format(e=-3))

    def pen_up(self):
        self.pen = False
        #self.do(self.G1e.format(e=-3))

    def pendown(self):
        self.pen = True

    def pen_down(self):
        self.pen = True

    def yaw(self, angle):
        theta = self.convert_angle(angle)
        new_forward = [math.cos(theta)*self.forward_vec[i] + math.sin(theta)*self.left_vec[i] for i in range(3)]
        new_left = [math.cos(theta)*self.left_vec[i] - math.sin(theta)*self.forward_vec[i] for i in range(3)]
        self.forward_vec = new_forward
        self.left_vec = new_left

    def pitch(self, angle):
        theta = self.convert_angle(angle)
        new_forward = [math.cos(theta)*self.forward_vec[i] + math.sin(theta)*self.up_vec[i] for i in range(3)]
        new_up = [math.cos(theta)*self.up_vec[i] - math.sin(theta)*self.forward_vec[i] for i in range(3)]
        self.forward_vec = new_forward
        self.up_vec = new_up

    def roll(self, angle):
        theta = self.convert_angle(angle)
        new_left = [math.cos(theta)*self.left_vec[i] + math.sin(theta)*self.up_vec[i] for i in range(3)]
        new_up = [math.cos(theta)*self.up_vec[i] - math.sin(theta)*self.left_vec[i] for i in range(3)]
        self.left_vec = new_left
        self.up_vec = new_up

    def left(self, angle):
        self.yaw(angle)

    def right(self, angle):
        self.yaw(-angle)

    def pitch_up(self, angle):
        self.pitch(angle)

    def pitch_down(self, angle):
        self.pitch(-angle)

    def roll_left(self, angle):
        self.roll(-angle)

    def roll_right(self, angle):
        self.roll(angle)

    def set_heading(self, yaw, pitch=0, roll=0):
        self.forward_vec = [1, 0, 0]
        self.left_vec = [0, 1, 0]
        self.up_vec = [0, 0, 1]
        self.yaw(yaw)
        self.pitch(pitch)
        self.roll(roll)

    def set_angle(self, yaw, pitch=0, roll=0):
        self.forward_vec = [1, 0, 0]
        self.left_vec = [0, 1, 0]
        self.up_vec = [0, 0, 1]
        self.yaw(yaw)
        self.pitch(pitch)
        self.roll(roll)

    def change_heading(self, yaw=0, pitch=0, roll=0):
        self.set_heading(self.yaw + yaw, self.pitch + pitch, self.roll + roll)

    def set_color(self, r=0,g=0,b=0):
        self.current_color = int(r),int(g),int(b)

    def set_tube_color(self, r=0,g=0,b=0):
        tube_dist,volume,mass = self.mass_of_path()
        self.set_color(r,g,b)
        self.tube_color = int(r),int(g),int(b),tube_dist,volume,mass
        self.tube_color_history.append(self.tube_color)

    def get_color(self):
        return self.current_color

    def get_tube_color(self):
        return self.tube_color[0],self.tube_color[1],self.tube_color[2]

    def convert_angle(self, angle):
        if self.use_degrees: return math.radians(angle)
        return angle

    def record_move(self, dx, dy, dz, de=0,r=0,g=0,b=0):
        if self.track_history:
            prev_point = self.prev_points[-1]
            next_point = (prev_point[0]+dx, prev_point[1]+dy, prev_point[2]+dz) 
            self.prev_points.append(next_point)
            if self.pen: 
                self.line_segs.append([self.prev_points[-2], self.prev_points[-1]])
                self.extrusion_history.append(de)
                self.color_history.append(self.current_color)

    def forward(self, distance):
        extrusion = abs(distance) * self.extrude_rate
        dx = float(distance * self.forward_vec[0])
        dy = float(distance * self.forward_vec[1])
        dz = float(distance * self.forward_vec[2])
        self.x += dx
        self.y += dy
        self.z += dz
        dx_w = '{:.3f}'.format(dx) 
        dy_w = '{:.3f}'.format(dy) 
        dz_w = '{:.3f}'.format(dz) 
        e_w = '{:.3f}'.format(extrusion) 
        self.record_move(dx, dy, dz, de=extrusion)
        if self.pen:
            self.do(self.G1xyze.format(x=dx_w, y=dy_w, z=dz_w, e=e_w))
        else:
            self.do(self.G1xyz.format(x=dx_w, y=dy_w, z=dz_w))

    def forward_lift(self, distance, height):
        extrusion = math.sqrt(distance**2+height**2) * self.extrude_rate
        dx = distance * self.forward_vec[0] + height * self.up_vec[0]
        dy = distance * self.forward_vec[1] + height * self.up_vec[1]
        dz = distance * self.forward_vec[2] + height * self.up_vec[2]
        self.x += float(dx)
        self.y += float(dy)
        self.z += float(dz)
        dx_w = '{:.3f}'.format(dx) 
        dy_w = '{:.3f}'.format(dy) 
        dz_w = '{:.3f}'.format(dz) 
        e_w = '{:.3f}'.format(extrusion)
        self.record_move(dx, dy, dz, de=extrusion)
        if self.pen:
            self.do(self.G1xyze.format(x=dx_w, y=dy_w, z=dz_w, e=e_w))
        else:
            self.do(self.G1xyz.format(x=dx_w, y=dy_w, z=dz_w))

    def backward(self, distance):
        self.forward(-distance)

    def back(self, distance):
        self.forward(-distance)

    def lift(self, height):
        height = float(height)
        self.z += height
        self.record_move(0, 0, height)
        height = '{:.3f}'.format(height) 
        self.do(self.G1z.format(z=height))

    # set position from a rhinoscript point
    def set_position_point(self,point):
        self.set_position(point.X, point.Y, point.Z)

    # set position from optional x, y, and z values
    def set_position(self, x=False, y=False, z=False):
        if x is False: x = self.x
        if y is False: y = self.y
        if z is False: z = self.z
        dx = x-self.x
        dy = y-self.y
        dz = z-self.z
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        distance = math.sqrt(dx*dx+dy*dy+dz*dz)
        extrusion = abs(distance) * self.extrude_rate

        #!!!! NOTE should keep track of all angles, right now only yaw
        if (distance!=0):
            yaw = math.degrees(math.acos(dx/distance))
            self.left(-self.get_yaw()) # return to 0 heading
        else:
            yaw = 0.0

        if (dy>0):
            self.left(float(yaw))
        else:
            self.left(-float(yaw))

        dx_w = '{:.3f}'.format(float(dx)) 
        dy_w = '{:.3f}'.format(float(dy)) 
        dz_w = '{:.3f}'.format(float(dz)) 
        e_w = '{:.3f}'.format(float(extrusion))
        self.record_move(dx, dy, dz, de=extrusion)
        if self.pen:
            self.do(self.G1xyze.format(x=dx_w, y=dy_w, z=dz_w, e=e_w))
        else:
            self.do(self.G1xyz.format(x=dx_w, y=dy_w, z=dz_w))

    
    def get_pen(self):
        return self.pen

    # get position as a rhinoscript point
    def get_position(self):
        return rs.CreatePoint(self.x, self.y, self.z)

    def getX(self):
        return self.x

    def getY(self):
        return self.y
    
    def getZ(self):
        return self.z

    def get_yaw(self):
        x, y, z = self.forward_vec
        net_yaw = math.atan2(y, x)
        if self.use_degrees: return math.degrees(net_yaw)
        return net_yaw
    
    def get_pitch(self):
        x, y, z = self.forward_vec
        r = math.sqrt(x**2+y**2)
        net_pitch = math.atan2(z, r)
        if self.use_degrees: return math.degrees(net_pitch)
        return self.net_pitch
   
    def get_roll(self):
        net_yaw = self.get_yaw()
        net_pitch = self.get_pitch()
        if self.use_degrees:
            net_yaw = math.radians(net_yaw)
            net_pitch = math.radians(net_pitch)
        left_vech = [-math.sin(net_yaw), math.cos(net_yaw), 0]
        up_vech = [-math.sin(net_pitch)*math.cos(net_yaw), -math.sin(net_pitch)*math.sin(net_yaw), math.cos(net_pitch)]
        y = sum([self.left_vec[i]*up_vech[i] for i in range(3)])
        x = sum([self.left_vec[i]*left_vech[i] for i in range(3)])
        net_roll = math.atan2(y, x)
        if self.use_degrees: return math.degrees(net_roll)
        return self.net_roll

    def draw_turtle(self):
        new_forward = [math.cos(math.radians(90))*self.forward_vec[i] + math.sin(math.radians(90))*self.left_vec[i] for i in range(3)]
        dx = 2 * new_forward[0]
        dy = 2 * new_forward[1]
        dz = 2 * new_forward[2]
        point1 = rs.AddPoint(self.getX()+dx, self.getY()+dy, self.getZ()+dz)
        new_forward = [math.cos(math.radians(-90))*self.forward_vec[i] + math.sin(math.radians(-90))*self.left_vec[i] for i in range(3)]
        dx = 2 * new_forward[0]
        dy = 2 * new_forward[1]
        dz = 2 * new_forward[2]
        point2 = rs.AddPoint(self.getX()+dx, self.getY()+dy, self.getZ()+dz)
        dx = 5 * self.forward_vec[0]
        dy = 5 * self.forward_vec[1]
        dz = 5 * self.forward_vec[2]
        point3 = rs.AddPoint(self.getX()+dx, self.getY()+dy, self.getZ()+dz)
        points = (point1, point2, point3)
        surface = rs.AddSrfPt(points)
        return surface

    def get_lines(self):
        lines = []
        for l in self.line_segs:
            if (l[0] != l[1]):
                lines.append(rs.AddLine(l[0], l[1]))
        return lines

    def get_points(self):
        points = []
        for l in self.line_segs:
            if (l[0] != l[1]):
                points.append(rs.CreatePoint(l[0][0],l[0][1],l[0][2]))
        return points

    def length_of_path(self):
        total_distance = 0
        for l in self.line_segs:
            if (l[0] != l[1]):
                total_distance = total_distance + rs.Distance(l[0],l[1])
        #print("total distance of path in mm: " +str(round(total_distance,2)))
        return total_distance

    def volume_of_path(self, print_out=False, distance_multiplier = .54):
        total_distance = self.length_of_path()
        volume = total_distance*math.pi*(self.extrude_width/2)*(self.extrude_width/2)*self.extrude_rate*distance_multiplier
        extruder_distance = volume/1000/2
        if (print_out):
            #print("total volume of path in cubic mm: " +str(round(volume,2)))
            print("total volume of path in ml: " +str(round(volume/1000, 0)))
            print("total mm on extruder: " +str(round(extruder_distance,0)))
            print("approximate time in minutes: " +str(round(total_distance/self.get_speed(), 0)))
        return extruder_distance, volume

    # density must be in g/ml
    def mass_of_path(self, density=False, print_out=False, mass_multiplier = 1.0):
        if (density):
            self.density = density
        extruder_distance, volume = self.volume_of_path(print_out)
        mass = volume/1000*self.density*mass_multiplier 
        mass = round(mass,0)
        if (print_out):
            print("total mass of path in g: " +str(round(mass,2)))
        return extruder_distance, volume, mass

    def get_print_time(self, print_out=False, distance_multiplier = .54):
        total_distance = self.length_of_path()
        time = round(total_distance/self.get_speed(),0)
        return time

    def get_path(self):
        return get_lines(self)

    def get_last_line(self):
        i = len(self.line_segs)
        print(self.line_segs[i-1])
        return rs.AddLine(self.line_segs[i-1][0],self.line_segs[i-1][1])

    def get_solids(self,resolution=10):
        solids = []
        box_width = self.extrude_width
        box_height = self.layer_height+self.layer_height/4
        skip = int(resolution) # the higher the number the lower the resolution. Will help render
        colors = []
        print(len(self.line_segs))
        for l in range(0,len(self.line_segs)-skip,skip):
            l0 = self.line_segs[l]
            l1 = self.line_segs[l+skip]
            color = self.color_history[l]
            if (l0 != l1 and l1):
                #points for first side of rect
                point0 = rs.CreatePoint(l0[0])
                point1 = rs.CreatePoint(l0[0][0],l0[0][1],l0[0][2]+box_height)
                point2 = rs.CreatePoint(l1[0][0],l1[0][1],l1[0][2]+box_height)
                point3 = rs.CreatePoint(l1[0])
                lines = []
                lines.append(rs.AddLine(point0,point1))
                lines.append(rs.AddLine(point1,point2))
                lines.append(rs.AddLine(point2,point3))
                lines.append(rs.AddLine(point3,point0))
                surface = rs.AddPlanarSrf(lines)
                if (surface):
                    n = rs.SurfaceNormal(surface,[0,0])
                    point4 = point0+n*box_width
                    point5 = point1+n*box_width
                    point6 = point2+n*box_width
                    point7 = point3+n*box_width
                    box = rs.AddBox([point0, point1, point2, point3, point4, point5, point6, point7])
                    solids.append(box)
                    colors.append(color)
        return solids, colors

    def get_colors(self):
        return self.color_history

    def diffuse_colors(self, diffusion=50.0, look_ahead=1000):
        color_history_new = []
        total_distance = 0
        current_color = self.color_history[0]
        r = float(current_color[0])
        g = float(current_color[1])
        b = float(current_color[2])
        target_color = current_color
        r_diff = 0.0
        g_diff = 0.0
        b_diff = 0.0
        i = 1
        for l in self.line_segs:
            if (l[0] != l[1]):
                total_distance = total_distance + rs.Distance(l[0],l[1])
                if (i<len(self.color_history)):
                    if (i+look_ahead>=len(self.color_history)):
                        next_color = self.color_history[i]
                    else:
                        next_color = self.color_history[i+look_ahead] # look past current location for next color to account for backward color diffusion


            if (total_distance >= 50):
                total_distance = 0
                if ((abs(next_color[0]-current_color[0])>0) or 
                    (abs(next_color[1]-current_color[1])>0) or 
                    (abs(next_color[2]-current_color[2])>0)):
                    # if you haven't fully transitioned to the current color
                    # take that into account
                    if (abs(target_color[0]-r)>0 or 
                        abs(target_color[1]-g)>0 or 
                        abs(target_color[2]-b)>0):
                        current_color = (int(r),int(g),int(b))
                    
                    target_color = next_color
                    r_diff = (next_color[0]-current_color[0])/diffusion
                    g_diff = (next_color[1]-current_color[1])/diffusion
                    b_diff = (next_color[2]-current_color[2])/diffusion

                if (abs(r-target_color[0])>abs(r_diff) and int(r)<255 and int(r)>0):
                    r = r+r_diff
                elif (r<0):
                    r = 0
                elif(r>255):
                    r = 255

                if (abs(g-target_color[1])>abs(g_diff) and int(g)<255 and int(g)>0):
                    g = g+g_diff
                elif (g<0):
                    g = 0
                elif(g>255):
                    g = 255

                if (abs(b-target_color[2])>abs(b_diff) and int(b)<255 and int(b)>0):
                    b = b+b_diff
                elif (b<0):
                    b = 0
                elif(b>255):
                    b = 255
                current_color = next_color

            color_history_new.append((int(r),int(g),int(b)))
            i+=1

        self.color_history = color_history_new

        return color_history_new

    def draw_print_tube(self):
        # tube_color = 0, 0, 0, 0, 0, 0 # r,g,b,tube_dist,volume,mass
        r0,g0,b0 = self.get_tube_color()
        self.set_tube_color(r0,g0,b0) # add final shift to record current color
        tube_distance0 = 0
        startingX = 70
        startingZ = 10
        colors = []

        
        # rectangle next to tube for background for information
        tube_distance = self.tube_color_history[len(self.tube_color_history)-1][3]
        p0 = rs.CreatePoint(startingX,0,startingZ)
        p1 = rs.CreatePoint(startingX+100,0,startingZ)
        p2 = rs.CreatePoint(startingX+100,0,startingZ+tube_distance)
        p3 = rs.CreatePoint(startingX,0,startingZ+tube_distance)
        rectangle = rs.AddPolyline([p0,p1,p2,p3,p0])
        #surface = rs.AddPlanarSrf(rectangle)
        #tube_shapes=surface
        #colors.append((200,200,200))

        # tube
        p0 = rs.CreatePoint(startingX,0,startingZ)
        p1 = rs.CreatePoint(startingX+50,0,startingZ)
        p2 = rs.CreatePoint(startingX+50,0,startingZ+250)
        p3 = rs.CreatePoint(startingX,0,startingZ+250)
        rectangle = rs.AddPolyline([p0,p1,p2,p3,p0])
        surface = rs.AddPlanarSrf(rectangle)
        colors.append((255,255,255))
        tube_shapes = surface
        # nozzle
        p0 = rs.CreatePoint(startingX+20,0,startingZ)
        p1 = rs.CreatePoint(startingX+30,0,startingZ)
        p2 = rs.CreatePoint(startingX+30,0,startingZ-10)
        p3 = rs.CreatePoint(startingX+20,0,startingZ-10)
        rectangle = rs.AddPolyline([p0,p1,p2,p3,p0])
        surface = rs.AddPlanarSrf(rectangle)
        tube_shapes = tube_shapes + surface
        colors.append((255,255,255))

        text = []
        m0 = 0.0
        #text.append((str(tube_distance0),p0))

        for i in range (len(self.tube_color_history)):
            r = self.tube_color_history[i][0]
            g = self.tube_color_history[i][1]
            b = self.tube_color_history[i][2]
            tube_distance = self.tube_color_history[i][3]
            volume = self.tube_color_history[i][4]
            m = self.tube_color_history[i][5] #mass
            p0 = rs.CreatePoint(startingX,0,startingZ+tube_distance0)
            p1 = rs.CreatePoint(startingX+50,0,startingZ+tube_distance0)
            p2 = rs.CreatePoint(startingX+50,0,startingZ+tube_distance)
            p3 = rs.CreatePoint(startingX,0,startingZ+tube_distance)
            if (tube_distance>0.0):
                z_diff = tube_distance-tube_distance0
                z_text = startingZ+tube_distance0+z_diff/2
                rectangle = rs.AddPolyline([p0,p1,p2,p3,p0])
                surface = rs.AddPlanarSrf(rectangle)
                tube_shapes = tube_shapes + surface
                color = r0,g0,b0
                colors.append(color)
                if (tube_distance >0.0):
                    tp = rs.CreatePoint(startingX+25,0,z_text)
                    text.append((str(int(tube_distance-tube_distance0))+" mm",tp))

                    tp = rs.CreatePoint(startingX+60,0,z_text)
                    text.append((str(int(m-m0))+" g ",tp))
                tube_distance0 = tube_distance
            r0 = r
            g0 = g
            b0 = b
            m0 = m
        return tube_shapes, colors, text

