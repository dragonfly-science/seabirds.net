from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def get_first_available_label(model, start_name, field, iexact=False):
    """ Check for the first free label on [model].[field]
    
    If 'test-name' is the start_name, it will iterate and check variants like
    test-name-1, test-name-2 etc. until no instance of [model] is found with
    [label] == 'test-name-X'.

    This is often a pattern when generating post slugs, or usernames...
    but it can be tricky to get correct if it has to be reimplemented
    everytime it's needed.
    """
    try:
        name = start_name
        field_lookup = field
        if iexact:
            field_lookup += '__iexact'
        model.objects.get(**{field_lookup:name})
        count = 0
        max_length = model._meta.get_field(field).max_length
        while True:
            count += 1
            name = start_name[:(max_length - 1 - len(str(count)))]
            name.rstrip('-') # in case the last character is '-' to avoid e.g. '--2'
            name += ('-' + str(count))
            model.objects.get(**{field_lookup:name})
            if count > 1000:
                raise ValueError("More than 1000 %s instances with %s based off of %s" % (
                        model.__name__, field, start_name))
    except model.DoesNotExist:
        # When we get here we know that field==name does not exist for model.
        pass
    return name

def generate_email(to_user, subject, template_data, text_template, html_template):
    """ Create an email with html and text versions.

    Note that the same template_data is used for both rendering the text and html
    versions of the email.
    """
    from django.contrib.sites.models import Site
    current_site = Site.objects.get_current()
    template_data = dict(template_data)
    template_data['site'] = current_site
    # First generate the text version
    body = render_to_string(text_template, template_data)
    msg = EmailMultiAlternatives(subject, body, to=[to_user.email])

    # Then generate the html version with rendered markdown
    html_content = render_to_string(html_template, template_data)
    msg.attach_alternative(html_content, "text/html")
    return msg

def perm_to_code(permission):
    """ Django's has_perm forces you to pass a string instead of a permissions object """
    ct, name = (permission.content_type.app_label, permission.codename)
    return "%s.%s" % (ct, name)
