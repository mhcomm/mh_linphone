#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : lp_rpc_server
"""
  Summary    :  rpc server for linphone wrapper

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

 rpc server to access fionctionnalities of linphone wrapper

"""
# #############################################################################
from __future__ import absolute_import
from __future__ import print_function

__author__    = "Julien Barreau"
__copyright__ = "(C) 2014 by MHComm. All rights reserved"
__email__     = "info@mhcomm.fr"

# -----------------------------------------------------------------------------
#   Imports
# -----------------------------------------------------------------------------
import logging
from wrappers.bd_linphone_wrapper import Event
import socket

from threading import Thread
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

# from wrappers.bd_linphone_wrapper import MHLinphoneEvents

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)


class OurXMLRPCServer(SimpleXMLRPCServer):
    allow_reuse_address = True


class RequestHandler(SimpleXMLRPCRequestHandler):
    """ request handler for rpc server """
    rpc_paths = ('/MH_LP',)


def logwrap(name, func):
    def wrapper(*args, **kwargs):
        logger.debug("RPCCALL start: %s %r %r", name, args, kwargs)
        ret = func(*args, **kwargs)
        logger.debug("RPCALL end: %s %r", name, ret)
        return ret

    return wrapper


class LPRpcServer(object):
    """
        RPC server for linphone wrapper
    """
    exclude_funcs = ["execute", "EVT", "join", "run", "getName", "setName",
        "is_command_response_to", "isAlive", "isDaemon", "setDaemon"]

    def __init__(self, engine, addr='localhost', port=8000, mh_lp_funcs=None):
        cls = self.__class__
        if mh_lp_funcs is None:
           self.funcs = MHLPFuncs(engine)
        else:
            self.funcs = mh_lp_funcs
        # Create server
        server = self.server = OurXMLRPCServer((addr, port),
            requestHandler=RequestHandler,
            allow_none=True,
        )
        self.thread = None

        for attr in dir(engine.__class__):
            if attr.startswith('_'):
                continue
            if attr in cls.exclude_funcs:
                continue

            func = getattr(engine, attr)
            if not hasattr(func, '__call__'):
                continue

            wrapped = logwrap(attr, func)
            server.register_function(wrapped , attr)

        self.server.register_instance(self.funcs)
        self.server.register_introspection_functions()

    def start(self):
        """ start rpc server in current thread """
        self.server.serve_forever()

    def start_in_thread(self):
        """ start rpc server in a dedicatedd thread """
        thread = Thread(target=self.start, name='rpc_server thread')
        thread.daemon = True
        thread.start()
        self.thread = thread

class MHLPFuncs(object):
    """
        functions for rpc server to add to wrapper's functions
    """
    def __init__(self, engine, quit_func=None, show_func=None):
        self.engine = engine
        self.quit_func = quit_func
        self.show_func = show_func

    def get_current_call_contact(self):
        """ return (id, sip_addr) of current call contact """
        current_call = self.engine.current_call
        if current_call:
            sip_addr = current_call.remote_address_as_string
            contact = self.engine.get_adress_book().find_by_address(sip_addr)
            if not contact:
                return ("unfound", sip_addr)
            return (contact.id_, sip_addr)
        return None

    def clear_event(self, name):
        ev = getattr(self.engine, name, None)
        if ev is None:
            logger.warning("unknown event name %r", name)
            return False
        ev.clear()
        return True

    def quit_linphone(self):
        if self.quit_func is None:
            logger.error('no quit functions specified')
            return 0
        return self.quit_func()

    def show_linphone(self, do_show=True):
        if self.show_func is None:
            logger.error('no quit functions specified')
            return 0
        return self.show_func(do_show)


def main():
    """ The main for testing"""
    pass

if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
