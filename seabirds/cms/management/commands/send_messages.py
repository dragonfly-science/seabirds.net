from django.core.management.base import BaseCommand
from pigeonpost.tasks import send_email

class Command(BaseCommand):
    help = "Sends any pending emails"

    def handle(self, *args, **options):
        send_email()
