import types
import os
import re
import logging

from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, get_list_or_404
from django.template import RequestContext
from django.conf import settings
from django.views.static import serve

from PIL import Image as PILImage

from cms.models import Page, Person, File, Navigation
from bibliography.models import Reference
from django.conf import settings

def top(request, name):
    context_instance=RequestContext(request)
    context_instance.autoescape=False
    if name == 'index': 
        name = 'home'
        fullpath = ""
    else:
        fullpath = name
    name = os.path.basename(name)
    page =  get_object_or_404(Page, name = name)
    navigation = page.get_absolute_url().split(settings.SITE_URL)[1]
    level = page
    while level.parent:
        if Navigation.objects.filter(url = navigation):
            break
        level = level.parent
        navigation = level.get_absolute_url().split(settings.SITE_URL)[1]
    c = dict(
            page = page, 
            navigation = get_navigation(navigation),
            )
    return render_to_response('index.html', c, context_instance)


def people(request):
    persons = Person.objects.all().order_by('order')
    page = Page.objects.get(name = 'people')
    return render_to_response('people.html', dict(person_list=persons, page=page, navigation=get_navigation('/people.html')),
        RequestContext(request))
		
def image(request, filename):
    path = os.path.join(settings.MEDIA_ROOT, 'images', 'cache', filename)
    if os.path.exists(path):
        return serve(request, filename, document_root=os.path.join(settings.MEDIA_ROOT, 'images', 'cache'))

    # make the image if we don't already have it
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

