@echo off
title AIlucinator
set inst_dir=%CD%
set PYTHON=%inst_dir%\python-embedded\python.exe

%PYTHON% main.py %*
