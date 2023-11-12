import os
import tempfile
import unittest
import logging
from metrics_local import purge_cache

class TestPurgeCache(unittest.TestCase):

    def setUp(self):
        # Set up a temporary directory with files
        self.test_dir = tempfile.mkdtemp()
        self.create_test_files(self.test_dir, num_files=5, file_size=1024)  # Creating 5 files of 1 KB each

    def tearDown(self):
        # Clean up the directory after tests
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def create_test_files(self, directory, num_files, file_size):
        # Create a number of test files with specified size
        for i in range(num_files):
            with open(os.path.join(directory, f'test_file_{i}.txt'), 'wb') as f:
                f.write(b'0' * file_size)

    def test_purge_cache(self):
        # Test if purge_cache reduces the directory size as expected
        initial_size_kb = sum(os.path.getsize(os.path.join(self.test_dir, f)) for f in os.listdir(self.test_dir)) // 1024
        allowed_size_kb = initial_size_kb // 2  # Allow only half of the initial size

        purge_cache(self.test_dir, allowed_size_kb)

        final_size_kb = sum(os.path.getsize(os.path.join(self.test_dir, f)) for f in os.listdir(self.test_dir)) // 1024
        self.assertLessEqual(final_size_kb, allowed_size_kb)

if __name__ == '__main__':
    unittest.main()