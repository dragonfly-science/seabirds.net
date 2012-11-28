import datetime
import os

from django.db import models
from django.db.models import permalink
from django.conf import settings
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve, Resolver404
from django.core.mail import EmailMessage

from pigeonpost.signals import pigeonpost_queue
from mptt.models import MPTTModel, TreeForeignKey

from license.models import License
from categories.models import SeabirdFamily

def get_image_path(instance, filename):
    base, ext = os.path.splitext(os.path.split(filename)[1])
    return os.path.join('images', '%s%s'%(instance.key, ext))

class Image(models.Model):
    image = models.ImageField(upload_to = get_image_path)
    title = models.CharField(max_length = 100, 
        help_text="The title is displayed when you mouse over the image")
    source_url = models.URLField(null=True, blank=True, verify_exists = not settings.DEBUG, 
        help_text="Optional. A url used to link to the original image (e.g. http://www.flickr.com/picture.png).")
    caption = models.TextField(null=True, blank=True, 
        help_text="Optional. Displayed under the image.")
    key = models.SlugField(max_length = 50, unique=True, 
        help_text="A unique name for each image on the website. Must only be letters, number, underscores, or hyphens.")
    seabird_families = models.ManyToManyField(SeabirdFamily, related_name='images', null=True, blank=True, help_text="Optional. If this is an image of a seabird or seabirds, please select the correct families.") 
    owner = models.CharField(max_length = 200, 
        help_text="The name of the copyright holder of the image")
    owner_url = models.URLField(null=True, blank=True, verify_exists = not settings.DEBUG,
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
            width = int(float(width*height)/max_height)
        return width, height       

    def get_qualified_url(self, width=None, height=None, max_height=None):
	if not width or not height or max_height:
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
      return  "%s/%s" % (settings.SITE_URL, self.file.url)
   def html(self):
      return "<a href=\"%s/%s\">%s</a>" % (settings.SITE_URL, self.file.url, self.title)

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
        return markdownplus(self, self.text)
    
    @property   
    def markdown_sidebar(self):
        return markdownplus(self, self.sidebar)

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
    _notify_moderator = models.BooleanField(default=False, editable=False,
        help_text='True if the moderator should be notified of edits to this post') 
    _sent_to_list = models.BooleanField(default=False, editable=False, 
        help_text='True if the post has been sent to lists')

    def __str__(self):
        return self.name

    @property
    def markdown_text(self):
        return markdownplus(self, self.text)

    @property
    def markdown_teaser(self, max_length=200):
        chars = [(len(x), x) for x in self.text.split('\n')]
        n = 0
        i = 0
        teaser = ''
        while n < max_length and i < len(chars):
            n += chars[i][0]
            teaser += '\n'
            teaser += chars[i][1]
            i += 1
        return markdownplus(self, teaser.strip())
            
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
        if user.profile.get().is_moderator:
            subject = render_to_string('email_list_subject.txt', {'title': self.title, 'user': user, 'post': self})
            body = render_to_string('email_list_body.txt', {'text': self.text, 'user': user, 'post': self})
            return EmailMessage(subject, body, to=[user.email])

    def save(self, *args, **kwargs):
        # The first time it is saved it is published
        if not self.date_published:
            self.published = True
            self.date_published = datetime.date.today()
            self.enable_comments = self.listing.allow_comments
        super(Post, self).save(*args, **kwargs)
        
        # When the post is saved, the moderators are notified, with a delay
        if self.published and self._notify_moderator and kwargs.get('commit', True):
            pigeonpost_queue.send(sender=self, 
                render_email_method='email_moderator', 
                defer_for=settings.PIGEONPOST_DEFER_POST_MODERATOR)
            self._notify_moderator = False

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
        help_text="Order of the items in the fully expanded menu (a postive integer)")
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
        
class Listing(models.Model):
    key = models.SlugField(max_length=50)
    description = models.TextField()

    # Permissions
    staff_only_write = models.BooleanField()
    staff_only_read = models.BooleanField()
    allow_comments = models.BooleanField()

    optional_list = models.BooleanField(default=True)

    def __unicode__(self):
        return self.description
    
