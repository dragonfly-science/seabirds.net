import datetime
import os
import re
import random

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, render, get_list_or_404, redirect
from django.conf import settings

from django.views.static import serve
from django.views.decorators.http import require_POST

from django.template.defaultfilters import slugify
from django.template import RequestContext

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.contrib.comments.models import Comment
from django.contrib.comments.views.moderation import perform_delete
from django.contrib import comments

from django.utils.html import strip_tags

from PIL import Image as PILImage

from bibliography.models import Reference

from categories.models import SeabirdFamily

# We don't use cms.tasks in this module, but need to import to insure signal
# listeners are in place
from cms.tasks import generate_comment_pigeons
from cms.models import Page,  Navigation, Image, Post, Listing
from cms.forms import PostForm, ImageForm, SimpleComment

from utils import get_first_available_label
from license.models import License
from profile.models import UserProfile

def page(request, name):
    context_instance=RequestContext(request)
    context_instance.autoescape=False
    if name == 'index': 
        name = 'home'
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
            twitter = False
            )
    if name in (u'home',):
        c['twitter'] = 'seabirders'
        if len(UserProfile.objects.all()) > 8:
            c['seabirders'] = random.sample(
                [profile for profile in UserProfile.objects.all() if hasattr(profile.photograph, 'file')],
                9)
        else:
            c['seabirders'] = []
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
    if request.user.is_authenticated() and (request.user == image.uploaded_by or request.user.is_staff):
        editform = True
        action = reverse('edit-image', args=(), kwargs={'image_id': image.id})
    else:
        editform = False
        action = None
    return render_to_response('cms/imagepage.html', {'image': image, 'editform': editform, 'action':action},
        context_instance=RequestContext(request))

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
    if request.user.is_authenticated():
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
    if request.method == 'POST' and request.POST.has_key('submit'): # If we are saving the form
        if not image_id:
            form = ImageForm(request.POST, request.FILES, prefix='image') # A form bound to the POST data
        else:
            image = get_object_or_404(Image, id=image_id)
            form = ImageForm(request.POST, request.FILES, prefix='image', instance=image)
        if form.is_valid(): # All validation rules pass
            image = form.save(commit=False)
            print 'Image', image_id, image
            if image:
                form.cleaned_data['image'] = image
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
                image.key = key
            if not image_id:
                if not request.user.is_authenticated():
                    raise ValidationError, 'User must be logged in'
                else:
                    image.uploaded_by = request.user
            image.save()
            form.redirect_url = image.get_absolute_url()
    else: #unbound forms
        if not image_id:
            form = ImageForm(initial=get_initial_data(request), prefix='image')
        else:
            image = get_object_or_404(Image, id=image_id)
            #form = ImageForm(initial=get_initial_data(request), prefix='image', instance=image) 
            form = ImageForm(prefix='image', instance=image)
    return form

REQUIRED_FIELDS = ('image', 'title', 'owner', 'text',)
@login_required
def edit_image(request, image_id=None):
    imageform = process_image_form(request, image_id=image_id)
    if hasattr(imageform, 'redirect_url'):
        return HttpResponseRedirect(imageform.redirect_url)
    else:
        return render_to_response('cms/edit_image.html', 
            {'imageform': imageform, 'required': REQUIRED_FIELDS}, 
            context_instance=RequestContext(request)
            )

# Process comments
@login_required
def process_comment(request, commentform, post):
    try:
        comment = Comment.objects.get(id=commentform.cleaned_data.get('id', None))
    except Comment.DoesNotExist:
        comment = Comment()
    comment.content_object = post
    comment.site = Site.objects.get_current()
    comment.user = request.user
    try:
        profile = UserProfile.objects.get(user = request.user)
        comment.user_url = profile.get_absolute_url()
    except UserProfile.DoesNotExist:
        pass
    comment.comment = strip_tags(commentform.cleaned_data['comment'])
    comment.submit_date = datetime.datetime.now()
    comment.ip_address = request.META['REMOTE_ADDR']
    comment.is_public = True
    comment.is_removed = False
    comment.save()
    return comment

@require_POST
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(comments.get_model(), pk=comment_id)
    if comment.user == request.user:
        next_page = comment.content_object.get_absolute_url()
        perform_delete(request, comment)
        return redirect(next_page)
    else:
        raise Http404

