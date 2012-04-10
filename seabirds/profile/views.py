from urllib import urlencode

from profiles.views import profile_detail
from profiles import utils
from django.http import Http404, HttpResponseRedirect
from django.views.generic.list_detail import object_list
from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth.decorators import login_required

from django_countries.countries import COUNTRIES

from categories.models import SeabirdFamily
from profile.models import UserProfile, CollaborationChoice

@login_required
def profile(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/petrel/%s/' % request.user.username)
    else:
        raise Http404

COUNTRIES = dict(COUNTRIES)

@login_required
def custom_list(request, template_name='profiles/profile_list.html', **kwargs):
    """
    A list of user profiles, based on code from django-profiles
    https://bitbucket.org/ubernostrum/django-profiles
    """
    profile_model = utils.get_profile_model()
    queryset = profile_model._default_manager.all()
    birds_queryset = profile_model._default_manager.all()
    countries_queryset = profile_model._default_manager.all()
    collaboration_queryset = utils.get_collaboration_choice_model()._default_manager.all()

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
        extra_context['country'] =  unicode(COUNTRIES[country])
        extra_context['country_tag'] =  country

    collab_choice = request.GET.get('r', None)
    if collab_choice:
        choice = CollaborationChoice.objects.get(id=collab_choice)
        queryset = queryset.filter(collaboration_choices=choice)
        collaboration_queryset = profile_model._default_manage.all()
        extra_content['collaboration_choice'] = collaborator_choice_id

    kwargs['queryset'] = queryset.order_by('user__last_name')
    extra_context['profile_birds'] = SeabirdFamily.objects.filter(profiles__in=UserProfile.objects.all()).distinct()
    countries = list(set([(u.country.name, u.country) for u in UserProfile.objects.all()]))
    extra_context['profile_countries'] =  [c[1] for c in sorted(countries)]
    extra_context['profile_collaboration_choices'] = CollaborationChoice.objects.filter(p)

    def _record_details(r, queryset, record_type, activetest, country=None, seabird=None, collab_choice=None):
        query_string_params = {}
        r.tag = "a"
        href = "/petrel/"
        r.records = len(queryset.filter(**{record_type: r}))
        classes = ["badge"]
        if activetest(r.name) == extra_context['country']:
            classes.append("activebadge")
        elif r.records > 0:
            classes.append("linkbadge")
        else:
           classes.extend(["smallbadge", "inactivebadge"])
           r.tag = "span"

        if country:
            query_string_params['c'] = country
        if seabird:
            query_string_params['s'] = seabird[:3].lower()
        if collab_choice:
            query_string_params['r'] = collab_choice

        query_string = urlencode(query_string_params)
        if query_string:
            href = href + '?' + query_string
            r.href = 'href="{0}"'.format(href)
        if r.records > 0:
            r.href = ""
        pc.classes = " ".join(classes)
        return pc

    def birds_activetest(bird_name):
        return bird_name == extra_context['seabird']

    def country_activetest(country_name):
        return country_name == extra_context['country']

    def collab_choice_activetest(collab_choice_id):
        try:
            c = CollaborationChoice.objects.get(pk=collab_choice_id)
            return c.label == extra_context['collaboration_choice']
        except CollaborationChoice.DoesNotExist:
            return False

    for pb in extra_context['profile_birds']:
        pb = _record_details(pb, birds_queryset, 'birds', birds_activetest, country, seabird, collab_choice)
    for pc in extra_context['profile_countries']:
        pc = _record_details(pc, countries_queryset, 'country', country_activetest, country, seabird, collab_choice)
    for pr in extra_context['profile_collaboration_choices']:
        pr = _record_details(pr, collaboration_queryset, 'collaboration_choice', collab_choice_activetest, country, seabird, collab_choice)
    return object_list(request, template_name=template_name, extra_context=extra_context, **kwargs)
