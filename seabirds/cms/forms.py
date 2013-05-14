from django import forms

from form_utils.widgets import ImageWidget

from cms.models import Post, Image, Listing

class PostForm(forms.ModelForm):
    """ Form for creating a post """
    
    listing = forms.ModelChoiceField(queryset=Listing.objects.none(), empty_label=None)

    def __init__(self, user, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        # This is not ideal because we need to convert a list into a queryset.
        # Not sure how to tell a form to just use a list instead.
        listings = Listing.objects.user_postable(user)
        self.fields['listing'].queryset = Listing.objects.filter(id__in=[l.id for l in listings])
    
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
