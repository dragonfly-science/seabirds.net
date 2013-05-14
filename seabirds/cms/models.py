import datetime
import os

from django.db import models
from django.db.models import permalink
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.urlresolvers import resolve, Resolver404

from pigeonpost.signals import pigeonpost_queue
from pigeonpost.models import Pigeon
from mptt.models import MPTTModel, TreeForeignKey

from profile.models import UserProfile
from license.models import License
from categories.models import SeabirdFamily

from utils import generate_email

def get_image_path(instance, filename):
    base, ext = os.path.splitext(os.path.split(filename)[1])
    return os.path.join('images', '%s%s'%(instance.key, ext))

class Image(models.Model):
    image = models.ImageField(upload_to = get_image_path)
    title = models.CharField(max_length = 100, 
        help_text="The title is displayed when you mouse over the image")
    source_url = models.URLField(null=True, blank=True,
        help_text="Optional. A url used to link to the original image (e.g. http://www.flickr.com/picture.png).")
    caption = models.TextField(null=True, blank=True, 
        help_text="Optional. Displayed under the image.")
    key = models.SlugField(max_length = 50, unique=True, 
        help_text="A unique name for each image on the website. Must only be letters, number, underscores, or hyphens.")
    seabird_families = models.ManyToManyField(SeabirdFamily, related_name='images', null=True, blank=True, help_text="Optional. If this is an image of a seabird or seabirds, please select the correct families.") 
    owner = models.CharField(max_length = 200, 
        help_text="The name of the copyright holder of the image")
    owner_url = models.URLField(null=True, blank=True,
        help_text="Optional. A url linking to a website giving more information on the copyright owner (e.g., http://www.people.com/mr-nice.html)")
    license = models.ForeignKey(License, null=True, blank=True, 
        help_text="Optional copyright license. Available licenses include <a href='http://creativecommons.org/'>creative commons</a> or public domain licenses. If no license is specified it is assumed that the owner has the copyright and has granted permission for the image to be used")
    uploaded_by = models.ForeignKey(User, 
        help_text="The user who uploaded the image")
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def thumbnail(self, width=100, max_height=300):
        width, height = self.get_dimensions(width=width, max_height=max_height)
        return "<img src='%s' title='%s'>"%(self.get_qualified_url(width, height), self.title)
    thumbnail.allow_tags=True

    def render(self, width=None, height=None, caption=None, place=None):
        width, height = self.get_dimensions(width=width, height=height)
        url = self.get_qualified_url(width, height)
        if not caption:
            caption=self.caption
        return render_to_string('image/plain.html', dict(image=self, width=width, place=None, url=url, caption=caption))

    def tag(self):
        return "[Image %s]"%(self.key,)
        
    def __str__(self):
        return '%s - %s'%(self.key, self.title)

    def get_dimensions(self, width=None, height=None, max_height=None):
        if not height and not width:
            height = self.image.height
            width = self.image.width
        elif not height:
            height = int(float(self.image.height*width)/self.image.width)
        elif not width:
            width = int(float(self.image.width*height)/self.image.height)
        if max_height and height > max_height:
            height = max_height
            # I feel as though this is wrong since it will never change the width
            width = int(float(width*height)/max_height)
            # To keep aspect ratio it should be
            #width = int(float(self.image.width*height)/self.image.height)
        return width, height       

    def get_qualified_url(self, width=None, height=None, max_height=None):
        width, height = self.get_dimensions(width=width, height=height, max_height=max_height)
        base, ext = os.path.splitext(os.path.split(self.image.path)[1])
        return os.path.join('/images', '%s-%ix%i%s'%(base, width, height, ext))

    @permalink
    def get_image_url(self):
        return ('cms.views.image', (), {'filename': os.path.split(self.image.path)[1]}) 
    
    @permalink
    def get_absolute_url(self):
        return ('cms.views.imagepage', (), {'key': self.key}) 


