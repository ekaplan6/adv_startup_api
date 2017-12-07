import unittest
from main import app

class MainTest(unittest.TestCase):
    """This class uses the Flask tests app to run an integration test against a
    local instance of the server."""

    def setUp(self):
        self.app = app.test_client()

    def test1(self):
        self.assertEqual(1, 1)

if __name__ == '__main__':
    unittest.main()