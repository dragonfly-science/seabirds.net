import urllib
from hashlib import sha256

import logging

from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.urlresolvers import reverse

import settings

MIN_PASSWORD_LENGTH = 6

def password_reset_key(user):
    return sha256(user.username + user.password).hexdigest()


def policy_compliant_password(username, password):
    if password:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise forms.ValidationError("Passwords must contain at least %s characters" % MIN_PASSWORD_LENGTH)
        if username == password:
            raise forms.ValidationError("Password needs to be different from the username")
        # TODO: password needs to contain at least one alpha character?
        # TODO: password needs to contain at least one digit?
    return password

# http://djangosnippets.org/snippets/956/
def autostrip(cls):
    fields = [(key, value) for key, value in cls.base_fields.iteritems() if isinstance(value, forms.CharField)]
    for field_name, field_object in fields:
        def get_clean_func(original_clean):
            return lambda value: original_clean(value and value.strip())
        clean_func = get_clean_func(getattr(field_object, 'clean'))
        setattr(field_object, 'clean', clean_func)
    return cls

class SetPasswordPolicyForm(SetPasswordForm):
    '''
    Same as the built-in form but with a password policy.
    '''
    def clean_new_password1(self):
        return policy_compliant_password(self.user.username, self.cleaned_data['new_password1'])

@autostrip
class PasswordResetForm(forms.Form):
    email = forms.EmailField(label="Email address")

    def save(self):
        if not self.cleaned_data['email']:
            return False

        try:
            user = User.objects.get(email=self.cleaned_data['email'])
        except User.DoesNotExist:
            return False

        email_address = user.email
        key = password_reset_key(user)

        link = settings.SITE_URL + reverse('account.views.password_reset_confirm')
        link += '?verification_key=%s&email_address=%s' % (key, urllib.quote_plus(email_address))

        email_subject = 'Password reset for %s' % settings.SITE_NAME
        email_body = """Someone, probably you, requested a password reset for your
%(site_name)s account.

If that's what you want, please go to the following page:

  %(reset_link)s

Otherwise, please accept our apologies and ignore this message.

- The %(site_name)s accounts team
""" % {'reset_link' : link, 'site_name' : settings.SITE_NAME }

        send_mail(email_subject, email_body, settings.FROM_ADDRESS, [email_address])

        return True

