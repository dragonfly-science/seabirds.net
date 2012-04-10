from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils import unittest
from django.test.client import Client
from categories.models import SeabirdFamily, InstitutionType
from profile.models import UserProfile


class TestPages(unittest.TestCase):
    def setUp(self):
        self.c = Client()

    def test_model_supports_twitter(self):
        u = UserProfile()
        self.assertTrue(hasattr(u, 'twitter'))

    def test_model_supports_twitter_optout(self):
        u = UserProfile()
        self.assertTrue(hasattr(u, 'display_twitter'))

    def test_can_enter_twitter(self):
        response = self.c.get('/accounts/register')
        twitter_in_form = 'twitter' in response.content.lower()
        self.assertTrue(twitter_in_form)

    def test_can_opt_out_of_twitter_feed_being_displayed(self):
        response = self.c.get('/accounts/register')
        twitter_optout_in_form = 'Display your Twitter feed on your profile page' in response.content.lower()
        self.assertTrue(twitter_optout_in_form)
 
class TestCustomListView(unittest.TestCase):
    fixtures = ['testdata.json']

    def setUp(self):
        self.c = Client()
        self.c.login(username="alice", password="secrets")       

    def test_anonymous_users_are_barred(self):
        response = Client().get('/petrel', follow=True)
        assert response.status_code is not 200

    def test_logged_in_users_can_visit_page(self):
        assert self.c.get('/petrel', follow=True).status_code == 200
        assert self.c.get('/petrel/', follow=True).status_code == 200

    def test_default_listing(self):
        response = self.c.get('/petrel/', follow=True)
        assert 'activebadge' not in response.content

    def test_country_no_seabirds_nor_collab_choices(self):
        link =  '/petrel/?c=GB'
        response = self.c.get(link)
       
        desired = [
          '<a href="/petrel/?c=SE" class="badge linkbadge">Sweden</a>',
          '<a href="/petrel/" class="badge activebadge">United Kingdom</a>'
        ]
        for s in desired:
            content = response.content
            self.assertTrue(s in content, msg=u'\nMISSING: {0}\nFROM:    {1}\n{2}\n'.format(s, link, content))

        
    def test_country_seabirds_but_no_collab_choices(self):
        link = '/petrel/?c=GB&s=alb'
        response = self.c.get(link)

        desired = [
          '<a href="/petrel/?c=SE&s=alb" class="badge linkbadge">Sweden</a>',
          '<a href="/petrel/?s=alb" class="badge activebadge">United Kingdom</a>',
          '<a href="/petrel/?c=GB" class="badge activebadge">Albatrosses</a>',
          '<a href="/petrel/?c=GB&s=auk" class="badge linkbadge">Auks</a>'
        ]
        for s in desired:
            content = response.content
            self.assertTrue(s in content, msg=u'\nMISSING: {0}\nFROM:    {1}\n{2}\n'.format(s, link, content))

    def test_country_seabirds_and_collab_choices(self):
        link = '/petrel/?c=GB&s=alb&r=graduate+student'
        response = self.c.get(link) 
        desired = [
          '<a href="/petrel/?c=SE&s=alb&r=graduate+student" class="badge linkbadge">Sweden</a>',
          '<a href="/petrel/?s=alb&r=graduate+student" class="badge activebadge">United Kingdom</a>',
          '<a href="/petrel/?c=GB&r=graduate+student" class="badge activebadge">Albatrosses</a>',
          '<a href="/petrel/?c=GB&s=auk&r=graduate+student" class="badge linkbadge">Auks</a>'
        ]
        for s in desired:
            content = response.content
            self.assertTrue(s in content, msg=u'\nMISSING: {0}\nFROM:    {1}\n{2}\n'.format(s, link, content))

    def test_seabirds_no_countries_nor_collab_choices(self):
        link = '/petrel/?s=alb'
        response = self.c.get(link)
        desired = [
          '<a href="/petrel/?c=SE&s=alb" class="badge linkbadge">Sweden</a>',
          '<a href="/petrel/" class="badge activebadge">Albatrosses</a>'
        ]
        for s in desired:
            content = response.content
            self.assertTrue(s in content, msg=u'\nMISSING: {0}\nFROM:    {1}\n{2}\n'.format(s, link, content))
        

    def test_seabirds_countries_and_collab_choices(self):
        response = self.c.get('/petrel/?s=alb&r=graduate+student')
