#!/bin/sh
bd=`dirname $0`
bd=`cd $bd ; pwd`
rmhooks="$bd/shared/install/rmhooks.sh"

if [ ! -f $install ] ; then
  cd $bd ; cd ..
  git submodule init
  git submodule update
fi

if [ ! -f $rmhooks ] ; then
    echo "ERROR: cannot find rmhooks script $rmhooks"
fi

"$rmhooks"