# View an individual post
def individual_post(request, year=None, month=None, day=None, slug=None):
    if not slug:
        return Http404
    post = get_object_or_404(Post, name=slug)
    if request.method == 'POST' and request.user.is_authenticated():
        if 'edit_comment' in request.POST or 'delete_comment' in request.POST:
            commentform = SimpleComment(request.POST, prefix='comment')
            comment_id = commentform.data.get('comment-id', None)
            if 'edit_comment' in request.POST:
                if commentform.is_valid():
                    comment = process_comment(request, commentform, post)
                    comment_id = comment.id
                if comment_id:
                    anchor = '#comment-%s'%comment_id
                else:
                    anchor = ''
                return HttpResponseRedirect(post.get_absolute_url() + anchor) 
            else:
                try:
                    Comment.objects.get(id=comment_id).delete()
                except Comment.DoesNotExist:
                    pass
        elif 'edit' in request.POST:
            return HttpResponseRedirect(reverse('edit-post', args=(), kwargs={'post_id': post.id}))
        elif 'publish' in request.POST or 'restore' in request.POST:
            post.published = True
            if request.user.is_authenticated() and request.user.profile.get().is_moderator:
                post._notify_moderator = False
            else:
                post._notify_moderator = True
            post.save()
        elif 'retract' in request.POST:
            post.published = False
            post.save()
        elif 'delete' in request.POST:
            profile = UserProfile.objects.get(user = post.author)
            if not post.published:
                del post
            return HttpResponseRedirect(profile.get_absolute_url())
        return HttpResponseRedirect(post.get_absolute_url())
    # Logic to decide whether or not to allow comment to be added
    add_comment =  post.enable_comments and post.published and request.user.is_authenticated()

    # Is there an existing comment by this user that should be edited or should we get a new one?
    # TODO: How is the below supposed to work? Currently users can just add multiple comments
    commentset = []
    if request.user.is_authenticated():
        commentset = Comment.objects.for_model(Post).filter(object_pk=post.id).filter(user=request.user)
        commentset = commentset.filter(submit_date__gt=datetime.datetime.now() - datetime.timedelta(seconds=60*10)).order_by('-submit_date')[0:1]
    if commentset:
        latest_comment = commentset[0]
        initial = {'comment': latest_comment.comment, 'id': latest_comment.id }
    else:
        latest_comment = None
        initial = None
    ######
    
    # Decide whether to allow editing of the Post form
    if request.user.is_authenticated() and (request.user == post.author or request.user.is_staff or \
            request.user.profile.get().is_moderator):
        return render(request, 'cms/post.html', {
            'object': post,
            'form': True,
            'add_comment': add_comment,
            'commentform': SimpleComment(prefix='comment', initial=initial)
            }
            )
    elif request.user.is_authenticated():
        # Decide whether to allow comments on the Post
        return render(request, 'cms/post.html', {
            'object': post,
            'form': False,
            'add_comment': add_comment,
            'commentform': SimpleComment(prefix='comment', initial=initial)
            }
            )
    elif post.date_published:
        # Or it is publicly viewable
        navigation = get_base_navigation(request)
        return render(request, 'cms/post.html', {
            'object': post,
            'form': False,
            'navigation': navigation['navigation'],
            })
    else:
        # Or we shouldn't know it exists
        raise Http404

@login_required
def edit_post(request, post_id=None):
    post = None
    image_id = None
    hasimage = False
    if post_id:
        # If post_id specified we are editing an existing post.
        post = get_object_or_404(Post, id=post_id)
        if post.image:
            image_id = post.image.id
    if request.method == 'POST': # If the form has been submitted...
        if post:
            postform = PostForm(request.POST, request.FILES, prefix='post', instance=post)
        else:
            postform = PostForm(request.POST, request.FILES, prefix='post') 
        if (post and post.image) or request.FILES.has_key('image-image'):
            imageform = process_image_form(request, image_id=image_id)
        else:
            imageform = None
        if postform.is_valid(): # All validation rules pass
            post = postform.save(commit=False)
            if imageform and imageform.is_valid():
                post.image = imageform.cleaned_data['image']
            else:
                post.image = None
            if not post_id:
                name = slugify(post.title)[:50]
                post.name = get_first_available_label(Post, name, 'name')
                if not post.author:
                    post.author = request.user
                if request.user.is_authenticated() and request.user.profile.get().is_moderator:
                    post._notify_moderator = False
                else:
                    post._notify_moderator = True
            post.save()
            return HttpResponseRedirect(post.get_absolute_url())
    else:
        if not post_id:
            # unbound forms
            postform = PostForm(prefix='post')
            imageform = ImageForm(initial=get_initial_data(request), prefix='image')
        else:
            post = get_object_or_404(Post, id=post_id)
            postform = PostForm(instance=post, prefix='post')
            if not post.image:
                imageform = ImageForm(initial=get_initial_data(request), prefix='image') # An unbound form
            else:
                imageform = ImageForm(instance=post.image, initial=get_initial_data(request), prefix='image')
                hasimage = True
    if post_id:
        action = reverse('edit-post', args=(), kwargs={'post_id': post.id})
    else:
        action = reverse('new-post')
    return render_to_response('cms/edit_post.html', {
            'postform': postform,
            'imageform': imageform, 
            'required': REQUIRED_FIELDS,
            'action': action,
            'hasimage': hasimage}, 
        context_instance=RequestContext(request))

def jobs(request):
    max_days = request.GET.get('max_days_since_creation', None)
    try:
       max_days = int(max_days)
    except (TypeError, ValueError):
        return redirect('/jobs/?max_days_since_creation=90')
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=max_days)
    target_time = now - delta
    
    jobs = Post.objects.filter(date_created__gt=target_time, published=True, listing=Listing.objects.get(key='jobs'))
    ctx = RequestContext(request)
    return render_to_response('cms/jobs.html', dict(jobs=jobs, max_days=max_days), context_instance=ctx)

def gallery(request, seabird_family=None):
    if seabird_family:
        try:
            seabird_family = seabird_family.replace('-', ' ')
            seabird_family = SeabirdFamily.objects.get(choice__iexact=seabird_family)
            images = seabird_family.images.all()
        except SeabirdFamily.DoesNotExist:
            raise Http404
    else:
        images = Image.objects.filter(seabird_families__in=SeabirdFamily.objects.all())
    random.shuffle(images)
    seabird_families = SeabirdFamily.objects.all()
    d = dict(images=images, seabird_family=seabird_family, seabird_families=seabird_families)
    return render_to_response('cms/gallery.html', d, RequestContext(request))
