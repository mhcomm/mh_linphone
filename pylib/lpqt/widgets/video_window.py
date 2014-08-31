#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : video_window.py
"""
  Summary    :  Main video window

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

 This is the main GUI window with all functional button to make a video call

"""
# #############################################################################
from __future__ import absolute_import
from __future__ import print_function

__author__    = "Mrugesh Chauhan"
__copyright__ = "(C) 2014 by MHComm. All rights reserved"
__email__     = "info@mhcomm.fr"

# -----------------------------------------------------------------------------
#   Imports
# -----------------------------------------------------------------------------
import os
import sys
import logging
import gettext

import set_paths

import mh_qtwrapper

from python_qt_binding import QtGui
from python_qt_binding import QtCore
from python_qt_binding.QtCore import Qt

import mhlinphone_wrapper
import build.mh_linphone_pixmaps_rc

from lp_config import LPConfig

from lpqt.widgets.common_widgets import MHPushButton, MHProfilePushButton
from lpqt.widgets.common_widgets import MHDialogCnf, MHDialogMsg
from lpqt.widgets.common_widgets import MHProgressDialog

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)
MAX_CHAR_CNT = 1020 #TextEdit will not take more than this. It's one page image.
WIN_TITLE = "MH_LINPHONE"

###### I18N ######
#

# table of available languages
if sys.platform == 'win32':
    lang_table = dict(
        french="fr",
        spanish="es",
        english="en",
        german="de")
    date_table = dict(
        french="fra",
        spanish="esp",
        english="eng",
        german="deu")

else:
    lang_table = dict(
        french="fr_FR.UTF-8",
        english="en_US.UTF-8",
        german="de_DE.UTF-8",
        spanish="es_ES.UTF-8",
        )

    date_table = dict(
        french="fr_FR.UTF-8",
        english="en_US.UTF-8",
        german="deu",
        spanish="es_ES.UTF-8",
        )

def set_locale(pm_i18n_dirpath):
    """ sets the language for application """
    language = 'french'
    lang = lang_table.get(language, 'C')
    os.environ["LANG"] = lang
    gettext.install('mh_linphone',
                    pm_i18n_dirpath,
                    unicode=1)
#
#
###### I18N ######

