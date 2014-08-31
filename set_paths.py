#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : set_paths.py
"""
  Summary    :  to be imported by any executable. sets up paths etc.

 ****************************************************************************
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 ****************************************************************************

This module shall be imported by any executable located on the bin directory
it will setup the python path as required and do any setups common to 
executables
"""
# #############################################################################
from __future__ import absolute_import
from __future__ import print_function

__author__    = "Klaus Foerster"
__copyright__ = "(C) 2014 by MHComm. All rights reserved"
__email__     = "info@mhcomm.fr"

# -----------------------------------------------------------------------------
#   Imports
# -----------------------------------------------------------------------------
import os, sys

MY_DIR = os.path.dirname(__file__)
TOP_DIR = os.path.realpath(os.path.join(MY_DIR))
LIB_DIR = os.path.join(TOP_DIR, 'pylib')
sys.path[:0] = [ LIB_DIR, MY_DIR ] 

from uniq_pl import uniq_pathlist
sys.path[:] = uniq_pathlist(sys.path)
