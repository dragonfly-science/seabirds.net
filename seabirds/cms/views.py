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

from cms.models import Page, File, Navigation, Image
from cms.forms import PostForm, ImageForm
from bibliography.models import Reference
from license.models import License
from profile.models import UserProfile

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

def imagepage(request, key):
    image = get_object_or_404(Image, key=key)
    return render_to_response('cms/imagepage.html', {'image': image})

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

@login_required
def edit_post(request):
    if request.method == 'POST': # If the form has been submitted...
        form = PostForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            form.save()
            return HttpResponseRedirect(reverse('individual-post', args=(), kwargs={
            'year': form.cleaned_data['date_published'].year,
            'month': form.cleaned_data['date_published'].strftime('%m'), 
            'day': form.cleaned_data['date_published'].strftime('%d'), 
            'slug': form.cleaned_data['name']}))
    else:
        form = PostForm() # An unbound form
    return render_to_response('cms/edit_post.html', {'form': form,}, 
        context_instance=RequestContext(request))



@login_required
def edit_image(request):
    if request.method == 'POST': # If the form has been submitted...
        form = ImageForm(request.POST, request.FILES) # A form bound to the POST data
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
            new_image.key = key
            if not request.user:
                raise ValidationError, 'User must be logged in'
            else:
                new_image.uploaded_by = request.user
            new_image.save()
            return HttpResponseRedirect(new_image.get_absolute_url())
    else:
        initial = {'owner': '%s %s'%(request.user.first_name.capitalize(), request.user.last_name.capitalize()),
            'license': License.objects.get(name='BY-SA')}
        try:
            profile = UserProfile.objects.get(user = request.user)
            initial['owner_url'] = settings.SITE_URL + reverse('profiles_profile_detail', 
                args=(), 
                kwargs={'username': request.user.username})
        except UserProfile.DoesNotExist:
            pass
        form = ImageForm(initial=initial) # An unbound form
    return render_to_response('cms/edit_image.html', {'form': form,}, context_instance=RequestContext(request))


