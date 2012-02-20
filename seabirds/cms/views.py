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

def process_image_form(request, image_id=None):
    if request.method == 'POST': # If the form has been submitted...
        form = ImageForm(request.POST, request.FILES, prefix='image') # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            if not image_id:
                new_image = form.save(commit=False)
            else:
                new_image = get_object_or_404(Image, id=image_id)
                new_image = form.save(commit=False, instance=new_image)
            form.cleaned_data['image'] = new_image
            # Get the key
            if not image_id:
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
                new_image.key = key
            if not image_id:
                if not request.user:
                    raise ValidationError, 'User must be logged in'
                else:
                    new_image.uploaded_by = request.user
            new_image.save()
            form.redirect_url = new_image.get_absolute_url()
    else: #unbound forms
        if not image_id:
            form = ImageForm(initial=get_initial_data(request), prefix='image')
        else:
            image = get_object_or_404(Image, id=image_id)
            form = ImageForm(initial=get_initial_data(request), prefix='image', instance=image) 
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
def individual_post(request, year=None, month=None, day=None, slug=None):
    if not slug:
        return Http404
    post = get_object_or_404(Post, name=slug)
    if request.method == 'POST':
        if 'edit' in request.POST:
            return HttpResponseRedirect(reverse('edit-post', args=(), kwargs={'post_id': post.id}))
        elif 'publish' in request.POST:
            post.published = True
            post.retracted = False
            post.save()
        elif 'retract' in request.POST:
            post.retracted = True
            post.save()
        elif 'restore' in request.POST:
            post.retracted = False
            post.save()
        elif 'delete' in request.POST:
            profile = UserProfile.objects.get(user = post.author)
            if not post.published:
                del post
            return HttpResponseRedirect(profile.get_absolute_url())
        return HttpResponseRedirect(post.get_absolute_url())
    # Check that we are allowed to view this
    if not request.user and post.published and not post.retracted: #Publically viewable to an anonymous user
        return render_to_response('cms/post.html', {'object': post, 'form': False})
    elif request.user and (request.user == post.author or request.user.is_staff):
        return render_to_response('cms/post.html', {'object': post, 'form': True},
            context_instance=RequestContext(request))
    else:
        raise Http404


@login_required
def edit_post(request, post_id=None):
    # Get the post
    post = None
    image_id = None
    if post_id:
        post = get_object_or_404(Post, id=post_id)
        if post.image:
            image_id = post.image.id
    if request.method == 'POST': # If the form has been submitted...
        if post:
            postform = PostForm(request.POST, request.FILES, prefix='post', instance=post)
        else:
            postform = PostForm(request.POST, request.FILES, prefix='post') 
        # check that the image form has been completed (look for a file path)
        if request.FILES.has_key('image-image'):
            imageform = process_image_form(request, image_id=image_id)
        else:
            imageform = None
        if postform.is_valid(): # All validation rules pass
            post = postform.save(commit=False)
            if imageform:
                post.image = imageform.cleaned_data['image']
            else:
                post.image = None
            post.date_published =  datetime.date.today()
            if not post_id:
                name = slugify(post.title)[:50]
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
                post.name = name
            post.save()
            return HttpResponseRedirect(post.get_absolute_url())
    else:
        if not post_id:
            postform = PostForm(prefix='post') # An unbound form
            imageform = ImageForm(initial=get_initial_data(request), prefix='image') # An unbound form
        else:
            post = get_object_or_404(Post, id=post_id)
            postform = PostForm(instance=post, prefix='post')
            if not post.image:
                imageform = ImageForm(initial=get_initial_data(request), prefix='image') # An unbound form
            else:
                imageform = ImageForm(post.image, initial=get_initial_data(request), prefix='image')
    if post_id:
        action = reverse('edit-post', args=(), kwargs={'post_id': post.id})
    else:
        action = reverse('new-post')
    return render_to_response('cms/edit_post.html', {'postform': postform, 'imageform': imageform, 'required': REQUIRED_FIELDS, 'action': action}, 
        context_instance=RequestContext(request))
