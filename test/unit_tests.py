import unittest
import sys

# For use in running tests from console
if __name__ == "__main__":
    sys.path.insert(0, '../src')
    loader = unittest.TestLoader()
    start_dir = 'units/'
    suite = loader.discover(start_dir)
    runner = unittest.TextTestRunner()
    runner.run(suite)
