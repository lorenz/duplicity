# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2014 Canonical Ltd
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

import os
import io
import unittest

import duplicity.backend
from duplicity import log
from duplicity import path
from duplicity.errors import BackendException
from . import UnitTestCase


class BackendInstanceBase(UnitTestCase):

    def setUp(self):
        UnitTestCase.setUp(self)
        assert not os.system(u"rm -rf testfiles")
        os.makedirs(u'testfiles')
        self.backend = None
        self.local = path.Path(u'testfiles/local')
        self.local.writefileobj(io.BytesIO(b"hello"))

    def tearDown(self):
        if self.backend is None:
            return
        if hasattr(self.backend, u'_close'):
            self.backend._close()

    def test_get(self):
        if self.backend is None:
            return
        self.backend._put(self.local, u'a')
        getfile = path.Path(u'testfiles/getfile')
        self.backend._get(b'a', getfile)
        self.assertTrue(self.local.compare_data(getfile))

    def test_list(self):
        if self.backend is None:
            return
        self.backend._put(self.local, b'a')
        self.backend._put(self.local, b'b')
        # It's OK for backends to create files as a side effect of put (e.g.
        # the par2 backend does), so only check that at least a and b exist.
        self.assertTrue(b'a' in self.backend._list())
        self.assertTrue(b'b' in self.backend._list())

    def test_delete(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, u'_delete'):
            self.assertTrue(hasattr(self.backend, u'_delete_list'))
            return
        self.backend._put(self.local, b'a')
        self.backend._put(self.local, b'b')
        self.backend._delete(b'a')
        self.assertFalse(b'a' in self.backend._list())
        self.assertTrue(b'b' in self.backend._list())

    def test_delete_clean(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, u'_delete'):
            self.assertTrue(hasattr(self.backend, u'_delete_list'))
            return
        self.backend._put(self.local, b'a')
        self.backend._delete(b'a')
        self.assertEqual(self.backend._list(), [])

    def test_delete_missing(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, u'_delete'):
            self.assertTrue(hasattr(self.backend, u'_delete_list'))
            return
        # Backends can either silently ignore this, or throw an error
        # that gives log.ErrorCode.backend_not_found.
        try:
            self.backend._delete(b'a')
        except BackendException as e:
            pass  # Something went wrong, but it was an 'expected' something
        except Exception as e:
            code = duplicity.backend._get_code_from_exception(self.backend, u'delete', e)
            self.assertEqual(code, log.ErrorCode.backend_not_found)

    def test_delete_list(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, u'_delete_list'):
            self.assertTrue(hasattr(self.backend, u'_delete'))
            return
        self.backend._put(self.local, b'a')
        self.backend._put(self.local, b'b')
        self.backend._put(self.local, b'c')
        self.backend._delete_list([b'a', b'd', b'c'])
        files = self.backend._list()
        self.assertFalse(b'a' in files, files)
        self.assertTrue(b'b' in files, files)
        self.assertFalse(b'c' in files, files)

    def test_move(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, u'_move'):
            return

        copy = path.Path(u'testfiles/copy')
        self.local.copy(copy)

        self.backend._move(self.local, u'a')
        self.assertTrue(b'a' in self.backend._list())
        self.assertFalse(self.local.exists())

        getfile = path.Path(u'testfiles/getfile')
        self.backend._get(b'a', getfile)
        self.assertTrue(copy.compare_data(getfile))

    def test_query_exists(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, u'_query'):
            return
        self.backend._put(self.local, u'a')
        info = self.backend._query(u'a')
        self.assertEqual(info[u'size'], self.local.getsize())

    def test_query_missing(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, u'_query'):
            return
        # Backends can either return -1 themselves, or throw an error
        # that gives log.ErrorCode.backend_not_found.
        try:
            info = self.backend._query(u'a')
        except BackendException as e:
            pass  # Something went wrong, but it was an 'expected' something
        except Exception as e:
            code = duplicity.backend._get_code_from_exception(self.backend, u'query', e)
            self.assertEqual(code, log.ErrorCode.backend_not_found)
        else:
            self.assertEqual(info[u'size'], -1)

    def test_query_list(self):
        if self.backend is None:
            return
        if not hasattr(self.backend, u'_query_list'):
            return
        self.backend._put(self.local, u'a')
        self.backend._put(self.local, u'c')
        info = self.backend._query_list([u'a', u'b'])
        self.assertEqual(info[u'a'][u'size'], self.local.getsize())
        self.assertEqual(info[u'b'][u'size'], -1)
        self.assertFalse(u'c' in info)


class LocalBackendTest(BackendInstanceBase):
    def setUp(self):
        super(LocalBackendTest, self).setUp()
        url = u'file://testfiles/output'
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, u'LocalBackend')


class Par2BackendTest(BackendInstanceBase):
    def setUp(self):
        super(Par2BackendTest, self).setUp()
        url = u'par2+file://testfiles/output'
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, u'Par2Backend')

    # TODO: Add par2-specific tests here, to confirm that we can recover from
    # a missing file


# class RsyncBackendTest(BackendInstanceBase):
#     def setUp(self):
#         super(RsyncBackendTest, self).setUp()
#         os.makedirs('testfiles/output')  # rsync needs it to exist first
#         url = 'rsync://%s/testfiles/output' % os.getcwd()
#         self.backend = duplicity.backend.get_backend_object(url)
#         self.assertEqual(self.backend.__class__.__name__, 'RsyncBackend')


class TahoeBackendTest(BackendInstanceBase):
    def setUp(self):
        super(TahoeBackendTest, self).setUp()
        os.makedirs(u'testfiles/output')
        url = u'tahoe://testfiles/output'
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, u'TAHOEBackend')


class HSIBackendTest(BackendInstanceBase):
    def setUp(self):
        super(HSIBackendTest, self).setUp()
        os.makedirs(u'testfiles/output')
        # hostname is ignored...  Seemingly on purpose
        url = u'hsi://hostname%s/testfiles/output' % os.getcwd()
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, u'HSIBackend')


class FTPBackendTest(BackendInstanceBase):
    def setUp(self):
        super(FTPBackendTest, self).setUp()
        os.makedirs(u'testfiles/output')
        url = u'ftp://user:pass@hostname/testfiles/output'
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, u'LFTPBackend')


class FTPSBackendTest(BackendInstanceBase):
    def setUp(self):
        super(FTPSBackendTest, self).setUp()
        os.makedirs(u'testfiles/output')
        url = u'ftps://user:pass@hostname/testfiles/output'
        self.backend = duplicity.backend.get_backend_object(url)
        self.assertEqual(self.backend.__class__.__name__, u'LFTPBackend')


if __name__ == u"__main__":
    unittest.main()
