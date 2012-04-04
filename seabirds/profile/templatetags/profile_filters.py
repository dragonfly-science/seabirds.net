from django import template

register = template.Library()

@register.filter
def twitter(value):
    return value.replace('@', '').strip()


