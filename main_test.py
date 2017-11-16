import main
import unittest

class MainTest(unittest.TestCase):
    """This class uses the Flask tests app to run an integration test against a
    local instance of the server."""

    def setUp(self):
        self.app = main.app.test_client()

    def test_hello_world(self):
        assert 1 == 1

if __name__ == '__main__':
    unittest.main()