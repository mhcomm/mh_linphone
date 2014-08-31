#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : sqlite_wrao.py
"""
  Summary    :  small thread save sqlite wrapper

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

Allows keeping contact information

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
import logging
import sqlite3
import threading


from lp_config import LPConfig
# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)

_CREATE_QRY = """
create table if not exists  %s(
id_    varchar(20) primary key,
address varchar(128),
s
name   varchar(50),
typ    varchar(10),
status varchar(10)
)
"""
class SqliteWrapError(Exception):
    """ custom Exception"""

class SqliteDB(object):
    """ thread safe sqlite wrapper """
    table = None
    _CREATE_QRY = ""

    cnt = 0

    def __init__(self, fname):
        cls = self.__class__
        if cls.cnt:
            raise SqliteWrapError("There can only be one (%s db)" % fname)
        cls.cnt += 1
        self.lock = threading.RLock()
        self.fname = fname
        self.con = None
        self.cur = None
        self.first_connect()

    def first_connect(self):
        con = self.connect()
        cur = con.cursor()
        cur.execute(self._CREATE_QRY % self.table)
        con.commit()

    def connect(self):
        if self.con:
            return self.con
        with self.lock:
            self.con = sqlite3.connect(self.fname, check_same_thread=False)
            return self.con

    def mk_cur(self):
        if self.cur:
            return self.cur
        self.connect()
        with self.lock:
            cur = self.con.cursor()
        return cur

    def commit(self):
        """ commits changes """
        with self.lock:
            self.con.commit()

    def close(self):
        """ closes the sqlite db """
        with self.lock:
            self.con.commit()
            self.con.close()
            self.con = self.cur = None

    def mk_query(self, qry_str, vals):
        with self.lock:
            cur = self.mk_cur()
            rslt = cur.execute(qry_str, vals)
            for entry in cur:
                yield entry

def main():
    pass


if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
