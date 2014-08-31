#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : log_config.socket_handler
"""
  Summary    :  allows logging to a socket server

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
import logging
from logging.handlers import SocketHandler
from logging.handlers import DEFAULT_TCP_LOGGING_PORT

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------

def mk_filter(service_name):
    """ creates a socket filter class with that injects a given service name 
    """
    class ContextFilter(logging.Filter):
        """ closure filter class injecting service name  """
        def filter(self, record): # pylint: disable=C0103
            """ inject service name """
            record.service = service_name
            return True
    return ContextFilter()


class NamedSocketHandler(SocketHandler):
    """ socket handler with a 'service_name' tag """
    def __init__(self, host="localhost", port=DEFAULT_TCP_LOGGING_PORT,
            service_name=None):
        if service_name is None:
            import __main__
            service_name=__main__.__name__
        SocketHandler.__init__(self, host, port)

        filt = mk_filter(service_name)
        self.addFilter(filt)

def main():
    """ the main function """

if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
