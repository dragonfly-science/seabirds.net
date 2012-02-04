from django.contrib.auth.models import User
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import RequestSite
from django.contrib.sites.models import Site

from registration import signals
from registration.forms import RegistrationForm
from registration.models import RegistrationProfile


from registration.backends.default import DefaultBackend

attrs_dict = {'class': 'required'}

class ProfileRegistrationForm(forms.Form):
    """
    Form for registering a new user account.
    
    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    
    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.
    
    """
    username = forms.RegexField(regex=r'^[\w.@+-]+$',
                                max_length=30,
                                widget=forms.TextInput(attrs=attrs_dict),
                                label=_("Username"),
                                error_messages={'invalid': _("This value must contain only letters, numbers and underscores.")})
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)),
                             label=_("E-mail"))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=attrs_dict, render_value=False),
                                label=_("Password (again)"))
    
    first_name = forms.CharField(label="First name",help_text='', max_length=30)
    last_name = forms.CharField(label="Last name",help_text='', max_length=30)
    
    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        
        """
        try:
            user = User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']
        raise forms.ValidationError(_("A user with that username already exists."))

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
