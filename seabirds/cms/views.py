import datetime
import os
import re
import random

from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response, render, get_list_or_404, redirect
from django.conf import settings

from django.views.static import serve
from django.views.decorators.http import require_POST

from django.template.defaultfilters import slugify
from django.template import RequestContext

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.contrib.comments.views.moderation import perform_delete
from django.contrib.contenttypes.models import ContentType
from django.contrib import comments

from django.utils.html import strip_tags

from PIL import Image as PILImage

from bibliography.models import Reference
from pigeonpost.models import Pigeon
from categories.models import SeabirdFamily

# We don't use cms.tasks in this module, but need to import to insure signal
# listeners are in place
from cms.tasks import generate_comment_pigeons

from cms.models import Page,  Navigation, Image, Post, Listing
from cms.forms import PostForm, ImageForm, SimpleComment

from utils import get_first_available_label
from license.models import License
from profile.models import UserProfile

from django.views.generic.dates import ArchiveIndexView
from django.views.generic import TemplateView


class PostArchiveView(ArchiveIndexView):
    model = Post
    allow_empty = True # Don't 404 on an empty queryset
    # This would show 10 discussions at a time, but we have not added pagination to
    # our templates yet
    #paginate_by = 10
    
    def get(self, request, *args, **kwargs):
        """
        Taken from django.views.generic.dates.BaseDateListView
        """
        listing = kwargs.get('listing', None)

        u = request.user if request.user.is_authenticated else None
        self.viewable_listings = Listing.objects.user_readable(u)

        self.date_list, self.object_list, extra_context = self.get_dated_items(request, listing)
        if listing is None:
            # On general recent posts page, we limit to the last couple of months or so
            today = datetime.date.today()
            two_months_ago = today- datetime.timedelta(days=2*31)
            self.object_list = self.object_list.filter(**{self.get_date_field() + '__gt':two_months_ago})
        context = self.get_context_data(object_list=self.object_list,
                                        date_list=self.date_list)
        context.update(extra_context)
        context.update({"twitter" : "seabirders"})
        context.update({'listings': self.viewable_listings})
        return self.render_to_response(context)

    def get_dated_items(self, request, listing):
        """
        Return (date_list, items, extra_context) for this request.

        Taken from django.views.generic.dates.BaseArchiveIndexView

        Extended to take account of user and what posts they are allowed to see,
        and allows viewing posts in a given listing.
        """
        if listing:
            listing_object = get_object_or_404(Listing, key=listing)
            if listing_object not in self.viewable_listings:
                raise Http404
            qs = self.get_dated_queryset(listing=listing_object)
        else:
            listing_object = None
            qs = self.get_dated_queryset(listing__in=self.viewable_listings)

        date_list = self.get_date_list(qs, 'year')

        if date_list:
            object_list = qs.order_by('-' + self.get_date_field())
        else:
            object_list = qs.none()
        return (date_list, object_list, {'listing': listing_object })


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
            navigation = get_navigation(request, navigation),
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

def image(request, filename):
    # Return the file if it is in the images directory
    if os.path.exists(os.path.join(settings.MEDIA_ROOT, 'images', filename)):
        return serve(request, filename, document_root=os.path.join(settings.MEDIA_ROOT, 'images'))
    # If not then look for it in the cache directory
    path = os.path.join(settings.MEDIA_ROOT, 'images', 'cache', filename)
    if os.path.exists(path):
        return serve(request, filename, document_root=os.path.join(settings.MEDIA_ROOT, 'images', 'cache'))

    # If it isn't there, then make the image
    # look for an image that is the same without size info
    m = re.search('-(\d+)x(\d+)', filename)
    if not m:
        raise Http404
    origname = re.sub('-\d+x\d+', '', filename)
    origpath = os.path.join(settings.MEDIA_ROOT, 'images', origname)
    if not os.path.exists(origpath):
        raise Http404
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
            navigation = get_navigation(request, '/publications.html'),
        ), RequestContext(request))

