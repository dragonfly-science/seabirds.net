from django.utils import unittest
from django.test.client import Client

class SimpleTest(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_details(self):
        response = self.client.get('/posts/')
        self.assertEqual(response.status_code, 200)
        
