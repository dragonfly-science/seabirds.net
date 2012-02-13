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
        exclude = ('author',)

class ImageForm(forms.ModelForm):
    "Form for creating a post"
    source_url = forms.URLField(required = False, 
        help_text="Optional. A url used to link to the original image (e.g. http://www.flickr.com/picture.png).")

    owner_url = forms.URLField(required = False,
        help_text="Optional. A url linking to a website giving more information on the copyright owner (e.g., http://www.people.com/mr-nice.html)")

    def clean_title(self):
        if not self.cleaned_data.get('title', None):
            raise ValidationError, 'Title must not be empty'
        else:
            key = slugify(title)
            try:
                Image.objects.get(key=key)
            except Image.DoesNotExist:
                count = 1
                while True:
                    newkey = '%s-%s'%(key, count)
                    try:
                        Image.objects.get(key=newkey)
                        count += 1
                    except Image.DoesNotExist:
                        key = newkey
                        break
                self.cleaned_data['key'] = key

    class Meta:
        model = Image
        exclude = ('key', 'uploaded_by')
