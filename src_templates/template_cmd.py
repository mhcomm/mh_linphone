#!/usr/bin/env python

# #############################################################################
# Copyright : (C) 2014 by MHComm. All rights reserved
#
# Name       : template.py
"""
  Summary :     <enter a mandatory>

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

 <multline description here>

"""
# #############################################################################
from __future__ import absolute_import
from __future__ import print_function

__author__ = AUTH_STR
__copyright__ = "(C) 2014 by MHComm. All rights reserved"
__email__     = "info@mhcomm.fr"

# -----------------------------------------------------------------------------
#   Imports
# -----------------------------------------------------------------------------
import os
import sys

import argparse
import logging

import set_paths

from log_config.config import setup_logging

# pylint: disable=E1101
if hasattr(sys, 'frozen') and sys.frozen in [ "windows_exe", "console_exe" ]:
    __file__ = sys.executable
# pylint: enable=E1101

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = None
MYNAME = os.path.splitext(os.path.basename(__file__))[0]

def mk_parser():
    """ commandline parser """
    log_config = os.environ.get("MH_LOG_CONFIG", MYNAME)
    description = SHORT_DOC_STRING
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--log-config", "-l", default=log_config,
        help="allows to setup a log config")
    parser.add_argument("--cli", "-c", action='store_true',
        help="starts a CLI for debugging")
    return parser
    

def main():
    global logger
    args = sys.argv[1:]
    parser = mk_parser()
    options = parser.parse_args(args)
    setup_logging(options.log_config)
    logger = logging.getLogger(__name__)
    if options.cli:
        from mh_cli import CLI
        namespace = dict(
            args=args,
            options=options,
        )
        cli = CLI(options, namespace=namespace)
        cli.run_as_thread(daemon=False)

if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
