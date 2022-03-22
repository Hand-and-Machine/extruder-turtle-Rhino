; 3D POTTER INITIALIZATION SEQUENCE
; for 3mm nozzle
; layer height = 3mm
; extrude rate = 5mm
M82                             ; absolute extrusion mode
G28                             ; Home all axes
G92 E0                          ; Reset Extruder
G90 							; Absolute coordinates for X,Y,Z   
G0 F3000 X209.083 Y140.009 Z0   ; go to the starting position (center of print bed)
