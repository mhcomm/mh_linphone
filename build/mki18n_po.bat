@echo off
set curdir=%cd%
cd %~d0%~p0
cd %curdir%

echo creating pot file
%PYDIR%\Tools\i18n\pygettext.py --no-location -p pylib\lpresources\locale\src -o mh_linphone.pot .
echo pot to unix 
dos2unix pylib/lpresources/locale/src/mh_linphone.pot
rem to create a new language use msginit -l bla bla bla

cd pylib\lpresources\locale\src
echo merging into french translation
msgmerge -s -U mh_linphone.fr.po mh_linphone.pot
grep -n -i fuzzy mh_linphone.fr.po

echo merging into english translation
msgmerge -s -U mh_linphone.en.po mh_linphone.pot
grep -n -i fuzzy mh_linphone.en.po

cd %curdir%
