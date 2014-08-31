#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : mh_qtwrapper.py
"""
  Summary    :  helper to write code that runs with PyQt and PySide

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

# choose QT binding for python_qt_binding module
# this change just sets an attribute in the sys module 
# and should have no other impact if python_qt_binding
# is not used
qt_binding = os.environ.get('QT_BINDING', None)
if qt_binding in [ 'pyqt', 'pyside' ]:
    setattr(sys, 'SELECT_QT_BINDING', qt_binding)

from python_qt_binding import QT_BINDING
from python_qt_binding import QtCore as Qc

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------


QString = unicode # SHOULD NOT BE USED FOR ANY NEW CODE. Use unicode directly

qt_binding_version = None
qt_binding_version_str = None

if QT_BINDING == 'pyside':
    qt_binding_version_str = Qc.__version_info__ #pylint: disable=E1101
    qt_binding_version = Qc.__version__ # pylint: disable=E1101
else:
    qt_binding_version_str = Qc.PYQT_VERSION_STR
    qt_binding_version = Qc.PYQT_VERSION
    Qc.Signal = Qc.pyqtSignal 
    Qc.Slot = Qc.pyqtSlot

# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
