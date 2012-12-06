from django import forms

from form_utils.widgets import ImageWidget

from cms.models import Post, Image, Listing

class PostForm(forms.ModelForm):
    """ Form for creating a post """
    
    listing = forms.ModelChoiceField(queryset=Listing.objects.none(), empty_label=None)

    def __init__(self, user, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        if user.is_staff:
            self.fields['listing'].queryset = Listing.objects.all()
        else:
            self.fields['listing'].queryset = Listing.objects.filter(staff_only_write = False)
    
    class Meta:
        model = Post
        exclude = ('author', 'name', 'date_published', 'published', 'image',
                'date_created', 'date_updated', 'enable_comments',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 27}),
            }

class ImageForm(forms.ModelForm):
    """ Form for creating a post """

    source_url = forms.URLField(required = False, 
        help_text="Optional. A url used to link to the original image (e.g. http://www.flickr.com/picture.png).")
    owner_url = forms.URLField(required = False,
        help_text="Optional. A url linking to a website giving more information on the copyright owner (e.g., http://www.people.com/mr-nice.html)")

    class Meta:
        model = Image
        exclude = ('key', 'uploaded_by', 'date_created', 'date_updated')
        widgets = {
            'image': ImageWidget(),
            }

class SimpleComment(forms.Form):
    comment = forms.CharField(
        widget=forms.Textarea,
        help_text='Comment text. Formatted using <a href="http://daringfireball.net/projects/markdown/syntax">markdown</a>')
    id = forms.IntegerField(required=True)
