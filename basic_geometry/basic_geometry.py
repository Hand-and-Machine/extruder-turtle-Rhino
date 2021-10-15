import math

# parameters for potterbot w/ 3mm nozzle and red clay, WH8
extrude_width = 3.6
layer_height = 2.0
extrude_rate = 3.0 #mm extruded/mm
speed = 1000 #mm/minute

# parameters for potterbot w/ 3mm nozzle and white porcelain clay
#extrude_width = 2.5
#layer_height = 1.5
#extrude_rate = 3 #mm extruded/mm
#speed = 1000 #mm/minute

def non_centered_poly(diameter, number_sides, t):
    r = diameter/2
    circumference = diameter * math.pi
    c_inc = circumference/number_sides
    outer_angle = 360.0/number_sides
    inner_angle = 180.0-360.0/number_sides
    
    for i in range (number_sides):
        t.forward(c_inc)
        t.right(outer_angle)

def polygon_layer (diameter, number_sides, t):
    d = extrude_width*2
    t.left(90)
    t.forward(extrude_width)
    t.right(90)
    non_centered_poly(d,number_sides,t)
    while (d < (diameter-extrude_width*2)):
        t.left(90)
        t.forward(extrude_width)
        t.right(90)
        d = d+extrude_width*2 
        non_centered_poly(d,number_sides,t)
    t.left(90)
    t.forward((diameter-d)/2)
    t.right(90)
    non_centered_poly(diameter,number_sides,t)


def centered_poly(diameter, number_sides, t):
    r = diameter/2
    circumference = diameter * math.pi
    c_inc = circumference/number_sides
    outer_angle = 360/number_sides
    inner_angle = 180-360/number_sides
    t.lift(layer_height*2)
    t.penup()
    t.forward(r)
    t.left(outer_angle + inner_angle/2)
    t.lift(-layer_height*2)
    t.pendown()
    for i in range (number_sides):
        t.forward(c_inc)
        t.left(outer_angle)
    t.penup()
    t.lift(layer_height*2)
    t.right(outer_angle + inner_angle/2)
    t.backward(r)
    t.lift(-layer_height*2)
    t.pendown()

# generates a polygon with edges that are side_length long
def polygon(side_length, number_sides, t):
    r = side_length/(2*math.sin(math.radians(180/number_sides)))
    outer_angle = 360/number_sides
    inner_angle = 180-360/number_sides
    t.penup()
    t.forward(r)
    t.left(outer_angle + inner_angle/2)
    t.pendown()
    for j in range(number_sides):
        t.forward(side_length)
        t.left(outer_angle)
    t.penup()
    t.right(outer_angle + inner_angle/2)
    t.backward(r)
    t.pendown()

def oscillating_circle_xy(diameter, a, nOscillations, t, steps=360, spiral_up = False):
    dtheta = 360.0/steps
    b = diameter/2
    x0 = t.getX()
    y0 = t.getY()
    z = t.getZ()
    z_inc = layer_height/steps
    # this is a problematic if statement. Will cause problems later!
    if (x0==0):
        theta0 = 0
        # could also be theta0 = 90 or theta0 = 270
    elif (x0 < 0):
        theta0 = math.degrees(math.atan(y0/x0))+180
    else:
        theta0 = math.degrees(math.atan(y0/x0))

    for s in range(1,steps+1):
        theta = theta0+dtheta*s
        r= b+a*math.cos(nOscillations*math.radians(theta))
        x = r*math.cos(math.radians(theta))
        y = r*math.sin(math.radians(theta))
        if (spiral_up):
            z = z + z_inc
        t.set_position(x,y,z)

def filled_oscillating_circle_xy(diameter, a, nOscillations, t, steps=360):
    d = extrude_width*2
    number_cycles = diameter/(extrude_width*2)
    da = float(a)/number_cycles
    a2=da
    while(d<diameter):
        oscillating_circle_xy(d, a2, nOscillations, t, steps)
        t.left(90)
        t.forward(extrude_width)
        t.right(90)
        d = d+extrude_width*2 
        a2 = a2+da
    oscillating_circle_xy(diameter, a2, nOscillations, t, steps)

def oscillating_circle_z(diameter, amplitude, nOscillations, t, steps=100, spiral_up = False):
    circumference = diameter * math.pi
    dc = circumference/steps
    dtheta = 360.0/steps
    z_inc = layer_height/steps
    for s in range(1,steps+1):
        theta = s*dtheta
        #print(theta)
        t.forward_lift(dc, amplitude*math.sin(math.radians(nOscillations*theta)))
        t.right(dtheta)
        if (spiral_up):
            t.lift(z_inc)

def oscillating_circle_xyz(diameter, axy, az, nOscillationsxy, nOscillationsz, t, steps=360, spiral_up = False, spiral_out=0, theta_offset=0):
    dtheta = 360.0/steps
    b = diameter/2
    x0 = t.getX()
    y0 = t.getY()
    z0 = t.getZ()
    z = z0
    z_inc = layer_height/steps
    # this is a problematic if statement. Will cause problems later!
    if (x0==0):
        theta0 = 0
        # could also be theta0 = 90 or theta0 = 270
    elif (x0 < 0):
        theta0 = math.degrees(math.atan(y0/x0))+180
    else:
        theta0 = math.degrees(math.atan(y0/x0))

    for s in range(1,steps+1):
        theta = theta0+dtheta*s
        if (theta_offset==0):
            r= b+axy*math.cos(nOscillationsxy*math.radians(theta))
        else:
            #this is a hack. amount to add needs to be calculated based on nOscillations
            r= b+axy*math.cos(nOscillationsxy*math.radians(theta+180/nOscillationsxy))
        x = r*math.cos(math.radians(theta))
        y = r*math.sin(math.radians(theta))
        z = z + az*math.sin(math.radians(nOscillationsz*theta))
        if (spiral_up):
            z = z + z_inc
        t.set_position(x,y,z)

def square_oscillating_circle(inner_diameter, outer_diameter, nOscillations, t, steps=360):
    inner_radius = inner_diameter/2
    outer_radius = outer_diameter/2
    r_dif = outer_radius-inner_radius
    inner_circumference = math.pi*inner_diameter
    outer_circumference = math.pi*outer_diameter
    inner_c_step = inner_circumference/steps
    outer_c_step = outer_circumference/steps
    theta_step = 360.0/steps
    for i in range(0,nOscillations):
        for j in range (0,int(steps/(nOscillations*2))):
            t.forward(inner_c_step)
            t.left(theta_step)
        t.right(90)
        t.forward(r_dif)
        t.left(90)
        for j in range (0,int(steps/(nOscillations*2))):
            t.forward(outer_c_step)
            t.left(theta_step)
        t.left(90)
        t.forward(r_dif)
        t.right(90)


