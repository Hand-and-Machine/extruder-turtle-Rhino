; *************** Lutum initialization **************
; 300 x 300 x 400 build volume
; T0 extruder 0
; T1 extruder 1

G28            ; Home all
G21	           ; Metric units
G90            ; Absolute positioning
M82            ; Absolute extrusion
M302           ; Allow cold extrusion

T1			   ; Use extruder 1
G92 E0         ; Zero extruder
G1 F2000 E100  ; Prime Extruder: Extrude some clay
G92 E0         ; Zero extruder

G0 F2000 X150.0 Y150.0 Z3.0 ; Move to starting position above bed
G0 F2000 X150.0 Y150.0 Z0.5 ; Move to starting position onto bed
M83 					  ; Relative extrustion
G91                       ; Relative coordinates for X,Y,Z axes

