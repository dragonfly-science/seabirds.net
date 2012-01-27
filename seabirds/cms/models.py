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

# Process references if the bibliography is installed
try:
    from bibliography.views import markdown_post_references
except ImportError:
    def markdown_post_references(text):
        return text

check=True
def markdownplus(instance, text, check=False):
    text = markdown(text)
    print text
    def insert_image(m):
        print m.group(0)
        try:
            image = Image.objects.get(key=m.group(1))
            try:
                width = int(re.findall('width=([\w-]+)', m.group(2))[0])
                print width
            except:
                width = None
            try:
                height = int(re.findall('height=([\w-]+)', m.group(2))[0])
            except:
                height = None
            try:
                place = re.findall('place=([\w]+)', m.group(2))[0]
            except:
                place = ''
            ih = float(image.image.height)
            iw = float(image.image.width)
            if not width and height:  
                width  = floor(iw * ( height / ih))
            elif not height and width: 
                height  = floor(ih * ( width / iw))
            elif not height and not width: 
                height  = floor(ih)
                width  = floor(iw)
            url = image.get_qualified_url(width, height)
            if place.upper() == 'R':
                place = 'float-right'
            elif place.upper() == 'L':
                place = 'float-left'
            elif place.upper() == 'C':
                place = 'center'
            caption = m.group(3)
            return render_to_string('image/plain.html', dict(image=image, width=width, place=place, url=url, caption=caption))
        except:
            if check: raise
            raise
    text = re.sub('\[Image\s+([-\w]+)(\s+\w[\w=%\'" -]+)?\s*\](.*)(</p>)?', insert_image,  text)
    print text

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
    name = models.SlugField(max_length = 50, unique = True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    title = models.CharField(max_length = 100)
    order = models.PositiveIntegerField(default = 1)
    published = models.BooleanField(default=False)
    text = models.TextField(null=True, blank=True)
    sidebar = models.TextField(null=True, blank=True)
    images = models.ManyToManyField('Image', related_name = 'pages')
     
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']

    @property   
    def markdown_text(self):
        return markdownplus(self, self.text)
    
    @property   
    def markdown_sidebar(self):
        return markdownplus(self, self.sidebar)

    def get_absolute_url(self):
        return "%s/%s.html" % (settings.SITE_URL, self.name)

    def breadcrumb(self):
        path = [self]
        this = self
        while this.parent:
            path.append(this.parent)
            this = this.parent
        path.reverse()
        res = []
        fullpath = []
        for p in path:
            if p.name == 'home': 
                res.append({'name': "Home",
                    'href': p.get_absolute_url(),
                })
            else:
                fullpath.append(p.name)
                res.append({'name': p.title,
                    'href': p.get_absolute_url(),
                })
        return res

class Post(models.Model):
    name = models.SlugField(max_length = 50, unique = True)
    title = models.CharField(max_length = 100)
    author = models.ForeignKey('Person', null=True, blank=True)
    date_published = models.DateField()
    published = models.BooleanField(default=False)
    teaser = models.TextField()
    text = models.TextField()
    images = models.ManyToManyField('Image', related_name = 'posts')
     
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

class Person(models.Model):
    username = models.TextField()
    firstname = models.TextField()
    lastname = models.TextField()
    teaser = models.TextField()
    image = models.OneToOneField('Image')
    email = models.TextField(null=True, blank=True)
    phone = models.TextField(null=True, blank=True)
    mobile = models.TextField(null=True, blank=True)
    order = models.PositiveIntegerField(default = 1)
    active = models.BooleanField()
    role = models.TextField()
    class Meta:
        ordering = ['order',]
        verbose_name_plural = 'people'

    def __str__(self):
        return "%s %s"%(self.firstname, self.lastname)

    @permalink
    def get_absolute_url(self):
        return ('person', (), {'name': self.firstname.lower() + '-' + self.lastname.lower()})

    def has_link(self):
        linkname = ('%s-%s' % (self.firstname, self.lastname)).lower()
        pages = Page.objects.filter(name = linkname)
        return pages


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
    base, ext = os.path.splitext(os.path.split(filename)[1])
    return os.path.join('images', '%s%s'%(instance.key, ext))

class Image(models.Model):
    image = models.ImageField(upload_to = get_image_path)
    title = models.CharField(max_length = 100) #Displays on mouse over
    key = models.SlugField(max_length = 50, unique=True)
    source_url = models.URLField(null=True, blank=True)
    owner = models.CharField(max_length = 200, null = True, blank=True)
    owner_url = models.URLField(null=True, blank=True)
    license = models.ForeignKey(License, null=True, blank=True)
    uploaded_by = models.ForeignKey(User, null=True, blank=True)
        
    def __str__(self):
        return '%s - %s'%(self.key, self.title)

    def get_qualified_url(self, width, height):
        base, ext = os.path.splitext(os.path.split(self.image.path)[1])
        return os.path.join('images', '%s-%ix%i%s'%(base, width, height, ext))

    @permalink
    def get_absolute_url(self):
        base, ext = os.path.splitext(os.path.split(self.image.path)[1])
        return ('cms.views.image', (), {'path': os.path.join(base, '%s.html'%self.key) }) 

class Navigation(MPTTModel):
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=20)
    url = models.CharField(max_length = 100)
    title = models.CharField(max_length = 100)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')

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
        

