; *************** Prusa i3 mk3 initialization **************
;TARGET_MACHINE.NAME:Prusa i3 Mk3/Mk3s
G21 ; set units to millimeters
G90 ; use absolute positioning
M82 ; absolute extrusion mode
M104 S200 ; set extruder temp
M140 S60 ; set bed temp
M190 S60 ; wait for bed temp
M109 S200 ; wait for extruder temp
G28 W ; home all without mesh bed level
G80 ; mesh bed leveling
G92 E0.0 ; reset extruder distance position
G1 Y-3.0 F1000.0 ; go outside print area
G1 X60.0 E9.0 F1000.0 ; intro line
G1 X100.0 E21.5 F1000.0 ; intro line
G92 E0.0 ; reset extruder distance position
G1 0 0 .3               ; Lift nozzle above bed a little
G1 X100 Y100 Z.1        ; Go to the starting position 
F300 E3                 ; Extrude to get ready
M83 					; Relative extrustion
G91                     ; Relative coordinates for X,Y,Z axes