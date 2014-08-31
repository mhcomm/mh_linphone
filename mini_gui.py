#!/usr/bin/env python

# #############################################################################
# Copyright : (C) 2014 by MHComm. All rights reserved
#
# Name       : mini_gui.py
"""
  Summary :     minimal GUI, use to dev

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

 simple gui, 2 windows and an ipython CLI

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
import time
import xmlrpclib

import set_paths
from log_config.config import setup_logging
from lp_config import LPConfig



# pylint: disable=E1101
if hasattr(sys, 'frozen') and sys.frozen in [ "windows_exe", "console_exe" ]:
    __file__ = sys.executable
# pylint: enable=E1101

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = None
MYNAME = os.path.splitext(os.path.basename(__file__))[0]

item = None
rpc_client = None
linphone_wrap = None
config = None

def auto_answer(caller):
    linphone_wrap.answer()

def unzip_test(url):
    """ example of ExchangeItem.make_from_url """
    from wrappers.common import SnapshotItem
    from wrappers.common import WebClient

    global item
    global config

    if config is not None:
        https_key = config.get('http.key', None)
        https_cert = config.get('https.cert', None)
        ssl_verify = config.get('https.ssl_verify', True)
        cert_info = (https_cert, https_key)
        webclient = WebClient(cert=cert_info, ssl_verify=ssl_verify)
    else:
        webclient = None

    app_data_dir = LPConfig.get_default_lp_data_dir()
    tmp_dir = LPConfig().get('mh_lp.tmp_dir')
    tmp_dir = os.path.join(app_data_dir, tmp_dir)


    item = SnapshotItem.fetch_from_url(tmp_dir, url, webclient=webclient)
    logger.debug('info : %r', item.info_json['filename'])

    item.unzip(item.info_json['filename'],
       os.path.join(tmp_dir, item.info_json['filename']))



class Scenarios(object):
    @staticmethod
    def scenario1_apply_profiles():
        """ call, answer, and apply profile, 3 time
            with sleep(7) in each mode
        """
        global linphone_wrap
        global rpc_client

        other_addr = LPConfig().get('test.remote_sip_addr')
        linphone_wrap.call(other_addr)
        rpc_client.wait_for_incoming()
        rpc_client.answer()
        linphone_wrap.wait_for_answered()

        linphone_wrap.apply_profile("3g")
        linphone_wrap.show_tx_stats()
        rpc_client.show_rx_stats()
        time.sleep(7)
        linphone_wrap.apply_profile("fluid")
        linphone_wrap.show_tx_stats()
        rpc_client.show_rx_stats()
        time.sleep(7)
        linphone_wrap.apply_profile("quality")
        linphone_wrap.show_tx_stats()
        rpc_client.show_rx_stats()
        time.sleep(7)

        linphone_wrap.terminate_call()

    @staticmethod
    def scenario2_cancel_call():
        """
        """
        global linphone_wrap
        global rpc_client

        other_addr = LPConfig().get('test.remote_sip_addr')
        linphone_wrap.call(other_addr)
        rpc_client.wait_for_incoming()
        time.sleep(5)

        linphone_wrap.terminate_call()


def mk_parser():
    """ commandline parser """
    log_config = os.environ.get("MH_LOG_CONFIG", MYNAME)
    description = "simple gui for debugging with CLI "
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--log-config", "-l", default=log_config,
        help="set the log config")
    parser.add_argument("--cli", "-c", action='store_true',
        help="starts a CLI for debugging")

    parser.add_argument("--xmlrpcsrv", "-s", metavar="ADDR:PORT",
        nargs='?', help="set xml rpc server", default=None)

    parser.add_argument("--linphonerc", "-r", metavar="RCFILE",
        help="set a linphonerc file for configuration", default=None)
    parser.add_argument("--config-file", "-C", metavar="FNAME",
        help="set a linphonerc file for configuration", default=None)

    parser.add_argument("--auto-answer", "-a", action="store_true",
        help="automatically answer incoming calls")
    return parser


def show(do_show=True):
    logger.debug("SHOW %r", do_show)
    print('-----------------------')


def quit_app():
    logger.debug("quit_app")
    print('_______________________')

def main():
    global logger
    global item
    global rpc_client
    global linphone_wrap
    global config


    args = sys.argv[1:]
    parser = mk_parser()
    options = parser.parse_args(args)
    setup_logging(options.log_config)
    logger = logging.getLogger(__name__)

    import mhlinphone_wrapper
    from linphone import linphone
    from wrappers import common
    from lp_rpc_server import lp_rpc_server
    from lp_config import LPConfig

    from python_qt_binding.QtGui import QApplication
    from python_qt_binding.QtGui import QWidget
    from python_qt_binding.QtGui import QDesktopWidget
    
    app = QApplication(sys.argv)
    preview_widget=QWidget()
    view_widget=QWidget()

    for w in [preview_widget,view_widget]:
        w.setBaseSize(300,300)
        w.show()
        wid = w.winId()
        print("WID %s %s" % (hex(wid), int(wid)))

    screen = QDesktopWidget()
    preview_widget.move(screen.width() - preview_widget.width(), 0)
    view_widget.move(screen.width() - view_widget.width(), screen.height() - view_widget.height())

    config=None
    if options.config_file:
        config = LPConfig(options.config_file)

    linphone_wrap = mhlinphone_wrapper.MHLinphoneWrapper(rc_config_file=options.linphonerc,
        config=config)
    linphone_wrap.init()

    if options.xmlrpcsrv:
        rpc_funcs = lp_rpc_server.MHLPFuncs(linphone_wrap,
            quit_func=quit_app, show_func=show)

        addr, port = (options.xmlrpcsrv + ':8000').split(':')[:2]
        rpc_server = lp_rpc_server.LPRpcServer(linphone_wrap, addr, int(port),
            rpc_funcs)
        rpc_server.start_in_thread()
    else:
        rpc_server = None

    if options.auto_answer:
        linphone_wrap.register_callback(linphone_wrap.EVT.INCOMING,
            auto_answer)

    linphone_wrap.set_vvideo(int(view_widget.winId()))
    linphone_wrap.set_pvideo(int(preview_widget.winId()))

    linphone_wrap.register_callback(linphone_wrap.EVT.RMT_PREVIEW_SNAPSHOT, unzip_test)

    addr = linphone_wrap.config.get('test.address')
    port = linphone_wrap.config.get('test.port')
    rpc_client = xmlrpclib.ServerProxy('http://'+addr+':'+str(port)+'/MH_LP')


    def dirfind(str, *objs):
        ret = []
        if not objs:
            objs = dir(linphone)
        for obj in objs:
            ret.extend([ (obj, v) for v in dir(obj) if str in v.lower() ])
        return ret


    def start(fname): #open file under win
        os.system('cmd /c start ' + fname)

    if options.cli:
        from mh_cli import CLI
        namespace = dict(
            dirfind=dirfind,
            start=start,
            linphone=linphone,
            os=os,
            app=app,
            preview_widget=preview_widget,
            view_widget=view_widget,
            mhlinphone_wrapper=mhlinphone_wrapper,
            lin=linphone_wrap,
            args=args,
            options=options,
            logger=logger,
            rpc_server=rpc_server,
            rpc_client=rpc_client,
            remote_sip_addr=linphone_wrap.config.get('test.remote_sip_addr'),
            local_sip_addr=linphone_wrap.config.get('local_sip_addr'),
            item=item,
            sce= Scenarios,
            auto_ans= auto_answer,
        )
        cli = CLI(options, namespace=namespace)
        cli.run_as_thread(daemon=False)

    exitcode = app.exec_()
    sys.exit(exitcode)


if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