class File(models.Model):
   name = models.CharField(max_length = 100)
   file = models.FileField(upload_to = "files")
   title = models.CharField(max_length = 100, null=True, blank=True)

   def __str__(self):
      return self.title
   def get_absolute_url(self):
      return  "%s%s" % (settings.SITE_URL, self.file.url)
   def html(self):
      return "<a href=\"%s%s\">%s</a>" % (settings.SITE_URL, self.file.url, self.title)

# Depends on models.Image and models.File
from utils.markdownplus import markdownplus

class Page(models.Model):
    title = models.CharField(max_length = 100, 
        help_text='Title of the page, appears in the title bar of the browser')
    name = models.SlugField(max_length = 50, unique = True, 
        help_text = 'The name of the page. Pages are referenced as "%s/{name}.html". The field name can only contain alphanumeric characters, dashes, and underscores.'%settings.SITE_URL)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', 
        help_text='Set the parent page. Used to define a page hierarchy across the site')
    published = models.BooleanField(default=False, 
        help_text='Page will appear on the site when this field is ticked')
    text = models.TextField(null=True, blank=True, 
        help_text='Page text. Formatted using <a href="http://daringfireball.net/projects/markdown/syntax">markdown</a>')
    sidebar = models.TextField(null=True, blank=True, 
        help_text='Sidebar text. Appears at the top of the right sidebar. Formatted using <a href="http://daringfireball.net/projects/markdown/syntax">markdown</a>')
    date_published = models.DateField(
        help_text="Publication date", null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
     
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.published and not self.date_published:
            self.date_published = datetime.date.today()
        super(Page, self).save(*args, **kwargs)
    
    @property   
    def markdown_text(self):
        return markdownplus(self.text)
    
    @property   
    def markdown_sidebar(self):
        if self.sidebar:
            return markdownplus(self.sidebar)
        return ''

    @permalink
    def get_absolute_url(self):
        return ('cms.views.page', (), {'name': self.name})

class Post(models.Model):
    title = models.CharField(max_length = 100,
        help_text="Title of the post")
    name = models.SlugField(max_length = 50, unique = True,
        help_text="Name used to refer to the post in the URL. Must be only letters, numbers, underscores, or hyphens.")
    author = models.ForeignKey(User, null=True, blank=True,
        help_text="Optional. User who made the post, leave blank for anonymous posts.")
    date_published = models.DateField(null=True, blank=True,
        help_text="Publication date")
    published = models.BooleanField(default=False,
        help_text="When this box is checked, the post will be visible on the site.")
    text = models.TextField(
        help_text='Post text. Formatted using <a href="http://daringfireball.net/projects/markdown/syntax">markdown</a>')
    seabird_families = models.ManyToManyField(SeabirdFamily, related_name='posts', null=True, blank=True, help_text="Optional. If this post is about a particular seabird or seabirds, please select the correct families.") 
    image = models.ForeignKey('Image', related_name = 'posts', null=True, blank=True,
	    help_text='Image associated with the post')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    enable_comments = models.BooleanField()
    listing = models.ForeignKey('Listing', related_name='posts', default=1,
        help_text='List that the post is published in')
    _sent_to_list = models.BooleanField(default=False, editable=False, 
        help_text='True if the post has been sent to lists')
    
    # This generic relation ensures that when a Post is deleted, so are any associated
    # Pigeons (and due to the link from Outbox to Pigeon, so are Outbox messages)
    pigeons = generic.GenericRelation(Pigeon,
            content_type_field='source_content_type',
            object_id_field='source_id')

    # These templates are used for notifying the author/subscriber/moderator
    # about a new post
    text_template = 'pigeonpost/new_post.txt'
    html_template = 'pigeonpost/new_post.html'

    def __str__(self):
        return self.name

    @property
    def markdown_text(self):
        return markdownplus(self.text)

    @property
    def markdown_teaser(self):
        # This was a method argument, but @properties can't be called with arguments!
        max_length=200
        chars = [(len(x), x) for x in self.text.split('\n')]
        n = 0
        i = 0
        teaser = ''
        while n < max_length and i < len(chars):
            n += chars[i][0]
            teaser += '\n'
            teaser += chars[i][1]
            i += 1
        return markdownplus(teaser.strip())
            
    @permalink
    def get_absolute_url(self):
        if self.date_published:
            date = self.date_published
        else:
            date = self.date_created
        return ('individual-post', (), {
            'year': date.year,
            'month': date.strftime('%m'), 
            'day': date.strftime('%d'), 
            'slug': self.name})

    def email_moderator(self, user):
        """ Email moderator when new post is made by a non-staff member
        
        This is to allow for the message to edited if necessary before they
        get sent to all subscribers. The moderator only gets emailed once it
        looks like there are no further changes from the author (i.e. after
        there are no new edits for a given time).
        """
        if self.listing.can_user_moderate(user):
            subject = '[seabirds.net] New post by %s' % self.author
            editable_until = (self.date_updated +
                    datetime.timedelta(seconds=settings.PIGEONPOST_DELAYS['cms.Post']['subscriber']))
            # If it's in the past, don't show it
            if editable_until < datetime.datetime.now():
                editable_until = None
            template_data = { 'user': user, 'post': self, 'is_moderator': True,
                    'editable_until': editable_until}
            return generate_email(user, subject, template_data, self.text_template, self.html_template)

    def email_author(self, user):
        """ Email author when they make a new post
        
        This lets the author know they have a while to make edits before
        it's checked by a moderator and sent out to subscibers.

        TODO: Think about if we really need this, since the user will
        already be aware they created it (and presumedly see the ability
        to edit it)
        """
        if user == self.author:
            subject = '[seabirds.net] Your new post "%s"' % self.title
            editable_until = (self.date_updated +
                    datetime.timedelta(seconds=settings.PIGEONPOST_DELAYS['cms.Post']['subscriber']))
            # If it's in the past, don't show it
            if editable_until < datetime.datetime.now():
                editable_until = None
            template_data = { 'user': user, 'post': self, 'editable_until': editable_until }
            return generate_email(user, subject, template_data, self.text_template, self.html_template)

    def email_subscriber(self, user):
        """ Email subscribers to the listing this post is part of """
        if not self.published:
            return None
        if user != self.author:
            subject = '[seabirds.net] New %s post "%s"' % (self.listing, self.title)
            template_data = { 'user': user, 'post': self }
            return generate_email(user, subject, template_data, self.text_template, self.html_template)

    def save(self, *args, **kwargs):
        just_published_now = False

        # The first time it is saved it is published automatically
        if not self.date_published:
            self.published = True
            self.date_published = datetime.date.today()
            self.enable_comments = self.listing.allow_comments
            just_published_now = True

            # Check that the author is allowed to post to this list
            if not self.listing.can_user_post(self.author):
                raise PermissionDenied

        super(Post, self).save(*args, **kwargs)

        # We send out the pigeons after the save statement because pigeonpost needs
        # the Post.id for source_id.
        #
        # Note that all pigeonpost signals won't send an email if there is already
        # a pigeon with the same parameters and to_send=False.
        
        # Staff and moderators can post without being moderated themselves
        if self.published and not self.author.is_staff and not self.listing.can_user_moderate(self.author):
            # When the post is saved, the moderators are notified, with a delay
            pigeonpost_queue.send(sender=self, render_email_method='email_moderator', 
                defer_for=settings.PIGEONPOST_DELAYS['cms.Post']['moderator'])

        if just_published_now:
            # We send the author an email to let them know they can edit it
            pigeonpost_queue.send(sender=self, render_email_method='email_author', 
                defer_for=settings.PIGEONPOST_DELAYS['cms.Post']['author'],
                send_to=self.author)

            # Let subscribers to the listing of this post know about it
            pigeonpost_queue.send(sender=self, render_email_method='email_subscriber', 
                defer_for=settings.PIGEONPOST_DELAYS['cms.Post']['subscriber'],
                send_to_method='get_subscribers')

    def get_subscribers(self):
        if not self.listing.optional_list:
            # If the list is mandatory, then all active users are subscribed
            subscribers = User.objects.filter(is_active=True)
        else:
            subscriber_profiles = UserProfile.objects.filter(subscriptions=self.listing)
            subscribers = [p.user for p in subscriber_profiles if p.user.is_active]
        return subscribers

    def can_user_comment(self, user):
        if not user.is_authenticated():
            return False
        if not user.profile.get().is_valid_seabirder or not self.listing.can_user_read(user):
            return False
        return self.enable_comments and self.published

    def can_user_modify(self, user):
        if not user.is_authenticated():
            return False
        # The auhtor, staff and moderators can modify posts
        return user == self.author or user.is_staff or self.listing.can_user_moderate(user)

    class Meta:
        ordering = ['-date_published', '-date_created']

class Navigation(MPTTModel):
    name = models.CharField(max_length=20,
        help_text="Text that appears in the navigation menu")
    url = models.CharField(max_length = 100,
        help_text="URL of the link (e.g. '/home.html')")
    title = models.CharField(max_length = 100,
        help_text="Text that appears when you mouse over the menu item")
    order = models.PositiveIntegerField(
        help_text="Order of the items in the fully expanded menu (a positive integer)")
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children',
        help_text="Parent navigation item, used to define the navigation hierarchy")

    def __unicode__(self):
        return self.name

    def clean(self):
        if not self.url.startswith('/'):
            self.url = '/'+self.url
        try:
            resolve(self.url)
        except Resolver404:
            message = 'Unknown URL %s' % self.url
            raise ValidationError, message

    class MPTTMeta:
        order_insertion_by = ['order']

    class Meta:
        verbose_name_plural = 'navigation'
        
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from utils import perm_to_code

