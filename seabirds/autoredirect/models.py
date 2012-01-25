
from django.core.signals import post_save, pre_delete
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver

@receiver(post_save)
def post_save(sender, **kwargs):
    try:
        url = sender.get_absolute_url()
        content_type = ContentType.objects.get_for_model(sender)



class URLRedirect(models.Model):
   url = models.TextField()
   updated = models.ForeignKey('URLRedirect', null = True, blank = True)


