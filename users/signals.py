from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AuthUser, UserSettings


@receiver(post_save, sender=AuthUser)
def create_user_settings(sender, instance, created, **kwargs):
    print("signal---")
    if created:
        UserSettings.objects.create(user=instance)