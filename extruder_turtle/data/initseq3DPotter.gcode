; *************** 3D Potter initialization **************
M82                             ; Absolute extrusion mode
G28                             ; Home all axes
G92 E0                          ; Reset Extruder
G90 							; Absolute coordinates for X,Y,Z   
; M208 X0 Y0 Z0 S1              ; Set axis minima
; M208 X415 Y405 Z500 S0        ; Set axis maxima 
G1 X207.5 Y202.5 Z25 F10000 	; Go to the starting position (center of bed) 25mm above print
G1 F20000 E2000                 ; Prime Extruder, Extrude 2000mm of clay
G1 X207.5 Y202.5 Z0 F1000 		; Go to the starting position more slowly
M83                             ; Relative extrusion
G91                     		; Relative coordinates for X,Y,Z axes
G1 E5                 			; Extrude 5mm of clay