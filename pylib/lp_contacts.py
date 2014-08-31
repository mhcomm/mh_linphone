#!/usr/bin/env python

# ############################################################################
# Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : lp_contacts.py
"""
  Summary    :  persistent management of linphone contacts

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
import json
import threading
from collections import OrderedDict


from lp_config import LPConfig
from sqlite_wrap import SqliteDB
# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)

class ContactsError(Exception):
    """ custom Exception"""

class Contact(object):
    """ Entry of a phonebook contact 
    address can be populated from json files or an sqlite file
    Advantage of sqlite is higher robustness against powerloss / 
    file system problems
    """
    def __init__(self, address=None, name=None, typ=None, status=None, 
            id_=None):
        self.address = address
        self.name = name
        self.typ = typ
        self.status = status
        self.id_ = id_

    def __str__(self):
        return "%s (%s)" % (self.address, self.name)

    def __repr__(self):
        return "<%s %s %s (%s)>" % (type(self), self.id_, 
                self.address, self.name)

    def as_dict(self):
        return dict(vars(self))
    
    def as_tuple(self):
        return (
            self.id_,
            self.address,
            self.name,
            self.typ,
            self.status,
                )
    
    def update(self, other):
        """ updates existing contact with information of 
            another contact object.
            !!! The id_ MUST be identical
        """
        if self.id_ != other.id_:
            raise ContactsError("update requires identical ids")
        self.address = other.address
        self.name = other.name
        self.typ = other.typ
        self.status = other.status


class ContactDB(SqliteDB):
    _CREATE_QRY = """
    create table if not exists  %s(
    id_    varchar(20) primary key,
    address varchar(128),
    name   varchar(50),
    typ    varchar(10),
    status varchar(10)
    )
    """

    table = "contacts"

    def save_contact(self, contact, commit=True, update=True):
        if update:
            cmd = 'insert or replace'
        else:
            cmd = 'insert'
        qry = ("%s into %s (id_, address, name, typ, status) "
                "values(?,?,?,?,?)" %  (cmd, self.table))
        with self.lock:
            cur = self.mk_cur()
            cur.execute(qry, contact.as_tuple())
            if commit:
                self.con.commit() 

    def get_contacts(self):
        qry = ("select address, name, typ, status, id_ from %s" % 
                self.table )
        for entry in self.mk_query(qry, () ):
            contact = Contact(*entry) # pylint: disable=W0142
            yield contact

    def update_contacts(self, contacts):
        save = self.save_contact
        for contact in contacts:
            save(contact)

    def clear_contacts(self):
        with self.lock:
            cur = self.mk_cur()
            qry = ("delete from %s" % self.table)
            cur.execute(qry)
            self.con.commit() 


class ABookError(Exception):
    """ custom exception """


class AddressBook(object):
    def __init__(self, updated_callback=None):
        self.lock = threading.RLock()
        self.contacts = []
        self.updated_callback = updated_callback
        self._c_by_addr = {}
        self._c_by_id = {}
        self.fname = None
        self.db = None
        self.auto_save = True

    def _add_contact(self, contact):
        id_ = contact.id_
        if id_ is None:
            logger.warning('ignoring entry without id %r', contact)
        by_id = self._c_by_id
        by_addr = self._c_by_addr
        if id_ in by_id:
            msg = 'contact already in address book'
            raise ABookError(msg)
        self.contacts.append(contact)
        by_id[id_] = contact
        by_addr[contact.address] = contact
        if self.auto_save and self.db:
            self.db.save_contact(contact)
            
    def add_contact(self, contact):
        with self.lock:
            return self._add_contact(contact)

    def del_contact(self, contact):
        raise NotImplementedError('cannot remove contacts atm')

    def update_contact(self, contact):
        with self.lock:
            try:
                self.add_contact(contact)
                return contact
            except ABookError:
                pass
            old_contact = self._c_by_id[contact.id_]
            old_contact.update(contact)

    def as_json_dict(self):
        """ returns address book as a structure, that can be saved as json
        """
        data = OrderedDict()
        adict = OrderedDict([
            ('type', 'lp_addressbook'),
            ('version', '1.0'),
            ('data', data),
            ])
        data['entries'] = entries = []
        for entry in self.contacts:
            entries.append(entry.as_dict())

        return adict

    def load_from_json_dict(self, json_dict):
        """ loads abook from a dict """
        typ = json_dict['type']
        if typ != "lp_addressbook":
            raise ABookError("unknown type %r" % typ)
        #version = json_dict['version']
        entries = json_dict['data']['entries']
        self.contacts[:] = []
        for entry in entries:
            contact = Contact(**entry) # pylint: disable=W0142
            self.update_contact(contact)

    def load_json(self, fname='lp_contacts.json', autocreate=True):
        """ loads address book from a json file """
        if autocreate:
            LPConfig.copy_from_template_if_not_exists('contacts.json', fname)

        self.fname = fname
        if not os.path.exists(fname):
            with open(fname, 'wb') as fout:
                json.dump(self.as_json_dict, fout)

        with open(fname, 'rb') as fin:
            adict = json.load(fin)
        self.load_from_json_dict(adict)

    def _sqlite_open(self, fname):
        """ open related db if not already opened """
        if not self.db:
            self.db = ContactDB(fname)
        return self.db

    def _sqlite_close(self):
        """ close related db """
        self.db.close()
        self.db = None

    def load_sqlite(self, fname):
        db = self._sqlite_open(fname)
        for contact in db.get_contacts():
            self.update_contact(contact)

    def __getitem__(self, key):
        with self.lock:
            if type(key) == int:
                return self.contacts[key]
            else:
                return self._c_by_id[key]

    def save_json(self, fname=None,):
        with open(fname, 'wb') as fout:
            json.dump(self.as_json_dict(), fout, indent=1)

    def save_sqlite(self, fname):
        print("SAVE SQL")
        db = self._sqlite_open(fname)
        for contact in self.contacts:
            db.save_contact(contact)

    def save(self, fname=None):
        """ saves contact list to a file """
        fname = fname or self.fname
        suffix = os.path.splitext(fname)[1]
        if suffix.lower() == '.json':
            self.save_json(fname)
        elif suffix.lower() in ('.sqlite', '.db'):
            self.save_sqlite(fname)
        else:
            self.save_json(fname)

    def load(self, fname=None, autocreate=True):
        """ loads contact list from a file """
        if fname is None:
            if self.fname is None:
                fname = 'lp_contacts.json'
            else:
                fname = self.fname
        self.fname = fname

        suffix = os.path.splitext(fname)[1]
        if suffix.lower() == '.json':
            self.load_json(fname, autocreate)
        elif suffix.lower() in ('.sqlite', '.db'):
            self.load_sqlite(fname)
        else:
            self.load_json(fname, autocreate)
        callbk = self.updated_callback
        if callbk:
            callbk()

    def reload(self):
        self.load(self.fname, autocreate=False)

    def all(self):
        for contact in self.contacts:
            yield contact

    def find_by_address(self, search):
        if search is None:
            return None
        for contact in self.contacts:
            if contact.address == search.strip():
                return contact
        return None
    

def main():
    abook = AddressBook()
    contact1 = Contact(id_='01', name='contact1', 
            address="sip:toto@1.2.3.4", typ="patient")
    contact2 = Contact(id_='02', name='contact2', 
            address="sip:tata@1.2.3.5", typ="medic")
    abook.add_contact(contact1)
    abook.add_contact(contact2)
    abook.save("contacts.json")
    abook = AddressBook()
    abook.load("contacts.json")
    for contact in abook.all():
        print(contact)
    abook.save("contacts.sqlite")
    abook.load("contacts.json")
    abook.load("contacts.sqlite")
    for contact in abook.all():
        print(contact)


if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
