import datetime
import types
import os
import re
import logging

from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, get_list_or_404
from django.template import RequestContext
from django.conf import settings
from django.views.static import serve
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.template.defaultfilters import slugify


from PIL import Image as PILImage

from cms.models import Page, File, Navigation, Image, Post
from cms.forms import PostForm, ImageForm
from bibliography.models import Reference
from license.models import License
from profile.models import UserProfile

@login_required
def page(request, name):
    context_instance=RequestContext(request)
    context_instance.autoescape=False
    if name == 'index': 
        name = 'home'
        fullpath = ""
    else:
        fullpath = name
    name = os.path.basename(name)
    page =  get_object_or_404(Page, name = name)
    navigation = page.get_absolute_url()
    level = page
    while level.parent:
        if Navigation.objects.filter(url = navigation):
            break
        level = level.parent
        navigation = level.get_absolute_url()
    c = dict(
            page = page, 
            navigation = get_navigation(navigation),
            )
    return render_to_response('index.html', c, context_instance)

@login_required
def home(request):
    return page(request, 'home')

#def people(request):
#    persons = Person.objects.all().order_by('order')
#    page = Page.objects.get(name = 'people')
#    return render_to_response('people.html', dict(person_list=persons, page=page, navigation=get_navigation('/people.html')),
#        RequestContext(request))
		
def image(request, filename):
    #Return the file if it is in the  images directory
    if os.path.exists(os.path.join(settings.MEDIA_ROOT, 'images', filename)):
        return serve(request, filename, document_root=os.path.join(settings.MEDIA_ROOT, 'images'))
    #If not then look for it in the  cache directory
    path = os.path.join(settings.MEDIA_ROOT, 'images', 'cache', filename)
    if os.path.exists(path):
        return serve(request, filename, document_root=os.path.join(settings.MEDIA_ROOT, 'images', 'cache'))

    # If it  isn't their, then make the image
    # look for an image that is the same without size info
    m = re.search('-(\d+)x(\d+)', filename)
    if not m: raise Http404
    origname = re.sub('-\d+x\d+', '', filename)
    origpath = os.path.join(settings.MEDIA_ROOT, 'images', origname)
    if not os.path.exists(origpath): raise Http404
    orig = PILImage.open(origpath)
    format = orig.format
    (basewidth, baseheight) = (int(m.group(1)), int(m.group(2)))
    wpercent = (basewidth/float(orig.size[0]))
    hsize = int((float(orig.size[1])*float(wpercent)))
    img = orig.convert('RGB').resize((basewidth, hsize), PILImage.ANTIALIAS)
    img.save(path, format)

    response = HttpResponse(mimetype="image/%s"%(format))
    img.save(response, format)
    return response

@login_required
def imagepage(request, key):
    image = get_object_or_404(Image, key=key)
    return render_to_response('cms/imagepage.html', {'image': image})

@login_required
def reference(request, key):
    current = None
    for r in get_list_or_404(Reference, name=key):
        current = r
    return render_to_response('references/view.html', dict(
            current = current, page = dict(title=current.title),
            navigation = get_navigation('/publications.html'),
        ), RequestContext(request))

def get_navigation(url):
    try:
        home = Navigation.objects.root_nodes()[0]
    except IndexError:
        return []
    try:
        node = Navigation.objects.get(url=url)
    except:
        node = home
    actives = [node] + list(node.get_ancestors())
    links = []
    for child in home.get_children():
        if child == node:
            grandchildren = child.get_children()
            sublinks = [(g, False, []) for g in grandchildren]
            links.append((child, True, sublinks))
        elif child in actives:
            grandchildren = child.get_children()
            sublinks = []
            for g in grandchildren:
                if g in actives:
                    sublinks.append((g, True, []))
                else:
                    sublinks.append((g, False, []))
            links.append((child, False, sublinks))
        else:
            links.append((child, False, []))
    return links
            
