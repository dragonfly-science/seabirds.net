from django.db import models

class License(models.Model):
    name = models.CharField(max_length = 50)
    description = models.CharField(max_length = 200)
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length = 200)
    symbol =  models.ImageField(upload_to="images")

    def __str__(self):
        return "%s (%s)"%(self.description, self.name)
