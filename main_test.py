import main
import unittest

class MainTest(unittest.TestCase):
    """This class uses the Flask tests app to run an integration test against a
    local instance of the server."""

    def setUp(self):
        self.app = main.app.test_client()

    def test1(self):
        self.assertEqual(1, 1)

    def test2(self):
        self.assertEqual(2, 2)

if __name__ == '__main__':
    unittest.main()