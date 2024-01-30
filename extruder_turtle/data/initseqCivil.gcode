; *************** Matrix initialization **************
G28
G90                     		; Absolute coordinates for X,Y,Z axes
G0 F2000 X1000.0 Y1000.0 Z200 	; Move to starting position
M83 							; Relative extrustion
G91                     		; Relative coordinates for X,Y,Z axes