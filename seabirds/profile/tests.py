# -*- coding: utf-8 -*-
import os

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase

from mock import patch

from profile.models import UserProfile, get_photo_path


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

class TestProfile(TestCase):
    fixtures = ['test-data/profile.json']

    def test_misc(self):
        sooty = User.objects.get(username='sooty-shearwater')
        profile = sooty.profile.get()
        self.assertTrue('Sooty' in str(profile))


class TestAnonymous(TestCase):
    fixtures = ['test-data/profile.json']

    def test_anonymous_users_are_barred(self):
        response = self.client.get('/petrel/edit/', follow=False)
        self.assertFalse(response.status_code==200, msg=response.status_code)

    def test_anonymous_users_redirected_to_login(self):
        response = self.client.get('/petrel/edit/', follow=True)
        self.assertTrue('login' in response.content, msg='Not redirected to the login page')

class TestUnicodeNames(TestCase):
    fixtures = ['test-data/profile.json']

    def setUp(self):
        u = User(username='unicode-jack', first_name=u'Κνωσός', last_name=u'the_symbol_㉓')
        u.set_password('test')
        u.save()
        self.unicode_user = u
        self.client.login(username='unicode-jack', password='test')

    def test_profile_editable(self):
        response = self.client.get('/petrel/edit/')
        self.assertTrue(response.status_code==200)

    @patch('os.mkdir')
    def test_get_photo_path(self, mkdir):
        photo_path = get_photo_path(self.unicode_user.profile.get(), 'test.jpg')
        self.assertEqual(photo_path,'users/5/knosos-the_symbol_23.jpg')

class TestUsername(TestCase):
    fixtures = ['test-data/profile.json']

    def test_have_sooty(self):
        sooty = User.objects.get(username='sooty-shearwater')
        self.assertTrue(sooty.email=='sooty@seabirds.net')

    def test_login(self):
        response = self.client.post('/accounts/login/',
            {'username':'sooty-shearwater',
            'password': 'foo',
            }, follow=True)
        self.assertTrue('Dr Sooty Shearwater' in response.content)

    def test_login_email(self):
        response = self.client.post('/accounts/login/',
            {'username':'sooty@seabirds.net',
            'password': 'foo',
            }, follow=True)
        self.assertTrue('Dr Sooty Shearwater' in response.content)

    def test_login_long_username(self):
        sooty = User.objects.get(username='sooty-shearwater')
        sooty.username = 'sooty-shearwater-with-a-very-long-username'
        sooty.save()
        response = self.client.post('/accounts/login/',
            {'username':'sooty-shearwater-with-a-very-long-username',
            'password': 'foo',
            }, follow=True)
        self.assertTrue('Dr Sooty Shearwater' in response.content)

    def test_login_long_email(self):
        sooty = User.objects.get(username='sooty-shearwater')
        sooty.email = 'sooty.shearwater.with.a.very.long.email@seabirds.net'
        sooty.save()
        response = self.client.post('/accounts/login/',
            {'username':'sooty.shearwater.with.a.very.long.email@seabirds.net',
            'password': 'foo',
            }, follow=True)
        self.assertTrue('Dr Sooty Shearwater' in response.content)

    def test_login_sooty(self):
        sooty = User.objects.get(username='sooty-shearwater')
        self.assertFalse(sooty.profile.get().is_moderator)

    def test_long_username(self):
        sooty = User.objects.get(username='sooty-shearwater')
        sooty.username = 'sooty-shearwater-has-a-very-long-name' #32 characters
        sooty.save()
        self.assertTrue(len(sooty.username), 32)
        self.assertFalse(sooty.profile.get().is_moderator)


