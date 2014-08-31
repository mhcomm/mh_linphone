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


def get_program_path(tool_exe, tool_dir='', ):
    paths = []
    env = os.environ
    for path in [env.get('ProgramFiles', None), env.get('ProgramFiles(x86)', None)]:
        if path:
            paths.append(os.path.join(path, tool_dir))

    paths.extend(os.environ.get('PATH', '').split(os.pathsep))
    print(paths)

    for path in paths:
        prog_name = os.path.join(path, tool_exe)
        if os.path.exists(prog_name):
            return prog_name
        elif os.path.exists(prog_name + '.exe'):
            return prog_name + '.exe'
    return None


# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
