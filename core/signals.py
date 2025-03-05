from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Candidate, HiringManager
from .utils.email_utils import generate_random_password, send_candidate_credentials_email
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create the appropriate profile when a user is created.
    """
    if created:
        if instance.is_hiring_manager:
            HiringManager.objects.create(user=instance, company_name="Doodle Gmbh")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save the appropriate profile when a user is updated.
    """
    # Create profile if it doesn't exist but should
    if instance.is_candidate and not hasattr(instance, 'candidate_profile'):
        Candidate.objects.create(user=instance)
    if instance.is_hiring_manager and not hasattr(instance, 'hiring_manager_profile'):
        HiringManager.objects.create(user=instance, company_name="Doodle Gmbh")

    # Update existing profiles
    if hasattr(instance, 'candidate_profile'):
        instance.candidate_profile.save()
    if hasattr(instance, 'hiring_manager_profile'):
        instance.hiring_manager_profile.save()