class TestNewUser(TestCase):
    fixtures = ['test-data/profile.json']

    def setUp(self):
        os.environ['RECAPTCHA_TESTING'] = 'True'
        self.user_data = {
            'first_name':'Fairy',
            'last_name':'Prion',
            'email': 'fairy@prion.net',
            'accept_terms': True,
            'recaptcha_response_field': 'PASSED',
            'password1':'fairyprion',
            'password2':'fairyprion',
            }

    def tearDown(self):
        os.environ['RECAPTCHA_TESTING'] = 'False'

    def test_create_user(self):
        """ Ensure we can register new users """
        response = self.client.post('/accounts/register/', self.user_data)
        self.assertTrue(response.status_code == 302)
        u = User.objects.get(first_name='Fairy')
        self.assertTrue(u.last_name, 'Prion')
        # When profiles are created they should not be valid researchers
        self.assertFalse(u.profile.get().is_valid_seabirder)

    def test_activate_user(self):
        """ Admin should be emailed when user activates """
        response = self.client.post('/accounts/register/', self.user_data)
        self.assertTrue(response.status_code == 302)
        # activation email
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('Account registration for Seabirds.net' in mail.outbox[0].subject)
        u = User.objects.get(first_name='Fairy')
        self.assertFalse(u.is_active)
        u.is_active = True
        u.save()
        # validation email
        self.assertEqual(len(mail.outbox), 2)
        self.assertTrue('New user registered on Seabirds.net' in mail.outbox[1].subject)
        p = u.profile.get()
        self.assertEqual(p.is_valid_seabirder, False)
        p.is_valid_seabirder = True
        p.save()
        self.assertEqual(len(mail.outbox), 3)
        self.assertTrue('You have been validated on Seabirds.net' in mail.outbox[2].subject)
        # When profiles are created they should not be valid researchers
        p = u.profile.get()
        self.assertTrue(p.is_valid_seabirder)

    def test_create_duplicate_user(self):
        """ Test that users with the same name will generate a different username """
        start_users = User.objects.count()
        response = self.client.post('/accounts/register/', self.user_data)
        self.assertTrue(response.status_code == 302)
        self.user_data['email'] = 'fairy2@prion.net'
        response = self.client.post('/accounts/register/', self.user_data)
        self.assertTrue(response.status_code == 302)
        users = User.objects.filter(first_name='Fairy')
        self.assertTrue(len(users) - start_users, 2)
        # First username will be the prefix of the second one
        self.assertTrue(users[0].username in users[1].username)

class TestCustomListView(TestCase):
    fixtures = ['test-data/profile.json']

    def setUp(self):
        # Because displaying list tries to render thumbnails of these images
        for p in UserProfile.objects.all():
            p.photograph = ''
            p.save()

    def check_desired(self, link, desired):
        response = self.client.get(link)
        for s in desired:
            content = response.content
            self.assertTrue(s in content, msg=u'\nMISSING: {0}\nFROM:    {1}\n{2}\n'.format(s, link, content))

    def test_logged_in_users_can_visit_page(self):
        assert self.client.get('/petrel', follow=True).status_code == 200
        assert self.client.get('/petrel/', follow=True).status_code == 200

    def test_default_listing(self):
        response = self.client.get('/petrel/', follow=True)
        assert 'activebadge' not in response.content

    def test_country_no_seabirds_nor_collab_choices(self):
        link =  '/petrel/?c=NZ'
        desired = [
          '<a href="/petrel/" class="badge activebadge">New Zealand</a>',
          '<a href="/petrel/?s=alb&c=NZ" class="badge linkbadge">Albatrosses</a>',
          '<a href="/petrel/?s=pet&c=NZ" class="badge linkbadge">Petrels</a>',
        ]
        self.check_desired(link, desired)

    def test_country_seabirds_but_no_collab_choices(self):
        link = '/petrel/?c=NZ&s=alb'
        desired = [
          '<a href="/petrel/?s=alb" class="badge activebadge">New Zealand</a>',
          '<a href="/petrel/?c=NZ" class="badge activebadge">Albatrosses</a>',
        ]
        self.check_desired(link, desired)

    def test_country_seabirds_and_collab_choices(self):
        link = '/petrel/?c=NZ&s=alb&r=1'
        desired = [
          '<a href="/petrel/?s=alb&r=1" class="badge activebadge">New Zealand</a>',
          '<a href="/petrel/?c=NZ&r=1" class="badge activebadge">Albatrosses</a>',
        ]
        self.check_desired(link, desired)

    def test_seabirds_no_countries_nor_collab_choices(self):
        link = '/petrel/?s=alb'
        desired = [
          '<a href="/petrel/" class="badge activebadge">Albatrosses</a>'
        ]
        self.check_desired(link, desired)

    def test_seabirds_countries_and_collab_choices(self):
        link = '/petrel/?s=alb&r=1'
        desired = [
          '<a href="/petrel/?r=1" class="badge activebadge">Albatrosses</a>'
        ]
        self.check_desired(link, desired)

