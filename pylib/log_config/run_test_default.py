#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : log_config.run_test.py
"""
  Summary    :  default log configuration for this project

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
import os

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------

def get_log_settings(basedir='', basename='log'):
    """ returns a log configuration dict """
    logfile = os.path.join(basedir, basename)
    log_settings = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'verbose': {
                'format': '%(levelname)-8s %(asctime)s %(threadName)s %(name)s %(message)s'
            },
            'simple': {
                'format': '%(levelname)s %(module)s %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level':'DEBUG',
                'class':'logging.StreamHandler',
                'formatter': 'verbose'
            },
            'file': {
                'level':'DEBUG',
                'class':'logging.FileHandler',
                'formatter': 'verbose',
                'filename' : logfile,
                'mode' : 'w'
            }
        },
        'loggers': {
            # root loggers
            '': {
                'level': 'DEBUG',
                'handlers': ['console', 'file'],
                'propagate': True,
            },
            'wrappers.linphonecwrapper': {
                'level': 'DEBUG',
                'handlers': ['console','file'],
                'propagate': True,
            },
        }
    }
    return log_settings

# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
