from django import forms
from django.forms import widgets
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from PIL import Image as PILImage
from form_utils.widgets import ImageWidget

from profile.models import UserProfile, CollaborationChoice, ResearchField, SeabirdFamily
from cms.models import Listing

attrs_dict = {'class': 'required'}

class TwitterField(forms.CharField):
    def to_python(self, value):
        if value:
            return value.strip()

    def validate(self, value):
        super(TwitterField, self).validate(value)
        if value:
            if not value.startswith('@'):
                raise ValidationError('Prefix your username with @.')

            if len(value.strip().split()) > 1:
                raise ValidationError('There must be no spaces in your user name.') 

def research_field_validation(value):
    if '1' in value and len(value) > 1: # '1' is "Not a researcher"
        raise ValidationError('Do not select a research area if you are a not a researcher.')

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=75)))
    first_name = forms.CharField(label="First name", help_text='', max_length=30)
    last_name = forms.CharField(label="Last name", help_text='', max_length=30)

    # This is currently not shown in edit_profile.html template
    collaboration_choices = forms.ModelMultipleChoiceField(
            queryset=CollaborationChoice.objects.order_by("label"),
            required=False)

    # We use a CheckboxSelectMultiple widget, but we actually customise the rendering
    # since Django insists on displaying it as part of a <ul> element
    subscriptions = forms.ModelMultipleChoiceField(
            queryset=Listing.objects.filter(optional_list=True),
            required=False,
            widget=widgets.CheckboxSelectMultiple,
            )

    # We use a CheckboxSelectMultiple widget, but we actually customise the rendering
    # since Django insists on displaying it as part of a <ul> element
    seabirds = forms.ModelMultipleChoiceField(
            queryset=SeabirdFamily.objects.all(),
            required=False,
            widget=widgets.CheckboxSelectMultiple,
            )

    research_field = forms.ModelMultipleChoiceField(
        queryset=ResearchField.objects.all(),
        required=False,
        validators=[research_field_validation],
        widget=widgets.CheckboxSelectMultiple,
        )

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        try:
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
        except User.DoesNotExist:
            pass

    class Meta:
        model = UserProfile
        exclude = ('user', 'date_created', 'date_updated')
        widgets = { 'photograph': ImageWidget }


    def save(self, *args, **kwargs):
        """
        Save user and profile information
        """
        u = self.instance.user
        u.email = self.cleaned_data['email']
        u.first_name = self.cleaned_data['first_name']
        u.last_name = self.cleaned_data['last_name']
        twitter = self.cleaned_data['twitter']
        if twitter:
            u.twitter = twitter.strip()
        u.save()
        profile = super(ProfileForm, self).save(*args,**kwargs)
        return profile
