import logging
import re

from django.template.loader import render_to_string
from markdown import markdown

log = logging.getLogger(__name__)

# Process references if bibliography module is installed
try:
    from bibliography.views import markdown_post_references
except ImportError:
    log.warning('bibliography module missing or broken')
    def markdown_post_references(text):
        return text

IMAGE_REGEX = '\[Image\s+([-\w]+)(\s+\w[\w=%\'" -]+)?\s*\](.*)(?=</p>)'

def _insert_references(m, check):
    try:
        # TODO: listview doesn't exist, what is the idea behind it?
        # Is it django.views.generic.list.ListView or something else?
        return listview(None, query=m.group(1))
    except:
        if check: raise 
        return ""

def _insert_file(m, check):
    try:
        from cms.models import File
        file = File.objects.get(name=m.group(1))
        return file.html()
    except:
        if check: raise 
        return ""

def markdownplus(text, check=False):
    text = markdown(text)
    def insert_image(m):
        try:
            from cms.models import Image
            image = Image.objects.get(key=m.group(1))
            try:
                width = int(re.findall('width=([\d]+)', m.group(2))[0])
            except:
                width = None
            try:
                height = int(re.findall('height=([\d]+)', m.group(2))[0])
            except:
                height = None
            try:
                place = re.findall('place=([\w]+)', m.group(2))[0]
            except:
                place = ''
            width, height = image.get_dimensions(width, height)
            url = image.get_qualified_url(width, height)
            if place.upper().startswith('R'):
                place = 'float-right'
            elif place.upper().startswith('L'):
                place = 'float-left'
            else:
                place = 'center'
            caption = m.group(3)
            if not caption:
                caption = image.caption
            return render_to_string('image/plain.html',
                    dict(image=image, width=width, place=place, url=url, caption=caption))
        except:
            if check: 
                raise
            return m.group(0) 
    text = re.sub(IMAGE_REGEX, insert_image,  text)

    text = re.sub('\[References\s+(\w[\w=\'" -]+)\]', _insert_references, text)
    return text

    text = re.sub('\[File\s+(\w+)\]', _insert_file, text) 

    text = markdown_post_references(text)
    return text
