import re
import logging
import os
from math import floor

from django.db import models
from django.db.models import permalink
from django.conf import settings
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve, Resolver404

from markdown import markdown
from mptt.models import MPTTModel, TreeForeignKey

from license.models import License
from categories.models import SeabirdFamily

# Process references if the bibliography is installed
try:
    from bibliography.views import markdown_post_references
except ImportError:
    def markdown_post_references(text):
        return text

check=True
IMAGE_REGEX = '\[Image\s+([-\w]+)(\s+\w[\w=%\'" -]+)?\s*\](.*)(?=</p>)'
def markdownplus(instance, text, check=False):
    text = markdown(text)
    def insert_image(m):
        try:
            image = Image.objects.get(key=m.group(1))
            try:
                width = int(re.findall('width=([\d]+)', m.group(2))[0])
            except:
                width = None
            try:
                height = int(re.findall('height=([\d]+)', m.group(2))[0])
            except:
                height = None
            try:
                place = re.findall('place=([\w]+)', m.group(2))[0]
            except:
                place = ''
            width, height = image.get_dimensions(width, height)
            url = image.get_qualified_url(width, height)
            if place.upper().startswith('R'):
                place = 'float-right'
            elif place.upper().startswith('L'):
                place = 'float-left'
            else:
                place = 'center'
            caption = m.group(3)
            if not caption:
                caption = image.caption
            return render_to_string('image/plain.html', dict(image=image, width=width, place=place, url=url, caption=caption))
        except:
            if check: 
                raise
            return m.group(0) 
    text = re.sub(IMAGE_REGEX, insert_image,  text)

    def insert_references(m):
        try:
            return listview(None, query=m.group(1))
        except:
            if check: raise 
            return ""
    text = re.sub('\[References\s+(\w[\w=\'" -]+)\]', insert_references,  text)
    return text

    def insert_file(m):
        try:
            file = File.objects.get(name=m.group(1))
            return file.html()
        except:
            if check: raise 
            return ""
    text = re.sub('\[File\s+(\w+)\]',   insert_file, text) 

    text = markdown_post_references(text)
    return text

# Create your models here.
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
     
    def __str__(self):
        return self.name

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
    date_published = models.DateField(
        help_text="Publication date")
    published = models.BooleanField(default=False,
        help_text="When this box is checked, the post will be visible on the site.")
    teaser = models.TextField(max_length = 300,
        help_text='Teaser text. Short text that appears in lists of posts. Must be less than 300 characters long. Formatted using <a href="http://daringfireball.net/projects/markdown/syntax">markdown</a>')
    text = models.TextField(
        help_text='Post text. Formatted using <a href="http://daringfireball.net/projects/markdown/syntax">markdown</a>')
    image = models.ForeignKey('Image', related_name = 'posts', null=True, blank=True,
	help_text='Image associated with the post')
	
    def __str__(self):
        return self.name

    @property
    def markdown_text(self):
        return markdownplus(self, self.text)

    @property
    def markdown_teaser(self):
        return markdownplus(self, self.teaser)

    @permalink
    def get_absolute_url(self):
        return ('individual-post', (), {
            'year': self.date_published.year,
            'month': self.date_published.strftime('%m'), 
            'day': self.date_published.strftime('%d'), 
            'slug': self.name})

    class Meta:
        ordering = ['-date_published']


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


def get_image_path(instance, filename):
    print 'get path'
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
    owner = models.CharField(max_length = 200, 
        help_text="The name of the copyright holder of the image")
    owner_url = models.URLField(null=True, blank=True, verify_exists = not settings.DEBUG,
        help_text="Optional. A url linking to a website giving more information on the copyright owner (e.g., http://www.people.com/mr-nice.html)")
    license = models.ForeignKey(License, null=True, blank=True, 
        help_text="Copyright license. All uploaded images must be made available under a <a href='http://creativecommons.org/'>creative commons</a> or public domain license")
    uploaded_by = models.ForeignKey(User, 
        help_text="The user who uploaded the image")
    seabirds = models.ManyToManyField(SeabirdFamily, related_name='images', null=True, blank=True, help_text="If this is an image of a seabird, please select the correct family") 
    date_created = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)

    def thumbnail(self, width=100, max_height=300):
        width, height = self.get_dimensions(width=width, max_height=max_height)
        return "<img src='/%s' title='%s'>"%(self.get_qualified_url(width, height), self.title)
    thumbnail.allow_tags=True

    def render(self, width=None, height=None, caption=None, place=None):
        width, height = self.get_dimensions(widt=width, height=height)
        url = self.get_qualified_url(width, height)
        if not caption:
            caption=self.caption
        return render_to_string('image/plain.html', dict(image=image, width=width, place=None, url=url, caption=caption))

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
        return os.path.join('images', '%s-%ix%i%s'%(base, width, height, ext))

    @permalink
    def get_image_url(self):
        return ('cms.views.image', (), {'filename': os.path.split(self.image.path)[1]}) 
    
    @permalink
    def get_absolute_url(self):
        return ('cms.views.imagepage', (), {'key': self.key}) 

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
        

