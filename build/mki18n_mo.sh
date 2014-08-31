#!/bin/sh
basedir=`dirname $0`
cd "$basedir"
pwd=`pwd`

cd $pwd/../pylib/lpresources/locale/src

for lang in fr en ; do
    test -d "../$lang" || mkdir -p "../$lang/LC_MESSAGES"
    echo "compiling <$lang>"
    msgfmt -o ../$lang/LC_MESSAGES/mh_linphone.mo mh_linphone.$lang.po 
done

cd ..
ln -s -f fr fr_FR.UTF-8
ln -s -f en en_US.UTF-8

