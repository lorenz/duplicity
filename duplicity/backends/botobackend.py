# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2019 Lorenz Brun <lorenz@brun.one>
#
# This file is part of duplicity.
#
# Duplicity is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Duplicity is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with duplicity; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import duplicity.backend
from duplicity import globals

import os

import duplicity.backend
from duplicity import log
from duplicity import path
from duplicity.errors import BackendException

from botocore.client import Config

import boto3
import logging
import itertools

class BotoBackend(duplicity.backend.Backend):
    u"""
    Amazon S3-style storage backend
    """
    def __init__(self, parsed_url):
        duplicity.backend.Backend.__init__(self, parsed_url)

        path_segments = filter(bool, parsed_url.path.split('/'))

        if parsed_url.scheme == 's3':
            self.s3 = boto3.resource('s3').Bucket(parsed_url.netloc)
            self.prefix = '/'.join(path_segments)
        else:
            self.prefix = '/'.join(path_segments[1:])
            self.s3 = boto3.resource('s3',
                    endpoint_url=parsed_url.scheme[3:] + '://' + parsed_url.netloc,
                    config=Config(signature_version='s3v4'),
                    region_name='us-east-1').Bucket(path_segments[0])
        
        if not self.prefix == '':
            self.prefix += '/'

    def _put(self, source_path, remote_filename):
        self.s3.upload_file(source_path.name, self.prefix + remote_filename)

    def _get(self, filename, local_path):
        self.s3.download_file(self.prefix + filename, local_path.name)

    def _list(self):
        return itertools.imap(lambda o: o.key, self.s3.objects.filter(Prefix=self.prefix))

    def _delete(self, filename):
        self.s3.Object(self.prefix + filename).delete()

    def _query(self, filename):
        return {u'size': self.s3.Object(self.prefix + filename).content_length}

duplicity.backend.register_backend(u"s3", BotoBackend)
duplicity.backend.register_backend(u"s3+http", BotoBackend)
duplicity.backend.register_backend(u"s3+https", BotoBackend)
duplicity.backend.uses_netloc.extend([u's3', u's3+http', u's3+https'])
