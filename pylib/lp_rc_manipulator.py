# !/usr/bin/env python

# # Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : lp_rc_manipulator
"""
  Summary    :  manipulate linphone rc files

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
from six.moves import configparser
import StringIO

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)


class LpRcManipulator(object):
    def __init__(self, rc_filename):
        self.rc_filename = rc_filename
        self.config = configparser.RawConfigParser()

    def read_rc_file(self):
        self.config.read(self.rc_filename)

    def write_rc_file(self):
        tmp_out = StringIO.StringIO()
        self.config.write(tmp_out)
        buf = tmp_out.getvalue()

        # write in file when '= ' are replaced by '='
        with open(self.rc_filename, 'wb') as configfile:
            buf = buf.replace(' =', '=')
            configfile.write(buf.replace('= ', '='))
        tmp_out.close()

    def set_item(self, section, key, value):
        if type(value) == bool:
            if value:
                value = 1
            else:
                value = 0

        if not self.config.has_section(section):
            self.config.add_section(section)

        # self.config[section][key] = str(value)
        self.config.set(section, key, str(value))

    def enable_linphone_window(self, value):
        self.set_item('video', 'show_local', value)

    def remove_call_logs(self):
        section_prefix = 'call_log_'
        i = 0
        while self.config.has_section(section_prefix + str(i)):
            self.config.remove_section(section_prefix + str(i))
            i += 1


def main():
    pass


if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
