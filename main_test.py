import unittest
import main

def test_index():
    # This is a Flask feature - you can fire up a test client and access your endpoints for unit testing
    main.app.testing = True
    client = main.app.test_client()

    r = client.get('/')
    assert r.status_code == 200
    assert 'Hello World' in r.data.decode('utf-8')

if __name__ == "__main__":
    unittest.main()