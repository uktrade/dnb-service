from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from rest_framework.authtoken.models import Token

from user.models import User


class Command(BaseCommand):
    help = """
    Creates a usable auth token for rest framework token auth if DEBUG=True.
    This is used when bringing up docker copies to avoid the onerous task of
    recreating a Token DB record each time the database is wiped.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'dev_auth_email',
            type=str,
            help='The email for the user to create for our dev auth token.',
        )
        parser.add_argument('dev_auth_token', type=str, help='The token to use for our dev auth token.')

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("DEBUG is not set to True, exiting.")

        dev_user, _ = User.objects.get_or_create(email=options['dev_auth_email'])
        _, created = Token.objects.get_or_create(user=dev_user, key=options['dev_auth_token'])
        if created:
            self.stdout.write(self.style.SUCCESS(f'Successfully created auth token "{options["dev_auth_token"]}"'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing auth token "{options["dev_auth_token"]}"'))
