@echo off
start cmd /k "python C:\Users\EPS\Desktop\SD-23\weather\AD_Weather.py %1"
start cmd /k "call C:\kafka\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties"
timeout /t 2 /nobreak >nul 2>&1
start cmd /k "call C:\kafka\bin\windows\kafka-server-start.bat .\config\server.properties"

