; *************** End of print ***************
G91                     ; Relative coordinates for X,Y,Z axes
G1 Z5 F2000             ; move up in the z direction
T0						; Use extruder 0
G90                     ; Absolute coordinates 
G0 F5000 Y0 			; Move extruder to resting positions in Y
M84 X U Y               ; X U Y steppers off
M999					; reboot software
