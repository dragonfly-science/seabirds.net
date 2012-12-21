import logging

from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.views import logout
from django.contrib.auth.decorators import login_required

from account.forms import *


@login_required
def edit_profile_mailing_list(request):
    """
    This is a hack to allow a user to get passed a hash fragment identifier,
    even if they are not logged in (e.g. they have to use ?next= on login.

    We need this because hash fragments are not sent to the server, so get lost
    after the login.

    This view forces login first, and THEN redirects to a url with fragment identifier.
    """
    return HttpResponseRedirect('/petrel/edit#mailing_lists')

def profile(request):
    """The profile page checks to see where you should go next"""

    perms = request.user.get_all_permissions()
    if not [ p for p in perms if 'website' in p ]:
        return logout(request, template_name='account/permission_denied.html')
    
    return HttpResponseRedirect('/')

# login not required
@csrf_protect
def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save();
            return HttpResponseRedirect(reverse('account.views.password_reset_submitted'))
    else:
        form = PasswordResetForm()

    return render_to_response('account/password_reset.html', 
            { 'form': form },
            context_instance=RequestContext(request))

def password_reset_submitted(request):
    return render_to_response('account/password_reset_submitted.html',
            {'support_email' : settings.SUPPORT_EMAIL},
            context_instance=RequestContext(request))

# login not required
@csrf_protect
def password_reset_confirm(request):
    verification_key = None
    email_address = None

    if 'verification_key' in request.GET and request.GET['verification_key']:
        verification_key = request.GET['verification_key']

    if 'email_address' in request.GET and request.GET['email_address']:
        email_address = request.GET['email_address']

    # Note: all validation errors return the same error message to
    # avoid leaking information as to the existence or not of
    # particular email addresses on the system

    if not verification_key or not email_address:
        return render_to_response('account/reset_invalidparams.html',
                                  context_instance=RequestContext(request))

    if len(verification_key) < 64 or len(verification_key) > 64 or len(email_address) < 3:
        return render_to_response('account/reset_invalidparams.html',
                                  context_instance=RequestContext(request))

    try:
        logging.debug("Trying to look up email address %s" % email_address)
        user = User.objects.get(email=email_address)
    except User.DoesNotExist:
        logging.debug("Not found")
        return render_to_response('account/reset_invalidparams.html',
                                  context_instance=RequestContext(request))
    
    expected_key = password_reset_key(user)

    if verification_key != expected_key:
        return render_to_response('account/reset_invalidparams.html',
                                  context_instance=RequestContext(request))

    if request.method == 'POST':
        form = SetPasswordPolicyForm(user, request.POST)
        if form.is_valid():
            form.save()
            return render_to_response('account/password_change_done.html',
                                      context_instance=RequestContext(request))
    else:
        form = SetPasswordPolicyForm(user)

    return render_to_response('account/password_change.html', {'form' : form,
                              'verification_key' : verification_key, 'email_address' : email_address},
                              context_instance=RequestContext(request))


