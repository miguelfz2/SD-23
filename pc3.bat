@echo off

REM Verificar si se proporcionaron exactamente 7 argumentos (6 + el número de veces)
if not "%6"=="" (
    set /a veces_a_ejecutar=%1
) else (
    echo Uso: %0 ^<número de drones^> ^<IP Engine/Registry 1^> ^<Puerto Engine 2^> ^<Puerto Registry 3^> ^<IP Kafka 4^> ^<Puerto Kafka 5^>
    exit /b 1
)

REM Eliminar el primer argumento (el número de veces)
shift

REM Bucle para ejecutar el script Python
for /l %%i in (1,1,%veces_a_ejecutar%) do (
    echo Ejecución número %%i
    python AD_Drone.py %*
)
