import re, logging
from math import floor

from django.db import models
from django.db.models import permalink
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.core.urlresolvers import resolve, Resolver404

from markdown import markdown
from mptt.models import MPTTModel, TreeForeignKey


# Process references if the bibliography is installed
try:
    from bibliography.views import markdown_post_references
except ImportError:
    def markdown_post_references(text):
        return text

def markdownplus(instance, text, check=False):
    content_name = instance.name
    content_type = instance.__class__.__name__.lower()
    def insert_image(m):
        try:
            ct = ContentType.objects.get(name=content_type)
            cid = ct.model_class().objects.get(name=content_name)
            placement = Placement.objects.get(number=m.group(1), object_id=cid.id, content_type=ct.id)
            return render_to_string('image/plain.html', dict(placement=placement))
        except:
            if check: raise
            raise
    text = re.sub('\[Image (\d+)\]', insert_image, text)

#    def insert_link(m):
#        try:
#            item = ContentType.objects.get(name=content_type).model_class().objects.get(name=m.group(1))
#            return "(%s)" % (item.get_absolute_url())
#        except:
#            if check: raise 
#            return ""
#    text = re.sub('\((\w+)\)',       insert_link,  text)

    def insert_file(m):
        try:
            file = File.objects.get(name=m.group(1))
            return file.html()
        except:
            if check: raise 
            return ""
    text = re.sub('\[@(\w+)@\]',   insert_file, text) 
    text = markdown(text)
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
    images = generic.GenericRelation('Placement')
     
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
    images = generic.GenericRelation('Placement')
     
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


PLACE_CHOICES = (
    ('R', 'Right'),
    ('C', 'Centre'),
    ('L', 'Left'),
    )

class Image(models.Model):
    name = models.SlugField(max_length = 50, unique=True)
    title = models.CharField(max_length = 100) #Displays on mouse over
    image = models.ImageField(upload_to = "images")
    caption = models.TextField(null=True, blank=True)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    alignment = models.CharField(max_length=1, choices=PLACE_CHOICES, default='R')
    owner = models.CharField(max_length = 200, null = True, blank=True)
    source_url = models.URLField(null=True, blank=True)
    license = models.ForeignKey(License, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        ih = float(self.image.image.height)
        iw = float(self.image.image.width)
        if self.width and self.height:  
            self._width  = floor(iw * ( self.height / ih))
            self._height = floor(ih * ( self.width / iw))
        if not self.width and self.height:  
            self._width  = floor(iw * ( self.height / ih))
            self._height  = floor(ih)
        if not self.height and self.width: 
            self._width  = floor(iw)
            self._height = floor(ih * ( self.width / iw))
        if not self.height and not self.width: 
            self._height = floor(ih)
            self._width  = floor(iw)
        super(Image, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    @permalink
    def get_absolute_url(self):
        base, ext = os.path.splitext(os.path.split(self.image.path)[1])
        return ('cms.views.image', (), {'path': '%s-%dx%d%s'%(base, self._width, self._height, ext)}) 

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
        

