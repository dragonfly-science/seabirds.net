from profiles.views import profile_detail
from profiles import utils
from django.http import Http404, HttpResponseRedirect
from django.views.generic.list_detail import object_list
from django.core.exceptions import MultipleObjectsReturned

from django_countries.countries import COUNTRIES

from categories.models import SeabirdFamily
from profile.models import UserProfile

def profile(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/petrel/%s/' % request.user.username)
    else:
        raise Http404

ORDER_KEYS = {'fn': 'user__first_name', 'ln':'user__last_name', 'co':'country', 'in':'institution'}
COUNTRIES = dict(COUNTRIES)
def custom_list(request, template_name='profiles/profile_list.html', **kwargs):
    """
    A list of user profiles, based on code from django-profiles
    https://bitbucket.org/ubernostrum/django-profiles
    """
    profile_model = utils.get_profile_model()
    queryset = profile_model._default_manager.all()
    extra_context = {'seabird': None, 'country':None, 'order_key': ORDER_KEYS['ln'], 'order': ''}

    seabird = request.GET.get('s', None)
    if seabird is not None:
        try:
            bird = SeabirdFamily.objects.get(choice__istartswith = seabird)
            queryset = queryset.filter(seabirds = bird)
            extra_context['seabird'] =  bird
        except (SeabirdFamily.DoesNotExist, MultipleObjectsReturned):
            pass
    
    country = request.GET.get('c', None)
    if country is not None and country in COUNTRIES.keys():
        queryset = queryset.filter(country=country)
        extra_context['country'] =  unicode(COUNTRIES[country])
        extra_context['country_tag'] =  country

    key = request.GET.get('o', None)
    if (key in ORDER_KEYS.keys()) or (key in ['-' + k for k in ORDER_KEYS.keys()]):
        if key.startswith('-'):
            order = '-'
            order_key = ORDER_KEYS[key[1:]]
        else:
            order = ''
            order_key = ORDER_KEYS[key]
        extra_context['order'] = order
        extra_context['order_key'] = order_key
    else:
        order = extra_context['order']
        order_key = extra_context['order_key']    
    queryset = queryset.order_by(order + order_key)
    kwargs['queryset'] = queryset
    extra_context['profile_birds'] = SeabirdFamily.objects.filter(profiles__in=UserProfile.objects.all()).distinct()
    extra_context['profile_countries'] = sorted(list(set([u.country for u in UserProfile.objects.all()])))
    return object_list(request, template_name=template_name, extra_context=extra_context, **kwargs)
