@echo off
echo determine PYDIR

if "%PYDIR%" == "" goto CHECK_PYDIR
if exist %PYDIR%\nul: goto GOT_PYDIR

:CHECK_PYDIR
set PYDIR=C:\Python26
if exist %PYDIR%\nul: goto GOT_PYDIR
set PYDIR=D:\Python26
if exist %PYDIR%\nul: goto GOT_PYDIR
set PYDIR=E:\Python26
if exist %PYDIR%\nul: goto GOT_PYDIR
set PYDIR=C:\Python27
if exist %PYDIR%\nul: goto GOT_PYDIR
set PYDIR=D:\Python27
if exist %PYDIR%\nul: goto GOT_PYDIR
set PYDIR=E:\Python27
if exist %PYDIR%\nul: goto GOT_PYDIR
set PYDIR=NONE

:GOT_PYDIR
echo PYDIR is %PYDIR%
