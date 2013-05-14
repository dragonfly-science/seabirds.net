from datetime import datetime
import os
import pickle
import time

from django.test import TestCase
from django.contrib.auth.models import User
from django.core import mail
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.core.mail.message import EmailMessage

from cms.models import Page, Post, Listing, Image, File
from cms.tasks import send_digest
from cms.templatetags.cms_filters import twitter_widget

from comments.models import PigeonComment
from pigeonpost.models import Pigeon, Outbox
from profile.models import UserProfile
from django.contrib.auth.models import Permission

class TestFilter(TestCase):

    def test_twitter_filter(self):
        widget_src = twitter_widget('seabirders')
        assert '"seabirders"' in widget_src
        widget_src = twitter_widget('@seabirders')
        assert '"seabirders"' in widget_src

class TestImages(TestCase):
    fixtures = ['test-data/profile.json']

    def setUp(self):
        self.client.login(username="sooty-shearwater", password="foo")
        fid = open(os.path.join(settings.SITE_ROOT, 
                'test-data', 'bullers-and-cape-angrysunbird.jpg'), 'r')
        response = self.client.post(reverse('new-post'), {'post-title':'Test', 
            'post-text':'This is a test post', 
            'post-listing':1, 
            'post-seabird_families':[1, 2],
            'image-image': fid,
            'image-owner': 'Duncan Wright',
            'image-source_url': 'http://www.flickr.com/photos/angrysunbird/5187764485/',
            'image-title': "Buller's albatross and Cape Petrel"}, follow=True)
        self.assertTrue('src="/images/bullers' in response.content, msg=response.content)

        self.post = Post.objects.get(title='Test')
        self.image = Image.objects.get(owner='Duncan Wright')

    def tearDown(self):
        os.remove(self.image.image.file.name)

    def test_thumbnail(self):
        self.assertTrue('img src' in self.image.thumbnail())

    def test_render(self):
        self.assertTrue(self.image.source_url in self.image.render())

    def test_tag(self):
        self.assertTrue(self.image.key in self.image.tag())

    def test_str(self):
        self.assertTrue(self.image.key in str(self.image))

    def test_get_dimensions(self):
        self.assertEqual((160, 240), self.image.get_dimensions())
        self.assertEqual((10, 15), self.image.get_dimensions(width=10))
        self.assertEqual((6, 10), self.image.get_dimensions(height=10))
        self.assertEqual((10, 10), self.image.get_dimensions(width=10, height=10))
        # Not sure about the expected behaviour of the max_height parameter
        self.assertEqual((160, 15), self.image.get_dimensions(max_height=15))

    def test_get_qualified_url(self):
        self.assertTrue('160x240' in self.image.get_qualified_url())

    def test_get_image_url(self):
        self.assertTrue(self.image.get_image_url())

    def test_get_absolute_url(self):
        self.assertTrue(self.image.get_absolute_url())

class TestFiles(TestCase):

    def test_save_file(self):
        from django.core.files.base import ContentFile
        from StringIO import StringIO
        f = File(name='test_file', title='test_file_title')
        file_content = ContentFile(StringIO('dummy file content').read())
        f.file.save('original_name', file_content)
        f.save()
        self.assertTrue(f.html())
        self.assertTrue(f.get_absolute_url())
        self.assertTrue(str(f))

