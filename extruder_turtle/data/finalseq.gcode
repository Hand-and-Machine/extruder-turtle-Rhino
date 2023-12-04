; *************** End of print ***************
G1 Z25 F2000            ; move up 25 in the z direction
G90                     ; Absolute coordinates 
G1 F5000 X0 Y0          ; Move extruder to 0,0 in XY
M84 X Y                 ; X Y steppers off
M104 S0					; Set Hot-end to 0C (off)
M140 S0					; Set bed to 0C (off)