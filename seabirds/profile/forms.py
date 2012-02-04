from django import forms
from django.contrib.auth.models import User

from profile.models import UserProfile

attrs_dict = {'class': 'required'}

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.TextInput(attrs=dict(attrs_dict,
                                                               maxlength=75)))
    first_name = forms.CharField(label="First name",help_text='', max_length=30)
    last_name = forms.CharField(label="Last name",help_text='', max_length=30)
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
        exclude = ('user',)
        #widgets = { 'seabirds': forms.CheckboxSelectMultiple }

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
