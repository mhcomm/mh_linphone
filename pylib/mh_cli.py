#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : mh_cli.py
"""
  Summary    :  simple ipython debug cli

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
import threading
import logging

import readline


from six.moves import input

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)


class CLI(object):
    input_func = input

    def __init__(self, options=None, namespace=None):
        cls = self.__class__
        self._cli_thread = None
        self._options = options
        if namespace is None:
            namespace = dict(__lock=threading.Lock())
        self.namespace = namespace
        if not hasattr(namespace, '__lock'):
            namespace.update(dict(__lock=threading.Lock()))
        self._lock = namespace['__lock']

    def run(self):
        """ allows to run an ipython shell with the cli's context vars """
        namespace = self.namespace
        try:
            from IPython.terminal.embed import InteractiveShellEmbed
            use_ipython = True
        except ImportError:
            use_ipython = False
            
        if use_ipython:
            shell = InteractiveShellEmbed(user_ns=namespace)
            shell()
        else:
            self.mini_shell(namespace=namespace)

    def mini_shell(self, namespace):
        """ Rather lousy python shell for debugging.
            Just in case ipython is not installed or has the wrong version
        """
        while True:
            cmd_line = self.input_func('-->')
            upper_stripped = cmd_line.strip().upper()
            shall_quit = (upper_stripped == 'Q' or upper_stripped == 'QUIT')
            if shall_quit:
                break
            try:
                eval(compile(cmd_line, '<string>', 'single'), namespace) # pylint: disable=W0122,C0301
            except Exception as exc: # pylint: disable=W0703
                logger.error('ERROR: %r' % exc)

        print("END OF CLI")
        self.write_history()

    def write_history(self, fname=None):
        pass

    def run_as_thread(self, name='cli', daemon=True):
        """ start cli as a thread
            This is needed for Qt Apps, where the GUI must be called in the main thread
        """
        self._cli_thread = cli_thread = threading.Thread(target=self.run, 
            name=name)
        cli_thread.daemon = daemon 
        cli_thread.start()


def main():
    pass

if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
