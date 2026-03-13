; *************** Eazao Potter initialization **************
G21            ; Metric units
G90            ; Absolute positioning
M82            ; Absolute extrusion
M302           ; Allow cold extrusion
G28            ; Home
G4 S5          ; wait 5 seconds!
 
G92 E0         ; Zero extruder
G1 F2000 E20   ; Prime Extruder: Extrude 20mm of clay
G92 E0         ; Zero extruder
 
; Eazao Potter base mix factor
M163 S0 P0.85   ; Set Mix Factor small auger extruder
M163 S1 P0.15   ; Set Mix Factor large plunger extruder
M164 S0         ; Finalize mix
 

G0 F2000 X75.0 Y88.0 Z1.0 ; Move to starting position
M83 					  ; Relative extrustion
G91                       ; Relative coordinates for X,Y,Z axes