# -----------------------------------------------------------------------------
#   Main video widget
# -----------------------------------------------------------------------------
class MHVideoWindow(QtGui.QWidget):
    """
    Main video window
    """

    sig_incoming_call = QtCore.Signal(unicode)
    sig_failed = QtCore.Signal(unicode)
    sig_answered = QtCore.Signal(unicode)
    sig_rmt_snapshot_taken = QtCore.Signal(unicode)
    sig_call_terminated = QtCore.Signal()
    sig_stream_established = QtCore.Signal(list)

    #sig_registered = QtCore.Signal()

    def __init__(self, 
            pm_css_path, pm_config, pm_advanced_interface=False, parent=None):
        
        super(MHVideoWindow, self).__init__(parent)
        self.setObjectName("video_main_widget")

        config = pm_config

        #GUI elements
        self.advanced_interface = pm_advanced_interface
        self.tx_cam_win = None
        self.rx_cam_win = None
        self.contacts_combobox = None
        self.btn_call = None
        self.btn_hangup = None
        self.btn_snapshot = None
        self.rx_cam_win_winid = None
        self.tx_cam_win_winid = None
        self.btn_profile1 = None #Fluid
        self.btn_profile2 = None #3G
        self.btn_profile3 = None #Quality

        #Engine elements
        self._video_engine = None
        self._addr_book = None
        self._current_contact_addr = None
        self._index_to_address_dict = None
        self._webcams_list = None
        
        #Timer to obtain windows handle while linphone launches
        self._activate_video_timer = QtCore.QTimer()
        self._activate_video_timer.setSingleShot(True)
        self._activate_video_timer.timeout.connect(
                                                self._activate_video_elements)

        #Get profiles (Number and type of profiles are fixed for the moment.)
        self._profile1 = config.get("profile1.name")
        self._profile2 = config.get("profile2.name")
        self._profile3 = config.get("profile3.name")
        
        self._default_webcam = config.get("video.webcam")
        
        self._btn_call_text_incall = _("VISIO_MakeCall")
        self._btn_call_text_offcall = _("VISIO_MakingCall")
        
        self._setup_ui()

        #Apply CSS
        self._css_path = pm_css_path
        if os.path.exists(self._css_path):
            self.setStyleSheet(open(self._css_path).read())

    def _setup_ui(self):
        """ Initialize UI """

        size_policy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                    QtGui.QSizePolicy.MinimumExpanding)
        self.setSizePolicy(size_policy)

        #Main layout
        top_vlayout = QtGui.QHBoxLayout(self)
        top_vlayout.setContentsMargins(0, 0, 0, 0)

        # Remote video stream layout
        self.rx_cam_win = QtGui.QWidget()
        self.rx_cam_win.setObjectName("rx_cam_win")

        # Preview video stream
        self.tx_cam_win = QtGui.QWidget()
        self.tx_cam_win.setObjectName("tx_cam_win")

        # Build preview layout
        tx_widget = QtGui.QWidget()
        tx_widget.setObjectName('tx_widget')  # DON'T CHANGE OBJECT NAME
        tx_widget_vlayout = QtGui.QVBoxLayout(tx_widget)
        tx_widget_vlayout.addWidget(self.tx_cam_win, stretch=3) # Viewfinder

        # Build function btn frame
        call_func_frame = QtGui.QFrame()
        call_func_frame.setObjectName('call_func_frame')
        call_func_vlayout = QtGui.QVBoxLayout(call_func_frame)
 
        if self.advanced_interface:
            self.contacts_combobox = QtGui.QComboBox(self)
            self.contacts_combobox.setSizeAdjustPolicy(
                                              QtGui.QComboBox.AdjustToContents)
            self.contacts_combobox.setObjectName("AddressBook")

            call_func_vlayout.addWidget(self.contacts_combobox,
                                        alignment=Qt.AlignHCenter)

            self.btn_call = MHPushButton(
                                    self, 'btn_call',self._btn_call_text_incall)
            self.btn_snapshot = MHPushButton(
                                    self, 'btn_snapshot', _("VISIO_Photo"))
        self.btn_hangup = MHPushButton(
                                    self, 'btn_hangup', _("VISIO_hangup"))

        #Add func btns to layout
        #Call btn
        if self.advanced_interface:
            call_func_vlayout.addWidget(self.btn_call, 
                                        alignment=Qt.AlignCenter)

        #Hangup btn
        call_func_vlayout.addWidget(self.btn_hangup,
                                        alignment=Qt.AlignHCenter)
        #Snapshot btn
        if self.advanced_interface:
            call_func_vlayout.addWidget(self.btn_snapshot,
                                        alignment=Qt.AlignCenter)
        call_func_vlayout.addStretch()

        #Add functions
        func_btn_hlayout = QtGui.QHBoxLayout()
        func_btn_hlayout.addWidget(call_func_frame)

        # Quality adjustment profile frame bar buttons
        quality_profile_widget = QtGui.QFrame()
        quality_profile_widget.setObjectName("profile_frame")
        quality_profile_layout = QtGui.QVBoxLayout(quality_profile_widget)
        
        #Switch camera button
        self.btn_switch_camera = MHPushButton(self, 
                                               'btn_switch_camera',
                                               _("VISIO_SwitchCamera"))
        quality_profile_layout.addWidget(self.btn_switch_camera,
                                             alignment=Qt.AlignCenter)

        #Quality adjusment buttons
        if self.advanced_interface:
            self.btn_profile1 = MHProfilePushButton(
                                    self, 'btn_profile1', _("VISIO_Fluide+"),
                                    pm_profile_name=self._profile1)
            self.btn_profile2 = MHProfilePushButton(
                                    self, 'btn_profile2', _("VISIO_3G"),
                                    pm_profile_name=self._profile2)
            self.btn_profile3 = MHProfilePushButton(
                                    self, 'btn_profile3', _("VISIO_Qualite+"),
                                    pm_profile_name=self._profile3)
    
            quality_profile_layout.addWidget(self.btn_profile1,
                                             alignment=Qt.AlignCenter)
            quality_profile_layout.addWidget(self.btn_profile2,
                                             alignment=Qt.AlignCenter)
            quality_profile_layout.addWidget(self.btn_profile3,
                                             alignment=Qt.AlignCenter)
        
        quality_profile_layout.addStretch()
        func_btn_hlayout.addWidget(quality_profile_widget)

        #Side bar layout
        side_bar_vlayout = QtGui.QVBoxLayout()
        side_bar_vlayout.addLayout(func_btn_hlayout, stretch=2)
        side_bar_vlayout.addWidget(tx_widget, stretch=1)
        
        # Build the main video layout
        top_vlayout.addWidget(self.rx_cam_win, stretch=3)
        top_vlayout.addLayout(side_bar_vlayout, stretch=1)

        #Get windows Id of rx frame
        self.rx_cam_win_winid = int(self.rx_cam_win.winId())
        self.tx_cam_win_winid = int(self.tx_cam_win.winId())

        #Connect signals
        self._connect_signals()

        #Disable all btns
        self._set_btns_state(False)

    def _change_call_btn_text(self):
        """
        Change call btn text
        """
        if self.btn_call.isEnabled():
            self.btn_call.setText(self._btn_call_text_incall)
        else:
            self.btn_call.setText(self._btn_call_text_offcall)

    def _set_btns_state(self, pm_val=False):
        """
        Enable/disable btns
        """
        self.btn_hangup.setEnabled(pm_val)

        if self.advanced_interface:
            self.contacts_combobox.setEnabled(pm_val)
            self.btn_call.setEnabled(pm_val)
            self.btn_snapshot.setEnabled(pm_val)
            
            self.btn_profile1.setEnabled(
                                        pm_val and (self._profile1 is not None))
            self.btn_profile2.setEnabled(
                                        pm_val and (self._profile2 is not None))
            self.btn_profile3.setEnabled(
                                        pm_val and (self._profile3 is not None))

    def _connect_signals(self):
        """Connect the signals"""

        if self.advanced_interface:
            self.btn_call.clicked.connect(self._slot_make_call)
            self.btn_snapshot.clicked.connect(self._slot_snapshot)
            self.contacts_combobox.activated.connect(self._slot_set_contact_id)
        
            self.btn_profile1.clicked.connect(self._slot_load_profile)
            self.btn_profile2.clicked.connect(self._slot_load_profile)
            self.btn_profile3.clicked.connect(self._slot_load_profile)

            self.sig_rmt_snapshot_taken.connect(self._handle_rmt_snapshot)
            #self.sig_registered.connect(self._handle_registered)

        self.btn_hangup.clicked.connect(self._slot_terminate_call)
        self.btn_switch_camera.clicked.connect(self._slot_switch_camera)

        self.sig_incoming_call.connect(self._handle_incoming_call)
        self.sig_failed.connect(self._handle_failed_event)
        self.sig_answered.connect(self._handle_answered_event)
        self.sig_call_terminated.connect(self._handle_terminated_event)
        self.sig_stream_established.connect(self._handle_stream_established)

    def _change_incall_btn_states(self, pm_call_off=False):
        """
        Change btn states based on call status
        
        pm_call_off True means call is not in progress
        """
        self.btn_hangup.setEnabled(not pm_call_off)
        self.btn_switch_camera.setEnabled(not pm_call_off)

        if self.advanced_interface:

            self.contacts_combobox.setEnabled(pm_call_off)
            self.btn_call.setEnabled(pm_call_off)
            self.btn_snapshot.setEnabled(not pm_call_off)
            
            #Enable profile btns
            self.btn_profile1.setEnabled((not pm_call_off) and (
                                                    self._profile1 is not None))
            self.btn_profile2.setEnabled((not pm_call_off) and (
                                                    self._profile2 is not None))
            self.btn_profile3.setEnabled((not pm_call_off) and (
                                                    self._profile3 is not None))
            
            self._change_call_btn_text()

    def _slot_terminate_call(self):
        """
        Hang up the call
        """
        self._video_engine.terminate_call()

        self._change_incall_btn_states(pm_call_off=True)

    def _slot_set_contact_id(self, pm_index):
        """
        Set contact ID
        """
        if pm_index == 0:
            self._current_contact_addr = None
            self.btn_call.setEnabled(False)
            return

        self._current_contact_addr = self._index_to_address_dict[pm_index]
        self.btn_call.setEnabled(True)

    def _slot_make_call(self):
        """
        Make call to selected contact
        """
        if self._current_contact_addr is None:
            return

        self._video_engine.call(self._current_contact_addr)

        if self.advanced_interface:
            self.btn_call.setEnabled(False)

        self.btn_hangup.setEnabled(True)
        self._change_call_btn_text()
        
        logger.info("Making call to : %r", self._current_contact_addr)

        #self._change_incall_btn_states(pm_call_off=False)

    def _slot_snapshot(self):
        """
        Take remote snapshot
        """
        self.btn_snapshot.setEnabled(False)

        #Progress dialog while visio setup is in progress
        self._snapshot_progress_dlg = MHProgressDialog(
                                        _('VISIO_dlg_SnapshotInProgress'),
                                        _('VISIO_dlg_Cancel'),
                                        pm_css=self._css_path)

        #Show progress dialog
        self._snapshot_progress_dlg.show()

        logger.info("SNAPSHOT : send_preview_snapshot_control_message")
        self._video_engine.send_preview_snapshot_control_message()
        
        #If user cancels the dialog, the snapshot command sent to remote box
        #cannot be cancelled, hence the photo  will still be taken but the 
        #handle_rmt_snapshot will not prompt the user when the cancelled photo
        #is available.
        while True:
            QtGui.QApplication.processEvents()
            # above is needed otherwise QprogressDialog cancel event is not 
            # processed
                
            if self._snapshot_progress_dlg.wasCanceled():
                logger.debug("SNAPSHOT : progress dialog cancelled by user")
                self._snapshot_progress_dlg = None
                self.btn_snapshot.setEnabled(True)
                break

    def _slot_load_profile(self):
        """
        Load requested profile
        """
        requested_profile = self.sender().profile_name
        logger.info("Requested profile is: %r", requested_profile)
        self._video_engine.apply_profile(requested_profile)
        
    def _slot_switch_camera(self):
        """
        Switch camera
        """

        logger.info("Available webcams: %r", self._webcams_list)

        self._video_engine.change_webcam()

