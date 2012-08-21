from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.conf import settings
from django.test.utils import override_settings
from categories.models import SeabirdFamily, InstitutionType
from profile.models import UserProfile


class TestTwitter(TestCase):
    fixtures = ['test-data/profile.json']
    def setUp(self):
        self.client.login(username="sooty-shearwater", password="foo")

    def test_model_supports_twitter(self):
        u = UserProfile()
        self.assertTrue(hasattr(u, 'twitter'))

    def test_model_supports_twitter_optout(self):
        u = UserProfile()
        self.assertTrue(hasattr(u, 'display_twitter'))

    def test_can_enter_twitter(self):
        response = self.client.get('/petrel/edit/')
        twitter_in_form = 'id_twitter' in response.content.lower()
        self.assertTrue(twitter_in_form, msg=response.content)

    def test_can_opt_out_of_twitter_feed_being_displayed(self):
        response = self.client.get('/petrel/edit/')
        twitter_optout_in_form = 'Display your Twitter feed on your profile page' in response.content
        self.assertTrue(twitter_optout_in_form, msg=response.content)


class TestAnonymous(TestCase):
    fixtures = ['test-data/profile.json']
        
    def test_anonymous_users_are_barred(self):
        response = self.client.get('/petrel/edit/', follow=False)
        self.assertFalse(response.status_code==200, msg=response.status_code)

    def test_anonymous_users_redirected_to_login(self):
        response = self.client.get('/petrel/edit/', follow=True)
        self.assertTrue('login' in response.content, msg='Not redirected to the login page')

#class TestNewUser(TestCase):
#    @override_settings(DEBUG=True)
#    def test_create_user(self):
#        response = self.client.post('/accounts/register/', 
#            {'first_name':'Fairy', 
#            'last_name':'Prion', 
#            'email': 'fairy@prion.net',
#            'accept_terms': True,
#            'research_field': 1,
#            'password1':'fairyprion', 
#            'password': 'fairyprion', 
#            'password2':'fairyprion',
#            }, follow=True)
#        print(response.content)
#        print(settings.DEBUG)
#        self.assertTrue(response.status_code == 302)
#        u = User.objects.get(first_name='Fairy')
#        self.assertTrue(u.last_name, 'Prion')


#class TestCustomListView(TestCase):

    #def test_logged_in_users_can_visit_page(self):
    #    assert self.client.get('/petrel', follow=True).status_code == 200
    #    assert self.client.get('/petrel/', follow=True).status_code == 200

#    def test_default_listing(self):
#        response = self.client.get('/petrel/', follow=True)
#        assert 'activebadge' not in response.content
#
#    def test_country_no_seabirds_nor_collab_choices(self):
#        link =  '/petrel/?c=GB'
#        response = self.client.get(link)
#       
#        desired = [
#          '<a href="/petrel/?c=SE" class="badge linkbadge">Sweden</a>',
#          '<a href="/petrel/" class="badge activebadge">United Kingdom</a>'
#        ]
#        for s in desired:
#            content = response.content
#            self.assertTrue(s in content, msg=u'\nMISSING: {0}\nFROM:    {1}\n{2}\n'.format(s, link, content))
#
#        
#    def test_country_seabirds_but_no_collab_choices(self):
#        link = '/petrel/?c=GB&s=alb'
#        response = self.client.get(link)
#
#        desired = [
#          '<a href="/petrel/?c=SE&s=alb" class="badge linkbadge">Sweden</a>',
#          '<a href="/petrel/?s=alb" class="badge activebadge">United Kingdom</a>',
#          '<a href="/petrel/?c=GB" class="badge activebadge">Albatrosses</a>',
#          '<a href="/petrel/?c=GB&s=auk" class="badge linkbadge">Auks</a>'
#        ]
#        for s in desired:
#            content = response.content
#            self.assertTrue(s in content, msg=u'\nMISSING: {0}\nFROM:    {1}\n{2}\n'.format(s, link, content))
#
#    def test_country_seabirds_and_collab_choices(self):
#        link = '/petrel/?c=GB&s=alb&r=graduate+student'
#        response = self.client.get(link) 
#        desired = [
#          '<a href="/petrel/?c=SE&s=alb&r=graduate+student" class="badge linkbadge">Sweden</a>',
#          '<a href="/petrel/?s=alb&r=graduate+student" class="badge activebadge">United Kingdom</a>',
#          '<a href="/petrel/?c=GB&r=graduate+student" class="badge activebadge">Albatrosses</a>',
#          '<a href="/petrel/?c=GB&s=auk&r=graduate+student" class="badge linkbadge">Auks</a>'
#        ]
#        for s in desired:
#            content = response.content
#            self.assertTrue(s in content, msg=u'\nMISSING: {0}\nFROM:    {1}\n{2}\n'.format(s, link, content))
#
#    def test_seabirds_no_countries_nor_collab_choices(self):
#        link = '/petrel/?s=alb'
#        response = self.client.get(link)
#        desired = [
#          '<a href="/petrel/?c=SE&s=alb" class="badge linkbadge">Sweden</a>',
#          '<a href="/petrel/" class="badge activebadge">Albatrosses</a>'
#        ]
#        for s in desired:
#            content = response.content
#            self.assertTrue(s in content, msg=u'\nMISSING: {0}\nFROM:    {1}\n{2}\n'.format(s, link, content))
#        
#
#    def test_seabirds_countries_and_collab_choices(self):
#        response = self.client.get('/petrel/?s=alb&r=graduate+student')
#
#
