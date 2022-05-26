; *************** Eazao initialization **************
G21
G90 ;absolute positioning
M82 ;set extruder to absolute mode
G28 ;Home
G1 Z15.0 F1500 ; move the platform down 15mm
G92 E0
G1 F300 E20    ; Prime Extruder, Extrude 20mm of clay
G92 E0
M302
M163 S0 P0.9; Set Mix Factor
M163 S1 P0.1; Set Mix Factor
M164 S0
G0 F1800 X75.055 Y88.274 Z1 ; move to starting position
M83 					; Relative extrustion
G91                     ; Relative coordinates for X,Y,Z axes