#     def _handle_registered(self):
#         """
#         Handle registered event
#         """
#         if self._video_engine.is_ready_to_call():
#             self.contacts_combobox.setEnabled(True)
#             self._load_contacts_in_combobox()

    def _handle_stream_established(self, pm_contact_details):
        """
        Handles stream established event
        Enables GUI buttons accordingly
        """
        logger.info("STREAM established with %r", pm_contact_details)
        self._change_incall_btn_states(pm_call_off=False)

    def _handle_rmt_snapshot(self, pm_url=None):
        """
        Show a msg dialog that photo is available on portal
        """
        if self._snapshot_progress_dlg is None:
            #It means user has cancelled the snapshot action
            #Hence he should not be prompted if photo is available
            return
        
        self._snapshot_progress_dlg.cancel()
        
        logger.info("PHOTO URL: %r", pm_url)
        
        snapshot_msg_dlg = MHDialogMsg(
            'snapshot_msg', 
            _('VISIO_dlg_SnapshotTaken_ConsultPortal.'), 
            pm_css=self._css_path)

        snapshot_msg_dlg.exec_()

    def _handle_answered_event(self, pm_remote_address=None):
        """
        Handle GUI when call is answered
        """

        self._set_btns_state(True)

        self._change_incall_btn_states(pm_call_off=False)

    def _handle_incoming_call(self, pm_caller):
        """
        Handle an incoming call
        """
        #TODO: Use pm_caller for something?
        dlg = MHDialogCnf('incoming_call_alert',
                          _('VISIO_dlg_AcceptIncomingCall?'),
                          pm_css=self._css_path)

        code = dlg.exec_()
        dlg = None

        if code == QtGui.QDialog.Accepted:
            self._video_engine.answer()

            self._change_incall_btn_states(pm_call_off=False)

        elif code == QtGui.QDialog.Rejected:
            self._video_engine.decline_call()

            self._change_incall_btn_states(pm_call_off=True)

    def _handle_failed_event(self, pm_msg):
        """
        Handle failed event. Show an error message
        """

        logger.debug("CALL Error event because: %r", pm_msg)

        errdlg = MHDialogMsg(
                    'failed_msg', 
                    _('VISIO_dlg_ErrorInConnection.'), 
                    pm_css=self._css_path)

        errdlg.exec_()

        self._change_incall_btn_states(pm_call_off = True)

    def _handle_terminated_event(self):
        """
        Handle terminated
        """
        logger.debug("TERMINATED event")
        self._change_incall_btn_states(pm_call_off=True)

        errdlg = MHDialogMsg(
                    'terminated_msg', 
                    _('VISIO_dlg_CallWasEnded.'), 
                    pm_css=self._css_path)
        errdlg.exec_()

    #### Video engine related functions ####
    #
    def _start_video_win_timer(self):
        """
        Timer to set linphone video stream in mh_linphone wgts
        """
        self._activate_video_timer.start(1*1000)  # Every 1 s

    def _activate_video_elements(self, pm_check_webcam=True):
        """
        Activate video elements
        """

        self._video_engine.set_pvideo(self.tx_cam_win_winid)
        self._video_engine.set_vvideo(self.rx_cam_win_winid)

        if pm_check_webcam:
            self._prepare_webcam_list()

        if self.advanced_interface:
            self.contacts_combobox.setEnabled(True)
            self._load_contacts_in_combobox()

    def _prepare_webcam_list(self):
        """
        Prepares webcams list and prompts user if no webcam found
        """
        if self._default_webcam is not None:
            self._video_engine.webcam(use=self._default_webcam)
            
        self.btn_switch_camera.setEnabled(False)
        self._webcams_list = self._video_engine.webcam()

        logger.warning("WEBCAM list is : %r", self._webcams_list)
        
        #Even if there's no webcam attached, the list still contains one 
        #element: #'StaticImage: Static picture']. Hence, we verify if there
        #list length is more than 1, otherwise show an error dialog.
        #TODO: engine should detect "no webcam" instead of gui checking it?
        if self._webcams_list is None or len(self._webcams_list) < 2:

            webcam_msg_dlg = MHDialogMsg(
                                'webcam_msg', 
                                _('VISIO_dlg_MissingWebcam.'), 
                                pm_css=self._css_path)

            webcam_msg_dlg.exec_()

        if len(self._webcams_list) > 2:
            self.btn_switch_camera.setEnabled(True)


    def _load_contacts_in_combobox(self):
        """
        Load contacts in combobox
        """
        self._addr_book = self._video_engine.get_adress_book()
        self.contacts_combobox.clear()
        self.contacts_combobox.insertItem(0, _("VISIO_Contacts"))
        
        # For contacts
        if not self._addr_book:
            return

        self._index_to_address_dict = dict()
        for cnt, contact in enumerate(self._addr_book.contacts):
            self._index_to_address_dict[cnt+1] = contact.address
            text = str("%s" % contact.name)
            self.contacts_combobox.insertItem(cnt+1, text)

        self.contacts_combobox.update()
        self.contacts_combobox.updateGeometry()

    def set_engine(self, pm_engine):
        """
        Set engine
        """
        self._video_engine = pm_engine

    def register_callbacks(self):
        """
        Registers call backs
        """
        #Register events
        event = self._video_engine.EVT

        self._video_engine.register_callback(event.INCOMING,
                                             self.sig_incoming_call.emit)
        self._video_engine.register_callback(event.FAILED,
                                             self.sig_failed.emit)
        self._video_engine.register_callback(event.ANSWERED,
                                             self.sig_answered.emit)
        self._video_engine.register_callback(event.RMT_PREVIEW_SNAPSHOT,
                                             self.sig_rmt_snapshot_taken.emit)
        self._video_engine.register_callback(event.TERMINATED,
                                             self.sig_call_terminated.emit)
