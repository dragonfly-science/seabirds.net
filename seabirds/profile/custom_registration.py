from django.contrib.auth.models import User, check_password
from django.contrib.auth.backends import ModelBackend
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
from passwords.fields import PasswordField

from profile.forms import ProfileForm
from profile.models import UserProfile

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
    password1 = PasswordField(label=_("Password"))
    password2 = PasswordField(label=_("Password (again)"))
    captcha = ReCaptchaField(attrs={'theme' : 'clean'})
 
    def get_username(self):
        """
        Construct the username out of the firstname and the lastname, 
        """
        first = self.cleaned_data['first_name']
        last = self.cleaned_data['last_name']
        user = slugify('%s %s' % (first, last))[:30].rstrip('-').lower()
        try:
            u = User.objects.get(username__iexact=user)
            user_root = user[:26]
            if user_root.endswith('-'):
                suffix_join = ''
            else:
                suffix_join = '-'
            for suffix in range(2, 1000):
                try:
                    user = '%s%s%s'%(user_root, suffix_join, suffix)
                    u = User.objects.get(username__iexact=user)
                except:
                    break
        except User.DoesNotExist:
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
        self.cleaned_data['username'] = self.get_username()
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

        user = User.objects.get(username=new_user.username)
        user.first_name = kwargs['first_name']
        user.last_name = kwargs['last_name']
        user.save() 
        # Create profile
        profile = UserProfile.objects.get(user = user)
        for key, value in kwargs.items():
            if hasattr(profile, key):
                profile.__setattr__(key, value)
        profile.save()

        return new_user
    
    def get_form_class(self, request):
        """
        Return the default form class used for user registration.
        
        """
        return ProfileRegistrationForm


class EmailAuthBackend(ModelBackend):
    """Allow a user to login with their email address"""
    def authenticate(self, username=None, password=None):
        if not username or not password:
            return None
        possibles = User.objects.filter(email__istartswith=username)
        for possible in possibles:
            if username[:30].lower() == possible.email.lower() and \
                check_password(password, possible.password):
                return possible
        return None
