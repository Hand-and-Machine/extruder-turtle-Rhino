; *************** Matrix initialization **************
G21	           ; Metric units
G90            ; Absolute positioning
M82            ; Absolute extrusion
M302           ; Allow cold extrusion
G1 Z45.0 F1500 ; Allow room for autohome

G92 E0         ; Zero extruder
G1 F2000 E20   ; Prime Extruder: Extrude 20mm of clay
G92 E0         ; Zero extruder

; Clay mix factor
M163 S0 P0.87   ; Set Mix Factor small auger extruder
M163 S1 P0.13   ; Set Mix Factor large plunger extruder
M164 S0		   ; Finalize mix


G0 F2000 X200.0 Y200.0 Z0 ; Move to starting position
M83 					; Relative extrustion
G91                     ; Relative coordinates for X,Y,Z axes