import os
import unittest

from auto_archive_files.archiver import get_files

DIR_PATH = os.path.dirname(os.path.abspath(__file__))


class TestGetFiles(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_all_files(self):
        print(list(get_files('/tmp', {'msince__le': 18000})))


if __name__ == '__main__':
    unittest.main()
