# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2014 Michael Terry <michael.terry@canonical.com>
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
import subprocess
import pytest
import fnmatch
import os

if os.getenv(u'RUN_CODE_TESTS', None) == u'1':
    # Make conditional so that we do not have to import in environments that
    # do not run the tests (e.g. the build servers)
    import pycodestyle

from . import _top_dir, DuplicityTestCase  # @IgnorePep8
from . import find_unadorned_strings

skipCodeTest = pytest.mark.skipif(not os.getenv(u'RUN_CODE_TESTS', None) == u'1',
                                  reason=u'Must set environment var RUN_CODE_TESTS=1')


class CodeTest(DuplicityTestCase):

    def run_checker(self, cmd, returncodes=[0]):
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output = process.communicate()[0]
        self.assertTrue(process.returncode in returncodes, output)
        self.assertEqual(b"", output, output)

    @skipCodeTest
    def test_2to3(self):
        # As we modernize the source code, we can remove more and more nofixes
        self.run_checker([
            u"2to3",
            u"--nofix=next",
            u"--nofix=types",
            u"--nofix=unicode",
            # The following fixes we don't want to remove, since they are false
            # positives, things we don't care about, or real incompatibilities
            # but which 2to3 can fix for us better automatically.
            u"--nofix=callable",
            u"--nofix=dict",
            u"--nofix=future",
            u"--nofix=imports",
            u"--nofix=print",
            u"--nofix=raw_input",
            u"--nofix=urllib",
            u"--nofix=xrange",
            u"--nofix=map",
            _top_dir])

    @skipCodeTest
    def test_pylint(self):
        u"""Pylint test (requires pylint to be installed to pass)"""
        self.run_checker([
            u"pylint",
            u"-E",
            u"--msg-template={msg_id}: {line}: {msg}",
            u"--disable=E0203",  # Access to member before its definition line
            u"--disable=E0602",  # Undefined variable
            u"--disable=E0611",  # No name in module
            u"--disable=E1101",  # Has no member
            u"--disable=E1102",  # is not callable (_)
            u"--disable=E1103",  # Maybe has no member
            u"--disable=E0712",  # Catching an exception which doesn't inherit from BaseException
            u"--ignore=_librsync.so",
            u"--msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'",
            os.path.join(_top_dir, u'duplicity'),
            os.path.join(_top_dir, u'bin/duplicity'),
            os.path.join(_top_dir, u'bin/rdiffdir')],
            # Allow usage errors, older versions don't have
            # --msg-template
            [0, 32])

    @skipCodeTest
    def test_pep8(self):
        u"""Test that we conform to PEP-8 using pycodestyle."""
        # Note that the settings, ignores etc for pycodestyle are set in tox.ini, not here
        style = pycodestyle.StyleGuide(config_file=os.path.join(_top_dir, u'tox.ini'))
        result = style.check_files([os.path.join(_top_dir, u'duplicity'),
                                    os.path.join(_top_dir, u'bin/duplicity'),
                                    os.path.join(_top_dir, u'bin/rdiffdir')])
        self.assertEqual(result.total_errors, 0,
                         u"Found %s code style errors (and warnings)." % result.total_errors)

    @skipCodeTest
    def test_unadorned_string_literals(self):
        u"""For predictable results in python2/3 all string literals need to be marked as unicode, bytes or raw"""

        ignored_files = [
                         # These are not source files we want to check
                         os.path.join(_top_dir, u'.tox', u'*'),
                         os.path.join(_top_dir, u'.eggs', u'*'),
                         os.path.join(_top_dir, u'docs', u'conf.py'),
                         # TODO Every file from here down needs to be fixed and the exclusion removed
                         os.path.join(_top_dir, u'setup.py'),
                         os.path.join(_top_dir, u'duplicity', u'compilec.py'),
                         ]


        # Find all the .py files in the duplicity tree
        # We cannot use glob.glob recursive until we drop support for Python < 3.5
        matches = []

        def multi_filter(names, patterns):
            u"""Generator function which yields the names that match one or more of the patterns."""
            for name in names:
                if any(fnmatch.fnmatch(name, pattern) for pattern in patterns):
                    yield name

        for root, dirnames, filenames in os.walk(_top_dir):
            for filename in fnmatch.filter(filenames, u'*.py'):
                matches.append(os.path.join(root, filename))

        excluded = multi_filter(matches, ignored_files) if ignored_files else []
        matches = list(set(matches) - set(excluded))

        for python_source_file in matches:
            # Check each of the relevant python sources for unadorned string literals
            unadorned_string_list = find_unadorned_strings.check_file_for_unadorned(python_source_file)
            self.assertEqual([], unadorned_string_list,
                             u"Found %s unadorned strings: \n %s" % (len(unadorned_string_list), unadorned_string_list))


if __name__ == u"__main__":
    unittest.main()
