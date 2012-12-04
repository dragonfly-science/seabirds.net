from datetime import datetime
import os
import pickle

from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.core.mail.message import EmailMessage

from cms.models import Page, Post, Listing
from cms.tasks import send_digest
from pigeonpost.models import Pigeon, Outbox
from pigeonpost.tasks import process_outbox
from profile.models import UserProfile


class TestPages(TestCase):
    fixtures = ['test-data/profile.json']
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
        self.assertEqual(response.status_code, 200)

    def test_home(self):
        response = self.client.get('/home.html')
        self.assertEqual(response.status_code, 200)
    
    def test_posts(self):
        response = self.client.get('/posts/')
        self.assertEqual(response.status_code, 200)

class TestPosts(TestCase):
    fixtures = ['test-data/profile.json']
    TEST_EMAIL_DELAYS = {
            'cms.Post': {
                'moderator': 5*60,
                'subscriber': 3*60*60, # 3 hours
                'author': 10*60,
                },
            'cms.Comment': {
                'post_author': 5*60,
                'post_other_commenters': 5*60,
                },
    }

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
    
#    def test_create_post_with_image(self):
#        """ Test that we can create a post with an associated image, using the new-post url """
#        fid = open(os.path.join(settings.SITE_ROOT, 
#                'test-data', 'bullers-and-cape-angrysunbird.jpg'), 'r')
#        response = self.client.post(reverse('new-post'), {'post-title':'Test', 
#            'post-text':'This is a test post', 
#            'post-listing':1, 
#            'post-seabird_families':[1, 2],
#            'image-image': fid,
#            'image-owner': 'Duncan Wright',
#            'image-source_url': 'http://www.flickr.com/photos/angrysunbird/5187764485/',
#            'image-title': "Buller's albatross and Cape Petrel"}, follow=True)
#        self.assertTrue('src="/images/bullers' in response.content, msg=response.content)

    @override_settings(PIGEONPOST_DELAYS=TEST_EMAIL_DELAYS)
    def test_create_post(self):
        self.client.post(reverse('new-post'), {'post-title':'Test', 
            'post-text':'This is a test post', 
            'post-listing':1, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(title='Test')
        # Check the Post is published
        self.assertTrue(p.published)

        # After a Post is created, there should be a pigeon notifications to:
        # - the author who posted it
        # - the moderator, who can edit/modify the post before members are notified
        # - members who subscribed to the listing
        pigeons = Pigeon.objects.all()
        self.assertTrue(len(pigeons) == 3, msg=str(pigeons))

        # After the Post is modified, the moderator/user isn't notified again, but
        # if the pigeon notification has not been sent, it's scheduled_at time
        # is reset to 10 minutes from now.
        p.save()
        pigeons = Pigeon.objects.all()
        self.assertTrue(len(pigeons) == 3, msg=str(pigeons))
        
    def test_create_post_dupe_title(self):
        """ Test that a post with the same title can be posted multiple times """
        post_data = {
                'post-title':'Test',
                'post-text':'This is a test post',
                'post-listing':1,
                'post-seabird_families':[1, 2]
                }
        self.client.post(reverse('new-post'), post_data, follow=True)
        p = Post.objects.get(title='Test')
        post_data['post-text'] = 'copycat'
        self.client.post(reverse('new-post'), post_data, follow=True)
        p2 = Post.objects.get(text='copycat')
        self.assertNotEqual(p, p2)

        pigeons = Pigeon.objects.all()
        self.assertTrue(len(pigeons) == 6, msg=str(pigeons))

    def test_edit_post(self):
        response = self.client.post(reverse('new-post'), {'post-title':'Test', 
            'post-text':'This is a test post', 
            'post-listing':1, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(title='Test')
        response = self.client.post(reverse('edit-post', kwargs={'post_id':p.id}), 
            {'post-title':'Edited', 
            'post-text':'This is a test post', 
            'post-listing':1, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(id=p.id)
        self.assertTrue(p.title=='Edited')

class TestPermissions(TestCase):
    fixtures = ['test-data/profile.json']

    def setUp(self):
        self.no_comments = Listing.objects.get(key='jobs')
        self.staff_only_write_listing = Listing.objects.get(key='news')
        self.staff_only_read_listing = Listing.objects.get(key='staff')
        self.everyone_read_listing = Listing.objects.get(key='discussion')
        self.counter = 0

        #self.staff_client = self.client.login(username="sooty-shearwater", password="foo")

    def _create_test_post(self, user_name, listing):
        self.client.login(username=user_name, password="foo")
        response = self.client.post(reverse('new-post'), {
            'post-title': 'Test %d' % self.counter, 
            'post-text': 'This is a test post', 
            'post-listing': listing.id, 
            'post-seabird_families': [1, 2]}, follow=True)
        self.assertEqual(response.status_code, 200)
        slug = response.request['PATH_INFO'].split('/')[-2]
        self.assertEqual(slug, 'test-%d' % self.counter)
        self.counter += 1
        return slug

    def _post_comment(self, user_name, post_slug):
        self.client.login(username=user_name, password="foo")
        comment_response = self.client.post(reverse('individual-post', kwargs={
            'slug':post_slug,
            'year':'2012',
            'month':'2',
            'day':'2',
            }), {
            'edit_comment': 'Post',
            'comment-id':-1, 
            'comment-comment': 'test comment',
            }, follow=True)
        return comment_response

    def test_no_comments_listing(self):
        slug = self._create_test_post('albert-ross', self.no_comments)
        # Comments forbidden
        response = self._post_comment('sooty-shearwater', slug)
        self.assertEqual(response.status_code, 403)

        # Even to staff members
        response = self._post_comment('albert-ross', slug)
        self.assertEqual(response.status_code, 403)

    def test_no_comments_post(self):
        slug = self._create_test_post('albert-ross', self.everyone_read_listing)

        # Comments currently okay
        response = self._post_comment('sooty-shearwater', slug)
        self.assertEqual(response.status_code, 200)

        # Disable comments on post, even though they are allowed on the listing
        p = Post.objects.get(name=slug)
        p.enable_comments = False
        p.save()

        # Comments forbidden
        response = self._post_comment('sooty-shearwater', slug)
        self.assertEqual(response.status_code, 403)

        # Even to staff members
        response = self._post_comment('albert-ross', slug)
        self.assertEqual(response.status_code, 403)

    def test_staff_only_write_public_read(self):
        slug = self._create_test_post('albert-ross', self.staff_only_write_listing)

        # Users not allowed to post to "staff write" listing
        self.client.login(username='sooty-shearwater', password="foo")
        response = self.client.post(reverse('new-post'), {
            'post-title': 'Test normal user',
            'post-text': 'This is a test post', 
            'post-listing': self.staff_only_write_listing, 
            'post-seabird_families': [1, 2]})
        self.assertTrue('Select a valid choice' in response.content)

        # But users can see the post
        response = self.client.get(reverse('individual-post', kwargs={
            'slug':slug,
            'year':'2012',
            'month':'2',
            'day':'2',
            }))
        self.assertEqual(response.status_code, 200)

        # Comments are okay though
        response = self._post_comment('sooty-shearwater', slug)
        self.assertEqual(response.status_code, 200)

    def test_staff_only_read(self):
        slug = self._create_test_post('albert-ross', self.staff_only_read_listing)

        # Users not allowed to post to "staff read" listing
        # (technically this is not a required test, but
        # the fixture data is set up to support this and
        # allowing writes by normal users would be weird)
        self.client.login(username='sooty-shearwater', password="foo")
        response = self.client.post(reverse('new-post'), {
            'post-title': 'Test normal user',
            'post-text': 'This is a test post', 
            'post-listing': self.staff_only_read_listing, 
            'post-seabird_families': [1, 2]})
        self.assertTrue('Select a valid choice' in response.content)

        # normal users can't see the post
        response = self.client.get(reverse('individual-post', kwargs={
            'slug':slug,
            'year':'2012',
            'month':'2',
            'day':'2',
            }))
        self.assertEqual(response.status_code, 404)

        # staff can see the post though
        self.client.login(username='albert-ross', password="foo")
        response = self.client.get(reverse('individual-post', kwargs={
            'slug':slug,
            'year':'2012',
            'month':'2',
            'day':'2',
            }))
        self.assertEqual(response.status_code, 200)
        # and can comment
        response = self._post_comment('albert-ross', slug)
        self.assertEqual(response.status_code, 200)



class TestDigest(TestCase):
    fixtures = ['test-data/profile.json']

    def setUp(self):
        albert = User.objects.get(username='albert-ross')
        listing = Listing.objects.all()[0]
        self.subscribers = [p.user for p in UserProfile.objects.all() if \
            listing in p.subscriptions.all()]

        # This post is too short to be sent out
        Post(title='New Post', text='too short',  
            listing=listing, author=albert, name='short-post').save()
        # This post is long enough to be sent out
        Post(title='New Post', text='A sentence that is long enough to go to the digest',  
            listing=listing, author=albert, name='new-post').save()

    def test_no_messages(self):
        """Test that nothing is sent if there are no messages that were made in the
            time period"""
        send_digest(earliest=10, latest=1)
        self.assertTrue(len(Outbox.objects.all()) == 0)
    
    def test_digest(self):
        """Test that messages are sent to the digest"""
        send_digest(earliest=1, latest=-1)
        outbox = Outbox.objects.all()
        self.assertEqual(len(outbox), len(self.subscribers))
        for o in outbox:
            message = pickle.loads(o.message)
            # The outbox contains email messages
            self.assertTrue(type(message) == EmailMessage)
            # Every outbox user is in the list of subscribers
            self.assertTrue(o.user in self.subscribers)
    
    def test_not_twice(self):
        """Test that messages are not sent multiple times"""
        send_digest(earliest=1, latest=-1)
        send_digest(earliest=1, latest=-1)
        send_digest(earliest=1, latest=-1)
        outbox = Outbox.objects.all()
        self.assertEqual(len(outbox), len(self.subscribers))

    def test_digest_rendering(self):
        send_digest(earliest=1, latest=-1)
        outbox = Outbox.objects.all()
        for o in outbox:
            message = pickle.loads(o.message)
            # The outbox ontains email messages
            self.assertTrue('[Seabirds.net]' in message.subject)
            self.assertTrue('long enough' in message.body, msg=message.body)

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
