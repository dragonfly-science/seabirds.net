from datetime import datetime
import pickle

from django.test import TestCase
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.core.mail.message import EmailMessage

from categories.models import SeabirdFamily
from cms.models import Page, Post, Navigation, Listing
from cms.tasks import send_digest
from pigeonpost.models import Pigeon, Outbox
from profile.models import UserProfile

class TestPages(TestCase):
    def setUp(self):
        try:
            Page.objects.get(name='home')
        except Page.DoesNotExist:
            home = Page(name='home', title='home')
            home.save()

    def test_page_absolute_url(self):
        home = Page.objects.get(name='home')
        self.assertEqual(home.get_absolute_url(), '/home.html')

    def test_index(self):
        response = self.client.get('/index.html')
        self.assertEqual(response.status_code, 302)

    def test_home(self):
        response = self.client.get('/home.html')
        self.assertEqual(response.status_code, 302)
    
    def test_posts(self):
        response = self.client.get('/posts/')
        self.assertEqual(response.status_code, 200)

class TestPosts(TestCase):
    fixtures = ['test-data/profile.json']

    def setUp(self):
        self.client.login(username="sooty-shearwater", password="foo")

    def test_have_albert(self):
        albert = User.objects.get(username='albert-ross')
        self.assertTrue(albert.profile.get().is_moderator)

    def test_basic_email(self):
        # Send message.
        mail.send_mail('Subject here', 'Here is the message.',
            'from@example.com', ['to@example.com'],
            fail_silently=False)

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, 'Subject here')
        mail.outbox = [] # Reset the mail outbox

    @override_settings(PIGEONPOST_DEFER_POST_MODERATOR=5)
    def test_create_post(self):
        response = self.client.post(reverse('new-post'), {'post-title':'Test', 
            'post-teaser':'A test post', 
            'post-text':'This is a test post', 
            'post-listing':1, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(title='Test')
        #p._notify_moderator = True
        #p.save()
        # The post is published        
        self.assertTrue(p.published)
        #self.assertFalse(p._notify_moderator)
        # The moderator is notified
        pigeons = Pigeon.objects.all()
        self.assertTrue(len(pigeons) == 1, msg=str(pigeons))
        # If the post is saved again the moderator isn't notified again
        p.save()
        pigeons = Pigeon.objects.all()
        self.assertTrue(len(pigeons) == 1, msg=str(pigeons))
        
    def test_edit_post(self):
        response = self.client.post(reverse('new-post'), {'post-title':'Test', 
            'post-teaser':'A test post', 
            'post-text':'This is a test post', 
            'post-listing':1, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(title='Test')
        response = self.client.post(reverse('edit-post', kwargs={'post_id':p.id}), 
            {'post-title':'Edited', 
            'post-teaser':'A test post', 
            'post-text':'This is a test post', 
            'post-listing':1, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(id=p.id)
        self.assertTrue(p.title=='Edited')

class TestDigest(TestCase):
    fixtures = ['test-data/profile.json']

    def test_no_messages(self):
        """Test that nothing is sent if there are no messages to send"""
        send_digest(earliest=0, latest=0)
        self.assertTrue(len(Outbox.objects.all()) == 0)
    
    def test_digest(self):
        """Test that messages are sent to the digest"""
        albert = User.objects.get(username='albert-ross')
        listing = Listing.objects.all()[0]
        subscribers = [p.user for p in UserProfile.objects.all() if listing in p.subscriptions.all()]
        Post(title='title', text='text', teaser='a sufficient teaser to the story', listing=listing, author=albert).save()

        send_digest(earliest=1, latest=-1)
        outbox = Outbox.objects.all()
        self.assertTrue(len(outbox) == len(subscribers))
        for o in outbox:
            message = pickle.loads(o.message)
            # The outbox ontains email messages
            self.assertTrue(type(message) == EmailMessage)
            # Every outbox user is in the list of subscribers
            self.assertTrue(o.user in subscribers)

    def test_digest_rendering(self):
        albert = User.objects.get(username='albert-ross')
        listing = Listing.objects.all()[0]
        Post(title='alpha', text='beta', teaser='gamma rays are powerful and deadly', 
            listing=listing, author=albert, name='alpha').save()
        Post(title='one', text='two', teaser='three people in a bath is two people too many', 
            listing=listing, author=albert, name='one').save()
        
        send_digest(earliest=1, latest=-1)
        outbox = Outbox.objects.all()
        for o in outbox:
            message = pickle.loads(o.message)
            # The outbox ontains email messages
            self.assertTrue('[Seabirds.net]' in message.subject)
            self.assertTrue('three' in message.body, msg=message.body)
            self.assertTrue('gamma' in message.body, msg=message.body)

#  TestJobs(TestCase):
#
#    def test_redirect(self):
#        response = self.client.get('/jobs/', follow=True)
#        assert response.redirect_chain[-1] == ('/jobs/?max_days_since_creation=90', 302)
#
#
#class TestGallery(TestCase):
#
#    def test_gallery_url(self):
#        r = self.client.get('/gallery')
#        assert r.status_code == 200
#
#    def test_seabird_families_urls(self):
#        for s in SeabirdFamily.objects.all():
#            r = self.client.get('/gallery/' + slugify(str(s)))
#            assert r.status_code == 200
#
