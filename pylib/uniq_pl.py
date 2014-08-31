#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : uniq_pl.py
"""
  Summary    :  uniqifies a path list

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

uniqifies a list of file paths

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
import os

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------

def uniq_pathlist(path_list):
    """ uniquifies a path list 
    
    >>> mypath = os.path.expanduser('~')
    >>> mybase = os.path.basename(mypath)
    >>> up = os.path.join(mypath, '..')
    >>> my_down_up = os.path.join(mypath, '..', mybase.lower())
    >>> pathlist = [ mypath, up, my_down_up ]
    >>> [ os.path.relpath(path, mypath) for path in uniq_pathlist(pathlist)]
    ['.', '..']
    """
    in_list = set()
    uniq_path_list = []
    for path in path_list:
        real_path = os.path.normcase(os.path.realpath(path))
        if real_path in in_list:
            continue
        uniq_path_list.append(path)
        in_list.add(real_path)
    return uniq_path_list

# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
