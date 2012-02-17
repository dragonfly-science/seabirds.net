from django import forms
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError

from form_utils.widgets import ImageWidget

from cms.models import Post, Image

class PostForm(forms.ModelForm):
    "Form for creating a post"
    
    class Meta:
        model = Post
        exclude = ('author', 'name', 'date_published', 'published', 'image', 'retracted')
        widgets = {
            'teaser': forms.Textarea(attrs={'rows': 6}),
            'text': forms.Textarea(attrs={'rows': 27}),
            }

class ImageForm(forms.ModelForm):
    "Form for creating a post"
    source_url = forms.URLField(required = False, 
        help_text="Optional. A url used to link to the original image (e.g. http://www.flickr.com/picture.png).")

    owner_url = forms.URLField(required = False,
        help_text="Optional. A url linking to a website giving more information on the copyright owner (e.g., http://www.people.com/mr-nice.html)")


    class Meta:
        model = Image
        exclude = ('key', 'uploaded_by')

