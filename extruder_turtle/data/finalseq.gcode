; *************** End of print ***************
G1 Z25 F2000            ; move up 25 in the z direction
G90                     ; Absolute coordinates 
G1 F5000 X0 Y0          ; Move extruder to 0,0 in XY
M84 X Y                 ; X Y steppers off