
#!/usr/bin/env python

# #############################################################################
# Copyright : (C) 2014 by MHComm. All rights reserved
#
# Name       : run_test.py
"""
  Summary :     Run tests using nose

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

__author__ = "Kevin Man Sang"
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

import nose

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
    description = "Run tests with nose, run it at the project root"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--nocapture', '-s', action='store_true',
        help="don't capture stdout")
    parser.add_argument('--where', '-w', action='append',
        help="paths to search tests in")
    parser.add_argument('--attr', '-a', action='append', default=None,
        help="attribute for tests to launch")
    parser.add_argument("--stop", "-x", action='store_true', default=False,
        help="stop after first error or faillure")
    #parser.add_argument('--no-verify', '-n', action='store_true', default=False)
    #parser.add_argument('offset', type=int, nargs='?', default=0)
    parser.add_argument("--log-config", "-l", default=log_config,
        help="set the log config")

    return parser


def main():
    global logger
    args = sys.argv[1:]
    parser = mk_parser()
    options = parser.parse_args(args)
    setup_logging(options.log_config)
    logger = logging.getLogger(__name__)

    argv = [ sys.argv[0]]
    argv.extend(['-c', '.noserc'])
    if options.nocapture:
        argv.append('-s')

    if not options.where:
        options.where = ['.', 'pylib']

    if options.where:
        print('W: %r' % options.where)
        argv.extend(['-w'])
        for where in options.where:
            argv.extend([where])

    if options.attr:
        print('attr: %r' % options.attr)
        argv.extend(['-a'])
        for attr in options.attr:
            argv.extend([attr])

    if options.stop:
        argv.append('-x')
    print(argv)
    if not argv:
        argv=argv

    print('argv: %r' % argv)

    nose.main(argv=argv)


if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
