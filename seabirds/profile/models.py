import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django_countries import CountryField
from django.db.models.signals import post_save
from django.template.defaultfilters import slugify


from categories.models import SeabirdFamily, InstitutionType, ResearchField

TITLES = ('Mr', 'Ms', 'Mrs', 'Miss', 'Dr', 'Prof')

def get_photo_path(instance, filename):
    if filename:
	    print 'get path'
	    base, ext = os.path.splitext(os.path.split(filename)[1])
	    try: 
	        os.mkdir(os.path.join(settings.MEDIA_ROOT, 'users', '%s'%instance.user.id))
	    except OSError:
	        pass
	    print 'Upload image', '%s'%instance.user.id
	    return os.path.join('users', '%s'%instance.user.id, '%s%s'%(slugify(str(instance).lower()), ext))

class CollaborationChoice(models.Model):
    label = models.CharField(max_length=50)
    description = models.TextField()

    def __unicode__(self):
        return self.label

class UserProfile(models.Model):
    user = models.ForeignKey(User, related_name = 'profile', unique=True)
    title = models.CharField(max_length=5, choices=zip(TITLES, TITLES), null=True, blank=True)
    webpage = models.URLField(null=True, blank=True)
    display_email = models.BooleanField(default=True)
    institution = models.CharField(max_length=50, null=True, blank=True)
    institution_type = models.ForeignKey(InstitutionType, null=True, blank=True)
    institution_website = models.URLField(null=True, blank=True)
    country = CountryField(null=True, blank=True)
    research = models.TextField(null=True, blank=True)
    research_field = models.ManyToManyField(ResearchField)
    photograph = models.ImageField(upload_to=get_photo_path, null=True, blank=True)
    seabirds = models.ManyToManyField(SeabirdFamily, related_name='profiles', null=True, blank=True)
    twitter = models.CharField(max_length=15, null=True, blank=True)
    display_twitter = models.BooleanField(default=False)
    collaboration_choices = models.ManyToManyField(CollaborationChoice)
    accept_terms = models.BooleanField(default=False)
    date_created = models.DateField(auto_now_add = True)
    date_updated = models.DateField(auto_now = True)
    wid = models.IntegerField(null=True, blank=True, editable=False)

    def __str__(self):
        return "%s %s"%(self.user.first_name, self.user.last_name)

    @models.permalink
    def get_absolute_url(self):
        return ('profiles_profile_detail', (), {'username': self.user.username})

#Automatically create a profile when a User is created (if one doesn't already exits)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            UserProfile.objects.get(user=instance)
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=instance)
post_save.connect(create_user_profile, sender=User)


