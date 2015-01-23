from urllib import urlencode

from profiles import utils
from django.http import Http404, HttpResponseRedirect
from django.utils.encoding import force_unicode
from django.views.generic.list_detail import object_list
from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import logout
from django.core.urlresolvers import reverse

from django_countries import countries as COUNTRIES

from categories.models import SeabirdFamily
from profile.models import UserProfile, CollaborationChoice

@login_required
def profile(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/petrel/%s/' % request.user.username)
    else:
        raise Http404

@require_POST
def delete_profile(request):
    if request.user.is_authenticated():
        request.user.is_active = False
        request.user.save()
        logout(request)
        return HttpResponseRedirect(reverse('home'))


COUNTRIES_REVERSED = dict((force_unicode(c[1]), c[0]) for c in COUNTRIES)
COUNTRIES = dict((c[0], force_unicode(c[1])) for c in COUNTRIES)

def custom_list(request, template_name='profiles/profile_list.html', **kwargs):
    """
    A list of user profiles, based on code from django-profiles
    https://bitbucket.org/ubernostrum/django-profiles
    """
    profile_model = utils.get_profile_model()
    queryset = profile_model._default_manager.filter(user__is_active=True)
    birds_queryset = profile_model._default_manager.all()
    countries_queryset = profile_model._default_manager.all()
    collaboration_queryset = utils.get_model('profile', 'collaborationchoice')._default_manager.all()
    extra_context = {'seabird': None, 'country':None, 'country_tag':None, 'collaboration_choice':None}

    seabird = request.GET.get('s', None)
    if seabird is not None:
        try:
            bird = SeabirdFamily.objects.get(choice__istartswith = seabird)
            queryset = queryset.filter(seabirds = bird)
            countries_queryset = countries_queryset.filter(seabirds = bird)
            extra_context['seabird'] =  bird
        except (SeabirdFamily.DoesNotExist, MultipleObjectsReturned):
            pass

    country = request.GET.get('c', None)
    if country is not None and country in COUNTRIES.keys():
        queryset = queryset.filter(country=country)
        birds_queryset = birds_queryset.filter(country=country)
        extra_context['country'] = unicode(COUNTRIES[country])
        extra_context['country_tag'] =  country

    collab_choice = request.GET.get('r', None)
    if collab_choice:
        choice = CollaborationChoice.objects.get(id=collab_choice)
        queryset = queryset.filter(collaboration_choices=choice)
        extra_context['collaboration_choice'] = int(collab_choice)

    kwargs['queryset'] = queryset.order_by('user__last_name')
    extra_context['profile_birds'] = SeabirdFamily.objects.filter(profiles__in=UserProfile.objects.all()).distinct()
    countries = list(set([(u.country.name, u.country) for u in UserProfile.objects.all()]))
    extra_context['profile_countries'] =  [c[1] for c in sorted(countries)]
    extra_context['profile_collaboration_choices'] = CollaborationChoice.objects.all()

    def _record_details(r, filter_queryset, record_type, activetest, country=None, seabird=None, collab_choice=None):
        query_string_params = {}
        r.tag = "a"
        href = "/petrel/"
        classes = ["badge"]
        if record_type == 'seabirds':
            name_attr = 'choice'
            r.records = len(filter_queryset.filter(**{record_type: r}))
        elif record_type == 'country':
            name_attr = 'name'
            r.records = len(filter_queryset.filter(**{record_type: r}))
        elif record_type == 'collaboration_choice':
            name_attr = 'id'
            r.records = len(filter_queryset.filter(userprofile__in=queryset))
        else:
            raise ValueError

        name  = getattr(r, name_attr)
        active = activetest(name)
        if active:
            classes.append("activebadge")
        elif r.records > 0:
            classes.append("linkbadge")
        else:
           classes.extend(["smallbadge", "inactivebadge"])
           r.tag = "span"

        if active:
	    if country and not record_type == 'country':
                query_string_params['c'] = country
            if seabird and not record_type == 'seabirds':
	        query_string_params['s'] = seabird[:3].lower()
            if collab_choice and not record_type == 'collaboration_choice':
                query_string_params['r'] = collab_choice
        elif record_type == 'country':
            query_string_params['c'] = force_unicode(name)
            if seabird:
	        query_string_params['s'] = seabird[:3].lower()
            if collab_choice:
                query_string_params['r'] = collab_choice
        elif record_type == 'seabirds':
	    query_string_params['s'] = name[:3].lower()
            if country:
                query_string_params['c'] = force_unicode(country)
            if collab_choice:
                query_string_params['r'] = collab_choice
        elif record_type == 'collaboration_choice':
            query_string_params['r'] = name
            if country:
                query_string_params['c'] = force_unicode(country)
            if seabird:
	        query_string_params['s'] = seabird[:3].lower()

        try:
            c = query_string_params['c']
            if c and len(c) != 2:
                query_string_params['c'] = COUNTRIES_REVERSED[c]
        except KeyError:
            pass
        query_string = urlencode(dict((k,unicode(v).encode('utf-8', 'xmlcharreplace')) for k,v in query_string_params.iteritems()))
        if query_string:
            href = href + '?' + query_string
            href = 'href="{0}"'.format(href)
        elif r.records > 0:
            href = 'href="/petrel/"'
        else:
            href = ''
        r.href = href
        r.classes = " ".join(classes)
        return r

    def birds_activetest(bird_name):
        try:
            return bird_name == extra_context['seabird'].choice
        except AttributeError:
            return False

    def country_activetest(country_name):
        try:
            return country_name == force_unicode(extra_context['country'].encode('utf-7', 'xmlcharreplace'))
        except AttributeError:
            return False

    def collab_choice_activetest(collab_choice_id):
        try:
            c1 = CollaborationChoice.objects.get(pk=collab_choice_id).pk
            c2 = extra_context['collaboration_choice']
            return c1 == c2
        except CollaborationChoice.DoesNotExist:
            return False

    for pb in extra_context['profile_birds']:
        pb = _record_details(pb, birds_queryset, 'seabirds', birds_activetest, country, seabird, collab_choice)
    for pc in extra_context['profile_countries']:
        pc = _record_details(pc, countries_queryset, 'country', country_activetest, country, seabird, collab_choice)
    for pr in extra_context['profile_collaboration_choices']:
        pr = _record_details(pr, collaboration_queryset, 'collaboration_choice', collab_choice_activetest, country, seabird, collab_choice)
    return object_list(request, template_name=template_name, extra_context=extra_context, **kwargs)
