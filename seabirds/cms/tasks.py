import datetime

from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings

from profile.models import UserProfile
from pigeonpost.tasks import add_to_outbox
from cms.models import Listing, Post

def send_digest(earliest=36, latest=12):
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
                from_email=settings.EMAIL_NOREPLY, 
                to=[profile.user.email])
            add_to_outbox(message=message, user=profile.user)
            # mark posts as sent
            for substantive in posts.values():
                for post in substantive:
                    sent_to_list.add(post)
    for post in sent_to_list:
        post._sent_to_list = True
        post.save()