def get_base_navigation(request):
    try:
        root = Navigation.objects.root_nodes()[0]
    except IndexError:
        return []
    return {'navigation': get_navigation(root.url)}



def get_initial_data(request):
    if request.user:
        initial = {'owner': '%s %s'%(request.user.first_name.capitalize(), request.user.last_name.capitalize()), 
            'license': License.objects.get(name='BY-SA'), 
            'author': request.user}
        try:
            profile = UserProfile.objects.get(user = request.user)
            initial['owner_url'] = settings.SITE_URL + reverse('profiles_profile_detail', 
                args=(), 
                kwargs={'username': request.user.username})
        except UserProfile.DoesNotExist:
            pass
    else:
        initial = {}
    return initial

def process_image_form(request):
    if request.method == 'POST': # If the form has been submitted...
        form = ImageForm(request.POST, request.FILES, prefix='image') # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Get the key
            key = slugify(form.cleaned_data['title'])
            try:
                Image.objects.get(key=key)
            except Image.DoesNotExist:
                count = 1
                while True:
                    newkey = '%s-%s'%(key, count)
                    try:
                        Image.objects.get(key=newkey)
                        count += 1
                    except Image.DoesNotExist:
                        key = newkey
                        break
            new_image = form.save(commit=False)
            form.cleaned_data['image'] = new_image
            new_image.key = key
            if not request.user:
                raise ValidationError, 'User must be logged in'
            else:
                new_image.uploaded_by = request.user
            new_image.save()
            form.redirect_url = new_image.get_absolute_url()
    else:
        form = ImageForm(initial=get_initial_data(request), prefix='image') # An unbound form
    return form

REQUIRED_FIELDS = ('image', 'title', 'owner', 'text', 'teaser')
@login_required
def edit_image(request):
    imageform = process_image_form(request)
    if hasattr(imageform, 'redirect_url'):
        return HttpResponseRedirect(imageform.redirect_url)
    else:
        return render_to_response('cms/edit_image.html', 
            {'imageform': imageform, 'required': REQUIRED_FIELDS}, 
            context_instance=RequestContext(request)
            )

@login_required
def edit_post(request, post_id = None):
    if request.method == 'POST': # If the form has been submitted...
        postform = PostForm(request.POST, request.FILES, prefix='post') # A form bound to the POST data
        # check that the image form has been completed (look for a file path)
        if request.FILES.has_key('image-image'):
            imageform = process_image_form(request)
        else:
            imageform = None
        if postform.is_valid(): # All validation rules pass
            new_post = postform.save(commit=False)
            if imageform:
                new_post.image = imageform.cleaned_data['image']
            else:
                new_post.image = None
            new_post.date_published =  datetime.date.today()
            name = slugify(new_post.title)[:50]
            try:
                Post.objects.get(name=name)
                count = 0
                while True:
                    count += 1
                    newname = name[:(50 - 1 - len(str(count)))] + '-' + str(count)
                    try:
                        Post.objects.get(name=newname)
                    except Post.DoesNotExist:
                        name = newname
            except Post.DoesNotExist:
                pass
            new_post.name = name
            new_post.save()
            return HttpResponseRedirect(new_post.get_absolute_url())
    else:
        if not post_id:
            postform = PostForm(prefix='post') # An unbound form
            imageform = ImageForm(initial=get_initial_data(request), prefix='image') # An unbound form
        else:
            post = get_object_or_404(Post, id=post_id)
            postform = PostForm(post, prefix='post')
            if not post.image:
                imageform = ImageForm(initial=get_initial_data(request), prefix='image') # An unbound form
            else:
                imageform = ImageForm(post.image, initial=get_initial_data(request), prefix='image') # An unbound form
                
    return render_to_response('cms/edit_post.html', {'postform': postform, 'imageform': imageform, 'required': REQUIRED_FIELDS,}, 
        context_instance=RequestContext(request))
