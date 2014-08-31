#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : linphonec_wrapper
"""
  Summary    :  <enter a mandatory>

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

__author__    = "Julien Barreau"
__copyright__ = "(C) 2014 by MHComm. All rights reserved"
__email__     = "info@mhcomm.fr"

# -----------------------------------------------------------------------------
#   Imports
# -----------------------------------------------------------------------------
import logging
from subprocess import Popen, PIPE, STDOUT
import threading
from threading import RLock
import time
import re
import os
import tempfile

import lp_config

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)

#linphone exe
LINPHONEC_EXE = lp_config.LPConfig.get_default_linphonec_exe()


class LinphonecWrapper(threading.Thread):
    """
    Linphonec wrapper for Python.
    Provides the basic interface for sending commands and receiving responses
    to and from Linphone, such as starting and stopping the phone, initiating
    and terminating a call, etc.
    Note that this does not implement the embedding of the video window into
    the GUI. You may have to use this hack to embed Linphone video:
    os.environ['SDL_VIDEODRIVER']='x11'
    os.environ['SDL_WINDOWID']=str(self.frame_1.video_panel.GetHandle())
    where getHandle() returns the window id of the frame where to put the video.
    """
    def __init__(self, args=()):
        threading.Thread.__init__(self, name="linphone_read thread")

        self._command = None
        self.__subprocess = None
        self.on_call = False

        self.caller = None
        # self.callee = None # unused

        self.lock = RLock()
        self.command_ready = threading.Event()
        self.command_ready.set()
        self.current_command = ''
        self.command_result = []

        logger.debug("args : %s", str(args))
        self.set_args(args)

        logger.info("linphonec wrapper initialized")

    def __del__(self):
        pass

    # core functions
    def spawn(self):
        """
        Checks first whether the instance is already running. If not running,
        Linphonec will be started. Connection to the sip proxy server will then
        be initialized. Currently, there are no diagnostic messages outputted
        whenever there is a failed connection.
        Note: Before starting, the wx element that will receive the phone events
        should be set.
        """
        if not self.is_running():
            self.__subprocess = Popen(self._command, stdin=PIPE, stdout=PIPE,
                                      stderr=STDOUT)

        logger.debug("linphonec subprocess launch")

    def stop(self):
        """
        Stops the instance of Linphonec. This should be called before closing
        the application.
        """

        if self.is_running():
            #In Python2.6, subprocess has terminate() and send signal function
            #Those should be used in the future
            #cmd = 'kill -15 ' + str(self.__subprocess.pid)
            #os.system(cmd)
            #return self.__subprocess.poll()
            logger.debug("killing linphonec subprocess")
            return self.__subprocess.kill()
        else:
            return None

    def is_running(self):
        """
        Checks if an instance of the linphonec is running.
        Returns True if running, False othewise.
        """
        try:
            return True if self.__subprocess.poll() is None else False
        except AttributeError:
            return False

    def is_on_call(self):
        """
        Checks whether a call is going.
        Returns True if a call is on going, and False otherwise.
        """
        return self.on_call

    def set_args(self, args):
        """
        Sets additional options to the linphonec call. Refer to the linphonec
        usage to know the available options.
        """
        # args must either be a tuple or a list
        if not isinstance(args, (list, tuple)):
            raise TypeError("args should either be a tuple or list of strings")
        if args:
            for arg in args:
                if not isinstance(arg, basestring):
                    raise TypeError("args should either be a tuple or list of\
                                     strings")
        logger.debug("setting args")
        logger.debug("linphonec exe : %s", LINPHONEC_EXE)
        #self._command = ["linphonec", "-V"]
        self._command = [LINPHONEC_EXE, "-V"]
        self._command.extend(args)
        logger.info("args set up : %s", str(self._command))

    def run(self):
        """
        main callback functions
        the run method is the thread main function
        it parse STDOUT of subprocess to call callbacks functions
        :return: nothing
        """
        answer_rex = re.compile(r'Call answered by (.*).')
        msg_rex = re.compile(r'Message received from(.*): (.*)')
        snap_rex = re.compile(r'Taking video snapshot in file (.*)')
        prev_snap_rex = re.compile(r'Taking video preview snapshot in file (.*)')
        register_rex = re.compile(r'Registration on (.+) successful.')
        prompt = "linphonec> "

        while self.is_running():
            if self.current_command.strip().lower() == 'quit':
                self.command_ready.set()
                break

            line = self.__subprocess.stdout.readline()
            logger.debug("LPCRD: %r", line)

            while line.startswith(prompt):
                line = line[len(prompt):]
                logger.debug('stripped %r', line)
            l_line = line.lower().strip()

            if self.is_command_response_to(line, self.current_command):
                self.command_result.append(line)
                logger.debug('command result append : %r', line)

            # registration on server
            match = register_rex.search(line)
            if match:
                server = match.group(1)
                self.cb_registered_on_server(server)

            # call failed
            if "service unavailable" in l_line or \
                            "could not reach destination." in l_line:

                self.on_call = False
                self.cb_failed_call()
                continue

            # end of call
            if "call terminated." in l_line or "call ended" in l_line:
                self.on_call = False
                self.cb_terminated_call()
                continue

            # call answered
            match = answer_rex.search(line)
            if match:
                self.on_call = True
                self.caller = match.group(1)
                self.cb_answered_call()
            if l_line.endswith(" connected."):
                self.on_call = True
                self.cb_answered_call()
                continue

            #not 'incoming'
            #if "is contacting you" in l_line:
            if "receiving new incoming call from" in l_line:
                #Assumes four-digit extension
                i = line.find("sip:")
                j = line.find(",", i)
                self.caller = line[i:j]
                self.cb_incoming_call(self.caller)
                continue

            if "no active call." in l_line:
                if self.on_call:
                    self.on_call = False
                continue

            # snapshot
            # (r'Taking video snapshot in file (.*)')
            match = snap_rex.search(line)
            if match:
                path = match.group(1)
                logger.debug('run method : snapshot: %r', repr(line))
                self.cb_snapshot(path)
                continue

            # preview-snapshot
            # (r'Taking video preview snapshot in file (.*)')
            match = prev_snap_rex.search(line)
            if match:
                path = match.group(1)
                logger.debug('run method : prev_snapshot: %r', repr(line))
                self.cb_preview_snapshot(path)
                continue

            # message received
            # (r'Message received from (.*): (.*)')
            match = msg_rex.search(line)
            if match:
                sender = match.group(1)
                msg = match.group(2)
                self.cb_message(sender, msg)
                continue

            else:
                logger.debug('run method : else print: %r', repr(line))

            if line.startswith('echo cancellation'):
                self.command_result[:] = self.command_result[:-1]
                self.command_ready.set()
                logger.debug("mutex freed")

        logger.info('exiting parser thread')

    def _execute(self, cmd):
        """
        Sends a command to Linphonec. Ideally this should not be used unless
        the command is not yet supported by this module.
        """
        self.command_ready.wait()
        self.command_ready.clear()
        logger.debug("mutex locked")

        self.command_result[:] = []
        self.current_command = cmd
        logger.debug("LPCWR : %r", cmd)

        if not isinstance(cmd, basestring):
            logger.error("invalid command : \"command must be a string\"")
            raise TypeError("command must be a string")

        if not cmd:
            logger.error("invalid command : \"zero-length command\"")
            raise ValueError("zero-length command")

        if self.is_running():
            self.__subprocess.stdin.write('%s\n' % cmd)
            time.sleep(.2)
            self.__subprocess.stdin.write('ec show\n')

        self.command_ready.wait()
        result = list(self.command_result)
        return result

    def execute(self, command):
        """
        provides mutex for execute command
        :param command:
        :return: nothing
        """
        with self.lock:
            return self._execute(command)

    # command functions
    def call(self, extension):
        """ asynchronous function
        Async method, see the cb_answered_call if recipient answer to the call
        or cb_failed_call if the call failed

        Initiates a call. To handle a failed call, EVT_CALL_FAILED event should
        be handled; to handle an answered call, EVT_CALL_ANSWERED event should
        be handled; to handle a terminated call, EVT_CALL_TERMINATED event
        should be handled.
        The only parameter is the extension number, in string, of the phone
        to be called.
        :param extension: sip address of recipient
        :return: string immediate result of command.
        """
        logger.info("calling %s", extension)
        return self.execute('call ' + extension)

    def answer(self):
        """ synchronous function
        see cb_incoming_call before answer and cb_answered_call for an answered
        call
        Answers an incoming call. To handle an incoming call, EVT_CALL_INCOMING
        should be handled; to handle a terminated call, EVT_CALL_TERMINATED
        event should be handled.
        :return: string immediate result of command.
        """
        logger.info("call answered")
        return self.execute('answer')

    def terminate_call(self):
        """ synchronous function
        se the cb_terminated_call functions
        Terminates a call. To handle a terminated call, EVT_CALL_ANSWERED event
        should be handled.
        :return: string immediate result of command.
        """
        logger.info("call hanged up")
        self.on_call = False
        self.caller = None
        return self.execute('terminate')

    def request_vfu(self):
        """ synchronous function
        send a vfu request during a call
        :return: string immediate result of command.
        """
        if self.is_on_call():
            return self.execute("vfureq")
        else:
            return "not in an active call"

    def preview_snapshot(self, file_path=None):
        """ synchronous function
        see the cb_preview_snapshot functions
        save the preview image as jpeg
        :param file_path: path to save the jpg file
        :return: (file_path, string immediate result of command)
        """
        if not file_path:
            file = tempfile.NamedTemporaryFile()
            file_path = file.name
            file.close()

        if self.is_on_call():
            ret = self.execute("preview-snapshot %s" % file_path)
            return file_path, ret
        else:
            return "not in an active call"

    def snapshot(self, file_path=None):
        """ synchronous function
        save the view image as jpeg
        :param file_path:
        :return: (file_path, string immediate result of command)
        """
        if not file_path:
            file_path = tempfile.NamedTemporaryFile()

        if self.is_on_call():
            ret = self.execute("snapshot %s" % file_path)
            return file_path, ret
        else:
            return "not in an active call"

    def quit(self):
        """ asynchronous function
        send quit command to linphone, to quit it properly
        :return: nothing
        """
        self.execute("quit")

    def send_message(self, msg, receiver=None):
        """ synchronous function
        send a message 'msg' to the receiver 'receiver'
        :param receiver: sip address of the message receiver
        :param msg: message to send
        :return: string immediate result of command.
        """
        if not receiver and self.is_on_call():
            receiver = self.caller
        elif not receiver and not self.is_on_call():
            logger.error("not recipient specified, and not active call")
            logger.error("cannot send message '%s'", msg)
            return "no active call, ans no recipient specified"

        return self.execute("chat %s %s" % (receiver, msg))

    def set_pvideo(self, win_id=None, integrate=False, show=None):
        """
        set parameters for preview video
        :param win_id: windows id
        :param integrate: bool
        :param show: bool
        :return: nothing
        """
        result = []
        if win_id is not None:
            result += self.execute("pwindow id %s" % (str(win_id)))
            logger.debug("set preview video to windows %s\n", str(win_id))

        if not integrate:
            result = self.execute("pwindow standalone")
            logger.info("set preview video to standalone")
        elif integrate:
            result += self.execute("pwindow integrated")
            logger.info("set preview video to integrated")

        if show == False:
            result += self.execute("pwindow hide")
            logger.info("set preview video to hidden")
        elif show:
            result += self.execute("pwindow show")
            logger.info("set preview video to shown")
        return result

    def set_vvideo(self, win_id=None, show=None):
        """
        set parameters for video view
        :param win_id: windows id
        :param show: bool
        :return: nothing
        """
        result = []
        if win_id is not None:
            result += self.execute("vwindow id %s" % (str(win_id)))
            logger.debug("set view video to windows %s", (str(win_id)))

        if show == False:
            result += self.execute("vwindow hide")
            logger.info("set view video to hidden")
        elif show:
            result += self.execute("vwindow show")
            logger.info("set view video to shown")
        return result

    def set_param(self, section_param, value):
        """
        change parameters in linphone config file
        :param section_param: string formatted as : section.value
        :param value: string
        :return: nothing
        """
        section, param = section_param.split('.')
        result = self.execute("param %s %s %s" % (section, param, value))
        logger.debug("set param in rc file : %s : %s = %s",
                     section, param, value)
        return result

    def webcam(self, use=None):
        """
        list all availlable camera
        :param use: camera to use, do nothing if None
        :return: result of command(s)
        """
        if use == None:
            result = self.execute("webcam list")
        else:
            result = self.execute("webcam use %s" % str(use))
        return result

    def get_state(self):
        """
        :return: result of states command in linphone
        """
        result = self.execute("states")
        logger.info("states get")
        return result

    def get_status(self):
        """
        :return: result of status command in linphone
        """
        result = self.execute("status")
        logger.info("status get")
        return result






    def is_command_response_to(self, line, command):
        """
        use to define if a line is the result o the given command
        :param line: line read in stdout (or stderr)
        :param command: the command launch
        :return: bool
        """
        split_vals = command.split(' ', 1)
        if len(split_vals) == 2:
            cmd, args = split_vals
        else:
            cmd = split_vals[0]
            args = ''

        if line.startswith('Friend "') or \
                line.startswith("Registration on sip:") or \
                line.startswith("ortp-error-no such method on filter") or \
                line.startswith("ortp-error-Could not retrieve") or \
                line.startswith("Media streams established with"):
            logger.debug("removing line : %r", line)
            return False

        return True

    #Public virtual functions
    def cb_registered_on_server(self, server):
        """
        callback function for incoming calls
        :param caller:
        """
        logger.error("calling cb_registate_on_server, but it is not implemented yet")
        raise NotImplementedError()

    def cb_incoming_call(self, caller):
        """
        callback function for incoming calls
        :param caller:
        """
        logger.error("calling cb_incoming_call, but it is not implemented yet")
        raise NotImplementedError()

    def cb_terminated_call(self):
        """
        callback function for terminated calls
        """
        logger.error("calling cb_terminated_call, but it is not implemented yet")
        raise NotImplementedError()

    def cb_answered_call(self):
        """
        callback function for answered calls
        """
        logger.error("calling cb_answered_call, but it is not implemented yet")
        raise NotImplementedError()

    def cb_failed_call(self):
        """
        callback function for failed calls
        """
        logger.error("calling cb_failed_call, but it is not implemented yet")
        raise NotImplementedError()

    def cb_message(self, sender, msg):
        """
        callback function for received messages
        :param sender: the contact who send message
        :param msg: message
        """
        logger.error("calling cb_message, but it is not implemented yet")
        raise NotImplementedError()

    def cb_snapshot(self, path):
        """
        callback function for taken snapshots
        :param path: path of jpeg snapshot
        """
        logger.error("calling cb_snapshot, but it is not implemented yet")
        raise NotImplementedError()

    def cb_preview_snapshot(self, path):
        """
        callback function for taken preview snapshots
        :param path: path of jpeg snapshot
        """
        logger.error("calling cb_preview_snapshot, but it is not implemented yet")
        raise NotImplementedError()


def main():
    pass

if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
