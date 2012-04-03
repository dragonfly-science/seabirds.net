from django.utils import unittest
from django.test.client import Client
from profile.models import UserProfile


class TestPages(unittest.TestCase):
    def setUp(self):
        self.c = Client()

    def test_model_supports_twitter(self):
        u = UserProfile()
        self.assertTrue(hasattr(u, 'twitter_handle'))

    def test_model_supports_twitter_optout(self):
        u = UserProfile()
        self.assertTrue(hasattr(u, 'twitter_display_feed'))

    def test_can_enter_twitter(self):
        response = self.c.get('/accounts/register')
        twitter_in_form = 'twitter user name' in response.content.lower()
        self.assertTrue(twitter_in_form)
    def test_can_opt_out_of_twitter_feed_being_displayed(self):
        
        response = self.c.get('/accounts/register')
        twitter_optout_in_form = 'display your twitter' in response.content.lower()
