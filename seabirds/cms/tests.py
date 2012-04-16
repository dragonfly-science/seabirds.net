from datetime import datetime

from django.utils.unittest import TestCase
from django.test.client import Client
from django.template.defaultfilters import slugify

from categories.models import SeabirdFamily
from cms.models import Page, Post, Navigation


class TestPages(TestCase):
    def setUp(self):
        self.client = Client()
        try:
            Page.objects.get(name='home')
        except Page.DoesNotExist:
            home = Page(name='home', title='home')
            home.save()

    def test_page_absolute_url(self):
        home = Page.objects.get(name='home')
        self.assertEqual(home.get_absolute_url(), '/home.html')

    def test_index(self):
        response = self.client.get('/index.html')
        self.assertEqual(response.status_code, 302)

    def test_home(self):
        response = self.client.get('/home.html')
        self.assertEqual(response.status_code, 302)
    
    def test_posts(self):
        response = self.client.get('/posts/')
        self.assertEqual(response.status_code, 200)

class TestJobs(TestCase):
    def setUp(self):
        self.client = Client()

    def test_redirect(self):
        response = self.client.get('/jobs/', follow=True)
        assert response.redirect_chain[-1] == ('/jobs/?max_days_since_creation=90', 302)


class TestGallery(TestCase):
    def setUp(self):
        self.client = Client()

    def test_gallery_url(self):
        r = self.client.get('/gallery')
        assert r.status_code == 200

    def test_seabird_families_urls(self):
        for s in SeabirdFamily.objects.all():
            r = self.client.get('/gallery/' + slugify(str(s)))
            assert r.status_code == 200

    def test_can_add_image(self):
        self.client.('/')