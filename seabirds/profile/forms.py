from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from PIL import Image as PILImage
from form_utils.widgets import ImageWidget

from profile.models import UserProfile, CollaborationChoice

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

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict, maxlength=75)))
    first_name = forms.CharField(label="First name",help_text='', max_length=30)
    last_name = forms.CharField(label="Last name",help_text='', max_length=30)
    twitter = TwitterField(label="Twitter user name", max_length=15)
    collaboration_choices = forms.ModelMultipleChoiceField(queryset=CollaborationChoice.objects.order_by("label"), required=False)

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

#    def clean_image(self):
#        image = self.cleaned_data.get('image', False)
#        if image:
#            if image._size > 4*1024*1024: #4MB size limit
#                raise ValidationError("Image file too large (must be less than 4MB)")
#            else:
#                return image

    def save(self, *args, **kwargs):
        """
        Save user and profile information
        """
        u = self.instance.user
        u.email = self.cleaned_data['email']
        u.first_name = self.cleaned_data['first_name']
        u.last_name = self.cleaned_data['last_name']
        u.save()
        profile = super(ProfileForm, self).save(*args,**kwargs)
        return profile