def get_listing_content_type():
    return ContentType.objects.get(app_label="cms", model="listing")

class ListingManager(models.Manager):
    
    def user_readable(self, user):
        all_listings = Listing.objects.all()
        if user.is_authenticated and user.is_staff:
            return list(all_listings)

        viewable_listings = []
        for l in all_listings:
            if l.can_user_read(user):
                viewable_listings.append(l)
        return viewable_listings

    def user_postable(self, user):
        all_listings = Listing.objects.all()
        if user.is_authenticated and user.is_staff:
            return list(all_listings)

        viewable_listings = []
        for l in all_listings:
            if l.can_user_post(user):
                viewable_listings.append(l)
        return viewable_listings

class Listing(models.Model):
    key = models.SlugField(max_length=50)
    description = models.TextField()

    # Permissions
    allow_comments = models.BooleanField()

    post_permission = models.ForeignKey(Permission, null=True, blank=True,
            related_name='+',
            limit_choices_to = {'content_type': get_listing_content_type})
    read_permission = models.ForeignKey(Permission, null=True, blank=True,
            related_name='+',
            limit_choices_to = {'content_type': get_listing_content_type})
    moderation_permission = models.ForeignKey(Permission, null=True, blank=True,
            related_name='+',
            limit_choices_to = {'content_type': get_listing_content_type})

    optional_list = models.BooleanField(default=True)

    objects = ListingManager()

    @property
    def name(self):
        return self.description

    @property
    def url(self):
        return self.get_absolute_url()

    def get_absolute_url(self):
        return '/groups/' + self.key

    def __unicode__(self):
        return self.description

    def can_user_post(self, user):
        if user:
            if user.profile.get().is_valid_seabirder:
                return not self.post_permission or user.has_perm(perm_to_code(self.post_permission))
            else:
                return False
        return False

    def can_user_read(self, user):
        if self.read_permission:
            if user:
                return user.has_perm(perm_to_code(self.read_permission))
            else:
                return False
        return True

    def can_user_moderate(self, user):
        if user:
            if self.moderation_permission:
                return user.has_perm(perm_to_code(self.moderation_permission))
        return False

    class Meta:
        permissions = (
                ('committee', 'Can access and post to WSU committee listings'),
                ('site-announce', 'Can post to announcement list'),
                ('wsu-announce', 'Can post to WSU announcement list'),
                ('moderator', 'Can moderate all posts'),
                )
