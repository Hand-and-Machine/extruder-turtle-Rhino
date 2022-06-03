; *************** End of print **************
G1 E-3 					; Extrude backwards to prevent blob 
G1 F5000 Z50            ; Move extruder above print 50mm and to 0,0 in XY
G90                     ; Absolute coordinates  
G1 F5000 X0 Y0          ; Move extruder to 0,0 in XY
M104 S0                 ; Cool down hotend
M140 S0                 ; Cool down bed
M107                    ; Turn off fan
M84                     ; Disable motors