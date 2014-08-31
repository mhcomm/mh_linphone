#!/usr/bin/env python

# #############################################################################
# Copyright : (C) 2014 by MHComm. All rights reserved
#
# Name       : tst_rpc_client.py
"""
  Summary :  small rpc_client for et

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

__author__ = "Klaus Foerster"
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
import xmlrpclib
import functools

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

def setup_client(options):
    addr, port = (options.xmlrpcsrv + ':8000').split(':')[:2]
    rpc_client = xmlrpclib.ServerProxy('http://'+addr+':'+str(port)+'/MH_LP')
    return rpc_client

def helpfunc(rpc):
    print("please type rpc.<functionname>(<args>) tu run a comand")
    return rpc.system.listMethods()
    
def mk_parser():
    """ commandline parser """
    log_config = os.environ.get("MH_LOG_CONFIG", MYNAME)
    description = "small helper to send commands via ipython/xmlrpc"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--log-config", "-l", default=log_config,
        help="allows to setup a log config")
    parser.add_argument("--xmlrpcsrv", "-s", metavar="ADDR[:PORT]",
            nargs='?', default='localhost',
            help="specify  rpcserver address. dflt = localhost:8000")
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
    rpc = setup_client(options)
    myhelp = functools.partial(helpfunc, rpc)
    if options.cli or True:
        from mh_cli import CLI
        namespace = dict(
            hlp=myhelp,
            os=os,
            sys=sys,
            args=args,
            options=options,
            rpc=rpc,
        )
        msg = "Please type hpl() for some help"
        print("="*len(msg))
        print(msg)
        print("="*len(msg))
        cli = CLI(options, namespace=namespace)
        #cli.run_as_thread(daemon=False)
        cli.run()

if __name__ == '__main__':
    main()
## -----------------------------------------------------------------------------
##   End of file
## -----------------------------------------------------------------------------
