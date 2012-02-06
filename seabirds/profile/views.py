from profiles.views import profile_detail
from django.http import Http404, HttpResponseRedirect

def profile(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/petrel/%s/' % request.user.username)
    else:
        raise Http404

