from django.core.management.base import BaseCommand
from core.models import Session

class Command(BaseCommand):
    help = 'Sets the specified session as the current session'

    def add_arguments(self, parser):
        parser.add_argument('session_name', type=str, help='Name of the session to set as current')

    def handle(self, *args, **options):
        session_name = options['session_name']
        
        # First, unset any current session
        Session.objects.filter(is_current_session=True).update(is_current_session=False)
        
        try:
            # Set the specified session as current
            session = Session.objects.get(session=session_name)
            session.is_current_session = True
            session.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully set "{session_name}" as the current session'))
        except Session.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Session "{session_name}" does not exist')) 