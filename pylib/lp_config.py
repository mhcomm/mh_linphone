# !/usr/bin/env python

# # Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : lp_config.py
"""
  Summary    :  simple container for an mh_linphone's config

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
# from __future__ import absolute_import
from __future__ import print_function

__author__ = "Julien Barreau"
__copyright__ = "(C) 2014 by MHComm. All rights reserved"
__email__ = "info@mhcomm.fr"

# -----------------------------------------------------------------------------
#   Imports
# -----------------------------------------------------------------------------
import logging
import json
import os
import shutil

import path_tools
from set_paths import TOP_DIR
# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__),
      TOP_DIR, 'config', 'templates')


class LPConfig(object):
    """ class containing mh_linphone's config information in a 
        dict like/.ini file like manner
    """
    def __init__(self, filename=None):
        self.values = {}
        self.filename = filename

        if filename is None:
            filename = self.get_default_lp_config()

        self.copy_from_template_if_not_exists("lp_config.json", filename)

        if filename.endswith(".json"):
            self.load_from_json(filename)

    def get(self, name, default=None):
        """ fetches a value by name.
            name normally looks like "section.name"
        """
        val = self.values['data'].get(name, default)

        # create temp dir before anybody tries to use it
        # perhaps move it out there. this is a little strange
        if name == 'mh_lp.tmp_dir':
            dir = os.path.join(self.get_default_lp_data_dir(), val)
            if not os.path.isdir(dir):
                os.makedirs(dir)
        return val

    def set(self, name, value):
        """ sets a value by name.
            name normally looks like "section.name"
        """
        self.values['data'][name] = value

    def load_from_json(self, filename):
        self.filename = filename
        self.values.clear()
        with open(filename, 'rb') as fin:
            self.values.update(json.load(fin))

    #######    static methods    #######
    @staticmethod
    def get_default_lp_data_dir():
        """
        :return: the default path for data directory, or the one set in
            environment variable
        """
        dir_name = os.environ.get('MH_LP_DATA_DIR')
        if dir_name is None:
            dir_name = os.path.realpath(os.path.join(os.path.dirname(__file__),
               TOP_DIR, 'config'))
        return dir_name

    @classmethod
    def get_default_lp_config(cls):
        """
        :return: the default path for config file, or the one set in
            environment variable
        """
        filename = os.environ.get('MH_LP_CONFIG')
        if filename is None:
            filename = os.path.join(cls.get_default_lp_data_dir(),
               'lp_config.json')

        return filename

    @staticmethod
    def get_default_linphonec_exe():
        """
        :return: the default path linphonec.exe, or the one set in
            environment variable
        """
        linphonec_exe = os.environ.get('LINPHONEC_PATH')
        if linphonec_exe is None:
            linphonec_exe = path_tools.get_program_path('linphonec',
                        os.path.join('linphone', 'bin'))
        return linphonec_exe

    @staticmethod
    def copy_from_template_if_not_exists(base_name, dst):
        if not os.path.exists(dst):
            shutil.copy(os.path.join(TEMPLATE_DIR, base_name), dst)


def main():
    pass


if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
