#!/bin/sh
OS=`uname | cut -c-6`

basedir=`dirname $0`
cd "$basedir"
ui_files/build.sh

if [ "$OS" != "CYGWIN" ] ; then
    mki18n_mo.sh
fi
