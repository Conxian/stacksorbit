import os
import unittest
import shutil
import tempfile
from stacksorbit_secrets import is_safe_path

class TestSentinelPathSafety(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.outside_dir = tempfile.mkdtemp()

        # Create a secret file outside the test directory
        self.secret_file = os.path.join(self.outside_dir, "secret.txt")
        with open(self.secret_file, "w") as f:
            f.write("top secret info")

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.outside_dir)

    def test_should_reject_symlink_to_outside_file(self):
        # 🛡️ Sentinel: Regression test for Path Traversal via symlinks.
        # Ensure that symlinks pointing to files outside the base directory are rejected.
        link_path = os.path.join(self.test_dir, "link_to_secret")

        try:
            os.symlink(self.secret_file, link_path)
        except (AttributeError, OSError):
            # Skip test if symlinks are not supported (e.g. on some Windows setups)
            self.skipTest("Symlinks not supported in this environment")

        # The link_path itself is inside test_dir, but it points outside.
        # is_safe_path should resolve it and find it unsafe.
        self.assertFalse(is_safe_path(self.test_dir, "link_to_secret"))

    def test_should_allow_normal_file_inside_base(self):
        # Create a normal file inside
        normal_file = os.path.join(self.test_dir, "normal.txt")
        with open(normal_file, "w") as f:
            f.write("normal info")

        self.assertTrue(is_safe_path(self.test_dir, "normal.txt"))

    def test_should_reject_absolute_path(self):
        self.assertFalse(is_safe_path(self.test_dir, self.secret_file))

    def test_should_reject_relative_traversal(self):
        self.assertFalse(is_safe_path(self.test_dir, "../outside/secret.txt"))

if __name__ == '__main__':
    unittest.main()
