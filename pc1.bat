@echo off
cd weather
python3 AD_Weather.py %1
cd C:\bin\windows\
call zookeeper-server-start.bat .\config\zookeeper.properties
call kafka-server-start.bat .\config\server.properties

