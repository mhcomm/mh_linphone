# !/usr/bin/env python
#
# # Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : wrappers.bd_linphone_wrapper
"""
  Summary    : Wrapper for the linphone python binding 

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
from __future__ import absolute_import
from __future__ import print_function


__author__ = "Julien Barreau"
__copyright__ = "(C) 2014 by MHComm. All rights reserved"
__email__ = "info@mhcomm.fr"

# -----------------------------------------------------------------------------
#   Imports
# -----------------------------------------------------------------------------
import logging
import os
import threading
from threading import Event as _Event
from functools import partial
import time
import datetime
from collections import defaultdict
import tempfile
import traceback
import operator
import re
from set_paths import TOP_DIR

from six.moves import queue
from linphone import linphone

from .common import ControlMessage, MHLinphoneEvents, SnapshotItem
from .common import synchronized
from lp_contacts import AddressBook
from lp_config import LPConfig
from lp_rc_manipulator import LpRcManipulator

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)
lp_logger = logging.getLogger('linphone')

class Event(object):
    trace = True
    cnt = 0
    def __init__(self, name=None):
        cls = self.__class__
        self.name = name if name else str(cls.cnt)
        cls.cnt += 1

        self.ev = _Event()
    def set(self):
        if self.trace:
            logger.debug("EV_%r : set", self.name)
        self.ev.set()

    def wait(self, *args, **kwargs):
        if self.trace:
            logger.debug("EV_%r : wait start", self.name)
        rslt = self.ev.wait(*args, **kwargs)
        if self.trace:
            logger.debug("EV_%r : wait end, rslt : %r ", self.name, rslt)
        return rslt

    def clear(self):
        if self.trace:
            logger.debug("EV_%r : clear", self.name)
        self.ev.clear()


class StoppableThread(threading.Thread):
    """ Base class for stoppable thread """
    def __init__(self):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()

    def stop(self):
        """ Stop the thread and wait for correct termination
        """
        if self.isAlive() == True:
            # Set an event to signal the thread to terminate
            self.stop_event.set()
            # Block the calling thread until the thread really has terminated
            self.join()

class IntervalTimer(StoppableThread):
    """ class for linphone core thread """

    def __init__(self, interval, worker_func, kwargs=None):
        """ constructor
        """
        StoppableThread.__init__(self)

        if kwargs is None:
            kwargs = {}

        self._interval = interval
        self._worker_func = worker_func
        self._kwargs = kwargs

    def run(self):
        """ run method of thread
        """
        while not self.stop_event.is_set():
            self._worker_func(self._kwargs)
            time.sleep(self._interval)

class MHLinphoneError(Exception):
    """
     custom errors
    """


class MHLinphoneWrapper(object):

    """ class for mh linphone wrapper """
    EVT = MHLinphoneEvents
    core_lock = threading.RLock()
    lock = threading.RLock()
    call_state_queue_max_size = 10

    @staticmethod
    def encode_str(val):
        if type(val) == str:
            return val

        return val.encode('utf-8')

    ######### init and exit functions #########
    def __init__(self, rc_config_file=None, rc_factory_file=None, config=None):
        assert(linphone.__version__ >= '3.7.0-714')

        # config should be set as early as possible
        if config is None:
            config = LPConfig()
        self.config = config

        #TODO: partial(set theses callbacks)
        self.mh_callbacks = {}
        self.callbacks = defaultdict(partial(self.default_callback, "unknown"),
            # 'global_state_changed':global_state_changed,
            # 'registration_state_changed': None,
            # 'call_state_changed':   None,
            # 'display_message': None,
            global_state_changed= self.cb_global_state_changed,
            call_state_changed= self.cb_call_state_changed,
            # is_composing_received=self.cb_is_composing_received,
            message_received= self.cb_message_received,
            registration_state_changed= self.cb_registration_state_changed,
            # call_log_updated= self.cb_call_log_updated,

            # 'call_state_changed': default_callback,
            # registration_state_changed= default_callback,
            # notify_presence_received= default_callback,
            # new_subscription_requested= default_callback,
            # auth_info_requested= default_callback,
            # call_log_updated= default_callback,
            # is_composing_received= default_callback,
            # dtmf_received= default_callback,
            # refer_received= default_callback,
            # call_encryption_changed= default_callback,
            # transfer_state_changed= default_callback,
            # buddy_info_updated= default_callback,
            # call_stats_updated= default_callback,
            # info_received= default_callback,
            # subscription_state_changed= default_callback,
            # notify_received= default_callback,
            # configuring_status= default_callback,
            # display_status= default_callback,
            # display_message= default_callback,
            # display_warning= default_callback,
            # display_url= default_callback,
            # show= default_callback,

            # call_state_changed=\
                # partial(self.default_callback, "call_state_changed"),
            # registration_state_changed=\
                # partial(self.default_callback, "registration_state_changed"),
            notify_presence_received=\
                partial(self.default_callback, "notify_presence_received"),
            new_subscription_requested=\
                partial(self.default_callback, "new_subscription_requested"),
            auth_info_requested=\
                partial(self.default_callback, "auth_info_requested"),
            call_log_updated=\
                partial(self.default_callback, "call_log_updated"),
            is_composing_received=\
                partial(self.default_callback, "is_composing_received"),
            dtmf_received=partial(self.default_callback, "dtmf_received"),
            refer_received=partial(self.default_callback, "refer_received"),
            call_encryption_changed=\
                partial(self.default_callback, "call_encryption_changed"),
            transfer_state_changed=\
                partial(self.default_callback, "transfer_state_changed"),
            buddy_info_updated=\
                partial(self.default_callback, "buddy_info_updated"),

            #TODO: catch this event log it in file
            # call_stats_updated= partial(self.default_callback,
                # "call_stats_updated"),
            info_received=\
                partial(self.default_callback, "info_received"),
            subscription_state_changed=\
                partial(self.default_callback, "subscription_state_changed"),
            notify_received=partial(self.default_callback, "notify_received"),
            configuring_status= \
                partial(self.default_callback, "configuring_status"),
            display_status= partial(self.default_callback, "display_status"),
            display_message= partial(self.default_callback, "display_message"),
            display_warning= partial(self.default_callback, "display_warning"),
            display_url= partial(self.default_callback, "display_url"),
            show= partial(self.default_callback, "show"),

        )

        def lp_log_handler(level, msg):
            method = getattr(lp_logger, level)
            try:
                msg = msg.decode('utf-8')
            except:
                try:
                    msg = msg.decode('cp1252')
                except:
                    msg = msg.decode('utf-8', 'replace')
            method(msg)

        linphone.set_log_handler(lp_log_handler)

        #TODO:bug when a rc file is set, open an unused video window
        self.rc_config_file = rc_config_file
        self.rc_factory_file = rc_factory_file

        self.ready = False

        self.current_call = None
        self.chat_room = None
        self.address_book = None
        self.url = None
        self.call_state_queue = queue.Queue(self.call_state_queue_max_size)

        self.worker_queue = queue.Queue()
        self.worker_thread_exit = False
        self.worker_thread = threading.Thread(target=self.worker_proc,
            name="worker_thread")
        self.worker_thread.daemon = True

        self.core_thread_exit = False
        self.core_thread = threading.Thread(target=self._core_thread,
            name="core_thread")
        self.core_thread.daemon = True

        ##wait_for declarations
        #registered
        self.registered_event = Event()
        self.registered_event.clear()
        self.registered_server = None

        #message
        self.msg_sender = None
        self.msg_text = None
        self.msg_event = Event()
        self.msg_event.clear()

        #call state change
        self.call_state_change_event = Event()
        self.call_state_change_event.clear()

        #incoming call
        self.incoming_event = Event()
        self.incoming_event.clear()
        self.incoming_call = None

        #answered call
        self.answered_event = Event()
        self.answered_event.clear()

        #call updated
        self.call_updated_event = Event()
        self.call_updated_event.clear()

        #stream establish
        self.stream_established_event = Event()
        self.stream_established_event.clear()

        #hanged up call
        self.hangup_event = Event()
        self.hangup_event.clear()

        self._register_callbacks()

        # Set wrappers params with params in config file
        self.http_url = self.config.get('http.url')
        self.https_key = self.config.get('http.key', None)
        self.https_cert = self.config.get('https.cert', None)
        self.ssl_verify = self.config.get('https.ssl_verify', True)

        self.proxy_identity = None
        self.identity = None

        self.config_identity = self.config.get('mh_lp.local_sip_addr')
        self.proxy_enable = self.config.get("proxy.enable", False)
        if self.proxy_enable:
            self.identity = self.proxy_identity
        else:
            self.identity = self.config_identity

        if self.rc_config_file:
            rc_config = LpRcManipulator(self.rc_config_file)
            rc_config.read_rc_file()
            if not self.proxy_enable:
                rc_config.set_item('net', 'firewall_policy', 'nat_address')
                my_addr = self.identity.split('@')[1]
                rc_config.set_item('net', 'nat_address', my_addr)

            rc_config.enable_linphone_window(False)
            rc_config.write_rc_file()

        self.core = linphone.Core.new(self.callbacks, self.rc_config_file,
            self.rc_factory_file)

        # Set Core params with params in config file
        with self.core_lock:
            self._set_params()

    def _set_params(self):
        upload = self.config.get('bandwidth.upload', 0)
        download = self.config.get('bandwidth.download', 0)
        self.set_bandwidth(upload, download)

        webcam_device = self.config.get('video.webcam', None)
        if webcam_device:
            self.webcam(webcam_device)

        microphone_device = self.config.get('audio.micro', None)
        if microphone_device:
            self.microphone(microphone_device)

        speaker_device = self.config.get('audio.speaker', None)
        if speaker_device:
            self.speaker(speaker_device)

        ring_file = self.config.get('sound.ring', None)
        if ring_file:
            ring_file = os.path.join(TOP_DIR, ring_file)
            self.core.ring = self.encode_str(ring_file)
            self.core.ring_level = 10
        ring_back_file = self.config.get('sound.ringback', None)
        if ring_back_file:
            ring_back_file = os.path.join(TOP_DIR, ring_back_file)
            self.core.ringback = self.encode_str(ring_back_file)

    def _register_callbacks(self):
        """ register callback functions for rpc wait """
        self.register_callback(MHLinphoneEvents.REGISTERED,
              self._cb_registered, 'used by wait_for_registered')
        self.register_callback(MHLinphoneEvents.TERMINATED,
              self._cb_hangup, 'used by wait_for_hangup')
        self.register_callback(MHLinphoneEvents.INCOMING,
              self._cb_incoming, 'used by wait_for_incoming')
        self.register_callback(MHLinphoneEvents.MESSAGE,
              self._cb_message, 'used by wait_for_message')
        self.register_callback(MHLinphoneEvents.ANSWERED,
              self._cb_answered, 'used by wait_for_answered')
        self.register_callback(MHLinphoneEvents.STREAM_ESTABLISHED,
              self._cb_stream_established, 'used by wait_for_stream_establish')
        self.register_callback(MHLinphoneEvents.CALL_STATE_CHANGED,
              self._cb_call_state_changed, 'used by wait_for_call_state_change')
        self.register_callback(MHLinphoneEvents.CALL_UPDATED,
              self._cb_call_updated, 'used by wait_for_call_updated')

    def init(self):
        self.worker_thread.start()
        self.core_thread.start()

    def exit(self, delay=0.1):
        if self.is_in_call():
            self.terminate_call()

        if self.rc_config_file:
            self.core.clear_call_logs()

        self.worker_thread_exit = True
        self.core_thread_exit = True
        if delay:
            time.sleep(delay)

        if self.rc_config_file:
            rc_config = LpRcManipulator(self.rc_config_file)
            rc_config.read_rc_file()
            rc_config.remove_call_logs()
            rc_config.write_rc_file()
    ######### end of init and exit functions #########

    ######### callbacks functions #########
    def default_callback(self, *args, **kwargs):
        logging.info("default callback [cp_cb] : %r %r", args, kwargs)

    def call_mhcb(self, evt, *args, **kwargs):
        """ call all registered callbacks for 'evt' event
        :param evt:
        :param args:
        :param kwargs:
        :return:
        """
        for func, name in self.mh_callbacks.get(evt, []):
            func(*args, **kwargs)

    def cbab_updated(self):
        self.call_mhcb(self.EVT.ADDRESS_BOOK_UPDATED)#pylint:disable=E1121

    def cb_registration_state_changed(self, core, proxy_config,
              registration_state, message):
        logger.info('callback registration state change %r %r %r',
                    proxy_config, registration_state, message)
        logger.info('in the registered callback')

        if registration_state == linphone.RegistrationState.RegistrationOk:
            self.ready = True
            self.proxy_identity = proxy_config.identity

            if self.proxy_enable:
                self.identity = self.proxy_identity

            #pylint:disable=E1121
            self.call_mhcb(self.EVT.REGISTERED, proxy_config.server_addr)
            #pylint:enable=E1121

    def cb_global_state_changed(self, core, global_state, message):
        logging.info("[cp_cb (global state_changed)] : %r %r", global_state,
                        message)
        if global_state == linphone.GlobalState.GlobalOn and \
            not self.proxy_enable:
            self.ready = True

    def cb_call_state_changed(self, core, call, state, message):
        """  callback function for call
        :param core: the linphone core object
        :param call: linphone call object
        :param state: state of call
            (see linphone.CallState.LinphoneCallIncomingReceived)
        :param message: string description of state
        :return:
        """
        state_str = linphone.CallState.string(state)
        logging.info("[cp_cb (call_state_changed)] : %r %r", state_str, message)

        #pylint:disable=E1121
        self.call_mhcb(self.EVT.CALL_STATE_CHANGED, call, state, message)
        #pylint:enable=E1121

        if state == linphone.CallState.CallIncomingReceived:
            #incioming call
            self.incoming_call = call

            #pylint:disable=E1121
            self.call_mhcb(self.EVT.INCOMING, call.remote_address_as_string)
            #pylint:enable=E1121
        elif state == linphone.CallState.CallConnected:
            #answer
            self.incoming_call = None
            self._update_current_call(call, state_str)

            #pylint:disable=E1121
            self.call_mhcb(self.EVT.ANSWERED, call.remote_address_as_string)
            #pylint:enable=E1121
        elif state == linphone.CallState.CallStreamsRunning:
            #answer, and media established
            self.show_rx_stats(call)

            self.incoming_call = None
            self._update_current_call(call, state_str)

            #pylint:disable=E1121
            self.call_mhcb(self.EVT.STREAM_ESTABLISHED, call)
            #pylint:enable=E1121
        elif state == linphone.CallState.CallUpdatedByRemote or \
                state == linphone.CallState.CallUpdating:
            self.show_rx_stats(call)

            #REINVITE
            self._update_current_call(call, state_str)

            self.call_mhcb(self.EVT.CALL_UPDATED)#pylint:disable=E1121
        elif state == linphone.CallState.CallEnd:
            #Hangup
            self.incoming_call = None
            self._update_current_call(None, state_str)

            self.call_mhcb(self.EVT.TERMINATED)  #pylint:disable=E1121
        elif state == linphone.CallState.CallReleased:
            #Hanguped and media released
            self._update_current_call(None, state_str)
        elif state == linphone.CallState.CallError:
            #ERROR
            logger.warning('error in call : %r', message)
            self._update_current_call(None, state_str)

            self.call_mhcb(self.EVT.FAILED, state_str)  #pylint:disable=E1121
        else:
            logger.info('uncaught event on call changed : %r',
                           linphone.CallState.string(state))

    def cb_message_send_status(self, chat_msg, chat_msg_status, user_data):
        """ callbacks for send_message
        :param chat_msg: chat_message sent
        :param chat_msg_status:
        :param user_data: None
        :return:
        """
        logger.debug('in cb_sent_message ')

        logger.debug('debug one  : %r : %r', 'user_data', user_data)
        logger.debug('debug one  : %r : %r', 'chat_msg_status', chat_msg_status)

        ChatMessageState= linphone.ChatMessageState
        if chat_msg_status == ChatMessageState.ChatMessageStateDelivered:
            pass
        elif chat_msg_status == ChatMessageState.ChatMessageStateFileTransferError\
            or chat_msg_status == ChatMessageState.ChatMessageStateNotDelivered:
            logger.warning('message not delivered')
        elif chat_msg_status == ChatMessageState.ChatMessageStateIdle:
            pass
        elif chat_msg_status == ChatMessageState.ChatMessageStateInProgress:
            pass
        logger.debug('end of cb_sent_message')

    def cb_message_received(self, core, chat_room, msg=None):
        self.chat_room = chat_room

        self.msg_sender = chat_room.peer_address.as_string()
        logger.info("received message from %r :%r", self.msg_sender, msg.text)

        self.parse_control_message_from_sip_message(self.msg_sender, msg.text)

        #pylint:disable=E1121
        self.call_mhcb(self.EVT.MESSAGE, self.msg_sender, msg.text)
        #pylint:enable=E1121

    def register_callback(self, event_id, cb_function, name=None):
        """
        register a function to call when the event event_id coming
        :param event_id:
        :param cb_function:
        :param name:
        :return:
        """
        self.mh_callbacks[event_id] = self.mh_callbacks.get(event_id, [])
        self.mh_callbacks[event_id].append((cb_function, name,))

    def unregister_callback(self, event_id, cb_function=None, name=None):
        """
        unregistered a function to call when the event event_id coming
        :param event_id:
        :param cb_function:
        :param name:
        :return:
        """
        callbacks = self.mh_callbacks.get(event_id, None)
        if not callbacks:
            logger.warning("trying to unregistered a function for an event" \
                           " containing no functions")
            return

        for (func, _name,) in callbacks:
            if (cb_function and cb_function == func) or \
                    (name and name == _name):
                callbacks.remove((func, _name))

    ### callbacks for wait_for methods
    def _cb_incoming(self, caller):
        """ callback for incoming call, use for rpc wait for functions
        :param caller: call
        """
        logger.info("in incoming callback, %s",
            threading.current_thread().getName())

        self.incoming_event.set()

        self.hangup_event.clear()
        logger.info("in incoming callback end")

    def _cb_answered(self, caller):
        """ callback for answered call, use for wait for functions
        :param caller: caller
        """
        logger.info("in answered callback, %s",
            threading.current_thread().getName())

        self.answered_event.set()

        self.incoming_event.clear()
        logger.info("in answered callback end")

    def _cb_hangup(self):
        """ callback for hangup call, use for rpc wait for functions """
        logger.info("in hangup callback, %s",
            threading.current_thread().getName())

        self.hangup_event.set()

        self.stream_established_event.clear()
        logger.info("in hangup callback end")

    def _cb_message(self, sender, msg):
        """ callback for message receive, use for rpc wait for functions """
        logger.info("in message callback, %s",
            threading.current_thread().getName())

        self.msg_text = msg.strip()
        self.msg_sender = sender.strip()

        self.msg_event.set()
        logger.info("in message callback end")

    def _cb_registered(self, server):
        """ callback for registered on server, use for rpc wait for functions
        """
        logger.info("in registered callback, %s",
            threading.current_thread().getName())

        self.registered_server = server
        self.registered_event.set()
        logger.info("in registered callback end")

    def _cb_stream_established(self, call):
        """ callback for stream on server, use for rpc wait for functions
        """
        logger.info("in stream established callback, %s",
            threading.current_thread().getName())

        self.stream_established_event.set()

        self.answered_event.clear()
        logger.info("in stream established callback end")

    def _cb_call_updated(self):
        """ callback for registered on server, use for rpc wait for functions
        """
        logger.info("in call_updated callback, %s",
            threading.current_thread().getName())

        self.call_updated_event.set()
        logger.info("in call_updated callback end")

    def _cb_call_state_changed(self, call, state, message):
        """ callback for registered on server, use for rpc wait for functions
        """
        logger.info("in call_state_change callback, %s",
            threading.current_thread().getName())

        if self.call_state_queue.full():
            self.call_state_queue.get()

        self.call_state_queue.put({
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'state':state,
            'state_string':message
        })

        self.call_state_change_event.set()
        logger.info("in call_state_change callback end")

    ### end of callback for wait_for methods

    def parse_control_message_from_sip_message(self, sender, msg):
        """
        check for each message if it's a command,
        if it is, put it in a task for the worker thread
        :param sender: sender of message
        :param msg: message send
        :return: None if error
        """
        logger.info("in pars_command_from_sip")
        logger.debug("msg : %r", msg)

        ctrl_msg = ControlMessage.from_string(msg, sender)

        if not ctrl_msg:
            return None

        self.worker_queue.put(ctrl_msg)
    ######### end of callbacks functions #########

    ######### wait_for functions #########
    def wait_for_incoming(self, timeout=10):
        """ callback for incoming call, use for wait for functions
        :param timeout: time to wait before error (default 10 secs)
        :return: None (for time out), or sip server if success full
        """
        logger.info("wait incoming call, function, %s",
            threading.current_thread().getName())

        ret = self.incoming_event.wait(timeout)
        if not ret:
            logger.error("timeout %r", timeout)
            return None

        logger.info("wait incoming call, function: DONE")
        self.incoming_event.clear()
        return True

    def wait_for_answered(self, timeout=10):
        """ callback for answered call, use for wait for functions
        :param timeout: time to wait before error (default 10 secs)
        :return: None (for time out), or sip server if success full
        """
        logger.info("wait answered call, function, %s",
            threading.current_thread().getName())

        ret = self.answered_event.wait(timeout)
        if not ret:
            logger.error("timeout %r", timeout)
            return None

        self.answered_event.clear()
        logger.info("wait answered call, function: DONE")
        return True

    def wait_for_hangup(self, timeout=10):
        """ callback for hangup call, use for wait for functions
        :param timeout: time to wait before error (default 10 secs)
        :return: None (for time out), or sip server if success full
        """
        logger.info("wait hangup call, function, %s",
            threading.current_thread().getName())

        ret = self.hangup_event.wait(timeout)
        if not ret:
            logger.error("timeout %r", timeout)
            return None

        logger.info("wait hangup call, function: DONE")
        self.hangup_event.clear()
        return True

    def wait_for_message(self, timeout=10):
        """ callback for message, use for wait for functions
        :param timeout: time to wait before error (default 10 secs)
        :return: None (for time out), or sip server if success full
        """
        logger.info("wait message, function, %s",
            threading.current_thread().getName())

        ret = self.msg_event.wait(timeout)
        if not ret:
            logger.error("timeout %r", timeout)
            return None

        message = (self.msg_sender, self.msg_text)
        self.msg_event.clear()
        logger.info("wait message, function: DONE")

        return message

    def wait_for_stream_established(self, timeout=10):
        """ callback for message, use for wait for functions
        :param timeout: time to wait before error (default 10 secs)
        :return: None (for time out), or sip server if success full
        """
        logger.info("wait stream_established, function, %s",
            threading.current_thread().getName())

        ret = self.stream_established_event.wait(timeout)
        if not ret:
            logger.error("wait_for_stream_established : timeout %r", timeout)
            return None

        self.stream_established_event.clear()
        logger.info("wait stream_established, function: DONE")

        return True

    def wait_for_call_updated(self, timeout=10):
        """ callback for message, use for wait for functions
        :param timeout: time to wait before error (default 10 secs)
        :return: None (for time out), or sip server if success full
        """
        logger.info("wait call_updated, function, %s",
            threading.current_thread().getName())

        ret = self.call_updated_event.wait(timeout)
        if not ret:
            logger.error("wait call_updated, timeout %r", timeout)
            return None

        self.call_updated_event.clear()
        logger.info("wait call_updated, function: DONE")

        return True

    def wait_for_call_state_change(self, timeout=10):
        """ callback for call state changed, use for wait for functions
        :param timeout: time to wait before error (default 10 secs)
        :return: call state queue
        """
        logger.info("wait call_state_change, function, %s",
            threading.current_thread().getName())

        ret = self.call_state_change_event.wait(timeout)
        if not ret:
            logger.error("wait call_state_change, timeout %r", timeout)
            return None

        self.call_state_change_event.clear()
        logger.info("wait call_state_change, function: DONE")

        ret = list()
        while not self.call_state_queue.empty():
            ret.append(self.call_state_queue.get())

        return ret

    #TODO test this function with rpc
    def wait_for_registered(self, timeout=10):
        """ wait timeout seconds for sip registration on server
        :param timeout: time to wait before error (default 10 secs)
        :return: None (for time out), or sip server if success full
        """
        logger.info("wait registered on server, function, %s",
            threading.current_thread().getName())

        ret = self.registered_event.wait(timeout)
        if not ret:
            logger.error("timeout %r", str(timeout))
            return None

        self.registered_event.clear()
        logger.info("wait registered, function: DONE")

        return True

    ######### end of wait_for functions #########

    def _core_thread(self):
        """ main function for core thread """
        iterate = self.core.iterate

        lock = self.core_lock
        sleep = time.sleep
        while not self.core_thread_exit:
            with lock:
                iterate()
            sleep(0.02)

    def worker_proc(self, args=(), kwargs={}):
        """ worker function for worker thread
            just execute control message in the worker queue
        """
        logger.info('worker thread launched')

        while not self.worker_thread_exit:
            try:
                control_message = self.worker_queue.get(block=True,
                                                        timeout=1)
                control_msg = control_message.control_message

                if control_msg == 'rmt_preview_snapshot':
                    #pylint:disable=E1121
                    self.call_mhcb(self.EVT.PREVIEW_SNAPSHOT_IN_PROGRESS)
                    #pylint:enable=E1121
                    self.rmt_preview_snapshot(control_message)

                elif control_msg == 'photo_url':
                    #pylint:disable=E1121
                    self.call_mhcb(self.EVT.RMT_PREVIEW_SNAPSHOT,
                        control_message.args)
                    #pylint:enable=E1121

                elif control_msg == 'apply_profile':
                    self._apply_profile(control_message.args)

                #elif control_msg == '':
                else:
                    logger.warning("control message %r not found",
                                   control_msg)
                    logger.warning("control_message dump %s",
                                   str(vars(control_message)))

            except queue.Empty as empty_exc:
                #Exception for empty queue
                # logger.debug("worker_proc empty exception : %r", e)
                pass

            except Exception as exc:
                formatted_lines = traceback.format_exc().splitlines()
                logger.error("worker_proc exception : %r", exc)
                logger.error("worker_proc traceback :\n")
                for line in formatted_lines:
                    logger.error(line)

        logger.info('exiting worker_thread')

    def _update_current_call(self, call, comment=''):
        if call is not self.current_call:
            logger.info('updating current call %s' % comment)
            self.current_call = call

    def show_stats(self):
        self.show_rx_stats()
        self.show_tx_stats()

    def show_rx_stats(self, call=None):
        if call is None:
            call = self.current_call
        if not call:
            logger.warning("cannot stat without call")
            return

        params = call.current_params
        logger.info("received stats - frame rate : %.2f, size : %dx%d",
            params.received_framerate, params.received_video_size.width,
            params.received_video_size.height)
        print("received stats - frame rate : %.2f, size : %dx%d"%
            (params.received_framerate, params.received_video_size.width,
            params.received_video_size.height))

    def show_tx_stats(self, call=None):
        if call is None:
            call = self.current_call
        if not call:
            logger.warning("cannot stat without call")
            return

        params = call.current_params
        logger.info("sent stats - frame rate : %.2f, size : %dx%d",
            params.sent_framerate, params.sent_video_size.width,
            params.sent_video_size.height)
        print("sent stats - frame rate : %.2f, size : %dx%d"%
            (params.sent_framerate, params.sent_video_size.width,
            params.sent_video_size.height))

    @synchronized(core_lock)
    def set_framerate(self, framerate):
        """ set the preferred frame rate to 'frame rate'
            :param framerate: float
        """
        logger.debug("setting preferred frame rate to %.1f", float(framerate))
        self.core.preferred_framerate = float(framerate)

    @synchronized(core_lock)
    def set_video_size(self, size):
        """ set the preferred video_size
        :param size: (width,height) or resolution name
        """
        if not type(size) == tuple:
            logger.debug("setting preferred video_size to %s", size)
            self.core.preferred_video_size_by_name = self.encode_str(size)
        else:
            width, height = size
            logger.debug('setting preferred video size to %dx%d', width, height)
            self.core.preferred_video_size = linphone.VideoSize(width, height)

    @synchronized(core_lock)
    def set_preview_video_size(self, size):
        """ set the preview video_size
        :param size: (width, height) or resolution name
        """
        if not type(size) == tuple:
            logger.debug("setting preview video_size to %s", size)
            self.core.preview_video_size_by_name = self.encode_str(size)
        else:
            width, height = size
            logger.debug('setting preview video size to %dx%d', width, height)
            self.core.preview_video_size = linphone.VideoSize(width, height)

    @synchronized(core_lock)
    def set_echo_cancellation(self, enable=True):
        """ if enable is true enable echo cancellation,
            else disable it
        """
        logger.debug("setting echo cancellation to %r", enable)
        self.core.echo_cancellation_enabled = enable

    @synchronized(lock)
    def get_call_logs(self):
        """ return list of call_log (older entries at the end of list) """
        ret = []
        logs = None
        with self.core_lock:
            logs = self.core.call_logs

        adress_book = self.get_adress_book()
        for log in logs:
            tmp = {
                "start_time":log.start_date.isoformat(),
                "duration":log.duration,
                "contact":adress_book.find_by_address(
                    log.remote_address.as_string())
            }
            ret.append(tmp)
        ret.sort(key=operator.itemgetter('start_time'), reverse=True)
        return ret

    def get_call_info(self):
        pass #TODO this method

    def get_state(self):
        pass #TODO this method

    def send_control_message(self, recipient, control_message):
        """ send a command over sip
        :param recipient: recipient of control message
        :param control_message: control message string(ControlMessage.to_string)
        :return: immediate result of command
        """
        logger.info('sending control message to %r : %r',
            recipient, control_message)

        return self.send_message(control_message, recipient)

    def snapshot(self, file_path=None):
        """ save the view image as jpeg in file_path
        :param file_path: path to save the jpg file(tmp file created if None)
        :return: (file_path, ret)
        """
        with self.core_lock:
            if not self.current_call:
                logger.warning("cannot take video snapshot without call")
                return 1

        if not file_path:
            logger.debug("creating temp file")
            file = tempfile.NamedTemporaryFile()
            file_path = file.name
            file.close()

        with self.core_lock:
            logger.info("taking snapshot")
            ret_val = self.current_call.take_video_snapshot(file_path)

        if ret_val:
            logger.warning("problem taking video snapshot : %d", ret_val)
        return file_path, ret_val

    def preview_snapshot(self, file_path=None):
        """
        save the preview image as jpeg in file_path
        :param file_path: path to save the jpg file(tmp file created if None)
        :return: (file_path, ret)
        """
        with self.core_lock:
            if not self.current_call:
                logger.warning("cannot take preview snapshot without call")
                return None, 1

        if not file_path:
            logger.debug("creating temp file")
            file = tempfile.NamedTemporaryFile()
            file_path = file.name
            file.close()

        with self.core_lock:
            logger.info("taking preview-snapshot")
            ret_val = self.current_call.take_preview_snapshot(file_path)

        if ret_val:
            logger.warning("problem taking preview video snapshot : %d", ret_val)
        return file_path, ret_val

    @synchronized(core_lock)
    def send_message(self, msg, receiver=None):
        """ send chat message over SIP
        :param msg: message to send
        :param receiver: receiver of message(None for current_active contact)
        :return:
        """
        if not receiver and self.is_in_call():
            receiver = self.current_call.remote_address_as_string
        elif not receiver:
            logger.warning("cannot send message without recipient")
            return None

        chat_room = self.core.get_or_create_chat_room(receiver)
        message = chat_room.create_message(msg)
        chat_room.send_message2(message, self.cb_message_send_status, message)
        logger.debug("end of send_message")

    @synchronized(core_lock)
    def set_pvideo(self, win_id=None, integrate=False, show=True):
        """ set parameters for preview video
        :param win_id: windows id
        :param integrate: bool
        :param show: bool
        :return: nothing
        """
        core = self.core
        if win_id is not None:
            core.native_preview_window_id = win_id
            logger.debug("set view video to windows %s", (str(win_id)))

        if show == False:
            core.video_preview_enabled = False
            logger.info("set view video to hidden")
        elif show:
            core.video_preview_enabled = True
            logger.info("set view video to shown")

        if not integrate:
            core.use_preview_window(True)
            logger.info("set preview video to standalone")
        elif integrate:
            core.use_preview_window(False)
            logger.info("set preview video to integrated")

    @synchronized(core_lock)
    def set_vvideo(self, win_id=None, show=None):
        """
        set parameters for video view
        :param win_id: windows id
        :param show: bool (#TODO unused for the moment)
        :return: nothing
        """
        if win_id is not None:
            self.core.native_video_window_id = win_id
            logger.debug("set view video to windows %s", (str(win_id)))
        if show == False:
            raise NotImplementedError("show=False not implemented so far")
        elif show:
            pass

    def send_preview_snapshot_control_message(self, recipient=None):
        """ send rmt_preview_snapshot control message to recipient
        :param recipient: recipient of control message (current contact if None)
        """
        ctrl_msg = ControlMessage('rmt_preview_snapshot')
        self.send_control_message(recipient, ctrl_msg.to_string())

    def send_apply_profile_control_message(self, profile_number, recipient=None):
        """ send rmt_preview_snapshot control message to recipient
        :param recipient: recipient of control message (current contact if None)
        """
        ctrl_msg = ControlMessage('apply_profile', args=str(profile_number))
        self.send_control_message(recipient, ctrl_msg.to_string())

    @synchronized(core_lock)
    def get_used_webcam(self):
        """ return the current used webcam
        """
        return self.core.video_device

    @synchronized(core_lock)
    def webcam(self, use=None):
        """ return a list of webcam, set the current webcam if use is set
        :param use: index (0-based) of the webcam to use OR
                    regex for string representation of webcam
        """
        devices = self.core.video_devices
        if type(use) == int and use >= 0 and use < len(devices):
            logger.debug('setting video device to %s', devices[use])
            self.core.video_device = self.encode_str(devices[use])
        elif type(use) == str:
            use_rex = re.compile(use)
            to_use = None
            for device in devices:
                match = use_rex.search(device)
                if match:
                    to_use = device

            if not to_use:
                logger.warning("cannot find video device : %r", use)

            logger.debug('setting video device')
            self.core.video_device = self.encode_str(to_use)
        else:
            logger.debug('listing video devices')
            return devices

    @synchronized(core_lock)
    def change_webcam(self):
        """ change the current webcam, choosing the next cam in the list.
            It choose the first if the end is reached
        """
        used = self.core.video_device
        devices = self.core.video_devices
        try:
            index = devices.index(used)
            to_use = (index+1) % len(devices)
            logger.debug('set video device to %s', devices[to_use])
            self.core.video_device = self.encode_str(devices[to_use])
        except ValueError as exc:
            return -1
        return 0

    @synchronized(core_lock)
    def microphone(self, use=None):
        mic_name = use
        devices = self.core.sound_devices
        ret = []
        for mic in devices:
            if self.core.sound_device_can_capture(mic):
                ret.append(mic)
        if mic_name:
            logger.info("set capture device to %r", mic_name)
            self.core.capture_device = self.encode_str(mic_name)
            return True
        else:
            return ret

    @synchronized(core_lock)
    def speaker(self, use=None):
        spkr_name = use
        devices = self.core.sound_devices
        ret = []
        for speaker in devices:
            if self.core.sound_device_can_playback(speaker):
                ret.append(speaker)
        if spkr_name:
            logger.info("set playback device to %r", spkr_name)
            self.core.playback_device = self.encode_str(spkr_name)
            return True
        else:
            return ret

    @synchronized(core_lock)
    def set_bandwidth(self, upload=None, download=None):
        """ set bandwidth with specified value in Kbit/s
        :param upload: do nothing if None
        :param download: do nothing if None
        """
        if upload:
            self.core.upload_bandwidth = upload
            logger.info("set upload bandwidth to %d Kbit/s", upload)
        if download:
            self.core.download_bandwidth = download
            logger.info("set download bandwidth to %d Kbit/s", download)

    @synchronized(core_lock)
    def call(self, sip_addr):
        """ do a sip invite to call sip_addr
        :param sip_addr: sip address of callee
        :return:
        """
        if not self.is_in_call():
            self.current_call = self.core.invite(self.encode_str(sip_addr))
        else:
            logger.warning("cannot call when a call is active")

    @synchronized(core_lock)
    def answer(self):
        """ answer the current incoming call """
        if not self.incoming_call:
            logger.warning('answer, but no incoming call')
            return
        if self.is_in_call():
            logger.warning('multi call forbidden')
            return

        logger.info('answering call from %s',
            self.incoming_call.remote_address_as_string)
        return self.core.accept_call(self.incoming_call)

    @synchronized(core_lock)
    def decline_call(self, reason=None):
        if reason is None:
            reason = linphone.Reason.ReasonUnknown

        logger.info("decline incoming call for reason : %r",
            linphone.Reason.string(reason))
        self.core.decline_call(self.incoming_call, reason)
        self.incoming_call = None

    @synchronized(core_lock)
    def terminate_call(self):
        """ hangup current call """
        if self.is_in_call():
            logger.info("terminating call")
            self.core.terminate_call(self.current_call)

    def get_status(self):
        pass

    def request_vfu(self):
        pass

    def reload_address_book(self):
        """ update address book
            raise a callback with event 'ADRESS_BOOK_UPDATED'
        """
        logger.info('reloading address book')
        self.get_adress_book().reload()

    def get_adress_book(self):
        """
        return adress_book_object
        :return:
        """
        if self.address_book is None:
            self.address_book = AddressBook(self.cbab_updated)
            self.address_book.load(os.path.join(
                LPConfig.get_default_lp_data_dir(),
                self.config.get("contacts.filename")))
        logger.debug('getting adress book')
        return self.address_book

    def print_control_message(self, control_message):
        """ print command
        :param sender: who send this command
        :param control_message: the details command
        :return: nothing
        """
        text = ("%s sent command %s with args %s to respond to %s" %
                (control_message.sender, control_message.control_message,
                str(control_message.args), str(control_message.id_reference)))
        logger.info(text)
        print(text)

    def rmt_preview_snapshot(self, task=None):
        """
        take a preview snapshot and send it to the url specified in config
        :param sender: person who send this command
        :param args: possible arguments for this command
        :return:
        """
        tmp_dir = os.path.join(self.config.get_default_lp_data_dir(),
                               self.config.get('mh_lp.tmp_dir'))

        # taking snapshot
        with self.core_lock:
            path, ret = self.preview_snapshot()
        if ret != 0: # error occured?
            return ret

        # WORKAROUND: at the moment we don't know whether the file
        # is completely written
        prev_size = os.path.getsize(path)
        time.sleep(2)
        size = os.path.getsize(path)
        #TODO: find how to wait until the file is correctly created

        # assert (prev_size == size)
        if prev_size != size:
            logger.warning(
               'snapshot file size changed: %d -> %d',
                prev_size, size)
            # raise MHLinphoneError("file size of snapshot changed")

        cert_info = (self.https_cert, self.https_key)
        snap_item = SnapshotItem(path, tmp_dir, cert_info=cert_info,
            ssl_verify=self.ssl_verify)

        # making meta data
        logger.info("making meta data")
        contacts = self.get_adress_book()

        subject = contacts.find_by_address(self.identity)
        if not subject:
            logger.error('cannot find own sip address(%r) in address Book',
                self.identity)
            subject = 'unknown'

        photographer = contacts.find_by_address(task.sender)
        if not photographer:
            logger.error('cannot find remote sip address(%r) in address Book',
                task.sender)
            photographer = 'unknown'

        logger.info("end of search contacts")
        snap_item.make_meta(photographer, subject)
        snap_item.write_meta()

        logger.info("making zip")
        snap_item.make_zip(remove_files=False)

        ret = snap_item.upload(self.http_url)

        logger.info("removing file")
        os.unlink(snap_item.zip_path)  #remove zip file

        # send response over sip chat
        #TODO change the url parser when config change...
        view_url = self.http_url.rsplit('/', 1)[0] + ret
        logger.debug("dl url : %r", view_url)

        logger.info("doing response over sip")
        resp_msg = ControlMessage('photo_url', id_reference=task.id,
            args=view_url)
        self.send_control_message(task.sender, resp_msg.to_string())

    @synchronized(lock)
    def is_ready_to_call(self):
        return self.ready

    @synchronized(core_lock)
    def is_in_call(self):
        return self.current_call is not None

    @synchronized(core_lock)
    def audio_jitt_comp(self,value=None):
        if value:
            self.core.audio_jittcomp = int(value)
        else:
            return self.core.audio_jittcomp

    @synchronized(core_lock)
    def video_jitt_comp(self,value=None):
        if value:
            self.core.video_jittcomp = int(value)
        else:
            return self.core.video_jittcomp

    def is_running(self):
        return self.core_thread.isAlive()

    def __update_call(self, call_params, wait=False):
        #assert call is running and call state is stream established
        if not self.current_call.state == linphone.CallState.CallStreamsRunning:
            #callState == updating --> 1time

            #TODO: wait until condition true with Threading.Condition
            error_txt = "cannot update call because It isn't in the good state"
            raise MHLinphoneError(error_txt)

        with self.core_lock:
            self.call_updated_event.clear()
            self.stream_established_event.clear()
            self.core.update_call(self.current_call, call_params)

        if wait:
            self.wait_for_call_updated()
            self.wait_for_stream_established()

    def update_call(self, video_size=None, video_framerate=None):
        """ change video params, then update the call
        :param video_size: new video size : (width, height) or string
        :param video_framerate: new frame rate
        :return:
        """
        if not self.is_in_call():
            logger.warning("update call is called, without active calls")
            return None

        #TODO: to this function in one step instead of 2
        with self.core_lock:
            call_params = self.current_call.current_params
            call_params.video_enabled = False

        self.__update_call(call_params, wait=True)
        logger.debug('update_call done')

        # time.sleep(.3)
        logger.debug('wait for media established done')

        if video_framerate:
            self.set_framerate(video_framerate)
        if video_size:
            self.set_video_size(video_size)

        with self.core_lock:
            call_params = self.current_call.current_params
            call_params.video_enabled = True

        self.__update_call(call_params, wait=True)
        logger.debug('update_call done')


        # time.sleep(.3)
        logger.debug('wait for media established done')

    def _apply_profile(self, profile_number, update_call=True):
        """ apply parameters for profile 'profile_name', and apply them
            if update_call is true (default)
        :param profile_number: profile number to apply in conf
        :param update_call:  update the call when profile si applied
        """
        profile = 'profile' + str(profile_number)

        framerate = self.config.get(profile + '.framerate')
        video_size = self.config.get(profile + '.video_size')
        aec_enable = self.config.get(profile + '.aec_enabled')
        audio_jitter = self.config.get(profile + '.audio_jitt_comp')
        video_jitter = self.config.get(profile + '.video_jitt_comp')

        self.set_framerate(framerate)

        if video_size.startswith('(') and video_size.endswith(')'):
            video_size = video_size[1:-1].split(',')
            video_size = (video_size[0].strip(), video_size[1].strip())
        self.set_video_size(video_size)

        self.set_echo_cancellation(aec_enable)

        self.audio_jitt_comp(audio_jitter)
        self.video_jitt_comp(video_jitter)

        if update_call:
            self.update_call(None, None)

    def apply_profile(self, profile_name, update_call=True, update_rmt=True):
        """ apply parameters for profile 'profile_name', and apply them
            if update_call is true (default)
        :param profile_name: name of profile to apply in conf
        :param update_call:  update the call when profile si applied
        """
        if not profile_name:
            logger.warning("no profile name specified in apply_profile")
            return None
        number = 0
        for i in range(1,4):
            c_profile_name = self.config.get('profile' + str(i) + '.name', None)
            if c_profile_name:
                if c_profile_name == profile_name:
                    number = i

        if number == 0:
            logger.warning("profile name specified not found in config")
            return None

        if update_rmt:
            self.send_apply_profile_control_message(number)

        logger.info("setting profile : %s", profile_name)
        self._apply_profile(number, update_call)



def main():
    pass

if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
