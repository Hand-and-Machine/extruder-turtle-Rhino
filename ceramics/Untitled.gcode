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

G1 X50.0 Y0.0 Z0.0 E150.0
G1 X0.0 Y50.0 Z0.0 E150.0
G1 X-50.0 Y0.0 Z0.0 E150.0
G1 X-0.0 Y-50.0 Z0.0 E150.0

; FINALIZATION SEQUENCE

G1 E-3 					; Extrude backwards to prevent blob 
M104 S0                 ; cool down hotend
M140 S0                 ; cool down bed
M107                    ; turn off fan
G1 F5000 Z100           ; move extruder above print
G28                     ; Home all axes
M84                     ; disable motors

