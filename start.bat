@echo off
cd /d %~dp0
py -3.13 -m http.server 8000 -d docs
