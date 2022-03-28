 ; ############### begin header for EAZAO ############## 
G21
G90 ;absolute positioning
M82 ;set extruder to absolute mode
G28 ;Home
G1 Z15.0 F1500 ;move the platform down 15mm
G92 E0
G1 F300 E10
G92 E0
M302
M163 S0 P0.9; Set Mix Factor
M163 S1 P0.1; Set Mix Factor
M164 S0

G1 F{feedrate}			; set the speed/feedrate
M83 					; Relative extrustion
G91                     ; relative coordinates for X,Y,Z axes
 ; ############### end header for EAZAO ############## 