def get_navigation(request, url, staff=False):
    """
    Create the navigation data structure that is used for rendering
    the navigation sidebar.

    There are parts in this which are a bit of hack to allow the 
    "Discussion" entry to have Listing objects as it's children.
    """
    try:
        home = Navigation.objects.root_nodes()[0]
    except IndexError:
        return []
    selected_listing = None
    u = request.user if request.user.is_authenticated() else None
    try:
        selected_node = Navigation.objects.get(url=url)
        key = None
    except Navigation.DoesNotExist:
        try:
            key = os.path.split(url)[-1]
            # TODO: not too sure why we are getting "selected_listing" since
            # it doesn't seem like it's used elsewhere...
            selected_listing = Listing.objects.get(key=key)
            if not staff and not selected_listing.can_user_read(u):
                selected_listing = None
            selected_node = Navigation.objects.get(name='Discussion')
        except Listing.DoesNotExist:
            selected_node = home
    active_nodes = [selected_node] + list(selected_node.get_ancestors())
    links = []
    for child in home.get_children():
        if child == selected_node:
            if selected_node.name == 'Discussion':
                grandchildren = Listing.objects.all()
                if not staff:
                    grandchildren = [ g for g in grandchildren if g.can_user_read(u) ]
                sublinks = []
                for g in grandchildren:
                    sublinks.append((g, key and g.key == key, []))
                links.append((child, key is None, sublinks))
            else:
                grandchildren = child.get_children()
                sublinks = [(g, False, []) for g in grandchildren]
                links.append((child, True, sublinks))
        elif child in active_nodes:
            grandchildren = child.get_children()
            sublinks = []
            for g in grandchildren:
                if g in active_nodes:
                    sublinks.append((g, True, []))
                else:
                    sublinks.append((g, False, []))
            links.append((child, False, sublinks))
        else:
            links.append((child, False, []))
    return links
            
def get_base_navigation(request):
    show_staff = request.user.is_authenticated() and request.user.is_staff
    return {'navigation': get_navigation(request, request.path, show_staff)}

