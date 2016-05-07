import os
import unittest

from auto_archive_files.archiver import get_files
from auto_archive_files.tests.base import MockTreeNode

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


class TestGetFiles(MockTreeNode):

    def test_get_all_files(self):
        entries = list(get_files(self.directory, {}))
        entries = [entry.path for entry in entries]
        print(entries)
        import collections
        print([item for item, count in collections.Counter(entries).items() if count > 1])
        self.assertListEqual(entries, list(set(entries)))


if __name__ == '__main__':
    unittest.main()