#         self._video_engine.register_callback(event.REGISTRATED,
#                                              self.sig_registered.emit)
        
    def launch_video_engine(self):
        """
        Prepare video_engine
        """
        self._video_engine.init()
        self._start_video_win_timer()

    #### QT Overloaded functions ####
    #

    def showEvent(self, pm_event):  # pylint: disable=C0103
        """
        Catch the show event and set focus in text_input
        """
        if hasattr(self, 'text_input_field') and self.text_input_field is not None:
            self.text_input_field.setFocus()
        super(MHVideoWindow, self).showEvent(pm_event)

    def closeEvent(self, pm_close_event):  # pylint: disable=C0103
        """
        Catch the close event and emit signal
        """
        # send an event when main frame is closing
        dlg = MHDialogCnf('leave',
                          _('VISIO_dlg_DoYouReallyWantToCloseVideoWindow?'),
                          pm_css = self._css_path)

        code = dlg.exec_()
        dlg = None

        if code == QtGui.QDialog.Rejected:
            pm_close_event.ignore()
            logger.info("Window close cancelled.")
            return

        self._video_engine.exit()

        super(MHVideoWindow, self).closeEvent(pm_close_event)

# -----------------------------------------------------------------------------
#    Standalone launch (Unit test)
#------------------------------------------------------------------------------

