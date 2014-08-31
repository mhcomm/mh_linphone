@echo off
pushd %~d0%~p0


set PYDIR=%1

if not ""%1""=="""" goto NEXT_STEP
call %~d0%~p0\set_pydir.bat

:NEXT_STEP
echo Please Wait. ui files are being converted
call pyrcc4 -no-compress -o mh_linphone_pixmaps_rc.py mh_linphone_pixmaps.qrc
echo conversion finished
cd %~d0%~p0

call mki18n_mo.bat
popd