class TestPages(TestCase):
    fixtures = ['test-data/profile.json']

    def setUp(self):
        self.p = Page(title='A great page', name='great-page', text='A great page on a great site')
        self.p.save()
        try:
            Page.objects.get(name='home')
        except Page.DoesNotExist:
            home = Page(name='home', title='home')
            home.save()

    def test_new_page(self):
        self.assertTrue(str(self.p))
        self.p.published = True
        self.p.save()
        self.assertTrue(self.p.date_published)

    def test_markdown_page(self):
        self.assertTrue(self.p.markdown_text)
        self.assertFalse(self.p.markdown_sidebar)
        self.p.sidebar = 'hurray!'
        self.p.save()
        self.assertTrue(self.p.markdown_sidebar)

    def test_page_absolute_url(self):
        home = Page.objects.get(name='home')
        self.assertEqual(home.get_absolute_url(), '/home.html')

    def test_index(self):
        response = self.client.get('/index.html')
        self.assertEqual(response.status_code, 200)

    def test_home(self):
        response = self.client.get('/home.html')
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

    def tearDown(self):
        images = Image.objects.filter(owner='Duncan Wright')
        for i in images:
            os.remove(i.image.file.name)

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
    
    def test_create_post_with_image(self):
        """ Test that we can create a post with an associated image, using the new-post url """
        fid = open(os.path.join(settings.SITE_ROOT, 
                'test-data', 'bullers-and-cape-angrysunbird.jpg'), 'r')
        response = self.client.post(reverse('new-post'), {'post-title':'Test', 
            'post-text':'This is a test post', 
            'post-listing':1, 
            'post-seabird_families':[1, 2],
            'image-image': fid,
            'image-owner': 'Duncan Wright',
            'image-source_url': 'http://www.flickr.com/photos/angrysunbird/5187764485/',
            'image-title': "Buller's albatross and Cape Petrel"}, follow=True)
        self.assertTrue('src="/images/bullers' in response.content, msg=response.content)

    def test_post_with_duplicate_image_key(self):
        """ Test that two images with the same potential key don't break things """
        # First save an image whose name will clash
        from django.core.files import File
        fid = open(os.path.join(settings.SITE_ROOT, 
                'test-data', 'bullers-and-cape-angrysunbird.jpg'), 'r')
        albert = User.objects.get(username='albert-ross')
        i = Image(image=File(fid),
                title="Buller's albatross and Cape Petrel",
                key="bullers-albatross-and-cape-petrel",
                uploaded_by=albert)
        i.save()
        fid.close()

        fid = open(os.path.join(settings.SITE_ROOT, 
                'test-data', 'bullers-and-cape-angrysunbird.jpg'), 'r')
        response = self.client.post(reverse('new-post'), {'post-title':'Test2', 
            'post-text':'This is another test post', 
            'post-listing':1, 
            'post-seabird_families':[1, 2],
            'image-image': fid,
            'image-owner': 'Duncan Wright',
            'image-title': "Buller's albatross and Cape Petrel"}, follow=True)
        fid.close()
        images = list(Image.objects.all())
        self.assertEqual(len(images), 3) # One image in fixture
        self.assertTrue('src="/images/bullers' in response.content, msg=response.content)
 
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

    def test_misc(self):
        self.client.post(reverse('new-post'), {'post-title':'Test', 
            'post-text':'This is a test post' + 'x\n'*200, 
            'post-listing':1, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(title='Test')
        self.assertTrue(str(p))
        self.assertTrue(p.markdown_text)
        self.assertTrue(p.markdown_teaser)
        self.assertTrue(len(p.markdown_teaser) < len(p.markdown_text))

        self.assertTrue(p.get_absolute_url())

    def test_get_subscribers(self):
        self.client.post(reverse('new-post'), {'post-title':'Test', 
            'post-text':'This is a test post' + 'x\n'*200, 
            'post-listing':1, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(title='Test')
        self.assertEqual(len(p.get_subscribers()), 4)

        self.client.login(username="albert-ross", password="foo")
        self.client.post(reverse('new-post'), {'post-title':'Test2', 
            'post-text':'This is a test post' + 'x\n'*200, 
            'post-listing':2, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(title='Test2')
        self.assertEqual(len(p.get_subscribers()), 1)

    def test_get_subscribers_mandatory(self):
        self.client.login(username="albert-ross", password="foo")
        self.client.post(reverse('new-post'), {'post-title':'Test', 
            'post-text':'This is a test announcement ' + 'x\n'*200, 
            'post-listing':4, 
            'post-seabird_families':[]}, follow=True)
        p = Post.objects.get(title='Test')
        self.assertEqual(len(p.get_subscribers()), 4)

    def test_email_rendering(self):
        self.client.post(reverse('new-post'), {'post-title':'Test', 
            'post-text':'This is a test post' + 'x\n'*200, 
            'post-listing':1, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(title='Test')
        albert = User.objects.get(username='albert-ross')
        sooty  = User.objects.get(username='sooty-shearwater')

        self.assertFalse(p.email_moderator(albert))
        self.assertFalse(p.email_moderator(sooty))

        self.assertTrue(p.email_author(sooty))
        self.assertFalse(p.email_author(albert))

        self.assertTrue(p.email_subscriber(albert))
        self.assertFalse(p.email_subscriber(sooty))

        self.client.login(username="albert-ross", password="foo")
        self.client.post(reverse('new-post'), {'post-title':'Test2', 
            'post-text':'This is a test post' + 'x\n'*200, 
            'post-listing':5, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(title='Test2')
        jack = User.objects.get(username='committee-jack')
        self.assertTrue(p.email_moderator(jack))
        self.assertFalse(p.email_moderator(sooty))

    def test_moderate_logic(self):
        self.client.post(reverse('new-post'), {'post-title':'Test', 
            'post-text':'This is a test post' + 'x\n'*200, 
            'post-listing':1, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(title='Test')
        u = User.objects.get(username='albert-ross')
        self.assertTrue(p.can_user_modify(u))
        u = User.objects.get(username='sooty-shearwater')
        self.assertTrue(p.can_user_modify(u))
        u = User.objects.get(username='committee-jack')
        self.assertFalse(p.can_user_modify(u))

        self.client.login(username="albert-ross", password="foo")
        self.client.post(reverse('new-post'), {'post-title':'Testjob', 
            'post-text':'This is a test post' + 'x\n'*200, 
            'post-listing':5, 
            'post-seabird_families':[1, 2]}, follow=True)
        p = Post.objects.get(title='Testjob')
        u = User.objects.get(username='committee-jack')
        self.assertTrue(p.can_user_modify(u))

    def test_view_all_recent_posts(self):
        response = self.client.get('/posts/')
        self.assertEqual(response.status_code, 200)

    def test_view_listing_posts(self):
        response = self.client.get('/groups/jobs')
        self.assertEqual(response.status_code, 200)

        self.assertTrue('Sorry - there are no posts available in the "Job postings" group.' in response.content)

    def test_view_listing_without_permission(self):
        response = self.client.get('/groups/staff')
        self.assertEqual(response.status_code, 404)


class TestPermissions(TestCase):
    fixtures = ['test-data/profile.json']

    def setUp(self):
        self.no_comments = Listing.objects.get(key='jobs')
        self.announce_listing = Listing.objects.get(key='news')
        self.committee_listing = Listing.objects.get(key='staff')
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
        if user_name:
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

    def test_unauthenticated_user(self):
        slug = self._create_test_post('albert-ross', self.everyone_read_listing)

        response = self._post_comment('sooty-shearwater', slug)
        self.assertEqual(response.status_code, 200)

        total_comments = len(PigeonComment.objects.all())
        self.client.logout()
        response = self._post_comment(None, slug)
        # We don't say anything, we just silented ignore it
        self.assertEqual(response.status_code, 200)
        # But check there isn't a new comment
        self.assertEqual(total_comments, len(PigeonComment.objects.all()))

        pc = PigeonComment.objects.all()[0]
        # check we can't delete comments
        comment_response = self.client.post(reverse('individual-post', kwargs={
            'slug':slug,
            'year':'2012',
            'month':'2',
            'day':'2',
            }), {
            'delete_comment': 'Post',
            'comment-id':pc.id, 
            })
        self.assertEqual(response.status_code, 200)
        # But check there isn't a new comment
        pc2 = PigeonComment.objects.all()[0]
        self.assertEqual(pc2.is_removed, False)
        self.assertEqual(pc, pc2)

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
    
    def test_edited_comments_keep_user(self):
        albert = User.objects.get(username='albert-ross')
        sooty  = User.objects.get(username='sooty-shearwater')
        slug = self._create_test_post('albert-ross', self.everyone_read_listing)

        # Login as sooty shearwater
        self.client.login(username='sooty-shearwater', password="foo")
        response = self._post_comment('sooty-shearwater', slug)
        self.assertEqual(response.status_code, 200)

        pc = PigeonComment.objects.all()[0]
        self.assertEqual(pc.comment, 'test comment')
        self.assertEqual(pc.user, sooty)

        #Now login as albert-ross and edit the comment
        self.client.login(username='albert-ross', password="foo")
        comment_response = self.client.post(reverse('individual-post', kwargs={
                'slug':slug,
                'year':'2012',
                'month':'2',
                'day':'2',
            }), {
                'edit_comment': 'Post',
                'comment-id':pc.id,
                'comment-comment': 'comment by sooty, edited by albert',
            }, follow=True)
        pc = PigeonComment.objects.get(id=pc.id)
        self.assertEqual(pc.comment, 'comment by sooty, edited by albert')
        self.assertEqual(pc.user, sooty)
    
    def test_edited_comments_keep_datetime(self):
        slug = self._create_test_post('albert-ross', self.everyone_read_listing)

        # Make a comment and get the submit time
        response = self._post_comment('sooty-shearwater', slug)
        self.assertEqual(response.status_code, 200)

        pc = PigeonComment.objects.all()[0]
        self.assertEqual(pc.comment, 'test comment')
        submit_date = pc.submit_date

        #Now wait a bit and edit the comment
        time.sleep(0.1)
        comment_response = self.client.post(reverse('individual-post', kwargs={
                'slug':slug,
                'year':'2012',
                'month':'2',
                'day':'2',
            }), {
                'edit_comment': 'Post',
                'comment-id':pc.id,
                'comment-comment': 'edited by sooty',
            }, follow=True)
        pc = PigeonComment.objects.get(id=pc.id)
        # Confirm that we have modified the comment
        self.assertEqual(pc.comment, 'edited by sooty')
        # Confirm that the submit date is the same
        self.assertEqual(pc.submit_date, submit_date)

    def test_staff_only_write_public_read(self):
        slug = self._create_test_post('albert-ross', self.announce_listing)

        # Users not allowed to post to "permission write" listing
        self.client.login(username='sooty-shearwater', password="foo")
        response = self.client.get(reverse('new-post'))
        self.assertNotContains(response, self.announce_listing.description)

        response = self.client.post(reverse('new-post'), {
            'post-title': 'Test normal user',
            'post-text': 'This is a test post', 
            'post-listing': self.announce_listing.id, 
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

    def test_permission_only_write_public_read(self):
        slug = self._create_test_post('announcer-jill', self.announce_listing)

        # normal users can see the post
        self.client.login(username='sooty-shearwater', password="foo")
        response = self.client.get(reverse('individual-post', kwargs={
            'slug':slug,
            'year':'2012',
            'month':'2',
            'day':'2',
            }))
        self.assertEqual(response.status_code, 200)

        # Comments are good too
        response = self._post_comment('sooty-shearwater', slug)
        self.assertEqual(response.status_code, 200)

    def test_comment_deletion(self):
        slug = self._create_test_post('albert-ross', self.announce_listing)

        # Create comment
        response = self._post_comment('albert-ross', slug)
        self.assertEqual(response.status_code, 200)
        pc = PigeonComment.objects.all()[0]
        self.assertEqual(pc.user, User.objects.get(username='albert-ross'))

        # check sooty can't delete albert's comments
        self.client.login(username='sooty-shearwater', password="foo")
        comment_response = self.client.post(reverse('individual-post', kwargs={
            'slug':slug,
            'year':'2012',
            'month':'2',
            'day':'2',
            }), {
            'delete_comment': 'Post',
            'comment-id':pc.id, 
            })
        self.assertEqual(comment_response.status_code, 403)
        pc = PigeonComment.objects.all()[0]
        self.assertEqual(pc.is_removed, False)

        # check albert can delete
        self.client.login(username='albert-ross', password="foo")
        comment_response = self.client.post(reverse('individual-post', kwargs={
            'slug':slug,
            'year':'2012',
            'month':'2',
            'day':'2',
            }), {
            'delete_comment': 'Post',
            'comment-id':pc.id, 
            })
        self.assertEqual(comment_response.status_code, 200)
        pc = PigeonComment.objects.all()[0]
        self.assertEqual(pc.is_removed, True)

    def test_committee_only_read(self):
        slug = self._create_test_post('albert-ross', self.committee_listing)

        u = User.objects.get(username='albert-ross')
        self.assertTrue(self.committee_listing.can_user_post(u))
        self.assertFalse(self.committee_listing.can_user_moderate(u))

        u = User.objects.get(username='sooty-shearwater')
        self.assertFalse(self.committee_listing.can_user_post(u))
        self.assertFalse(self.committee_listing.can_user_moderate(u))

        self.assertFalse(self.committee_listing.can_user_post(None))
        self.assertFalse(self.committee_listing.can_user_moderate(None))
        # Users not allowed to post to "staff read" listing
        # (technically this is not a required test, but
        # the fixture data is set up to support this and
        # allowing writes by normal users would be weird)
        self.client.login(username='sooty-shearwater', password="foo")
        response = self.client.post(reverse('new-post'), {
            'post-title': 'Test normal user',
            'post-text': 'This is a test post', 
            'post-listing': self.committee_listing, 
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

        # committee members can read 
        self.client.login(username='committee-jack', password="foo")
        response = self.client.get(reverse('individual-post', kwargs={
            'slug':slug,
            'year':'2012',
            'month':'2',
            'day':'2',
            }))
        self.assertEqual(response.status_code, 200)
        # and can comment
        response = self._post_comment('committee-jack', slug)
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

class TestFeed(TestCase):
    fixtures = ['test-data/profile.json']

    def test_feed(self):
        response = self.client.get('/feed/rss/posts')
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        results = root.findall(".//item/title")
        self.assertEqual("World Seabird Conference", results[0].text)

