import unittest
from utils.util import Util

# For use in running tests from console
# You have to tell it where the main code is tho,
# PYTHONPATH=../
if __name__ == "__main__":
    Util.root = "../"

    loader = unittest.TestLoader()
    start_dir = 'units/'
    suite = loader.discover(start_dir)
    runner = unittest.TextTestRunner()
    runner.run(suite)
