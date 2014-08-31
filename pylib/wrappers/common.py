# !/usr/bin/env python

# # Copyright  : (C) 2014 by MHComm. All rights reserved
#
# Name       : wrappers.common
"""
  Summary    :  common wrapper functions

wrapper functions not to be supposed to change if the linphone wrapper 
mechanism changes

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
import json
from datetime import datetime
import re
import uuid
import os
from collections import OrderedDict
import zipfile
import tempfile

import requests

# -----------------------------------------------------------------------------
#   Globals
# -----------------------------------------------------------------------------
logger = logging.getLogger(__name__)



class ControlMessage(object):
    __new_id = 0
    __AUTHORIZED_CONTROL_MESSAGE = [
        "rmt_preview_snapshot",
        "photo_url",
        "apply_profile",
    ]

    @classmethod
    def get_new_id(cls):
        cls.__new_id += 1
        return cls.__new_id

    def __init__(self, control_message, id=None, sender=None, args="",
                 id_reference=""):
        if id is None:
            id = self.get_new_id()
        self.id = id
        self.control_message = control_message
        self.sender = sender
        self.args = args
        self.id_reference = id_reference

    @classmethod
    def from_string(cls, string, sender=None):
        if sender:
            sender = sender.strip()

        regex = r'^\|\|mh\|(\d+)\|(\d*)\|(.*)\|(.*)$'
        control_msg_rex = re.compile(regex)
        match = control_msg_rex.search(string)
        if not match:
            return None

        id_task = match.group(1)
        id_ref = match.group(2)
        ctrl_msg = match.group(3)
        args = match.group(4).strip()

        if ctrl_msg not in cls.__AUTHORIZED_CONTROL_MESSAGE:
            logger.warning("received unauthorized control message : %r",
                           ctrl_msg)
            logger.debug("string received : %s", string)
            logger.debug("regex for parsing : %s", regex)
            return None

        control_message = ControlMessage(ctrl_msg, id_task, sender, args,
                                         id_ref)
        return control_message

    def to_string(self):
        ret = ("||mh|%d|%s|%s|%s" %
               (self.id, str(self.id_reference), self.control_message,
                self.args))
        return ret


class MHLinphoneEvents(object):
    (
        INCOMING,
        TERMINATED,
        ANSWERED,
        FAILED,
        MESSAGE,
        STREAM_ESTABLISHED,
        REGISTERED,
        CALL_UPDATED,
        RMT_PREVIEW_SNAPSHOT,
        PREVIEW_SNAPSHOT_IN_PROGRESS,
        ADDRESS_BOOK_UPDATED,
        CALL_STATE_CHANGED,
    ) = range(12)


class WebClient(object):
    """ Web client
        default is rather simple, but it can be subclassed
        for more complex authentification etc
        procedure is required could be added here
    """

    def __init__(self, cert=None, ssl_verify=True):
        """ create a session good for cookie store etc
        """
        self.ssl_verify = ssl_verify
        self.cert = cert
        self.session = requests.Session()
        self.setup_headers()

    def login(self):
        pass

    def setup_headers(self):
        """ custom headers to be set up """
        hdrs = {}
        if hdrs:
            self.session.headers.update(hdrs)

    def _set_default_kwargs(self, kwargs):
        """ kwargs to be sent with each request """
        if not 'verify' in kwargs:
            kwargs['verify'] = self.ssl_verify
        if not 'cert' in kwargs and self.cert:
            kwargs['cert'] = self.cert
    
    def get(self, url, *args, **kwargs):
        """ get request """
        kwargs = dict(kwargs)
        self._set_default_kwargs(kwargs)
        #print("GET %r" % url)
        rslt =  self.session.get(url, *args, **kwargs)
        return rslt

    def post(self, url, data, *args, **kwargs):
        """ post request """
        kwargs = dict(kwargs)
        self._set_default_kwargs(kwargs)
        rslt = self.session.post(url, data=data, *args, **kwargs)
        return rslt

    
class ExchangeItem(object):
    type = 'unknown'
    version = '1.0'

    def __init__(self, tmp_dir=None, web_client=None, cert_info=None,
            ssl_verify=False):
        if tmp_dir is None:
            tmp_dir = tempfile.gettempdir()
        self.tmp_dir = tmp_dir

        self.web_client = web_client
        self.cert_info = cert_info
        self.ssl_verify = ssl_verify

        self.uuid = uuid.uuid4().hex
        self.info_json = OrderedDict()

        base_name = self.uuid+'.info.json'
        self.info_file_path = os.path.join(self.tmp_dir, base_name)

        self.zip_path = None
        self.files_in_zip = []

    def _setup_webclient(self):
        web_client = self.web_client
        if web_client is None:
            web_client = WebClient(cert=self.cert_info,
                ssl_verify=self.ssl_verify)
        self.web_client = web_client

    def make_zip(self, additional_files=None, zip_path=None, remove_files=True):
        """
        create a zip file in path 'zip_path', containing 'files' and
                'self.files_in_zip'
        :param additional_files: list of files to zip
        :param zip_path: path of resulting zip default is 'tmp_dir/uuid.zip'
        :param remove_files: if true remove files after zip is created
            /!\ additional_files WILL NOT DELETED
        :return: Nothing
        """
        if not zip_path:
            zip_path = os.path.join(self.tmp_dir, self.uuid + '.zip')
        if not additional_files:
            additional_files = []

        self.zip_path = zip_path
        logger.debug('will create zip file %r', zip_path)
        zip_file = zipfile.ZipFile(self.zip_path, mode='w',
                                   compression=zipfile.ZIP_STORED)

        for file_obj in self.files_in_zip + additional_files:
            if hasattr(file_obj, "__getitem__"):
                path = file_obj.get('path', file_obj)
                name = file_obj.get('name', os.path.basename(path))
            else:
                path = file_obj
                name = os.path.basename(path)
            logger.debug('add file %r as %r', path, name)

            zip_file.write(path , name)

        zip_file.testzip()
        zip_file.close()

        if remove_files:
            for _file in self.files_in_zip:
                os.unlink(_file['path'])

    def unzip(self, file_in_zip, path_file):
        zip_file = zipfile.ZipFile(self.zip_path, mode='r',
                                   compression=zipfile.ZIP_STORED)

        with zip_file.open(file_in_zip, 'r') as fout:
            with open(path_file, 'wb') as fin:
                fin.write(fout.read())
        zip_file.close()

    def upload(self, url):
        """
        upload the zip file to url, if the zip is not made, make it
        :param url: url to post img
        :return: webService result
        """
        if not self.zip_path:
            self.make_zip()

        self._setup_webclient()
        if url.lower().startswith('https:'):
            logger.debug('crt: %r', self.cert_info)

        with open(self.zip_path, 'rb') as file_obj:
            files = {'file': file_obj}
            data = {"uuid": str(self.uuid)}
            logger.debug("connecting to server %r", url)
            rslt = self.web_client.post(url, files=files, data=data)

        if rslt.status_code != 200:
            #TODO: error
            logger.error("upload file by http error, status code : %r",
                         str(rslt.status_code))
            return None
        return rslt.text

    def make_meta(self):
        """ create meta information as json """
        self.info_json.update([
            ('version',  self.version),
            ('type',  self.type),
            ('date', datetime.utcnow().isoformat()),  # utc, iso format
        ])

    def write_meta(self):
        """ write meta information to disk """
        if not self.info_json:
            self.make_meta()
        with open(self.info_file_path, 'wb') as json_file:
            json.dump(self.info_json, json_file, indent=4)
            logger.info('write meta to: %r', self.info_file_path)

        self.files_in_zip.append(dict(
            path=self.info_file_path,
            name=os.path.basename(self.info_file_path)
        ))


class SnapshotItem(ExchangeItem):
    type = 'visio_photo'

    def __init__(self, img_file_path=None, tmp_dir=None, web_client=None,
        cert_info=None, ssl_verify=False):
        ExchangeItem.__init__(self, tmp_dir=tmp_dir, web_client=web_client,
            cert_info=cert_info, ssl_verify=ssl_verify)

        self.img_file_path = img_file_path
        self.photographer = None
        self.subject = None


    @classmethod
    def fetch_from_url(cls, tmp_dir, url, webclient=None):
        obj = cls(tmp_dir=tmp_dir, web_client=webclient)

        obj._setup_webclient()
        webclient = obj.web_client

        #TODO: check CSRF Token
        logger.debug("connecting to server %r", url)
        rslt = webclient.get(url)

        # TODO. perhaps there's an existing module to parse get params?
        uuid = (rslt.url.split('uuid=')[1]).split('&')[0]
        fname = os.path.join(tmp_dir, uuid+'.zip')
        with open(fname, 'wb') as fout:
            fout.write(rslt.content)

        obj.uuid = uuid
        obj.zip_path = fname

        zip_file = zipfile.ZipFile(fname, mode='r',
            compression=zipfile.ZIP_STORED)

        with zip_file.open(obj.uuid+'.info.json') as info:
            obj.info_json.update(json.load(info))
        zip_file.close()

        return obj

    def make_meta(self, photographer=None, subject=None):
        """
         create meta information as json
        :param photographer: person who take the pictures
        :param subject: person who is on the photo
        :return:
        """
        ExchangeItem.make_meta(self)

        img_fname = 'snapshot_'+self.uuid+'.jpg'

        logger.info('json creating')
        try:
            photographer_name = photographer.name
            photographer_id = photographer.id_
        except:
            photographer_name = photographer
            photographer_id = None
        try:
            subject_name = subject.name
            subject_id = subject.id_
        except:
            subject_name = subject
            subject_id = None

        self.info_json.update([
            ("date", datetime.utcnow().isoformat()),  # utc, iso format
            ("filename", img_fname),
            # relative to this path
            ("photographer", photographer_name),
            ("photographer_uid", photographer_id),
            ("subject", subject_name),
            ("subject_uid", subject_id),
        ])

        self.files_in_zip.append(dict(
            path=self.img_file_path,
            name=img_fname,
        ))


def synchronized(lock):
    """Synchronization decorator."""
    def wrap(f):
        def new_function(*args, **kw):
            with lock:
                return f(*args, **kw)

        return new_function
    return wrap


def main():
    pass


if __name__ == '__main__':
    main()
# -----------------------------------------------------------------------------
#   End of file
# -----------------------------------------------------------------------------
