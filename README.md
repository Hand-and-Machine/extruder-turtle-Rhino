# extruder-turtle-Rhino

A Python package that uses the principles of 3D Turtle Geometry to generate GCODE. 
To be used as a Grasshopper/Rhino library. Relies on Rhinoscript functionality. 
This file covers only a subset of library funcitons. For
full library documentation see: https://handandmachine.org/projects/extruder_turtle_rhino/
Rhinoscript documentation: https://developer.rhino3d.com/api/RhinoScriptSyntax/

## Basic functionality

The `ExtruderTurtle` class implements the basic functionality of a turtle.

### Setup

Methods of the `ExtruderTurtle` class that are used to set up your turtle:

- The constructor `t = ExtruderTurtle()` which takes no arguments. The turtle is constructed with no associated
GCODE file or 3D printer and these starting parameters:
    - Default starting orientation, consisting of three vectors: `forward_vec` (which you may imagine as pointing out of the turtle's nose), `up_vec` (normal to the turtle's shell), and `left_vec` (pointing out of the turtle's left side).
    - Default starting `pendown` value is `True`.
    - Angles are measured in degrees.
- To associte the turtle with a GCODE file and 3D printer, use `t.setup()`, with arguments:
    - `x=0` is the starting x-value
    - `y=0` is the starting y-value
    - `z=0` is the starting z-value
    - `filename=False` the value of the file you need to write to. You must open a file with write access in Grasshopper/Rhino and then pass the name of this file to the setup function.
    - `printer=False` the printer you are using. The library currently supports the following printers: Ender Creality 3D "ender", 3D Potter Super 10 "super", 3D Potter Micro 10 "micro", and Eazao Zero Printer "eazao".
- To close the GCODE file and write the finalization sequence to the output file, use `t.finish()`. This cools down the bed, moves the extruder up and away from the print, etc.

### Turtle actions

The basic built-in actions of the turtle:

- `t.forward(distance)` moves the turtle forward a distance of `distance`, extruding along the way and writing GCODE if the pen is down.
- `t.left(theta)` turns the turtle left by an angle `theta`. This is just an easier-to-remember alias for `t.yaw(theta)`.
- `t.right(theta)` turns the turtle right by an angle `theta`. Alias for `t.yaw(-theta)`.
- `t.pitch_up(theta)` tilts the turtle "upwards" in the direction where its eyes would point. Alias for `t.pitch(theta)`.
- `t.pitch_down(theta)` tilts the turtle "downwards". Alias for `t.pitch(-theta)`.
- `t.roll_left(theta)` rolls the turtle towards its left side. Alias for `t.roll(-theta).
- `t.roll_right(theta)` rolls the turtle towards its right side. Alias for `t.roll(theta)`.
- `t.lift(height)` lifts the turtle up by a distance `height`. Usually used to move to the next layer of the print.
- `t.forward_lift(distance, height)` moves the turtle forward by a distance `distance` and up by a distance `height`, extruding along the way if the pen is down. Note that "up" here refers to the direction normal to the turtle's shell, not necessarily in the positive-z direction.
- `t.penup()` lifts the pen up (extrusion will not occur until the pen is back down).
- `t.pendown()` puts the pen down (extrusion will occur until the pen is lifted up again).

### Configuration and GCODE commands

The following functions are used to configure the turtle and write directly to the GCODE file:

- `t.set_extrude_rate(extrude_rate)` sets the rate of extrusion, that is, the ratio of mm filament extruded to mm moved by the turtle.
- `t.set_speed(speed)` sets the speed (AKA feedrate) of the turtle.
- `t.extrude(quantity)` extrudes the given quantity (in mm) of filament
- `t.write_gcode_comment(comment)` writes the input string to the GCODE file as a comment

### Visualization

The following functions are used to generate geometry objects that you can manipulate and visualize in Grasshopper/Rhino:

- `t.get_lines()` returns the path traveled by the turtle as a list of lines.
- `t.draw_turtle()` returns a triangular surface that shows the turtle's current location and orientation.
- `t.draw_print_bed()` returns a surface that corresponds to the size of the printer's print bed.


## Example code

See the examples directory.
