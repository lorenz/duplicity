# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2002 Ben Escoto <ben@emerose.org>
# Copyright 2007 Kenneth Loafman <kenneth@loafman.com>
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

import sys
import unittest

from duplicity import log  # @UnusedImport
from duplicity.path import *  # @UnusedWildImport
from . import UnitTestCase


class PathTest(UnitTestCase):
    u"""Test basic path functions"""
    def setUp(self):
        super(PathTest, self).setUp()
        self.unpack_testfiles()

    def test_deltree(self):
        u"""Test deleting a tree"""
        assert not os.system(u"cp -pR testfiles/deltree testfiles/output")
        p = Path(u"testfiles/output")
        assert p.isdir()
        p.deltree()
        assert not p.type, p.type

    # FIXME: How does this test make any sense?  Two separate Path objects
    # will never be equal (they don't implement __cmp__ or __eq__)
    # def test_compare(self):
    #    """Test directory comparisons"""
    #    assert not os.system("cp -pR testfiles/dir1 testfiles/output")
    #    assert Path("testfiles/dir1").compare_recursive(Path("testfiles/output"), 1)
    #    assert not Path("testfiles/dir1").compare_recursive(Path("testfiles/dir2"), 1)

    def test_quote(self):
        u"""Test path quoting"""
        p = Path(u"hello")
        assert p.quote() == u'"hello"'
        assert p.quote(u"\\") == u'"\\\\"', p.quote(u"\\")
        assert p.quote(u"$HELLO") == u'"\\$HELLO"'

    def test_unquote(self):
        u"""Test path unquoting"""
        p = Path(u"foo")  # just to provide unquote function

        def t(s):
            u"""Run test on string s"""
            quoted_version = p.quote(s)
            unquoted = p.unquote(quoted_version)
            assert unquoted == s, (unquoted, s)

        t(u"\\")
        t(u"$HELLO")
        t(u" aoe aoe \\ \n`")

    def test_canonical(self):
        u"""Test getting canonical version of path"""
        c = Path(u".").get_canonical()
        assert c == b".", c

        c = Path(u"//foo/bar/./").get_canonical()
        assert c == b"/foo/bar", c

    def test_compare_verbose(self):
        u"""Run compare_verbose on a few files"""
        vft = Path(u"testfiles/various_file_types")
        assert vft.compare_verbose(vft)
        reg_file = vft.append(u"regular_file")
        assert not vft.compare_verbose(reg_file)
        assert reg_file.compare_verbose(reg_file)
        file2 = vft.append(u"executable")
        assert not file2.compare_verbose(reg_file)
        assert file2.compare_verbose(file2)


if __name__ == u"__main__":
    unittest.main()
