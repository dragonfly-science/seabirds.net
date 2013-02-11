import datetime

from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.dispatch import receiver

from profile.models import UserProfile
from pigeonpost.signals import pigeonpost_queue
from pigeonpost.tasks import add_to_outbox

from cms.models import Post, Listing, Navigation

def send_digest(earliest=36, latest=12):
    """
    TODO: Convert this to use pigeon post.
    """
    now = datetime.datetime.now() 
    earliest_datetime = now - datetime.timedelta(seconds=earliest*60*60) 
    latest_datetime = now - datetime.timedelta(seconds=latest*60*60) 
    sent_to_list = set()
    for profile in UserProfile.objects.all():
        posts = {}
        for subscription in profile.subscriptions.all():
            items = Post.objects.filter(
                listing = subscription,
                date_created__gt = earliest_datetime,
                date_created__lt = latest_datetime,
                published = True,
                _sent_to_list = False)
            substantive = [item for item in items if len(item.text.strip()) > 20] 
            if substantive:
                posts[subscription.description] = substantive
        if posts:
            # Add the posts to the digest
            context =  {'user': profile.user, 'posts': posts}
            subject = render_to_string('pigeonpost/email_list_digest_subject.txt', context).strip()
            body = render_to_string('pigeonpost/email_list_digest_body.txt', context).strip()
            message = EmailMessage(subject, 
                body, 
                to=[profile.user.email])
            add_to_outbox(message=message, user=profile.user)
            # mark posts as sent
            for substantive in posts.values():
                for post in substantive:
                    sent_to_list.add(post)
    for post in sent_to_list:
        post._sent_to_list = True
        post.save()

# This is the correct signal to listen to, but the way comments were
# integrate does not seem to be the way django comments expects.
#from django.contrib.comments.signals import comment_was_posted
#@receiver(comment_was_posted)
# Instead we just listen to the post save signal.
from django.db.models.signals import post_save
from django.contrib import comments
@receiver(post_save, sender=comments.get_model())
def generate_comment_pigeons(sender, **kwargs):
    """ Whenever a comment is received, we create a number of pigeons """
    # (use 'comment' from kwargs if changing back to comment_was_posted signal)
    comment = kwargs.get('instance')
    post = comment.content_object

    # The first pigeon is to the post author
    pigeonpost_queue.send(sender=comment,
         render_email_method='email_author_about_comment',
         send_to=post.author)

    # The second pigeon is for any commenters on the post
    pigeonpost_queue.send(sender=comment,
         render_email_method='email_commenters',
         send_to_method='get_commenters')

