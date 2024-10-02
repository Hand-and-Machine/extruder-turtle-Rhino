; *************** Lutum initialization **************
; 300 x 300 x 400 build volume
; T0 extruder 0
; T1 extruder 1

G28            ; Home
G21	           ; Metric units
G90            ; Absolute positioning
M82            ; Absolute extrusion
M302           ; Allow cold extrusion

G1 Z15.0 F1500 ; Move up 15mm to extrude
G92 E0         ; Zero extruder
; G1 F2000 E5    ; Prime Extruder: Extrude some clay
G92 E0         ; Zero extruder

G0 F2000 X150.0 Y150.0 Z1.0 ; Move to starting position
M83 					  ; Relative extrustion
G91                       ; Relative coordinates for X,Y,Z axes
T0				; Use extruder 0
