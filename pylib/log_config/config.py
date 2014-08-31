#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : log_config.config
"""
  Summary    :  helper for setting up logging

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

helper module to setup logging

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
import importlib
try:
    from logging.config import dictConfig
except ImportError:
    from dictconfig import dictConfig

import __main__ # required to get name of executable

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------

def setup_logging(log_config=None, log_dir='', try_sample=True):
    """ sets up logging. falls back to default logging if config for
        the current program doesn't exist
    """
    program_name = os.path.splitext(os.path.basename(__main__.__file__))[0]
    if log_config:
        module_name = "log_config." + log_config
    else:
        program_name = os.path.splitext(os.path.basename(__main__.__file__))[0]
        module_name = "log_config." + program_name
          
    #print("LOG_CONF %r" % module_name)
    global exc
    try:
        mod = importlib.import_module(module_name)
    except ImportError as _exc:
        exc = _exc
        #print("ERR: %r" % _exc.args[0])
        missing_error = 'No module named ' + module_name.split('.')[-1]
        #print("MIS: %r" % missing_error)
        if not _exc.args[0] == missing_error:
            raise
        if try_sample:
            #print("WARNING %s. will try sample log settings" % _exc)
            setup_logging(log_config+"-sample", try_sample=False) # try sample
            return
        if log_config.split('-')[0] != 'default':
            #print("WARNING %s. will try default log settings" % _exc)
            setup_logging('default') # otherwise default config then
            return
        raise
    if hasattr(mod, 'log_settings'):
        log_settings = mod.log_settings
    else:
        log_settings = mod.get_log_settings(basedir=log_dir, basename=program_name + '.log')

    #print("set up log:\n", log_settings)
    dictConfig(log_settings)

# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