def get_initial_image_data(request):
    if request.user.is_authenticated():
        initial = { 'owner': '%s %s' % (
                        request.user.first_name.capitalize(),
                        request.user.last_name.capitalize()
                        ), 
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
    if request.method == 'POST':
        if not image_id:
            # form bound to the POST data
            form = ImageForm(request.POST, request.FILES, prefix='image')
        else:
            image = get_object_or_404(Image, id=image_id)
            form = ImageForm(request.POST, request.FILES, prefix='image', instance=image)
        if form.is_valid(): # All validation rules pass
            image = form.save(commit=False)
            if image:
                form.cleaned_data['image'] = image
            # Get the key
            if not image_id:
                key = get_first_available_label(Image, slugify(form.cleaned_data['title']), 'key')
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
            form = ImageForm(initial=get_initial_image_data(request), prefix='image')
        else:
            image = get_object_or_404(Image, id=image_id)
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
    C = comments.get_model()
    try:
        comment = C.objects.get(id=commentform.cleaned_data.get('id', None))
        if not comment.can_be_edited_by(request.user):
            import pdb; pdb.set_trace()
            raise PermissionDenied
    except C.DoesNotExist:
        if not post.can_user_comment(request.user):
            raise PermissionDenied
        comment = C()
        comment.content_object = post
        comment.site = Site.objects.get_current()
        comment.user = request.user
        try:
            profile = UserProfile.objects.get(user = request.user)
            comment.user_url = profile.get_absolute_url()
        except UserProfile.DoesNotExist:
            pass
        comment.submit_date = datetime.datetime.now()
        comment.ip_address = request.META['REMOTE_ADDR']
        comment.is_public = True
        comment.is_removed = False
    comment.comment = strip_tags(commentform.cleaned_data['comment'])
    comment.save()
    return comment

def individual_post(request, year=None, month=None, day=None, slug=None):
    """ View a post and handle dispatching various POST requests to the url """
    if not slug:
        raise Http404
    post = get_object_or_404(Post, name=slug)

    # Only authenticated users are allowed to POST any data
    if request.method == 'POST' and request.user.is_authenticated():
        if 'edit_comment' in request.POST or 'delete_comment' in request.POST:
            commentform = SimpleComment(request.POST, prefix='comment')
            comment_id = commentform.data.get('comment-id', None)
            if 'edit_comment' in request.POST:
                if commentform.is_valid():
                    comment = process_comment(request, commentform, post)
                    comment_id = comment.id
                if comment_id:
                    anchor = '#c%s' % comment_id
                else:
                    anchor = ''
                return HttpResponseRedirect(post.get_absolute_url() + anchor) 
            else:
                try:
                    c = comments.get_model().objects.get(id=comment_id)
                    if c.can_be_edited_by(request.user):
                        c.is_removed = True
                        # Delete any pigeons waiting to be sent out
                        c_model = ContentType.objects.get_for_model(c)
                        Pigeon.objects.filter(source_id=c.id,
                                source_content_type=c_model, to_send=True).delete()
                        c.save()
                    else:
                        raise PermissionDenied
                except comments.get_model().DoesNotExist:
                    raise Http404
        else:
            if not post.can_user_modify(request.user):
                raise PermissionDenied

            if 'edit' in request.POST:
                return HttpResponseRedirect(reverse('edit-post', args=(), kwargs={'post_id': post.id}))
            elif 'publish' in request.POST or 'restore' in request.POST:
                post.published = True
                post.save()
            elif 'retract' in request.POST:
                post.published = False
                post.save()
            elif 'delete' in request.POST:
                listing = post.listing
                if not post.published:
                    post.delete()
                return HttpResponseRedirect(listing.get_absolute_url())
            return HttpResponseRedirect(post.get_absolute_url())

    # Decide whether to allow editing of the Post form
    if post.can_user_modify(request.user):
        # If a user can modify a post, we assume they can comment
        return render(request, 'cms/post.html', {
            'object': post,
            'form': True,
            'add_comment': True,
            }
            )
    elif post.can_user_comment(request.user):
        # We only provide a comment form
        return render(request, 'cms/post.html', {
            'object': post,
            'form': False,
            'add_comment': True,
            }
            )
    elif post.date_published and (post.listing.can_user_read(request.user)):
        # We show the post if it published, but provide no forms
        navigation = get_base_navigation(request)
        return render(request, 'cms/post.html', {
            'object': post,
            'form': False,
            'add_comment': False,
            'navigation': navigation['navigation'],
            })
    else:
        # Otherwise we don't know about it
        raise Http404

@login_required
def edit_post(request, post_id=None):
    post = None
    image_id = None
    hasimage = False

    # If post_id specified we are editing an existing post.
    if post_id:
        post = get_object_or_404(Post, id=post_id)
        if not post.can_user_modify(request.user):
            raise PermissionDenied
        if post.image:
            image_id = post.image.id

    # If the form has been submitted...
    if request.method == 'POST':
        # Get a postform
        if post:
            postform = PostForm(request.user, request.POST, request.FILES, prefix='post', instance=post)
        else:
            postform = PostForm(request.user, request.POST, request.FILES, prefix='post') 
        # Get any attached image
        if (post and post.image) or request.FILES.has_key('image-image'):
            imageform = process_image_form(request, image_id=image_id)
        else:
            imageform = None

        # All validation rules pass
        # Via the post form, this also ensures the listing specified is allowed
        # and prevents users from posting to lists they don't have permission for
        if postform.is_valid():
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
            post.save()
            return HttpResponseRedirect(post.get_absolute_url())
    else:
        if not post_id:
            # unbound forms
            postform = PostForm(request.user, prefix='post')
            imageform = ImageForm(initial=get_initial_image_data(request), prefix='image')
        else:
            postform = PostForm(request.user, instance=post, prefix='post')
            if not post.image:
                # unbound form
                imageform = ImageForm(initial=get_initial_image_data(request), prefix='image')
            else:
                imageform = ImageForm(instance=post.image, initial=get_initial_image_data(request), prefix='image')
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
