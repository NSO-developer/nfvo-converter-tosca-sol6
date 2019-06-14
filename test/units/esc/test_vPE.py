import unittest
from src.util import Util


class TestvPE(unittest.TestCase):

    def setUp(self):
        self.vnfd = None
        #self.vnfd = Util.solcon("Tosca_vPE.yaml")

    def test_one(self):
        self.assertEqual(1, 1)
