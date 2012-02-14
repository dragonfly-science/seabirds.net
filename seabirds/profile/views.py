from profiles.views import profile_detail
from profiles import utils
from django.http import Http404, HttpResponseRedirect
from django.views.generic.list_detail import object_list
from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth.decorators import login_required

from django_countries.countries import COUNTRIES

from categories.models import SeabirdFamily
from profile.models import UserProfile

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
    extra_context = {'seabird': None, 'country':None}

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

    kwargs['queryset'] = queryset.order_by('user__last_name')
    extra_context['profile_birds'] = SeabirdFamily.objects.filter(profiles__in=UserProfile.objects.all()).distinct()
    countries = list(set([(u.country.name, u.country) for u in UserProfile.objects.all()]))
    extra_context['profile_countries'] =  [c[1] for c in sorted(countries)]
    for pb in extra_context['profile_birds']:
        pb.records = len(birds_queryset.filter(seabirds = pb))
    for pc in extra_context['profile_countries']:
        pc.records = len(countries_queryset.filter(country = pc))
    return object_list(request, template_name=template_name, extra_context=extra_context, **kwargs)
