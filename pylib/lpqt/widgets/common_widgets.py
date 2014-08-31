##!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : common_widgets.py
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

 This is the widgets used by GUI window
 #TODO: Update description as the coded evolves.

"""
# #############################################################################
from __future__ import absolute_import
#from __future__ import print_function

__author__    = "Mrugesh Chauhan"
__copyright__ = "(C) 2014 by MHComm. All rights reserved"
__email__     = "info@mhcomm.fr"

# -----------------------------------------------------------------------------
#   Imports
# -----------------------------------------------------------------------------
import logging
import os

#from visio_gui import gui
from python_qt_binding import QtGui
from python_qt_binding import QtCore
from python_qt_binding.QtCore import Qt

import build.mh_linphone_pixmaps_rc

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = logging.getLogger(__file__)

# -----------------------------------------------------------------------------
#    Dialog base class
# -----------------------------------------------------------------------------

class MHDialog(QtGui.QDialog):
    """
    Dialog with 'Yes' and 'No' buttons.
    """

    def __init__(self, pm_name, pm_label, pm_css=None, parent=None):
        super(MHDialog, self).__init__(parent)

        self.setObjectName(pm_name)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(
                          Qt.FramelessWindowHint|QtCore.Qt.WindowStaysOnTopHint)
        self.main_layout = None
        self.btn_layout = None

        self.setMouseTracking(True)

        self._msg_label = pm_label

        self._css = pm_css

    def _setup_ui(self):

        main_layout = QtGui.QVBoxLayout(self)

        main_layout.addStretch(1)
        msg_lb = QtGui.QLabel(self._msg_label)
        #msg_lb.setWordWrap(True)

        main_layout.addWidget(msg_lb, alignment=Qt.AlignCenter, stretch=1)

        main_layout.addStretch(1)

        btn_layout = QtGui.QHBoxLayout()

        main_layout.addLayout(btn_layout)
        main_layout.addStretch(1)

        #Apply CSS
        if self._css is not None and os.path.exists(self._css):
            self.setStyleSheet(open(self._css).read())

        self.btn_layout = btn_layout
        self.main_layout = main_layout

    def _create_nav_bar(self, pm_btns):
        """
        Create nav bar
        """
        for btn in pm_btns:
            self.btn_layout.addWidget(btn)

    def _insert_widget(self, pm_widget, pm_where):
        """
        Instert widget pm_widget at pm_where
        """
        self.main_layout.insertWidget(pm_where, pm_widget)

# -----------------------------------------------------------------------------
#    Dialog: confirmation dialog with yes and no options
# -----------------------------------------------------------------------------

class MHDialogCnf(MHDialog):
    """
    Dialog with 'Yes' and 'No' buttons.
    """

    def __init__(self, pm_name, pm_label, pm_css=None, parent=None):

        super(MHDialogCnf, self).__init__(pm_name,
                                          pm_label,
                                          pm_css=pm_css,
                                          parent=parent)

        self.setObjectName(pm_name)

        self._setup_ui()

        btns = [MHPushButton(self, 'valid', _("VISIO_btn_Yes"), self.accept),
                MHPushButton(self, 'cancel', _("VISIO_btn_No"), self.reject)]

        self._create_nav_bar(btns)

# -----------------------------------------------------------------------------
#    Dialog: Message dialog with "ok" button
# -----------------------------------------------------------------------------
class MHDialogMsg(MHDialog):
    """
    Dialog with an Ok button
    """

    def __init__(self, pm_name, pm_label, pm_css=None, parent=None):

        super(MHDialogMsg, self).__init__(pm_name,
                                          pm_label,
                                          pm_css=pm_css,
                                          parent=parent)

        self.setObjectName(pm_name)

        self._setup_ui()

        btns = [MHPushButton(self, 'valid', _("VISIO_btn_Ok"), self.accept)]

        self._create_nav_bar(btns)

# -----------------------------------------------------------------------------
#    Dialog: Shows a photo with "ok" button
# -----------------------------------------------------------------------------

class MHDialogShowPhoto(MHDialog):
    """
    Dialog with a title, image preview, validate and 'close' button.
    """

    def __init__(
                self,
                pm_name,
                pm_label,
                pm_image_path,
                pm_css=None, parent=None):
        super(MHDialogShowPhoto, self).__init__(pm_name,
                                                pm_label,
                                                pm_css=pm_css,
                                                parent=parent)

        self.setObjectName(pm_name)

        self._setup_ui()

        btns = [MHPushButton(self, 'valid', _("VISIO_btn_Ok"), self.accept)]

        self._create_nav_bar(btns)

        lb_preivew = QtGui.QLabel('snapshot')
        lb_preivew.setAlignment(Qt.AlignCenter)
        img_pixmap = QtGui.QPixmap(pm_image_path)
        lb_preivew.setPixmap(img_pixmap)
        self.adjustSize()

        self._insert_widget(lb_preivew, 2)

# -----------------------------------------------------------------------------
#    QProgressDialog
# -----------------------------------------------------------------------------

class MHProgressDialog(QtGui.QProgressDialog):
    """
    Progress Dialog.
    """

    def __init__(
        self, 
        pm_label, 
        pm_cancel_text,
        pm_css=None,
        pm_min=0, 
        pm_max=0, 
        parent=None):

        super(MHProgressDialog, self).__init__(
                                            pm_label, 
                                            pm_cancel_text, 
                                            pm_min, 
                                            pm_max)

        parent = parent

        self.setMinimum(pm_min)
        self.setMaximum(pm_max)
        self.setValue(-1)
        self.setModal(True)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(
                          Qt.FramelessWindowHint|QtCore.Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)
        
        #Apply CSS
        if pm_css is not None and os.path.exists(pm_css):
            self.setStyleSheet(open(pm_css).read())
            

# -----------------------------------------------------------------------------
#   Btns for video window
# -----------------------------------------------------------------------------
class MHPushButton(QtGui.QPushButton):
    """
    Video call buttons
    """
    def __init__(self, parent, pm_name, pm_label, *pm_args):
        super(MHPushButton, self).__init__(parent)

        policy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                   QtGui.QSizePolicy.Minimum)
        self.setSizePolicy(policy)

        if parent:
            setattr(parent, pm_name, self)
        self.setObjectName(pm_name)
        self.setText(pm_label)

        # Assign arguments to there proper functions
        if 0 < len(pm_args):
            if callable(pm_args[0]):
                self.clicked.connect(pm_args[0], Qt.UniqueConnection)
                pm_args = pm_args[1:]
            elif isinstance(pm_args[0], QtCore.QObject):
                if (1 == len(pm_args)):
                    raise Exception("Signal argument is missing")
                if not isinstance(pm_args[1], QtCore.Signal):
                    raise Exception("signal should be a QtCore.Signal type")
                self.clicked.connect(pm_args[0].pm_args[1].emit)
                pm_args = pm_args[2:]

        if 0 < len(pm_args):
            raise Exception("Too many arguments")

class MHProfilePushButton(MHPushButton):
    """
    Profile button
    """
    def __init__(self, parent, pm_name, pm_label, pm_profile_name, *pm_args):
        super(MHProfilePushButton, self).__init__(
                                        parent, pm_name, pm_label, *pm_args)
        
        self.profile_name = pm_profile_name

# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------