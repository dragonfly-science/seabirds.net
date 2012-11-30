from django.db import models

from django.contrib.comments.managers import CommentManager
from django.contrib.comments.models import Comment

from cms.models import Post

class PigeonComment(Comment):
    """
    Almost exactly the same, but we add methods for rendering emails for use with PigeonPost.
    """ 

    objects = CommentManager()

    def email_author_about_comment(self, user):
        subject = '[seabirds.net] New comment on your post "%s"' % self.title
        template = 'pigeonpost/email_list_body.txt'
        return self._generate_email(user, subject, template, template)

    def email_commenters(self, user):
        # TODO: If there is an op out for a conversation, or being emailed
        # about comments, then it could be checked here
        if user != self.author:
            subject = '[seabirds.net] New comment on post "%s"' % self.title
            template = 'pigeonpost/email_list_body.txt'
            return self._generate_email(user, subject, template, template)

    def get_commenters(self):
        from django.contrib import comments
        commentset = comments.get_model().objects.for_model(Post).filter(object_pk=self.id)
        return [c.user for c in commentset]





