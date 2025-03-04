import random
import string
from django.core.mail import send_mail
from django.conf import settings
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


def generate_random_password(length=12):
    """
    Generate a secure random password with the specified length
    that includes lowercase, uppercase, digits, and special characters.
    """
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = '!@#$%^&*()-_=+[]{}|;:,.<>?'

    # Ensure at least one character from each category
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(special_chars)
    ]

    # Fill the rest of the password with random characters from all categories
    all_chars = lowercase + uppercase + digits + special_chars
    password.extend(random.choice(all_chars) for _ in range(length - 4))

    # Shuffle the password characters to avoid predictable patterns
    random.shuffle(password)

    return ''.join(password)


def send_candidate_credentials_email(candidate_email, candidate_password, candidate_name=None):
    """
    Send an email with login credentials to a newly created candidate.

    Parameters:
    - candidate_email: Email address of the candidate (also used as login)
    - candidate_password: Auto-generated password for the candidate
    - candidate_name: Optional name of the candidate for personalization

    Returns:
    - Boolean indicating if the email was sent successfully
    """
    subject = "Your Recruiter Platform Credentials"

    greeting = f"Hello {candidate_name}," if candidate_name else "Hello,"

    message = f"""
{greeting}

Your account has been created on the Recruiter Platform. Please find your login details below:

Email: {candidate_email}
Password: {candidate_password}

Please login at: {settings.SITE_URL}/candidate-login/

For security reasons, we recommend changing your password after your first login.

Thank you,
The Recruiter Platform Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[candidate_email],
            fail_silently=False,
            auth_user=settings.EMAIL_HOST_USER,
            auth_password=settings.EMAIL_HOST_PASSWORD,
        )
        logger.info(f"Credentials email sent to candidate: {candidate_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send credentials email to {candidate_email}: {str(e)}")
        return False


def send_assessment_invitation_email(assessment):
    """
    Send an assessment invitation email to a candidate.

    Parameters:
    - assessment: Assessment object with candidate and details

    Returns:
    - Boolean indicating if the email was sent successfully
    """
    subject = "Your Coding Assessment Invitation"

    candidate_email = assessment.candidate.user.email
    candidate_name = assessment.candidate.user.full_name or "Candidate"

    message = f"""
Hello {candidate_name},

You have been invited to complete a coding assessment as part of your application process.

Assessment details:
- Title: {assessment.title}
- Time limit: {assessment.time_limit_minutes} minutes
- Expiry: The assessment link will expire in 7 days

Please click the link below to start your assessment:
{settings.SITE_URL}/candidate-assessment/{assessment.id}/

Note: Once you start the assessment, you will need to complete it within the time limit.

Good luck!
The Recruiter Platform Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[candidate_email],
            fail_silently=False,
            auth_user=settings.EMAIL_HOST_USER,
            auth_password=settings.EMAIL_HOST_PASSWORD,
        )
        logger.info(f"Assessment invitation sent to candidate: {candidate_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send assessment invitation to {candidate_email}: {str(e)}")
        return False


def send_assessment_acceptance_email(assessment):
    """
    Send an email confirming assessment acceptance and providing the start link.

    Parameters:
    - assessment: Assessment object with candidate and details

    Returns:
    - Boolean indicating if the email was sent successfully
    """
    subject = "Your Assessment is Ready to Start"

    candidate_email = assessment.candidate.user.email
    candidate_name = assessment.candidate.user.full_name or "Candidate"

    message = f"""
Hello {candidate_name},

Thank you for accepting the coding assessment invitation. You can now start your assessment when you're ready.

Important information:
- Title: {assessment.title}
- Once you start, you'll have 24 hours to complete and submit your work
- This link will expire on: {assessment.invite_expires_at.strftime('%Y-%m-%d %H:%M UTC')}

Click the link below to begin your assessment:
{settings.SITE_URL}/candidate/assessment/start/{assessment.assessment_url_token}/

Please ensure you have a stable internet connection and enough uninterrupted time to complete the assessment.

Best of luck!
The Recruiter Platform Team
"""

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[candidate_email],
            fail_silently=False,
            auth_user=settings.EMAIL_HOST_USER,
            auth_password=settings.EMAIL_HOST_PASSWORD,
        )
        logger.info(f"Assessment start link sent to candidate: {candidate_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send assessment start link to {candidate_email}: {str(e)}")
        return False


def send_interview_invitation_email(candidate, interview_date):
    """
    Send an interview invitation email to a candidate.

    Args:
        candidate: The Candidate model instance
        interview_date: The scheduled interview date
    """
    subject = "Interview Invitation - Next Steps in Your Application"

    context = {
        'candidate_name': candidate.user.get_full_name() or candidate.user.email,
        'interview_date': interview_date,
        'company_name': candidate.assessment_set.first().created_by.company_name if candidate.assessment_set.exists() else "Our Company",
        'contact_email': settings.DEFAULT_FROM_EMAIL,
    }

    html_message = render_to_string('emails/interview_invitation.html', context)
    plain_message = render_to_string('emails/interview_invitation_plain.txt', context)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[candidate.user.email],
        html_message=html_message,
        fail_silently=False,
        auth_user=settings.EMAIL_HOST_USER,
        auth_password=settings.EMAIL_HOST_PASSWORD,
    )

    return True


def send_rejection_email(candidate):
    """
    Send a rejection email to a candidate.

    Args:
        candidate: The Candidate model instance
    """
    subject = "Update on Your Application"

    context = {
        'candidate_name': candidate.user.get_full_name() or candidate.user.email,
        'company_name': candidate.assessment_set.first().created_by.company_name if candidate.assessment_set.exists() else "Our Company",
        'contact_email': settings.DEFAULT_FROM_EMAIL,
    }

    html_message = render_to_string('emails/rejection_notice.html', context)
    plain_message = render_to_string('emails/rejection_notice_plain.txt', context)

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[candidate.user.email],
        html_message=html_message,
        fail_silently=False,
        auth_user=settings.EMAIL_HOST_USER,
        auth_password=settings.EMAIL_HOST_PASSWORD,
    )

    return True