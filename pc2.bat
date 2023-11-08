@echo off
if "%~6"=="" (
	echo Uso : %0 <Puerto de escucha> <MAX_CONEXIONES> <IP AD_Weather/kafka> <Puerto kafka> <Puerto AD_Weather>
)
cd registry
rem <Puerto registro>
python AD_registry.py %1
cd ..
cd engine
rem <Puerto de escucha> <MAX_CONEXIONES> <IP AD_Weather/kafka> <Puerto kafka> <Puerto AD_Weather>
python AD_engine %2 %3 %4 %5 %6 

