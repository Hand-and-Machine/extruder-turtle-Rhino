; *************** 3D Potter initialization **************
M82                             ; Absolute extrusion mode
G28                             ; Home all axes
G92 E0                          ; Reset Extruder
G90 							; Absolute coordinates for X,Y,Z   

G1 F9000 E1000                  ; Prime Extruder, Extrude 1000mm of clay
G1 X132 Y150 Z25 F5000 			; Go to the starting position (center of bed) 25mm above print
G1 X132 Y150 Z0 F1000 			; Go to the starting position more slowly

M83                             ; Relative extrusion
G91                     		; Relative coordinates for X,Y,Z axes
G1 E5                 			; Extrude 5mm of clay