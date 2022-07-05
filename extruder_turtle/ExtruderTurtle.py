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

        # file settings
        self.out_filename = False
        self.initseq_filename = False
        self.finalseq_filename = False
        self.printer = False
        self.out_file = False;
        self.initseq_file = False;
        self.finalseq_file = False;

        # printer settings
        self.nozzle_size = 0;
        self.extrude_width = 0;
        self.layer_height = 0;
        self.extrude_rate = 0;
        self.speed = 0;
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
        else:
            print("Warning can't write file. No printer selected or filename given.")
            
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
            self.extrude_width = 1.75
            self.layer_height = 2.0
            self.extrude_rate = 1.25 #mm extruded/mm
            self.speed = 1000 #mm/minute
            self.printer = "eazao"
            self.resolution = 0.5
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

    def set_nozzle_size(self, nozzle_size):
        self.nozzle = nozzle_size
        self.extrude_width = nozzle_size*1.15
        self.layer_height = nozzle_size*.8
        self.extrude_rate = nozzle_size
        print("nozzle size set to: " +str(nozzle_size))
        print("extrude width set to: " +str(extrude_width))
        print("extrude rate set to: " +str(extrude_rate))
        print("layer height set to: " +str(layer_height))

    def set_nozzle(self, nozzle_size):
        set_nozzle_size(self,nozzle_size)

    def get_nozzle_size(self):
        return self.nozzle

    def get_nozzle(self):
        return self.nozzle

    def set_layer_height(self, layer_height):
        self.layer_height = layer_height
        print("new layer height set: " +str(round(layer_height,3)))

    def get_layer_height(self):
        return self.layer_height

    def set_density(self, extrude_rate):
        self.extrude_rate = extrude_rate

    def rate(self, feedrate):
        self.do(self.G1f.format(f=feedrate))

    def set_feedrate(self, feedrate):
        self.do(self.G1f.format(f=feedrate))

    def set_speed(self, feedrate):
        self.do(self.G1f.format(f=feedrate))

    def get_speed(self):
        return self.speed

    def dwell(self, ms):
        self.do(self.G4p.format(p=ms))

    def pause(self, ms):
        self.do(self.G4p.format(p=ms))

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

    def pendown(self):
        self.pen = True
        #self.do(self.G1e.format(e=3))

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

    def set_angle(self, yaw):
        self.yaw(yaw)

    def change_heading(self, yaw=0, pitch=0, roll=0):
        self.set_heading(self.yaw + yaw, self.pitch + pitch, self.roll + roll)

    def convert_angle(self, angle):
        if self.use_degrees: return math.radians(angle)
        return angle

    def record_move(self, dx, dy, dz, de=0):
        if self.track_history:
            prev_point = self.prev_points[-1]
            next_point = (prev_point[0]+dx, prev_point[1]+dy, prev_point[2]+dz) 
            self.prev_points.append(next_point)
            if self.pen: 
                self.line_segs.append([self.prev_points[-2], self.prev_points[-1]])
                self.extrusion_history.append(de)

    def forward(self, distance):
        extrusion = abs(distance) * self.extrude_rate
        dx = float(distance * self.forward_vec[0])
        dy = float(distance * self.forward_vec[1])
        dz = float(distance * self.forward_vec[2])
        self.x += dx
        self.y += dy
        self.z += dz
        dx_w = '{:.6f}'.format(dx) 
        dy_w = '{:.6f}'.format(dy) 
        dz_w = '{:.6f}'.format(dz) 
        e_w = '{:.6f}'.format(extrusion) 
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
        dx_w = '{:.6f}'.format(dx) 
        dy_w = '{:.6f}'.format(dy) 
        dz_w = '{:.6f}'.format(dz) 
        e_w = '{:.6f}'.format(extrusion)
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
        height = '{:.6f}'.format(height) 
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
        self.x = x
        self.y = y
        self.z = z
        distance = math.sqrt(dx*dx+dy*dy+dz*dz)
        extrusion = abs(distance) * self.extrude_rate

        #!!!! NOTE should keep track of all angles, right now only yaw
        if (distance!=0):
            angle = math.degrees(math.acos(dx/distance))
        else:
            angle = 0
        self.left(-self.get_yaw())
        self.left(angle)

        dx_w = '{:.6f}'.format(float(dx)) 
        dy_w = '{:.6f}'.format(float(dy)) 
        dz_w = '{:.6f}'.format(float(dz)) 
        e_w = '{:.6f}'.format(extrusion)
        self.record_move(dx, dy, dz, de=extrusion)
        if self.pen:
            self.do(self.G1xyze.format(x=dx_w, y=dy_w, z=dz_w, e=e_w))
        else:
            self.do(self.G1xyz.format(x=dx_w, y=dy_w, z=dz_w))

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

    def get_path(self):
        return get_lines(self)

    def get_last_line(self):
        i = len(self.line_segs)
        print(self.line_segs[i-1])
        return rs.AddLine(self.line_segs[i-1][0],self.line_segs[i-1][1])
