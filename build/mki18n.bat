@echo off
set curdir=%cd%
cd %curdir%

call %~d0%~p0\set_pydir.bat

if %PYDIR% == NONE: goto NO_PYDIR

echo make po
call build\mki18n_po.bat
echo make mo
call build\mki18n_mo.bat
goto END

:NO_PYDIR
echo did not find a python executable
:END


