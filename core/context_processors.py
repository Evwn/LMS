from datetime import datetime
from .models import Session

def session_progress(request):
    """
    Context processor to provide session progress data to all templates.
    Uses the Session model methods to calculate progress.
    """
    current_session = Session.objects.filter(is_current_session=True).first()
    
    if not current_session:
        return {
            'current_session': None,
            'session_progress': 0,
            'session_days_remaining': 0,
            'session_total_days': 0,
        }
    
    return {
        'current_session': current_session,
        'session_progress': current_session.get_progress(),
        'session_days_remaining': current_session.get_days_remaining(),
        'session_total_days': 0,  # Keeping this for backward compatibility
    } 