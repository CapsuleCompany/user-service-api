from celery import shared_task
from django.utils.timezone import now
from users.models import UserSession


@shared_task
def clean_expired_sessions():
    """Delete all expired user sessions."""
    print("celery cleanup")
    UserSession.objects.filter(expires_at__lt=now()).delete()