# def mk_parser():
#     """
#     Parse throught options
#     """
#     description = "Gui widget for visiophony"
#     parser = argparse.ArgumentParser(description=description)
#
#     parser.add_argument("--cli", "-c", action='store_true',
#         help="starts a CLI for debugging")
#
#     parser.add_argument("-a", "--app_base", dest="app_base",
#                          action = "store", default = None,
#                          help="The path to the application base")
#     return parser

def prepare_and_launch_window(pm_css_path, pm_i18n_dirpath,
                              pm_fullscreen_enabled=False,
                              pm_vpn_enabled=False):
    """
    Launch video window
    """

    css_path = os.path.realpath(pm_css_path)

    #i18n
    set_locale(pm_i18n_dirpath)

    app = QtGui.QApplication(sys.argv)

    #Create Video Widget
    mh_linphone_widget = MHVideoWindow(pm_css_path=css_path)

    #Create Video Engine
    #win_id_arg = "--wid " + str(widget.tx_cam_win_winid)
    video_engine = mhlinphone_wrapper.MHLinphoneWrapper((
                                '-c',
                                os.path.join(LPConfig.get_default_lp_data_dir(),
                                             "samples", "dev")))

    mh_linphone_widget.set_engine(video_engine)
    mh_linphone_widget.register_callbacks()

    mh_linphone_widget.setWindowTitle(WIN_TITLE)

    if pm_fullscreen_enabled:
        mh_linphone_widget.showFullScreen()
    else:
        mh_linphone_widget.show()

    #Launch video engine
    mh_linphone_widget.launch_video_engine()

    sys.exit(app.exec_())


def main():
    """
    To launch stand alone window (Unit test)
    """
#     args = sys.argv[1:]
#     parser = mk_parser()
#     #options = parser.parse_args(args)

    mydir = os.path.realpath(os.path.dirname(__file__))
    rsrc_dir =  os.path.join(mydir, "pylib", "lpresources")
    i18n_dir = os.path.join(rsrc_dir, "locale")
    css_path = os.path.join(rsrc_dir, 'css', 'mh_linphone.css')

    prepare_and_launch_window(css_path, i18n_dir)

if __name__ == '__main__':
    main()

# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
