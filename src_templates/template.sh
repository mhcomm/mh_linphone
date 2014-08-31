#!/bin/bash
# ############################################################################
#  <script name>
#
# Copyright  : (C) 2014 by MHComm
# Author     : <AUTHOR>
# Description: 
#
# ############################################################################

# setup base vars
bn=`basename $0`
bd=`dirname $0`
bd=`cd $bd; pwd`

# help text
show_help() {
cat << eot
usage: $bn 
eot
}

# basic command line parsing
#opt_quiet=0 
last=0
while [ $last = 0 -a $# -gt 0 ] ; do
    case "$1" in
        -h) show_help ; exit 0 ;;
#        -q) opt_quiet=1 ;;
        --) shift ; last=1 ;;
        *) last=1;;
    esac
    if [ $last = 0 ] ; then
        shift
    fi
done

# ############################################################################
# Main script starts here
# ############################################################################


# ############################################################################
# End of Script
# ############################################################################
