from django.db import models

class SeabirdFamily(models.Model):
    choice = models.CharField(max_length=60)
    family = models.CharField(max_length=60)

    def __str__(self):
        return self.choice

    class Meta:
        ordering = ('choice',)

class InstitutionType(models.Model):
    choice = models.CharField(max_length=60)
    
    def __str__(self):
        return self.choice

class RoleType(models.Model):
    choice = models.CharField(max_length=60)
    
    def __str__(self):
        return self.choice

class ResearchField(models.Model):
    choice = models.CharField(max_length=60)

    def __unicode__(self):
        return self.choice

