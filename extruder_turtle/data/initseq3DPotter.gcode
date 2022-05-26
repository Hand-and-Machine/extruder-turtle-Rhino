; *************** 3D Potter initialization **************
M82                             ; Absolute extrusion mode
G28                             ; Home all axes
G92 E0                          ; Reset Extruder
G1 F40000 E2000                 ; Prime Extruder, Extrude 2000mm of clay
G90 							; Absolute coordinates for X,Y,Z   
; M208 X0 Y0 Z0 S1              ; Set axis minima
; M208 X415 Y405 Z500 S0        ; Set axis maxima 
G1 X207.5 Y202.5 Z0 F10000 		; Go to the starting position (center of print bed)
M83                             ; Relative extrusion
G91                     		; Relative coordinates for X,Y,Z axes