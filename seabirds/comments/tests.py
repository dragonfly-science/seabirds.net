"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import datetime

from django.test import TestCase
from django.contrib import comments
from django.contrib.sites.models import Site
from django.utils.html import strip_tags
from django.contrib.auth.models import User

import django.core.mail as mail

from cms.models import Page, Navigation, Image, Post, Listing
from profile.models import UserProfile
from comments.models import PigeonComment
from cms.tasks import generate_comment_pigeons

from pigeonpost.tasks import process_queue, process_outbox

def deploy_pigeons():
    """ This version of deploy doesn't get blocked by a pid file """
    process_queue()
    process_outbox()

class CommentEmailTest(TestCase):
    fixtures = ['test-data/profile.json']

    def setUp(self):
        self.author = User.objects.get(username='albert-ross')
        self.sooty = User.objects.get(username='sooty-shearwater')
        listing = Listing.objects.all()[0]
        self.p = Post(title='New Post', text='A sentence that is long enough to go to the digest',  
            listing=listing, author=self.author, name='new-post')
        self.p.save()
        # Clear pigeon/mail created from adding a Post
        deploy_pigeons()
        mail.outbox = []
        self.counter = 1

    def new_comment(self, target, user):
        comment = comments.get_model()()
        comment.content_object = target
        comment.site = Site.objects.get_current()
        comment.user = user
        comment.comment = strip_tags("A new comment %d" % self.counter)
        self.counter += 1
        comment.submit_date = datetime.datetime.now()
        comment.is_public = True
        comment.is_removed = False
        comment.save()
        return comment

    def test_comment_can_be_seen(self):
        j = User.objects.get(username='committee-jack')
        listing = Listing.objects.get(key='staff')
        p = Post(title='New Post 2', text='A sentence that is long enough to go to the digest',  
            listing=listing, author=j, name='new-post-2')
        p.save()
        comment = self.new_comment(p, j)

        self.assertFalse(comment.can_be_seen_by(self.sooty))

    def test_author_comments_no_email(self):
        """ Comment by author sends no email to author """
        self.new_comment(self.p, self.author)
        # process pigeon post queue and check django mail outbox
        deploy_pigeons()

        self.assertEqual(len(mail.outbox), 0)

    def test_other_comments_author_emailed(self):
        """ Comment by other user, sends email to author """
        self.new_comment(self.p, self.sooty)
        # process pigeon post queue and check django mail outbox
        deploy_pigeons()

        self.assertEqual(len(mail.outbox), 1)

    def test_author_comments_after_b_comments(self):
        """ Comment by author, after sooty user has commented, sends email to sooty only """
        self.new_comment(self.p, self.sooty)
        # clear pigeons and outbox
        deploy_pigeons()
        mail.outbox = []

        self.new_comment(self.p, self.author)
        deploy_pigeons()
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(self.sooty.email, mail.outbox[0].to)
