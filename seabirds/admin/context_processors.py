from django.conf import settings

import socket
from django.conf import settings

def whereami(request):
    return {'database_host':  "%s on %s" % (settings.SITE_NAME, socket.gethostname()),
            'site_url': settings.SITE_URL}

