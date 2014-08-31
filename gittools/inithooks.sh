#!/bin/sh
bd=`dirname $0`
bd=`cd $bd ; pwd`
install="$bd/shared/install/inithooks.sh"

if [ ! -f $install ] ; then
  cd $bd ; cd ..
  git submodule init
  git submodule update
fi

if [ ! -f $install ] ; then
    echo "ERROR: cannot find install script"
fi

"$install"

