import datetime

from django.contrib.comments.managers import CommentManager
from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType
from django.contrib import comments
from django.conf import settings

from cms.models import Post
from utils import generate_email

class PigeonComment(Comment):
    """
    Almost exactly the same as the Django comment model, but we add methods for
    rendering emails for use with PigeonPost.

    It has additional expectations for models that can be commented on. That is,
    the models being commented on need to have:
    - a title attribute
    - an author attribute
    """ 

    objects = CommentManager()

    template = 'pigeonpost/new_comment.txt'
    html_template = 'pigeonpost/new_comment.html'

    def can_be_seen_by(self, user):
        if user.is_authenticated() and user.is_staff:
            # Authenticated staff members can see everything
            return True
        else:
            post_type = ContentType.objects.get(app_label="cms", model="post")
            # Otherwise, comments on staff only posts are invisible
            # everything else assumed to be public

            if (self.content_type == post_type):
                if self.content_object.listing.can_user_read(user):
                    return True
                else:
                    return False
            else:
                return True

    def can_be_edited_by(self, user):
        """ Return True if the user is allowed to edit or delete comment """
        some_time_ago = datetime.datetime.now() - datetime.timedelta(
                seconds=settings.COMMENT_EDIT_GRACE_PERIOD)
        # Staff can always edit,
        # Users can edit their own comments, if it's within the allowed grace period
        if user.is_staff or (self.user == user and self.submit_date > some_time_ago):
            return True
        return False

    def email_author_about_comment(self, user):
        if self.is_removed:
            return None
        assert user == self.content_object.author
        # Prevent sending a notification when a user comments on
        # something they authored.
        if self.user == self.content_object.author:
            return None
        title = self.content_object.title
        subject = '[seabirds.net] New comment on your %s "%s"' % (
                self.content_type.model, title)
        template_data = {'user': user, 'comment': self}
        return generate_email(user, subject, template_data, self.template, self.html_template)

    def email_commenters(self, user):
        # TODO: If there is an op out for a conversation, or being emailed
        # about comments, then it could be checked here

        if self.is_removed:
            return None
        # Do not email the commenter, or the author (the author is notified
        # by `email_author_about_comment`
        if user == self.user or user == self.content_object.author:
            return None
        title = self.content_object.title
        subject = '[seabirds.net] New comment on %s "%s"' % (
                self.content_type.model, title)
        template_data = {'user': user, 'comment': self}
        return generate_email(user, subject, template_data, self.template, self.html_template)

    def get_commenters(self):
        commentset = comments.get_model().objects.for_model(Post).filter(object_pk=self.object_pk)
        return [c.user for c in commentset if self.id != c.id]
