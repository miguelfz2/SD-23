@echo off
if "%~6"=="" (
	echo "Uso : %0 <Puerto de escucha> <MAX_CONEXIONES> <IP AD_Weather/kafka> <Puerto kafka> <Puerto AD_Weather>"
)
rem <Puerto registro>
start cmd /k "python C:\Users\EPS\Desktop\SD-23\registry\AD_registry.py %1"
rem <Puerto de escucha> <MAX_CONEXIONES %2> <IP AD_Weather/kafka %3> <Puerto kafka %4> <Puerto AD_Weather% 5>
start cmd /k "python C:\Users\EPS\Desktop\SD-23\engine\AD_engine.py %2 %3 %4 %5

