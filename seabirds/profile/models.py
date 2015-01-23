import os

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField
from django.template.defaultfilters import slugify
from django.db.models.signals import post_save, pre_save
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage

from categories.models import SeabirdFamily, InstitutionType, ResearchField
from unidecode import unidecode


def get_photo_path(instance, filename):
    if filename:
        base, ext = os.path.splitext(os.path.split(filename)[1])
        userid = str(instance.user.id)
        try:
            os.mkdir(os.path.join(settings.MEDIA_ROOT, 'users', '%s' % userid))
        except OSError:
            pass
        slugified_fn = '%s%s' % (slugify(unidecode(unicode(instance)).lower()), ext)
        return os.path.join('users', userid, slugified_fn)

class CollaborationChoice(models.Model):
    label = models.CharField(max_length=50)
    description = models.TextField()

    def __unicode__(self):
        return self.label

TITLES = ('Mr', 'Ms', 'Mrs', 'Miss', 'Dr', 'Prof')

class UserProfile(models.Model):
    user = models.ForeignKey(User, related_name='profile', unique=True)
    title = models.CharField(max_length=5, choices=zip(TITLES, TITLES), null=True, blank=True)
    webpage = models.URLField(null=True, blank=True)
    display_email = models.BooleanField(default=True)
    institution = models.CharField(max_length=50, null=True, blank=True)
    institution_type = models.ForeignKey(InstitutionType, null=True, blank=True)
    institution_website = models.URLField(null=True, blank=True)
    country = CountryField(null=True, blank=True)
    research = models.TextField(null=True, blank=True)
    research_field = models.ManyToManyField(ResearchField, null=True, blank=True)
    is_researcher = models.BooleanField(default=True)
    photograph = models.ImageField(upload_to=get_photo_path, null=True, blank=True)
    seabirds = models.ManyToManyField(SeabirdFamily, related_name='profiles', null=True, blank=True)
    twitter = models.CharField(max_length=16, null=True, blank=True)
    display_twitter = models.BooleanField(default=False)
    collaboration_choices = models.ManyToManyField(CollaborationChoice, null=True, blank=True)
    accept_terms = models.BooleanField(default=False)
    date_created = models.DateField(auto_now_add = True)
    date_updated = models.DateField(auto_now = True)
    wid = models.IntegerField(null=True, blank=True, editable=False)
    subscriptions = models.ManyToManyField('cms.Listing', related_name='profiles', null=True, blank=True)
    is_valid_seabirder = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False, editable=False)

    def __unicode__(self):
        return u"%s %s" % (self.user.first_name, self.user.last_name)

    @models.permalink
    def get_absolute_url(self):
        return ('profiles_profile_detail', (), {'username': self.user.username})

def create_user_profile(sender, instance, created, **kwargs):
    """ Automatically create a profile when a User is created (if one doesn't already exist) """
    if created:
        UserProfile.objects.get_or_create(user=instance)
post_save.connect(create_user_profile, sender=User)

def toggle_research_field(sender, instance, created, **kwargs):
    non_researcher, created = ResearchField.objects.get_or_create(choice='Not a researcher')
    if non_researcher in instance.research_field.all():
        if instance.is_researcher:
            instance.is_researcher = False
            instance.save()
post_save.connect(toggle_research_field, sender=UserProfile)

def _get_users_with_permission(permission_code):
    from django.contrib.auth.models import User, Permission
    from django.db.models import Q

    perm = Permission.objects.get(codename=permission_code)
    return User.objects.filter(Q(groups__permissions=perm) | Q(user_permissions=perm) ).distinct()

def user_validated(sender, instance, **kwargs):
    if kwargs['raw']: return
    if instance.id: # without an instance id, this is a create action
        old = sender.objects.get(pk=instance.id)
        if instance.is_valid_seabirder and not old.is_valid_seabirder:
            # Someone just marked a UserProfile as valid. Let's send them an
            # email to tell them the good news.
            current_site = Site.objects.get_current()
            context = { 'user': instance.user, 'site': current_site }
            subject = render_to_string('registration/user_validated_email_subject.txt', context).strip()
            body = render_to_string('registration/user_validated_email.txt', context).strip()
            message = EmailMessage(subject, body, to=[instance.user.email])
            message.send()
pre_save.connect(user_validated, sender=UserProfile)

def user_activated(sender, instance, **kwargs):
    if kwargs['raw']: return
    if instance.id: # without an instance id, this is a create action
        old = sender.objects.get(pk=instance.id)
        if instance.is_active and not old.is_active:
            # Notify admin when user activates account
            current_site = Site.objects.get_current()
            context = { 'user': instance, 'site': current_site }
            subject = render_to_string('registration/notify_admin_of_new_user_subject.txt', context).strip()
            body = render_to_string('registration/notify_admin_of_new_user.txt', context).strip()
            users = _get_users_with_permission('moderator')
            if len(users) == 0:
                # If no moderators, then use the email of the first defined admin
                moderator_emails = [ a[1] for a in settings.ADMINS ]
            else:
                moderator_emails = [u.email for u in users]
            message = EmailMessage(subject, body, to=moderator_emails)
            message.send()
pre_save.connect(user_activated, sender=User)
