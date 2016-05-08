import os
import unittest

import time

from auto_archive_files.archiver import get_files
from auto_archive_files.tests.base import MockTreeNode, FakeEntry

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


class TestGetFiles(MockTreeNode):

    def test_get_all_files(self):
        entries = list(get_files(self.directory, {}))
        entries = sorted([entry.path for entry in entries])
        self.assertListEqual(entries, sorted(list(set(entries))))
        self.assertListEqual(entries, sorted(self.deep_list_dir()))

    def test_get_filtered(self):
        entries = [entry.path for entry in get_files(self.directory, {'type': 'dir'})]
        walk_entries = filter(lambda x: os.path.isdir(x), self.deep_list_dir())
        self.assertListEqual(sorted(entries), sorted(walk_entries))

    def test_filters(self):
        mtime = time.time() - 1000
        fake = FakeEntry(mtime=mtime)
        self.assertTrue(fake.analize_filter('mtime', mtime))
        for param, value in {'eq': mtime, 'ne': mtime - 1, 'lt': mtime + 1, 'le': mtime, 'gt': mtime - 1,
                             'ge': mtime - 1}.items():
            self.assertTrue(fake.analize_filter('mtime__' + param, value), 'Fail with ' + param)
        for param, value in {'eq': mtime - 1, 'ne': mtime, 'lt': mtime - 1, 'le': mtime - 1, 'gt': mtime + 1,
                             'ge': mtime + 1}.items():
            self.assertFalse(fake.analize_filter('mtime__' + param, value), 'Fail with ' + param)



if __name__ == '__main__':
    unittest.main()
