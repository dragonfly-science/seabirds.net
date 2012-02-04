from django.contrib.auth.models import User
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import RequestSite
from django.contrib.sites.models import Site
from django.template.defaultfilters import slugify
from captcha.fields import  ReCaptchaField

from registration import signals
from registration.forms import RegistrationForm
from registration.models import RegistrationProfile
from registration.backends.default import DefaultBackend

from profile.forms import ProfileForm

attrs_dict = {'class': 'required'}


class ProfileRegistrationForm(ProfileForm):
    """
    Form for registering a new user account.

    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.
    """
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict,
            render_value=False),
        label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict,
            render_value=False),
        label=_("Password (again)"))
    captcha = ReCaptchaField(attrs={'theme' : 'clean'})
 
    def clean_username(self):
        """
        Construct the username out of the firstname and the lastname, 
        """
        first = self.cleaned_data['first_name']
        last = self.cleaned_data['last_name']
        user = slugify('%s %s' % (first, last))[:30].rstrip('-').lower()
        try:
            u = User.objects.get(username__iexact=user)
        except User.DoesNotExist:
            user_root = user[:26]
            if user_root.endswith('-'):
                suffix_join = ''
            else:
                suffix_join = '-'
            for suffix in range(2, 999):
                try:
                    user = '%s%s%s'%(user_root, suffix_join, suffix)
                    u = User.objects.get(username__iexact=user)
                    break
                except:
                    pass        
        return user

    def clean(self):
        """
        Verify that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data

    def clean_email(self):
        """
        We require a unique email address
        """
        email = self.cleaned_data['email']
        try:
            u = User.objects.get(email=email)
            raise forms.ValidationError(_("A user with that email already exists, have you tried logging in to the website?"))
        except:
            return email


class ProfileBackend(DefaultBackend):
    def register(self, request, **kwargs):
        username, email, password = kwargs['username'], kwargs['email'], kwargs['password1']
        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)
        new_user = RegistrationProfile.objects.create_inactive_user(username, email,                                                            password, site)
        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)

        u = User.objects.get(username=new_user.username)
        u.first_name = kwargs['first_name']
        u.last_name = kwargs['last_name']
        u.save() 
    
        return new_user
    
    def get_form_class(self, request):
        """
        Return the default form class used for user registration.
        
        """
        return ProfileRegistrationForm
