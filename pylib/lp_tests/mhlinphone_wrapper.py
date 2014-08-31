#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : mhlinphone_wrapper.py
"""
  Summary    :  tests for mh liphone wrapper

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

__author__    = "Julien Barreau"
__copyright__ = "(C) 2014 by MHComm. All rights reserved"
__email__     = "info@mhcomm.fr"

# -----------------------------------------------------------------------------
#   Imports
# -----------------------------------------------------------------------------
import logging
import os
import time

if True:
    from unittest import TestCase
else:
    class TestCase(object):
        pass

import unittest
from nose.plugins.attrib import attr
import xmlrpclib

from wrappers.bd_linphone_wrapper import MHLinphoneWrapper
from wrappers.common import ControlMessage
from lp_config import LPConfig
# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)

def isnotdev():
    return os.environ.get('DEV') != 'JULIEN'

# def skipifnotdev(*args, **kwargs):
#     return unittest.skipIf(os.environ.get('DEV') != 'JULIEN', *args, **kwargs)

class LPBaseTest(TestCase):
    """
        Base class for tests mhlinphone_wrapper
    """
    wrapper = None
    ref_count = 0
    @classmethod
    def setUpClass(cls):
        """ setUp method for tests in this class """
        logger.debug("----*---- setupclass %r", cls)
        TestCase.setUpClass()

        logger.debug('in SetUpClass, refcnt : %d', LPBaseTest.ref_count)
        if not LPBaseTest.wrapper:
            LPBaseTest.wrapper = MHLinphoneWrapper(
                rc_config_file=os.path.join(LPConfig.get_default_lp_data_dir(),
                "unit_test.linphonerc")
            )

            LPBaseTest.wrapper.init()
            if LPBaseTest.wrapper.proxy_enable:
                if not LPBaseTest.wrapper.is_ready_to_call():
                    server = LPBaseTest.wrapper.wait_for_registered(20)
                    assert server is not None
        LPBaseTest.ref_count += 1

    @classmethod
    def tearDownClass(cls):
        """ tearDown method for tests in this class """
        logger.debug('in tearDownClass, refcnt : %d', LPBaseTest.ref_count)
        LPBaseTest.ref_count -= 1
        logger.debug("----*---- tearDown class %r", cls)
        if LPBaseTest.ref_count == 0:
            TestCase.tearDownClass()
            logger.info("killing linphone")
            LPBaseTest.wrapper.exit()
            LPBaseTest.wrapper = None

@attr(needs_nothing=True)
class LPSimpleTest(LPBaseTest):
    """
        Simple tests class for mhlinphone_wrapper
    """

    def test_01_launch(self):
        """ if linphone is ready """
        LPBaseTest.wrapper.is_running()

        self.assertTrue(LPBaseTest.wrapper.is_running(),
                         msg="linphone core not running")

    def test_02_camera_exists(self):
        """ if linphone have connected camera """
        LPBaseTest.wrapper.get_status()
        cams = LPBaseTest.wrapper.webcam()

        self.assertTrue(len(cams) >= 1, "system doesn't have webcam")

    def test_03_use_camera(self):
        """ if linphone can use a camera """
        cams = LPBaseTest.wrapper.webcam()
        prefered = None
        all_cams = []
        for cam in cams:
            all_cams.append(cam)
            if "Logitech HD Pro Webcam C920" in cam:
                prefered = cams.index(cam)

        if prefered:
            cam = prefered
        else:
            cam = 0

        LPBaseTest.wrapper.webcam(cam)

        used_webcam = LPBaseTest.wrapper.get_used_webcam()
        logger.debug("cam : %r, used cam : %r", cams[cam], used_webcam)

        self.assertTrue(cams[cam] in used_webcam)


class ComLPTest(object):
# class ComLPTest(LPBaseTest):
    """
        Test class for on communication mhlinphone_wrapper
        without call tests
    """
#     config = None
#     remote_sip_addr = None
#     local_sip_addr = None
#     remote_linphone = None
#
#     @classmethod
#     def setUpClass(cls):
#         """ setUp method for tests in this class """
#         LPBaseTest.setUpClass()
#         logger.debug("----*---- setupclass %r", cls)
#         cls.config = LPConfig(LPConfig.get_default_lp_config())
#
#         rpc_addr = cls.config.get("test.address")
#         rpc_port = cls.config.get("test.port")
#
#         cls.remote_sip_addr = cls.config.get("test.remote_sip_addr")
#         logger.debug('-|-|-| remote_sip_addr : %r', cls.remote_sip_addr)
#         cls.local_sip_addr = cls.config.get("local_sip_addr")
#         logger.debug('-|-|-| local_sip_addr : %r', cls.local_sip_addr)
#
#         cls.remote_linphone = xmlrpclib.ServerProxy('http://%s:%s/MH_LP' %
#             (rpc_addr, str(rpc_port)),
#             allow_none=True,
#             )
#
#         logger.debug('--- remote: '+str(cls.remote_linphone.is_running())+
#               ' --- local: '+str(LPBaseTest.wrapper.is_running())+ ' --- '+
#               str(cls.__class__))
#
#         if not cls.remote_linphone.is_running():
#             cls.remote_linphone.init()
#             cls.remote_linphone.wait_for_registered()
#
#
# @attr(needs_rmt_lp=True, needs_net=True)
class ChatTest(object):
    pass
# class ChatTest(ComLPTest):
#
#     def test_01_com(self):
#         """ remote linphone is running  """
#         self.assertTrue(self.remote_linphone.is_running())
#         self.assertTrue(LPBaseTest.wrapper.is_running())
#
#     def test_02_chat(self):
#         """ sip message """
#         # time.sleep(3)
#         LPBaseTest.wrapper.send_message("msg1", self.remote_sip_addr)
#
#         ret = self.remote_linphone.wait_for_message(15)
#         self.assertIsNotNone(ret, "rpc wait for message fail")
#         sender, msg = ret
#         logger.debug("sender : %r, msg : %r, local addr : %r",
#              sender, msg, LPBaseTest.wrapper.identity)
#
#         self.assertEqual(sender, LPBaseTest.wrapper.identity,
#             "not same sender")
#         self.assertEqual(msg, "msg1", "not same message")
#
#
# @attr(needs_rmt_lp=True)
# @attr(needs_cam=True, needs_net=True)
class OnCallLPTest(object):
# class OnCallLPTest(ComLPTest):
    """ Test class for on call mhlinphone_wrapper """
#     def setUp(self):
#         """ setup method for call tests """
#         logger.debug("----*---- setup  %r", self)
#         ComLPTest.setUp(self)
#
#         logger.info("calling %r", self.remote_sip_addr)
#         LPBaseTest.wrapper.call(self.remote_sip_addr)
#
#         logger.debug("waiting for remote incoming")
#         ret = self.remote_linphone.wait_for_incoming(15)
#         self.assertIsNotNone(ret, "rpc wait for incoming call fail")
#
#         logger.debug("remote incoming call wait")
#         self.remote_linphone.answer()
#
#         ret = self.remote_linphone.wait_for_answered(15)
#         self.assertIsNotNone(ret, "rpc wait for answered call fail")
#
#         ret = LPBaseTest.wrapper.wait_for_answered(15)
#         self.assertIsNotNone(ret, "wait for answered call fail")
#
#         LPBaseTest.wrapper.get_status()
#
#     def tearDown(self):
#         """ tearDown method for call tests """
#         logger.debug("----*---- tearDown  %r", self)
#         ComLPTest.tearDown(self)
#
#         if LPBaseTest.wrapper.is_in_call():
#             LPBaseTest.wrapper.terminate_call()
#
#             ret = LPBaseTest.wrapper.wait_for_hangup(15)
#             self.assertIsNotNone(ret, "rpc wait for hangup call fail")
#             ret = self.remote_linphone.wait_for_hangup(15)
#             self.assertIsNotNone(ret, "rpc wait for hangup call fail")
#         else:
#             logger.warning("linphone should be on call, it isn't")
#             LPBaseTest.wrapper.terminate_call()
#
#
#     def test_01_call(self):
#         """ if linphone is on call """
#         time.sleep(3)  # 5seconds call
#         self.assertTrue(LPBaseTest.wrapper.is_in_call(),
#             "linphone is not on call, it should be")
#
#     def test_02_snapshot(self):
#         """ if linphone can take snapshot """
#         self.assertTrue(LPBaseTest.wrapper.is_in_call(),
#             "linphone is not on call, it should be")
#
#         tmp_dir = os.path.join(self.config.get_default_lp_data_dir(),
#             self.config.get('mh_lp.tmp_dir'))
#
#         snapshot_path = os.path.join(tmp_dir, "snapshot.jpg")
#
#         if not os.path.isdir(tmp_dir):
#             os.mkdir(tmp_dir)
#
#         snapshot_path, ret = LPBaseTest.wrapper.snapshot(snapshot_path)
#         logger.debug("return of snapshot : %r", str(ret))
#
#         time.sleep(1)
#
#         path_exist = os.path.exists(snapshot_path)
#
#         self.assertTrue(path_exist, "snapshot file %r doesn't exists"
#             % snapshot_path)
#
#         if path_exist:
#             os.unlink(snapshot_path)
#         else:
#             logger.error("cannot create snapshot")
#             logger.error("command result: %r", str(ret))
#
#         #TODO: assert jpeg readable
#         #TODO: assert img resolution
#
#     def test_03_preview_snapshot(self):
#         """ tests : if linphone can take preview-snapshot """
#         self.assertTrue(LPBaseTest.wrapper.is_in_call(),
#             "linphone is not on call, it should be")
#
#         tmp_dir = os.path.join(self.config.get_default_lp_data_dir(),
#             self.config.get('mh_lp.tmp_dir'))
#
#         snapshot_path = os.path.join(tmp_dir, "preview-snapshot.jpg")
#
#         if not os.path.isdir(tmp_dir):
#             os.mkdir(tmp_dir)
#
#         snapshot_path, ret = LPBaseTest.wrapper.preview_snapshot(snapshot_path)
#         logger.debug("return of preview snapshot : %r", str(ret))
#         time.sleep(1)
#
#         path_exist = os.path.exists(snapshot_path)
#
#         self.assertTrue(path_exist, "preview snapshot file %r doesn't exists"
#             % snapshot_path)
#
#         if path_exist:
#             os.unlink(snapshot_path)
#         else:
#             logger.error("cannot create preview snapshot")
#             logger.error("command result: %r", str(ret))
#
#         #TODO: assert jpeg readable
#         #TODO: assert img resolution
#
#     def test_04_msg_on_call(self):
#         """ if linphone can send message on call """
#         msg = "one verry verry long message"
#         LPBaseTest.wrapper.send_message(msg, self.remote_sip_addr)
#
#         ret = self.remote_linphone.wait_for_message(15)
#         self.assertIsNotNone(ret, "rpc wait for message fail")
#
#         (sender, rec_msg) = ret
#
#         logger.debug("sender : %r;local addr : %r", sender,
#             LPBaseTest.wrapper.identity)
#         self.assertEqual(sender, LPBaseTest.wrapper.identity,
#              "remote sender and local addr must be the same")
#         self.assertEqual(rec_msg, msg,
#              "messages must be the same")
#
#     @attr(in_dev=True)
#     @attr(needs_mh_si_srv=True)
#     def test_05_preview_snapshot_command(self):
#         """ --- preview snapshot command """
#         ctrl_msg = ControlMessage('rmt_preview_snapshot')
#         self.remote_linphone.send_control_message(LPBaseTest.wrapper.identity,
#             ctrl_msg.to_string())
#
#         # time.sleep(2)
#
#         logger.info('waiting for message')
#         ret = self.remote_linphone.wait_for_message(35)
#         self.assertIsNotNone(ret, "rpc wait for message fail")
#         if ret:
#             sender, rec_msg = ret
#             logger.debug("receive message from %r : %r", sender, rec_msg)
#         else:
#             logger.error("error waiting message")
#
#     @attr(nightly=True)
#     def test_06_stress(self):
#         """ tests : if linphone can do a lot of call, without bug """
#         self.assertTrue(LPBaseTest.wrapper.is_in_call(),
#             "linphone is not on call, it should be")
#
#         start = time.time()
#
#         # CALL_TIME = 20*60 # seconds
#         # TOTAL_TIME = 8*60*60 # seconds
#         CALL_TIME = 10 # seconds
#         TOTAL_TIME = 2*60 # seconds
#
#         while (time.time() - start) < TOTAL_TIME:
#             # assert
#             self.assertTrue(LPBaseTest.wrapper.is_in_call() and
#                 self.remote_linphone.is_in_call(),
#                 "both linphone must be on call")
#
#             # wait call_time
#             time.sleep(CALL_TIME)
#
#             # terminate
#             LPBaseTest.wrapper.terminate_call()
#             logger.info('call terminated')
#
#             ret = self.remote_linphone.wait_for_hangup(15)
#             self.assertIsNotNone(ret, "rpc wait for hangup call fail")
#
#             # assert
#             self.assertFalse(LPBaseTest.wrapper.is_in_call() or
#                 self.remote_linphone.is_in_call(),
#                 "both linphone mustn't be on call")
#
#             # call
#             LPBaseTest.wrapper.call(self.remote_sip_addr)
#             logger.debug('call launch')
#
#             # answer
#             ret = self.remote_linphone.wait_for_incoming(15)
#             self.assertIsNotNone(ret, "rpc wait incoming call fail")
#
#             self.remote_linphone.answer()
#             ret = self.remote_linphone.wait_for_answered(15)
#             self.assertIsNotNone(ret, "rpc wait answered call fail")
#             logger.debug('call answered')


def main():
    pass

if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
