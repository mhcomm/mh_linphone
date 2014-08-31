#!/usr/bin/env python

# #############################################################################
# Copyright : (C) 2014 by MHComm. All rights reserved
#
# Name       : mh_linphone.py
"""
  Summary :     simple PyQt-GUI for linphone

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

A simple QT front-end for Linphone intended for Doctor - Patient calls

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
import sys
import argparse
import logging
from functools import partial

import set_paths
import mh_qtwrapper

from python_qt_binding import QtGui

from lp_config import LPConfig
from log_config.config import setup_logging

# sets __file__ attribute even if compiled with py2exe
# pylint: disable=E1101
if hasattr(sys, 'frozen') and sys.frozen in ["windows_exe", "console_exe"]:
    # pylint: enable=E1101
    __file__ = sys.executable
# pylint: enable=E1101

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
TOP_DIR = os.path.dirname(__file__)
logger = None
exc = None
MYNAME = os.path.splitext(os.path.basename(__file__))[0]


def mk_parser():
    """ commandline parser """
    log_config = os.environ.get("MH_LOG_CONFIG", MYNAME)
    description = "GUI front end for visiophony"

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument("--log-config", "-l", default=log_config,
        help="allows to setup a log config")

    parser.add_argument("--cli", "-c", action='store_true',
        help="starts a CLI for debugging")

    parser.add_argument("--start-xmlrpcsrv", "-s", action='store',
        metavar='ADDR[:PORT]',
        help="start an xml rpc server for debugging")

    parser.add_argument('--fullscreen', '-f', action='store_true',
                    help='launch video screen in full screen')

    parser.add_argument('--css-file', '-e', type=str, default=None,
                    help='Applies this CSS to application')

    parser.add_argument('--i18n-dir', '-t', 
                help='Applies mo files from this i18n dir')
    
    parser.add_argument('--advanced-interface', '-i', type=int,
                    help='Activates advanced gui(call & quality adjustments)')
    return parser

def show(widget, do_show=True):
    logger.debug("SHOW %r", do_show)
    if do_show:
        widget.show()
    else:
        widget.hide()
    else:


def quit_app(widget):
    logger.debug("quit_app")
    widget.close()
    print('________ Complete me please _______________')


def main():
    """
    Main
    """
    global logger
    args = sys.argv[1:]

    config = LPConfig()
    log_dir = config.get('mh_lp.log_dir')
    if not log_dir:
        log_dir = '.'
    parser = mk_parser()
    options = parser.parse_args(args)
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    setup_logging(options.log_config, log_dir=log_dir)
    logger = logging.getLogger(__name__)
    logger.debug("MH_LINPHONE START")
    logger.info("CONFIG_FILE: %r", config.filename)

    import mhlinphone_wrapper
    from lp_rpc_server import lp_rpc_server
    from lpqt.widgets.video_window import set_locale, WIN_TITLE
    from lpqt.widgets.video_window import MHVideoWindow


    linphone = mhlinphone_wrapper.MHLinphoneWrapper(
        config=config,
        # rc_config_file=os.path.join(LPConfig.get_default_lp_data_dir(),
        #                     "samples",
        #                     "dev")
    )

    #Get options
    css_path = options.css_file
    i18n_dir = options.i18n_dir
    fullscreen_enabled = options.fullscreen
    advanced_interface = options.advanced_interface

    rls_dir = os.path.join(TOP_DIR, "pylib", "lpresources")
    if i18n_dir is None:
        i18n_dir = os.path.join(rls_dir,"locale")

    #i18n
    set_locale(i18n_dir)

    if css_path is None:
        css_path = os.path.join(rls_dir, 'css', 'mh_linphone.css')

    css_path = os.path.realpath(css_path)

    #Creat app
    app = QtGui.QApplication(sys.argv)

    #Create Video Widget
    mh_linphone_widget = MHVideoWindow(pm_css_path=css_path,
                                       pm_config=config,
                                       pm_advanced_interface=advanced_interface,
                                       )

    if options.start_xmlrpcsrv: # for debugging
        addr, port = (options.start_xmlrpcsrv + ':8080').split(':')[:2]

        my_quit_func = partial(quit_app,  mh_linphone_widget)
        my_show_func = partial(show,  mh_linphone_widget)

        rpc_funcs = lp_rpc_server.MHLPFuncs(linphone,
            quit_func=my_quit_func, show_func=my_show_func)

        rpc_server = lp_rpc_server.LPRpcServer(linphone, addr, int(port),
            rpc_funcs)
        rpc_server.start_in_thread()
    else:
        rpc_server = None



    #Set Video Engine and register callbacks
    mh_linphone_widget.set_engine(linphone)
    mh_linphone_widget.register_callbacks()

    mh_linphone_widget.setWindowTitle(WIN_TITLE)

    if fullscreen_enabled:
        mh_linphone_widget.showFullScreen()
    else:
        mh_linphone_widget.show()

    #Launch video engine
    mh_linphone_widget.launch_video_engine()

    if options.cli: # for debugging
        from mh_cli import CLI
        namespace = dict(
            os=os,
            app=app,
            mhlinphone_wrapper=mhlinphone_wrapper,
            lin=linphone,
            args=args,
            options=options,
            logger=logger,
            rpc_server=rpc_server,
        )
        cli = CLI(options, namespace=namespace)
        cli.run_as_thread(daemon=False)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
