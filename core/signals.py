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
        if instance.is_candidate:
            # Generate a secure random password if one wasn't set
            if not instance.has_usable_password():
                password = generate_random_password()
                instance.set_password(password)
                # Store the generated password temporarily for the email
                # This is safe since we're in the same process and this is only
                # available during this operation
                temp_password = password
                instance.save()  # Save the password to the user
            else:
                temp_password = None  # Password was already set

            # Create the candidate profile
            candidate = Candidate.objects.create(user=instance)

            # Store the generated password securely for first-time login verification
            # Note: In production, you might want to use a more secure approach
            if temp_password:
                candidate.generated_password = temp_password  # We're storing this temporarily
                candidate.save()

                # Send the credentials email
                send_candidate_credentials_email(
                    candidate_email=instance.email,
                    candidate_password=temp_password,
                    candidate_name=instance.full_name
                )
                logger.info(f"Created candidate account for {instance.email} and sent credentials")

        if instance.is_hiring_manager:
            HiringManager.objects.create(user=instance, company_name="Default Company Name")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save the appropriate profile when a user is updated.
    """
    # Create profile if it doesn't exist but should
    if instance.is_candidate and not hasattr(instance, 'candidate_profile'):
        Candidate.objects.create(user=instance)
    if instance.is_hiring_manager and not hasattr(instance, 'hiring_manager_profile'):
        HiringManager.objects.create(user=instance, company_name="Default Company Name")

    # Update existing profiles
    if hasattr(instance, 'candidate_profile'):
        instance.candidate_profile.save()
    if hasattr(instance, 'hiring_manager_profile'):
        instance.hiring_manager_profile.save()