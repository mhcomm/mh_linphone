@echo off
set curdir=%cd%

set PYDIR=%1

if not ""%1""=="""" goto NEXT_STEP
call %~d0%~p0\set_pydir.bat

cd %~d0%~p0
cd ..\pylib\lpresources\locale\src

if exist ..\fr\LC_MESSAGES\nul: goto HAVE_FR_MSG_DIR
if exist ..\fr\nul: goto HAVE_FR_DIR
mkdir ..\fr
:HAVE_FR_DIR
mkdir ..\fr\LC_MESSAGES
:HAVE_FR_MSG_DIR

if exist ..\en\LC_MESSAGES\nul: goto HAVE_EN_MSG_DIR
if exist ..\en\nul: goto HAVE_EN_DIR
mkdir ..\en
:HAVE_EN_DIR
mkdir ..\en\LC_MESSAGES
:HAVE_EN_MSG_DIR

echo compiling french
%PYDIR%\Tools\i18n\msgfmt.py mh_linphone.fr.po 
copy mh_linphone.fr.mo ..\fr\LC_MESSAGES\mh_linphone.mo

echo compiling english
%PYDIR%\Tools\i18n\msgfmt.py mh_linphone.en.po
copy mh_linphone.en.mo ..\en\LC_MESSAGES\mh_linphone.mo

cd %curdir%

