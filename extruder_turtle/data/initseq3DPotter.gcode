; 3D POTTER INITIALIZATION SEQUENCE
M82                             ; absolute extrusion mode
G28                             ; Home all axes
G92 E0                          ; Reset Extruder
G1 F40000 E2000                 ; Prime Extruder, Extrude 2000mm of clay
G90 							; Absolute coordinates for X,Y,Z   
; M208 X0 Y0 Z0 S1              ; set axis minima
; M208 X415 Y405 Z500 S0        ; set axis maxima 
G0 F3000 X209.083 Y140.009 Z1.5 ; go to the starting position (center of print bed)
G1 F500                         ; set the feedrate
M83                             ; Relative extrusion
G91                     		; relative coordinates for X,Y,Z axes
